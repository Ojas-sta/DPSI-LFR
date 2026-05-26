import pygame
import math
import sys
import os
import json
import torch
import torch.nn as nn
from AI_Goal import ParametricGridEngine, AI_CONFIG

print("Loading Systems...")
engine = ParametricGridEngine(AI_CONFIG)


class RobotTransformer(nn.Module):
    def __init__(self, input_dim=22, d_model=64, nhead=4, num_layers=2):
        super(RobotTransformer, self).__init__()
        self.embedding = nn.Linear(input_dim, d_model)
        self.pos_encoder = nn.Parameter(torch.zeros(1, 10, d_model))
        encoder_layers = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)
        self.fc_out = nn.Linear(d_model, 2)

    def forward(self, x):
        seq_len = x.size(1)
        x = self.embedding(x) + self.pos_encoder[:, :seq_len, :]
        out = self.transformer(x)
        return self.fc_out(out[:, -1, :])


def load_weights(model, filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            state_dict = {k: torch.tensor(v) for k, v in json.load(f).items()}
        model.load_state_dict(state_dict)
        return True
    return False


transformer_model = RobotTransformer()
WEIGHTS_FILE = "transformer_playground_weights.json"

if not load_weights(transformer_model, WEIGHTS_FILE):
    print("WARNING: Transformer weights not found! Run the RL training script first.")

transformer_model.eval()

MAX_HISTORY = 5
history_buffer = [[0.0] * 22 for _ in range(MAX_HISTORY)]


def extract_native_vector(lines):
    if not lines: return [0.0, 0.0]
    p1, p2 = lines[0]
    dx = p2[1] - p1[1]
    dy = -(p2[0] - p1[0])
    if dy < 0:
        dx, dy = -dx, -dy
    elif dy == 0 and dx < 0:
        dx = -dx
    return [float(dx), float(dy)]


def process_with_transformer(sensor_grid):
    global history_buffer

    bool_grid = [[bool(col) for col in row] for row in sensor_grid]
    lines = engine.extract_lines(bool_grid)
    vector = extract_native_vector(lines)

    flat_grid = [float(cell) for row in sensor_grid for cell in row]
    history_buffer.append(flat_grid + vector)
    history_buffer.pop(0)

    seq_tensor = torch.tensor([history_buffer], dtype=torch.float32)
    with torch.no_grad():
        predictions = transformer_model(seq_tensor)[0]
        pred_speed = predictions[0].item()
        pred_angle_normalized = predictions[1].item()

    actual_turn = pred_angle_normalized * 180.0

    pred_speed = max(0.0, pred_speed)

    return pred_speed, actual_turn


pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Transformer AI Line Follower - Memory & Attention")
clock = pygame.time.Clock()

mode = "draw"
paths = []
last_pos = None

# Robot Physical State
rx, ry = 400.0, 600.0
heading = 90.0
smooth_steering = 0.0


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if l2 == 0: return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    return math.hypot(px - proj_x, py - proj_y)


print("\nCONTROLS:")
print("- Click and drag to draw a thick path (start on top of the blue robot).")
print("- Try drawing a DASHED line or leaving a gap to test the Transformer's memory!")
print("- Press [SPACEBAR] to release the robot.")

running = True
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and mode == "draw":
                print("\n--- SWITCHING TO AUTONOMOUS TRACKING ---")
                mode = "follow"

    if mode == "draw":
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        if mouse_buttons[0]:
            if last_pos is None:
                last_pos = mouse_pos
            else:
                paths.append((last_pos[0], last_pos[1], mouse_pos[0], mouse_pos[1]))
                last_pos = mouse_pos
        else:
            last_pos = None

    LINE_THICKNESS = 16
    for (x1, y1, x2, y2) in paths:
        pygame.draw.line(screen, (0, 0, 0), (x1, y1), (x2, y2), LINE_THICKNESS)
        pygame.draw.circle(screen, (0, 0, 0), (x1, y1), LINE_THICKNESS // 2)
        pygame.draw.circle(screen, (0, 0, 0), (x2, y2), LINE_THICKNESS // 2)

    H_rad = math.radians(heading)
    f_x = math.cos(H_rad)
    f_y = -math.sin(H_rad)

    l_x = math.cos(H_rad + math.pi / 2)
    l_y = -math.sin(H_rad + math.pi / 2)

    CELL_SIZE = 14
    SENSOR_RADIUS = 6

    sensor_data = [[0] * 5 for _ in range(4)]

    for r in range(4):
        for c in range(5):
            forward_dist = (1.5 - r) * CELL_SIZE
            left_dist = (2 - c) * CELL_SIZE

            sx = rx + (f_x * forward_dist) + (l_x * left_dist)
            sy = ry + (f_y * forward_dist) + (l_y * left_dist)

            hit = False
            for (x1, y1, x2, y2) in paths:
                if point_to_segment_dist(sx, sy, x1, y1, x2, y2) <= (LINE_THICKNESS / 2 + SENSOR_RADIUS):
                    hit = True
                    break

            if hit:
                sensor_data[r][c] = 1
                color = (0, 200, 0)
            else:
                color = (255, 0, 0)

            pygame.draw.circle(screen, color, (int(sx), int(sy)), SENSOR_RADIUS)

    if mode == "follow":

        speed, transformer_angle = process_with_transformer(sensor_data)

        if speed > 0:
            active_cols = [c for r in range(4) for c in range(5) if sensor_data[r][c] == 1]

            offset_angle = 0.0
            if active_cols:
                avg_c = sum(active_cols) / len(active_cols)
                offset_error = avg_c - 2.0
                offset_angle = offset_error * 25.0

            target_steering_angle = transformer_angle + offset_angle

            smooth_steering += (target_steering_angle - smooth_steering) * 0.65

            STEERING_SENSITIVITY = 0.15
            heading -= (smooth_steering * STEERING_SENSITIVITY)

            rx += f_x * (speed * 4.0)
            ry += f_y * (speed * 4.0)

    p1 = (rx + f_x * 20, ry + f_y * 20)  # Nose
    p2 = (rx - f_x * 10 + l_x * 14, ry - f_y * 10 + l_y * 14)  # Back Left
    p3 = (rx - f_x * 10 - l_x * 14, ry - f_y * 10 - l_y * 14)  # Back Right
    pygame.draw.polygon(screen, (0, 50, 255), [p1, p2, p3])

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
