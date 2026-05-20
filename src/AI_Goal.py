import numpy as np
import math
import json
import os
import random

AI_CONFIG = {
    "MIN_CURVE_LENGTH": 3,
    "INTERSECTION_MIN_NEIGHBORS": 3,
    "LEARNING_RATE": 0.01,
    "EPOCHS": 1000,
    "WEIGHTS_FILE": "cnn_grid_weights_v2.json",
    "NUM_FILTERS": 8,
    "NUM_CLASSES": 7
}


class TrainableGridCNN:
    def __init__(self, cfg):
        self.cfg = cfg
        self.num_filters = cfg["NUM_FILTERS"]
        self.num_classes = cfg["NUM_CLASSES"]

        self.conv_out_h = 3
        self.conv_out_w = 4

        self.cnn_flat_size = self.num_filters * self.conv_out_h * self.conv_out_w
        self.orig_flat_size = 4 * 5
        self.flat_size = self.cnn_flat_size + self.orig_flat_size

        self.W_conv = np.random.randn(self.num_filters, 2, 2) * np.sqrt(2.0 / 4.0)
        self.b_conv = np.zeros(self.num_filters)

        self.W_dense = np.random.randn(self.flat_size, self.num_classes) * np.sqrt(2.0 / self.flat_size)
        self.b_dense = np.zeros(self.num_classes)

        self.classes = [
            "empty", "isolated point", "horizontal_line",
            "vertical_line", "diagonal_line", "intersection/cross", "curve"
        ]

    def relu(self, x):
        return np.maximum(0, x)

    def relu_derivative(self, x):
        return (x > 0).astype(float)

    def softmax(self, x):
        exp_x = np.exp(x - np.max(x))
        return exp_x / np.sum(exp_x)

    def forward(self, x):
        self.x_input = x
        self.conv_out = np.zeros((self.num_filters, self.conv_out_h, self.conv_out_w))

        for f in range(self.num_filters):
            for r in range(self.conv_out_h):
                for c in range(self.conv_out_w):
                    window = x[r:r + 2, c:c + 2]
                    self.conv_out[f, r, c] = np.sum(window * self.W_conv[f]) + self.b_conv[f]

        self.act_out = self.relu(self.conv_out)

        cnn_features = self.act_out.flatten()
        orig_features = self.x_input.flatten()
        self.flat = np.concatenate([cnn_features, orig_features])

        self.z_dense = np.dot(self.flat, self.W_dense) + self.b_dense
        self.probs = self.softmax(self.z_dense)
        return self.probs

    def backward(self, y_true, lr):
        dz_dense = self.probs - y_true
        dW_dense = np.outer(self.flat, dz_dense)
        db_dense = dz_dense

        d_flat = np.dot(self.W_dense, dz_dense)

        d_cnn_flat = d_flat[:self.cnn_flat_size]
        d_act_out = d_cnn_flat.reshape((self.num_filters, self.conv_out_h, self.conv_out_w))
        d_conv_out = d_act_out * self.relu_derivative(self.conv_out)

        dW_conv = np.zeros_like(self.W_conv)
        db_conv = np.zeros_like(self.b_conv)

        for f in range(self.num_filters):
            db_conv[f] = np.sum(d_conv_out[f])
            for r in range(self.conv_out_h):
                for c in range(self.conv_out_w):
                    window = self.x_input[r:r + 2, c:c + 2]
                    dW_conv[f] += d_conv_out[f, r, c] * window

        self.W_dense -= lr * dW_dense
        self.b_dense -= lr * db_dense
        self.W_conv -= lr * dW_conv
        self.b_conv -= lr * db_conv

        return -np.sum(y_true * np.log(self.probs + 1e-15))

    def train(self, X_train, y_train_labels, epochs=1000, lr=0.01):
        num_samples = len(y_train_labels)
        for epoch in range(epochs):
            total_loss = 0.0
            for idx in range(num_samples):
                x = np.array(X_train[idx], dtype=float)
                y_true = np.zeros(self.num_classes)
                class_idx = self.classes.index(y_train_labels[idx])
                y_true[class_idx] = 1.0

                self.forward(x)
                loss = self.backward(y_true, lr)
                total_loss += loss

            if epoch % 200 == 0:
                print(f"CNN Training -> Epoch {epoch:04d}/{epochs} | Avg Loss: {total_loss / num_samples:.4f}")

    def save_weights(self, filepath):
        data = {
            "W_conv": self.W_conv.tolist(), "b_conv": self.b_conv.tolist(),
            "W_dense": self.W_dense.tolist(), "b_dense": self.b_dense.tolist(),
            "classes": self.classes
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)

    def load_weights(self, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            self.W_conv = np.array(data["W_conv"])
            self.b_conv = np.array(data["b_conv"])
            self.W_dense = np.array(data["W_dense"])
            self.b_dense = np.array(data["b_dense"])
            return True
        return False


class ParametricGridEngine:
    def __init__(self, config):
        self.cfg = config
        self.cnn = TrainableGridCNN(config)
        self.trained = self.cnn.load_weights(self.cfg["WEIGHTS_FILE"])

    def train_classifier(self, training_grids, labels):
        print("Initializing CNN Training Sequence...")
        self.cnn.train(training_grids, labels, epochs=self.cfg["EPOCHS"], lr=self.cfg["LEARNING_RATE"])
        self.cnn.save_weights(self.cfg["WEIGHTS_FILE"])
        self.trained = True
        print(f"Weights saved safely to {self.cfg['WEIGHTS_FILE']}\n")

    def get_components(self, matrix):
        visited = set()
        components = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]

        for r in range(4):
            for c in range(5):
                if matrix[r, c] and (r, c) not in visited:
                    comp = []
                    stack = [(r, c)]
                    visited.add((r, c))
                    while stack:
                        curr_r, curr_c = stack.pop()
                        comp.append((curr_r, curr_c))
                        for dr, dc in directions:
                            nr, nc = curr_r + dr, curr_c + dc
                            if 0 <= nr < 4 and 0 <= nc < 5:
                                if matrix[nr, nc] and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    stack.append((nr, nc))
                    components.append(comp)
        return components

    def analyze_topology(self, comp):
        comp_set = set(comp)
        max_deg = 0
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for r, c in comp_set:
            deg = sum(1 for dr, dc in directions if (r + dr, c + dc) in comp_set)
            if deg > max_deg: max_deg = deg
        return max_deg

    def classify(self, grid):
        matrix = np.array(grid, dtype=float)
        if matrix.shape != (4, 5):
            raise ValueError("Grid must be exactly 4x5.")

        if self.trained:
            probs = self.cnn.forward(matrix)
            cnn_prediction = self.cnn.classes[np.argmax(probs)]
            if cnn_prediction != "empty":
                return cnn_prediction

        comps = self.get_components(matrix)
        if not comps: return "empty"
        if len(comps) > 1: return "multiple disconnected shapes"
        if len(comps[0]) == 1: return "isolated point"

        max_deg = self.analyze_topology(comps[0])
        rows = [p[0] for p in comps[0]]
        cols = [p[1] for p in comps[0]]

        if max_deg >= self.cfg["INTERSECTION_MIN_NEIGHBORS"]: return "intersection/cross"
        if len(set(rows)) == 1: return "horizontal_line"
        if len(set(cols)) == 1: return "vertical_line"
        return "curve"

    def extract_lines(self, grid):
        pattern = self.classify(grid)
        matrix = np.array(grid, dtype=bool)
        points = np.argwhere(matrix)
        if len(points) == 0: return []
        pts = [tuple(p) for p in points]

        if pattern == "intersection/cross":
            mean_r = sum(p[0] for p in pts) / len(pts)
            mean_c = sum(p[1] for p in pts) / len(pts)

            dists = [(p, (p[0] - mean_r) ** 2 + (p[1] - mean_c) ** 2) for p in pts]
            dists.sort(key=lambda x: x[1], reverse=True)

            endpoints = [d[0] for d in dists[:4]]
            lines = []
            used = set()

            for i in range(len(endpoints)):
                if i in used: continue
                r1, c1 = endpoints[i]
                v1_r, v1_c = r1 - mean_r, c1 - mean_c
                best_match = None
                max_dot = 2.0

                for j in range(i + 1, len(endpoints)):
                    if j in used: continue
                    r2, c2 = endpoints[j]
                    v2_r, v2_c = r2 - mean_r, c2 - mean_c
                    len1, len2 = math.sqrt(v1_r ** 2 + v1_c ** 2), math.sqrt(v2_r ** 2 + v2_c ** 2)
                    if len1 == 0 or len2 == 0: continue

                    dot = (v1_r * v2_r + v1_c * v2_c) / (len1 * len2)
                    if dot < max_dot:
                        max_dot = dot
                        best_match = j

                if best_match is not None and max_dot < -0.5:
                    lines.append((endpoints[i], endpoints[best_match]))
                    used.update([i, best_match])
            return lines

        else:
            if len(pts) == 1: return [(pts[0], pts[0])]
            mean_r, mean_c = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
            center_pt = min(pts, key=lambda p: (p[0] - mean_r) ** 2 + (p[1] - mean_c) ** 2)
            cov_rr = sum((p[0] - mean_r) ** 2 for p in pts)
            cov_cc = sum((p[1] - mean_c) ** 2 for p in pts)
            cov_rc = sum((p[0] - mean_r) * (p[1] - mean_c) for p in pts)

            trace, det = cov_rr + cov_cc, cov_rr * cov_cc - cov_rc ** 2
            discriminant = (trace / 2) ** 2 - det
            lambda1 = trace / 2 + math.sqrt(discriminant + 1e-8) if discriminant > 0 else trace / 2

            if abs(cov_rc) > 1e-8:
                v_r, v_c = lambda1 - cov_cc, cov_rc
            else:
                v_r, v_c = (1.0, 0.0) if cov_rr > cov_cc else (0.0, 1.0)

            v_len = math.sqrt(v_r ** 2 + v_c ** 2)
            if v_len > 0: v_r, v_c = v_r / v_len, v_c / v_len

            max_proj, min_proj = -float('inf'), float('inf')
            best_p1, best_p2 = center_pt, center_pt
            for p in pts:
                proj = (p[0] - center_pt[0]) * v_r + (p[1] - center_pt[1]) * v_c
                if proj > max_proj: max_proj, best_p1 = proj, p
                if proj < min_proj: min_proj, best_p2 = proj, p
            return [(best_p1, best_p2)]


def generate_robust_training_data():
    X_train, y_train = [], []

    def add_sample(grid, label):
        X_train.append(grid)
        y_train.append(label)

    def empty_grid():
        return [[False] * 5 for _ in range(4)]

    add_sample(empty_grid(), "empty")

    for r in range(4):
        for c in range(5):
            g = empty_grid();
            g[r][c] = True
            add_sample(g, "isolated point")

    for r in range(4):
        for start_c in range(3):
            for length in range(3, 6 - start_c):
                g = empty_grid()
                for c in range(start_c, start_c + length): g[r][c] = True
                add_sample(g, "horizontal_line")

    for c in range(5):
        for start_r in range(2):
            for length in range(3, 5 - start_r):
                g = empty_grid()
                for r in range(start_r, start_r + length): g[r][c] = True
                add_sample(g, "vertical_line")

    diagonals = [[(0, 0), (1, 1), (2, 2), (3, 3)], [(0, 1), (1, 2), (2, 3), (3, 4)], [(0, 2), (1, 3), (2, 4)],
                 [(1, 0), (2, 1), (3, 2)],
                 [(3, 0), (2, 1), (1, 2), (0, 3)], [(3, 1), (2, 2), (1, 3), (0, 4)], [(3, 2), (2, 3), (1, 4)],
                 [(2, 0), (1, 1), (0, 2)]]
    for diag in diagonals:
        g = empty_grid()
        for r, c in diag: g[r][c] = True
        add_sample(g, "diagonal_line")

    cross_anchors = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
    for r, c in cross_anchors:
        g = empty_grid()
        g[r][c] = g[r - 1][c] = g[r + 1][c] = g[r][c - 1] = g[r][c + 1] = True
        add_sample(g, "intersection/cross")
        g = empty_grid()
        g[r][c] = g[r][c - 1] = g[r][c + 1] = g[r + 1][c] = True
        add_sample(g, "intersection/cross")

    for r in range(1, 3):
        for c in range(1, 4):
            g = empty_grid();
            g[r][c] = True
            if r - 1 >= 0 and c - 1 >= 0: g[r - 1][c - 1] = True
            if r - 1 >= 0 and c + 1 < 5:  g[r - 1][c + 1] = True
            if r + 1 < 4 and c - 1 >= 0:  g[r + 1][c - 1] = True
            if r + 1 < 4 and c + 1 < 5:   g[r + 1][c + 1] = True
            add_sample(g, "intersection/cross")

            g = empty_grid()
            g[r][c] = g[r][c + 1] = g[r + 1][c] = g[r + 1][c + 1] = True
            if r - 1 >= 0 and c - 1 >= 0: g[r - 1][c - 1] = True
            if r - 1 >= 0 and c + 2 < 5:  g[r - 1][c + 2] = True
            if r + 2 < 4 and c - 1 >= 0:  g[r + 2][c - 1] = True
            if r + 2 < 4 and c + 2 < 5:   g[r + 2][c + 2] = True
            add_sample(g, "intersection/cross")

    curve_anchors = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for r, c in curve_anchors:
        g = empty_grid();
        g[r][c] = g[r + 1][c] = g[r + 2][c] = g[r + 2][c + 1] = g[r + 2][c + 2] = True
        add_sample(g, "curve")
        g = empty_grid();
        g[r][c] = g[r][c + 1] = g[r + 1][c + 1] = g[r + 1][c + 2] = g[r + 2][c + 2] = True
        add_sample(g, "curve")
        g = empty_grid();
        g[r][c] = g[r + 1][c] = g[r + 1][c + 1] = g[r + 1][c + 2] = g[r][c + 2] = True
        add_sample(g, "curve")

    combined = list(zip(X_train, y_train))
    random.shuffle(combined)
    X_train, y_train = zip(*combined)
    return list(X_train), list(y_train)


if __name__ == "__main__":
    engine = ParametricGridEngine(AI_CONFIG)
    X_train, y_train = generate_robust_training_data()

    if not engine.trained:
        print(f"Generated {len(X_train)} dataset profiles.")
        engine.train_classifier(X_train, y_train)

    test_grid = [
        [True, False, False, False, False],
        [False, True, False, False, False],
        [False, False, True, False, False],
        [False, False, False, True, False]
    ]

    detected_shape = engine.classify(test_grid)
    lines = engine.extract_lines(test_grid)

    print("\n--- Evaluation Log Summary ---")
    print(f"CNN Engine Decision  : {detected_shape}")
    print(f"Calculated Fit Line(s): {lines}")