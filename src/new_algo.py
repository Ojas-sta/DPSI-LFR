import numpy as np
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
import json
import os
from AI_Goal import ParametricGridEngine, AI_CONFIG

engine = ParametricGridEngine(AI_CONFIG)


if torch.cuda.is_available():
    DEVICE = torch.device("cuda")
    print("NVIDIA CUDA Active")
elif torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
    print("Apple Silicon MPS Active")
else:
    DEVICE = torch.device("cpu")
    print("CPU Fallback")



class VirtualPlayground:
    def __init__(self, size=250):
        self.size = size
        self.grid = np.zeros((size, size), dtype=bool)
        self.robot_x = float(size // 2)
        self.robot_y = float(size // 2)
        self.robot_heading = 0.0
        self.generate_dynamic_map()

    def generate_dynamic_map(self):
        self.grid.fill(False)
        c = self.size // 2
        thickness = random.choice([1, 2, 3])
        track_type = random.choice(["circuit", "city_grid", "sine_dash", "random_walk"])
        spawn_x, spawn_y, spawn_h = float(c), float(c), 0.0

        if track_type == "circuit":
            rx, ry = random.randint(40, 110), random.randint(40, 110)
            for angle in range(0, 360):
                x = int(c + rx * math.cos(math.radians(angle)))
                y = int(c + ry * math.sin(math.radians(angle)))
                self._draw_brush(x, y, radius=thickness)
            spawn_x, spawn_y, spawn_h = float(c + rx), float(c), 90.0

        elif track_type == "city_grid":
            num_v, num_h = random.randint(2, 4), random.randint(2, 4)
            for _ in range(num_v):
                x = random.randint(40, self.size - 40)
                for y in range(20, self.size - 20): self._draw_brush(x, y, radius=thickness)
                spawn_x = float(x)
            for _ in range(num_h):
                y = random.randint(40, self.size - 40)
                for x in range(20, self.size - 20): self._draw_brush(x, y, radius=thickness)
                spawn_y = float(y)
            spawn_h = random.choice([0.0, 90.0, 180.0, 270.0])

        elif track_type == "sine_dash":
            amp, freq = random.randint(20, 70), random.uniform(10.0, 40.0)
            is_dashed, dash_len = random.choice([True, False]), random.randint(6, 18)
            for i in range(20, self.size - 20):
                if is_dashed and (i % dash_len) < (dash_len // 2): continue
                x, y = i, int(c + amp * math.sin(i / freq))
                self._draw_brush(x, y, radius=thickness)
            spawn_x, spawn_y = 40.0, float(c + amp * math.sin(40.0 / freq))
            spawn_h = math.degrees(math.atan2(amp * math.cos(40.0 / freq) / freq, 1))

        elif track_type == "random_walk":
            cx, cy = float(c), float(c)
            angle = random.uniform(0, 360)
            spawn_x, spawn_y, spawn_h = cx, cy, angle
            for _ in range(random.randint(3, 7)):
                length = random.randint(40, 90)
                for _ in range(length):
                    cx += math.cos(math.radians(angle))
                    cy += math.sin(math.radians(angle))
                    if 15 < cx < self.size - 15 and 15 < cy < self.size - 15:
                        self._draw_brush(int(cx), int(cy), radius=thickness)
                angle += random.choice([-90, -45, 45, 90, random.uniform(-60, 60)])

        self.robot_x = spawn_x
        self.robot_y = spawn_y
        self.robot_heading = spawn_h + random.uniform(-15.0, 15.0)

    def _draw_brush(self, cx, cy, radius):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.size and 0 <= ny < self.size:
                        self.grid[ny, nx] = True

    def get_sensor_reading(self):
        sensor = np.zeros((4, 5), dtype=bool)
        for r in range(4):
            for c in range(5):
                fd, ld = 4 - r, c - 2
                rad = math.radians(self.robot_heading)
                wx = self.robot_x + fd * math.cos(rad) - ld * math.sin(rad)
                wy = self.robot_y + fd * math.sin(rad) + ld * math.cos(rad)
                iwx, iwy = int(round(wx)), int(round(wy))
                if 0 <= iwx < self.size and 0 <= iwy < self.size:
                    sensor[r, c] = self.grid[iwy, iwx]
        return sensor

    def step(self, speed, turn_angle):
        self.robot_heading += turn_angle
        rad = math.radians(self.robot_heading)
        self.robot_x += speed * math.cos(rad)
        self.robot_y += speed * math.sin(rad)



class SensorFusionWorkspace(nn.Module):
    def __init__(self, d_model=64, nhead=4):
        super(SensorFusionWorkspace, self).__init__()
        self.grid_embed = nn.Embedding(2, d_model)
        self.grid_pos = nn.Parameter(torch.randn(1, 20, d_model))
        self.vector_embed = nn.Linear(2, d_model)
        self.workspace_token = nn.Parameter(torch.randn(1, 1, d_model))

        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dropout=0.0)
        self.fusion_attention = nn.TransformerEncoder(encoder_layer, num_layers=1)

    def forward(self, grid, vector):
        B = grid.size(0)
        g_tokens = self.grid_embed(grid) + self.grid_pos
        v_token = self.vector_embed(vector).unsqueeze(1)
        w_token = self.workspace_token.expand(B, -1, -1)

        sequence = torch.cat([w_token, v_token, g_tokens], dim=1)
        fused_sequence = self.fusion_attention(sequence)
        return fused_sequence[:, 0, :]


class TemporalGlobalWorkspace(nn.Module):
    def __init__(self, d_model=64, nhead=4, seq_len=5):
        super(TemporalGlobalWorkspace, self).__init__()
        self.time_pos = nn.Parameter(torch.randn(1, seq_len, d_model))
        encoder_layers = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dropout=0.0)
        self.temporal_attention = nn.TransformerEncoder(encoder_layers, num_layers=2)

    def forward(self, x):
        x = x + self.time_pos[:, :x.size(1), :]
        return self.temporal_attention(x)


class MicroExpertTransformer(nn.Module):
    def __init__(self, d_model=64, nhead=4):
        super(MicroExpertTransformer, self).__init__()
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dropout=0.0)
        self.deep_attention = nn.TransformerEncoder(encoder_layer, num_layers=1)
        self.fc_out = nn.Linear(d_model, 2)

    def forward(self, x):
        out = self.deep_attention(x)
        return self.fc_out(out[:, -1, :])


class TaskNode(nn.Module):
    def __init__(self, d_model=64, num_micro=2):
        super(TaskNode, self).__init__()
        self.gating = nn.Sequential(
            nn.Linear(d_model, 16),
            nn.ReLU(),
            nn.Linear(16, num_micro),
            nn.Softmax(dim=-1)
        )
        self.micros = nn.ModuleList([MicroExpertTransformer(d_model) for _ in range(num_micro)])

    def forward(self, x):
        weights = self.gating(x[:, -1, :])
        expert_outputs = torch.stack([expert(x) for expert in self.micros], dim=1)
        final_out = torch.sum(expert_outputs * weights.unsqueeze(-1), dim=1)
        return final_out, weights


class MacroDomain(nn.Module):
    def __init__(self, d_model=64, num_tasks=3):
        super(MacroDomain, self).__init__()
        self.gating = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, num_tasks),
            nn.Softmax(dim=-1)
        )
        self.tasks = nn.ModuleList([TaskNode(d_model, num_micro=2) for _ in range(num_tasks)])

    def forward(self, x):
        weights = self.gating(x[:, -1, :])
        task_outputs = []
        for task in self.tasks:
            t_out, m_w = task(x)
            task_outputs.append(t_out)
        task_outputs = torch.stack(task_outputs, dim=1)
        final_out = torch.sum(task_outputs * weights.unsqueeze(-1), dim=1)
        return final_out, weights


class FractalHierarchicalMoE(nn.Module):
    def __init__(self, d_model=64, seq_len=5):
        super(FractalHierarchicalMoE, self).__init__()
        self.temporal_workspace = TemporalGlobalWorkspace(d_model, seq_len=seq_len)
        self.super_gating = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
            nn.Softmax(dim=-1)
        )
        self.normal_domain = MacroDomain(d_model, num_tasks=3)
        self.special_domain = MacroDomain(d_model, num_tasks=3)

    def forward(self, seq):
        belief_state = self.temporal_workspace(seq)
        macro_weights = self.super_gating(belief_state[:, -1, :])

        norm_out, norm_w = self.normal_domain(belief_state)
        spec_out, spec_w = self.special_domain(belief_state)

        final_output = (norm_out * macro_weights[:, 0:1]) + (spec_out * macro_weights[:, 1:2])
        return final_output, macro_weights




def extract_native_vector(lines):
    if not lines: return [0.0, 0.0]
    p1, p2 = lines[0]
    dx, dy = p2[1] - p1[1], -(p2[0] - p1[0])
    if dy < 0:
        dx, dy = -dx, -dy
    elif dy == 0 and dx < 0:
        dx = -dx
    return [float(dx), float(dy)]


def train_fractal_moe(fusion_net, hmoe_net, engine, epochs=600):
    print("\n--- Booting Fractal Workspace Training Pipeline ---")

    params = list(fusion_net.parameters()) + list(hmoe_net.parameters())
    optimizer = optim.Adam(params, lr=0.0005, weight_decay=1e-5)
    criterion = nn.SmoothL1Loss()

    playground = VirtualPlayground()
    MAX_HISTORY = 5

    for epoch in range(epochs):
        playground.generate_dynamic_map()
        latent_history = [torch.zeros(64, device=DEVICE) for _ in range(MAX_HISTORY)]
        total_loss, steps_survived, gap_frames, last_angle = 0.0, 0, 0, 0.0

        for step in range(150):
            sensor_grid = playground.get_sensor_reading().tolist()
            lines = engine.extract_lines(sensor_grid)
            vector = extract_native_vector(lines)
            flat_grid = [int(cell) for row in sensor_grid for cell in row]

            grid_t = torch.tensor([flat_grid], dtype=torch.long, device=DEVICE)
            vec_t = torch.tensor([vector], dtype=torch.float32, device=DEVICE)
            is_empty = (sum(flat_grid) == 0)

            active_cols = [c for r in range(4) for c in range(5) if sensor_grid[r][c]]
            offset_error = 0.0
            if active_cols:
                avg_c = sum(active_cols) / len(active_cols)
                offset_error = avg_c - 2.0  # Range is [-2.0 to 2.0]

            if is_empty:
                fusion_net.eval()
                with torch.no_grad():
                    latent_state = fusion_net(grid_t, vec_t).squeeze(0)
            else:
                fusion_net.train()
                latent_state = fusion_net(grid_t, vec_t).squeeze(0)

            latent_history.append(latent_state.detach() if is_empty else latent_state)
            latent_history.pop(0)
            seq_tensor = torch.stack([t.clone() if t.requires_grad else t for t in latent_history]).unsqueeze(0)

            hmoe_net.train()
            optimizer.zero_grad()
            predictions, macro_w = hmoe_net(seq_tensor)
            pred_speed, pred_angle = predictions[0][0], predictions[0][1]


            if is_empty:
                gap_frames += 1
                if gap_frames > 8:

                    ts = torch.tensor(0.0, device=DEVICE)
                    ta = torch.tensor(-pred_angle.item(), device=DEVICE)

                    loss_speed = criterion(pred_speed, ts) * 20.0
                    loss_angle = criterion(pred_angle, ta) * 50.0

                    loss = loss_speed + loss_angle
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(params, 1.0)
                    optimizer.step()
                    total_loss += loss.item()
                    break
                else:

                    ts = torch.tensor(1.0, device=DEVICE)
                    ta = torch.tensor(float(last_angle), device=DEVICE)

                    void_panic_multiplier = 2.0 * gap_frames
                    loss_speed = criterion(pred_speed, ts) * void_panic_multiplier
                    loss_angle = criterion(pred_angle, ta) * void_panic_multiplier

                    loss = loss_speed + loss_angle
                    loss.backward()
                    torch.nn.utils.clip_grad_norm_(params, 1.0)
                    optimizer.step()
                    total_loss += loss.item()
                    steps_survived += 1
                    playground.step(1.0, pred_angle.item() * 180.0)
            else:
                gap_frames = 0
                idx, idy = vector[0], max(vector[1], 0.1)
                ideal_trajectory_angle = math.degrees(math.atan2(idx, idy)) / 180.0


                centering_correction = (offset_error * 30.0) / 180.0
                target_angle_val = ideal_trajectory_angle + centering_correction
                target_angle_val = max(-1.0, min(1.0, target_angle_val))

                alignment_penalty_multiplier = 1.0 + (abs(offset_error) * 2.0)

                last_angle = target_angle_val
                ts = torch.tensor(1.0, device=DEVICE)
                ta = torch.tensor(float(target_angle_val), device=DEVICE)

                loss_speed = criterion(pred_speed, ts)
                loss_angle = criterion(pred_angle, ta) * alignment_penalty_multiplier

                loss = loss_speed + loss_angle
                loss.backward()
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                optimizer.step()
                total_loss += loss.item()
                steps_survived += 1
                playground.step(1.0, pred_angle.item() * 180.0)


            latent_history = [t.detach() for t in latent_history]

        if (epoch + 1) % 1 == 0:
            avg_err = total_loss / (steps_survived + 1)
            mw = macro_w[0].tolist()
            m_str = f"Normal: {mw[0]:.2f} | Anomaly: {mw[1]:.2f}"
            print(
                f"Epoch [{epoch + 1:04d}/{epochs}] | Survived: {steps_survived:03d} frames | Loss: {avg_err:.4f} | Priority: {m_str}")

    print("--- Fractal Architecture Fully Optimized ---\n")
    return fusion_net, hmoe_net



if __name__ == "__main__":
    workspace_fusion_model = SensorFusionWorkspace(d_model=64).to(DEVICE)
    fractal_moe_model = FractalHierarchicalMoE(d_model=64).to(DEVICE)

    WEIGHTS_FILE = "fractal_moe_workspace.json"


    def save_hmoe_weights(net1, net2, filepath):

        packed_weights = {
            "fusion": {k: v.cpu().numpy().tolist() for k, v in net1.state_dict().items()},
            "hmoe": {k: v.cpu().numpy().tolist() for k, v in net2.state_dict().items()}
        }
        with open(filepath, 'w') as f:
            json.dump(packed_weights, f)


    def load_hmoe_weights(net1, net2, filepath):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
            net1.load_state_dict({k: torch.tensor(v).to(DEVICE) for k, v in data["fusion"].items()})
            net2.load_state_dict({k: torch.tensor(v).to(DEVICE) for k, v in data["hmoe"].items()})
            return True
        return False



    if load_hmoe_weights(workspace_fusion_model, fractal_moe_model, WEIGHTS_FILE):
        print(f"Loaded existing weights from {WEIGHTS_FILE}. Continuing training to refine...")
    else:
        print("Starting fresh training session...")


    workspace_fusion_model, fractal_moe_model = train_fractal_moe(
        workspace_fusion_model, fractal_moe_model, engine, epochs=800
    )


    save_hmoe_weights(workspace_fusion_model, fractal_moe_model, WEIGHTS_FILE)
    print(f"Weights successfully saved to {WEIGHTS_FILE}. You can now run the Simulation!")
