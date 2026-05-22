import pygame
import math
import sys
import os
import json
import torch
import torch.nn as nn
from AI_Goal import ParametricGridEngine, AI_CONFIG

engine = ParametricGridEngine(AI_CONFIG)


# ==========================================
# 1. HI_MOE TRANSFORMER GLOBAL WORKSPACE MODULES
# ==========================================
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


class SubExpertTransformer(nn.Module):
    def __init__(self, d_model=64, nhead=4):
        super(SubExpertTransformer, self).__init__()
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, batch_first=True, dropout=0.0)
        self.deep_attention = nn.TransformerEncoder(encoder_layer, num_layers=1)
        self.fc_out = nn.Linear(d_model, 2)

    def forward(self, x):
        out = self.deep_attention(x)
        return self.fc_out(out[:, -1, :])


class MacroDomain(nn.Module):
    def __init__(self, d_model=64, num_sub=3):
        super(MacroDomain, self).__init__()
        self.gating = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, num_sub),
            nn.Softmax(dim=-1)
        )
        self.sub_experts = nn.ModuleList([SubExpertTransformer(d_model) for _ in range(num_sub)])

    def forward(self, x):
        weights = self.gating(x[:, -1, :])
        expert_outputs = torch.stack([expert(x) for expert in self.sub_experts], dim=1)
        final_out = torch.sum(expert_outputs * weights.unsqueeze(-1), dim=1)
        return final_out, weights


class HierarchicalMoE(nn.Module):
    def __init__(self, d_model=64, seq_len=5):
        super(HierarchicalMoE, self).__init__()
        self.temporal_workspace = TemporalGlobalWorkspace(d_model, seq_len=seq_len)
        self.super_gating = nn.Sequential(
            nn.Linear(d_model, 32),
            nn.ReLU(),
            nn.Linear(32, 2),
            nn.Softmax(dim=-1)
        )
        self.normal_domain = MacroDomain(d_model, num_sub=3)
        self.special_domain = MacroDomain(d_model, num_sub=3)

    def forward(self, seq):
        belief_state = self.temporal_workspace(seq)
        macro_weights = self.super_gating(belief_state[:, -1, :])

        norm_out, norm_w = self.normal_domain(belief_state)
        spec_out, spec_w = self.special_domain(belief_state)

        final_output = (norm_out * macro_weights[:, 0:1]) + (spec_out * macro_weights[:, 1:2])
        return final_output, macro_weights, norm_w, spec_w


# ==========================================
# 2. RUNTIME PARAMETERS & STORAGE LOADER
# ==========================================
workspace_fusion_model = SensorFusionWorkspace(d_model=64)
hierarchical_moe_model = HierarchicalMoE(d_model=64)
WEIGHTS_FILE = "hierarchical_moe_workspace.json"


def load_hmoe_weights(net1, net2, filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        net1.load_state_dict({k: torch.tensor(v) for k, v in data["fusion"].items()})
        net2.load_state_dict({k: torch.tensor(v) for k, v in data["hmoe"].items()})
        return True
    return False


if not load_hmoe_weights(workspace_fusion_model, hierarchical_moe_model, WEIGHTS_FILE):
    print("WARNING: Deep Hierarchical Workspace Weights File not found!")

workspace_fusion_model.eval()
hierarchical_moe_model.eval()

MAX_HISTORY = 5
latent_history = [torch.zeros(64) for _ in range(MAX_HISTORY)]


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


def process_with_moe_transformer(sensor_grid):
    global latent_history

    bool_grid = [[bool(col) for col in row] for row in sensor_grid]
    flat_grid = [int(cell) for row in sensor_grid for cell in row]
    is_empty = (sum(flat_grid) == 0)

    lines = engine.extract_lines(bool_grid)
    vector = extract_native_vector(lines)

    grid_t = torch.tensor([flat_grid], dtype=torch.long)
    vec_t = torch.tensor([vector], dtype=torch.float32)

    with torch.no_grad():
        latent_state = workspace_fusion_model(grid_t, vec_t).squeeze(0)

        latent_history.append(latent_state)
        latent_history.pop(0)

        seq_tensor = torch.stack(latent_history).unsqueeze(0)
        predictions, macro_w, norm_w, spec_w = hierarchical_moe_model(seq_tensor)

        pred_speed = predictions[0][0].item()
        pred_angle_normalized = predictions[0][1].item()

    actual_turn = pred_angle_normalized * 180.0

    if is_empty:
        pred_speed = 1.0
    else:
        pred_speed = max(0.0, pred_speed)

    # Output macro super-gating and domain level diagnostics safely to console
    mw = macro_w[0].tolist()
    nw = norm_w[0].tolist()
    sw = spec_w[0].tolist()
    m_str = f"Norm:{mw[0]:.0%}|Spec:{mw[1]:.0%}"
    n_str = f"N[{nw[0]:.0%},{nw[1]:.0%},{nw[2]:.0%}]"
    s_str = f"S[{sw[0]:.0%},{sw[1]:.0%},{sw[2]:.0%}]"

    sys.stdout.write(f"\rHierarchy Tree -> {m_str} -> {n_str} {s_str} | Heading adjustment: {actual_turn:+06.2f}°")
    sys.stdout.flush()

    return pred_speed, actual_turn


# ==========================================
# 3. PYGAME SIMULATION LOOP
# ==========================================
pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Hierarchical Workspace MoE Transformer AI Follower")
clock = pygame.time.Clock()

mode = "draw"
paths = []
last_pos = None

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


running = True
while running:
    screen.fill((255, 255, 255))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and mode == "draw":
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
        speed, transformer_angle = process_with_moe_transformer(sensor_data)

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

    p1 = (rx + f_x * 20, ry + f_y * 20)
    p2 = (rx - f_x * 10 + l_x * 14, ry - f_y * 10 + l_y * 14)
    p3 = (rx - f_x * 10 - l_x * 14, ry - f_y * 10 - l_y * 14)
    pygame.draw.polygon(screen, (0, 50, 255), [p1, p2, p3])

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()