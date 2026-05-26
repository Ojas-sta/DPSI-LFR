import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import random
import json
from collections import deque
from typing import Tuple

DEVICE = torch.device("cpu")
print(f"Using device: {DEVICE}\n")


class TerrainGenerator:

    def __init__(self, width=100, height=100, line_thickness=5):
        self.width = width
        self.height = height
        self.line_thickness = line_thickness
        self.canvas = None

    def _draw_line(self, canvas: np.ndarray, p1: Tuple[int, int],
                   p2: Tuple[int, int], thickness: int = 5) -> np.ndarray:

        x1, y1 = p1
        x2, y2 = p2

        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x2 > x1 else -1
        sy = 1 if y2 > y1 else -1
        err = dx - dy

        x, y = x1, y1
        points = []

        while True:
            points.append((x, y))
            if x == x2 and y == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

        for px, py in points:
            for dx in range(-thickness // 2, thickness // 2 + 1):
                for dy in range(-thickness // 2, thickness // 2 + 1):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        canvas[ny, nx] = 1

        return canvas

    def _draw_curve(self, canvas: np.ndarray, start: Tuple[int, int],
                    end: Tuple[int, int], control: Tuple[int, int]) -> np.ndarray:

        points = []
        for t in np.linspace(0, 1, 50):
            x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t ** 2 * end[0]
            y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t ** 2 * end[1]
            points.append((int(x), int(y)))

        for i in range(len(points) - 1):
            canvas = self._draw_line(canvas, points[i], points[i + 1], self.line_thickness)

        return canvas

    def generate_random_track(self) -> np.ndarray:

        canvas = np.zeros((self.height, self.width), dtype=np.float32)

        track_type = random.choice(['straight', 'curve', 'intersection', 'zigzag', 'spiral'])

        if track_type == 'straight':
            y_center = self.height // 2
            canvas = self._draw_line(canvas, (5, y_center), (self.width - 5, y_center), self.line_thickness)

        elif track_type == 'curve':
            if random.random() < 0.5:
                canvas = self._draw_curve(canvas, (10, 20), (self.width - 10, self.height - 20),
                                          (self.width // 2, self.height // 4))
                canvas = self._draw_curve(canvas, (self.width - 10, self.height - 20), (10, self.height),
                                          (self.width // 2, 3 * self.height // 4))
            else:
                canvas = self._draw_curve(canvas, (10, 10), (self.width - 10, 10),
                                          (self.width // 2, self.height // 2))

        elif track_type == 'intersection':
            y_center = self.height // 2
            x_center = self.width // 2
            canvas = self._draw_line(canvas, (5, y_center), (self.width - 5, y_center), self.line_thickness)
            canvas = self._draw_line(canvas, (x_center, 5), (x_center, self.height - 5), self.line_thickness)

        elif track_type == 'zigzag':
            segment_width = self.width // 4
            points = [(10, 20), (segment_width, self.height - 20),
                      (2 * segment_width, 20), (3 * segment_width, self.height - 20), (self.width - 10, 20)]
            for i in range(len(points) - 1):
                canvas = self._draw_line(canvas, points[i], points[i + 1], self.line_thickness)

        elif track_type == 'spiral':
            center_x, center_y = self.width // 2, self.height // 2
            points = []
            for angle in np.linspace(0, 4 * np.pi, 100):
                r = 5 + angle * 3
                x = center_x + r * np.cos(angle)
                y = center_y + r * np.sin(angle)
                points.append((int(x), int(y)))

            for i in range(len(points) - 1):
                canvas = self._draw_line(canvas, points[i], points[i + 1], self.line_thickness)

        self.canvas = canvas
        return canvas


class Sensor:
    def __init__(self, terrain: np.ndarray, grid_size: Tuple[int, int] = (5, 4)):
        self.terrain = terrain
        self.grid_h, self.grid_w = grid_size
        self.terrain_h, self.terrain_w = terrain.shape

    def read(self, agent_x: float, agent_y: float, agent_angle: float = 0) -> np.ndarray:

        look_ahead = 60
        spacing = 15
        sensor_readings = np.zeros((self.grid_h, self.grid_w), dtype=np.float32)

        for i in range(self.grid_h):
            for j in range(self.grid_w):
                px = agent_x + (j - self.grid_w // 2) * spacing + look_ahead * np.cos(agent_angle)
                py = agent_y + (i - self.grid_h // 2) * spacing + look_ahead * np.sin(agent_angle)

                px, py = int(px), int(py)

                if 0 <= px < self.terrain_w and 0 <= py < self.terrain_h:
                    sensor_readings[i, j] = self.terrain[py, px]

        return sensor_readings



class CrossAttentionBridge(nn.Module):
    def __init__(self, d_query, d_kv, nhead=8):
        super().__init__()
        self.kv_proj = nn.Linear(d_kv, d_query)
        self.cross_attn = nn.MultiheadAttention(d_query, nhead, batch_first=True)
        self.norm1 = nn.LayerNorm(d_query)
        self.ffn = nn.Sequential(
            nn.Linear(d_query, d_query * 4),
            nn.GELU(),
            nn.Linear(d_query * 4, d_query)
        )
        self.norm2 = nn.LayerNorm(d_query)

    def forward(self, query_tensor, kv_tensor):

        kv = self.kv_proj(kv_tensor)
        attn_out, _ = self.cross_attn(query_tensor, kv, kv)
        x = self.norm1(query_tensor + attn_out)
        x = self.norm2(x + self.ffn(x))
        return x



D_MAIN = 256
D_MEM = 128
N_HEADS = 8
FF_MAIN = 1024
FF_MEM = 512
FF_EXPERT = 512


class VisualCNN(nn.Module):

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(20, 256),
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 32)
        )

    def forward(self, x):
        return self.net(x)


class VisualTransformer(nn.Module):

    def __init__(self, d_model=D_MAIN):
        super().__init__()
        self.d_model = d_model
        self.grid_embed = nn.Embedding(2, d_model)
        self.pos_embed = nn.Parameter(torch.randn(1, 20, d_model))
        self.cnn_embed = nn.Linear(32, d_model)
        self.cls = nn.Parameter(torch.randn(1, 1, d_model))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model, N_HEADS, batch_first=True, dim_feedforward=FF_MAIN
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=5)

    def forward(self, grid, cnn_out):
        B = grid.size(0)
        g = self.grid_embed(grid) + self.pos_embed
        c = self.cnn_embed(cnn_out).unsqueeze(1)
        cls = self.cls.expand(B, 1, -1)

        x = torch.cat([cls, c, g], dim=1)   # [B, 22, d_model]
        x = self.transformer(x)
        return x                              # full tensor, not x[:, 0]


class TemporalTransformer(nn.Module):

    def __init__(self, d_model=D_MAIN, seq_len=5):
        super().__init__()
        self.pos_embed = nn.Parameter(torch.randn(1, seq_len, d_model))

        encoder_layer = nn.TransformerEncoderLayer(
            d_model, N_HEADS, batch_first=True, dim_feedforward=FF_MAIN
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=5)

    def forward(self, x):
        return self.transformer(x + self.pos_embed)


class SpatialMemoryTransformer(nn.Module):
    """11 layers — responsible for remembering the layout of lines."""

    def __init__(self, d_model=D_MEM):
        super().__init__()
        self.embed = nn.Linear(2, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, N_HEADS, batch_first=True, dim_feedforward=FF_MEM
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=11)

    def forward(self, positions):
        x = self.embed(positions)
        x = self.transformer(x)
        return x                  # full tensor [B, seq, d_model]


class VectorMemoryTransformer(nn.Module):

    def __init__(self, d_model=D_MEM):
        super().__init__()
        self.embed = nn.Linear(2, d_model)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, N_HEADS, batch_first=True, dim_feedforward=FF_MEM
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=4)

    def forward(self, vectors):
        x = self.embed(vectors)
        x = self.transformer(x)
        return x                  # full tensor [B, seq, d_model]


class EpisodicMemory(nn.Module):

    def __init__(self, d_model=D_MEM):
        super().__init__()
        self.spatial = SpatialMemoryTransformer(d_model)
        self.vector = VectorMemoryTransformer(d_model)
        # Cross-attention: spatial queries attend to vector keys/values
        self.cross_attn = CrossAttentionBridge(d_model, d_model, nhead=N_HEADS)

    def forward(self, positions, vectors):
        spatial_tensor = self.spatial(positions)     # [B, S1, d_model]
        vector_tensor = self.vector(vectors)         # [B, S2, d_model]
        fused = self.cross_attn(spatial_tensor, vector_tensor)  # [B, S1, d_model]
        return fused                                  # full tensor output


class MicroExpert(nn.Module):

    def __init__(self, d_model=D_MAIN):
        super().__init__()
        encoder_layer = nn.TransformerEncoderLayer(
            d_model, N_HEADS, batch_first=True, dim_feedforward=FF_EXPERT
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=4)
        self.out = nn.Linear(d_model, 2)

    def forward(self, x):
        x = self.transformer(x)
        return self.out(x[:, -1])


class TaskNode(nn.Module):

    def __init__(self, d_model=D_MAIN):
        super().__init__()
        self.experts = nn.ModuleList([MicroExpert(d_model) for _ in range(2)])
        self.gate = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        gate_weights = self.gate(x[:, -1])
        expert_outs = torch.stack([e(x) for e in self.experts], dim=1)
        return (expert_outs * gate_weights.unsqueeze(-1)).sum(1)


class MacroNode(nn.Module):

    def __init__(self, d_model=D_MAIN):
        super().__init__()
        self.tasks = nn.ModuleList([TaskNode(d_model) for _ in range(3)])
        self.gate = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 3),
            nn.Softmax(dim=-1)
        )

    def forward(self, x):
        gate_weights = self.gate(x[:, -1])
        task_outs = torch.stack([t(x) for t in self.tasks], dim=1)
        return (task_outs * gate_weights.unsqueeze(-1)).sum(1)


class FractalMoE(nn.Module):

    def __init__(self, d_model=D_MAIN):
        super().__init__()
        self.temporal = TemporalTransformer(d_model, seq_len=5)
        self.macros = nn.ModuleList([MacroNode(d_model) for _ in range(3)])

        self.top_gate = nn.Sequential(
            nn.Linear(d_model, 64),
            nn.ReLU(),
            nn.Linear(64, 3),
            nn.Softmax(dim=-1)
        )

    def forward(self, latent_seq):
        temporal_out = self.temporal(latent_seq)
        gate_weights = self.top_gate(temporal_out[:, -1])
        macro_outs = torch.stack([m(temporal_out) for m in self.macros], dim=1)
        return (macro_outs * gate_weights.unsqueeze(-1)).sum(1)


class Controller(nn.Module):

    def __init__(self, d_visual=D_MAIN, d_memory=D_MEM):
        super().__init__()
        # Project memory tensor to visual dimension for cross-attention
        self.mem_proj = nn.Linear(d_memory, d_visual)
        # Cross-attention: visual attends to memory context
        self.cross_attn = CrossAttentionBridge(d_visual, d_visual, nhead=N_HEADS)
        # Attention pooling to collapse tensor to single vector
        self.pool_query = nn.Parameter(torch.randn(1, 1, d_visual))
        self.pool_attn = nn.MultiheadAttention(d_visual, N_HEADS, batch_first=True)
        self.pool_norm = nn.LayerNorm(d_visual)
        # Final MLP: pooled vector + expert output → action
        self.fc = nn.Sequential(
            nn.Linear(d_visual + 2, 256),
            nn.GELU(),
            nn.Linear(256, 128),
            nn.GELU(),
            nn.Linear(128, 2)
        )

    def forward(self, visual_tensor, expert, memory_tensor):

        mem_proj = self.mem_proj(memory_tensor)
        context = torch.cat([visual_tensor, mem_proj], dim=1)
        enriched = self.cross_attn(visual_tensor, context)
        B = enriched.size(0)
        query = self.pool_query.expand(B, 1, -1)
        pooled, _ = self.pool_attn(query, enriched, enriched)
        pooled = self.pool_norm(pooled).squeeze(1)
        combined = torch.cat([pooled, expert], dim=-1)
        return self.fc(combined)


def save_weights_to_json(trainer, filepath='agent_weights.json'):

    weights = {}

    # Save all model state dicts
    weights['cnn'] = {k: v.cpu().numpy().tolist() for k, v in trainer.cnn.state_dict().items()}
    weights['visual'] = {k: v.cpu().numpy().tolist() for k, v in trainer.visual.state_dict().items()}
    weights['episodic'] = {k: v.cpu().numpy().tolist() for k, v in trainer.episodic.state_dict().items()}
    weights['moe'] = {k: v.cpu().numpy().tolist() for k, v in trainer.moe.state_dict().items()}
    weights['controller'] = {k: v.cpu().numpy().tolist() for k, v in trainer.controller.state_dict().items()}

    with open(filepath, 'w') as f:
        json.dump(weights, f)

    print(f"✅ Weights saved to {filepath}")


def load_weights_from_json(trainer, filepath='agent_weights.json'):

    with open(filepath, 'r') as f:
        weights = json.load(f)

    # Load each model
    cnn_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['cnn'].items()}
    trainer.cnn.load_state_dict(cnn_state)

    visual_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['visual'].items()}
    trainer.visual.load_state_dict(visual_state)

    episodic_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['episodic'].items()}
    trainer.episodic.load_state_dict(episodic_state)

    moe_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['moe'].items()}
    trainer.moe.load_state_dict(moe_state)

    controller_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['controller'].items()}
    trainer.controller.load_state_dict(controller_state)

    print(f"✅ Weights loaded from {filepath}")


class AgentTrainer:

    def __init__(self, terrain_size=100, line_thickness=5):
        self.terrain_size = terrain_size
        self.line_thickness = line_thickness
        self.terrain_gen = TerrainGenerator(terrain_size, terrain_size, line_thickness)

        # Models — upgraded dimensions
        self.cnn = VisualCNN().to(DEVICE)
        self.visual = VisualTransformer(d_model=D_MAIN).to(DEVICE)
        self.episodic = EpisodicMemory(d_model=D_MEM).to(DEVICE)
        self.moe = FractalMoE(d_model=D_MAIN).to(DEVICE)
        self.controller = Controller(d_visual=D_MAIN, d_memory=D_MEM).to(DEVICE)

        # Optimizer
        params = (list(self.cnn.parameters()) +
                  list(self.visual.parameters()) +
                  list(self.episodic.parameters()) +
                  list(self.moe.parameters()) +
                  list(self.controller.parameters()))

        self.optimizer = optim.AdamW(params, lr=2e-4)

        # History tracking
        self.position_history = deque(maxlen=50)
        self.action_history = deque(maxlen=50)
        self.latent_history = deque(maxlen=5)
        self.visit_map = {}

    def reset_episode(self):
        """Reset for new episode."""
        self.position_history.clear()
        self.action_history.clear()
        self.latent_history.clear()
        self.visit_map = {}

        terrain = self.terrain_gen.canvas
        valid_positions = np.where(terrain > 0)
        if len(valid_positions[0]) > 0:
            idx = random.randint(0, len(valid_positions[0]) - 1)
            agent_y = valid_positions[0][idx]
            agent_x = valid_positions[1][idx]
        else:
            agent_x, agent_y = self.terrain_size // 2, self.terrain_size // 2

        self.agent_x = float(agent_x)
        self.agent_y = float(agent_y)
        self.agent_angle = random.random() * 2 * np.pi

    def compute_loss(self, sensor_reading, speed, angle, step):

        on_line = sensor_reading.sum() > 0

        if on_line:
            line_positions = np.where(sensor_reading[2, :] > 0)[0]
            if len(line_positions) > 0:
                alignment = np.mean(line_positions)
                alignment_error = abs(alignment - 1.5)
            else:
                alignment_error = 5
        else:
            alignment_error = 5

        loss = torch.tensor(0.0, device=DEVICE, dtype=torch.float32)

        # --- Differentiable losses tied to model outputs ---

        # Speed regularization: encourage forward movement
        loss = loss + (speed - 1.0) ** 2 * 2.0
        # Angle regularization: discourage wild turning
        loss = loss + angle ** 2 * 2.0

        if not on_line:
            # Penalize going straight when off-line: encourage turning to find the line
            loss = loss + speed ** 2 * 5.0
            # Encourage some turning to search for the line
            loss = loss + 1.0 / (angle.abs() + 0.1) * 2.0
        else:
            # On line: reward speed, penalize turning proportional to alignment error
            loss = loss + (speed - 1.5) ** 2 * 1.0
            # Differentiable alignment: nudge angle toward correcting alignment
            target_angle = float(alignment_error) * 0.3
            loss = loss + (angle.abs() - target_angle) ** 2 * 3.0

        if step > 20 and not on_line:
            # Stronger penalty for being off-line later in episode
            loss = loss + speed ** 2 * 10.0

        # Visit penalty (non-differentiable but small relative to above)
        pos_key = (int(self.agent_x), int(self.agent_y))
        if pos_key in self.visit_map:
            loss = loss + 5.0 * (self.visit_map[pos_key] + 1)
        self.visit_map[pos_key] = self.visit_map.get(pos_key, 0) + 1

        # Stuck penalty: penalize speed if not moving
        if len(self.position_history) > 0:
            last_pos = self.position_history[-1]
            dist = np.sqrt((self.agent_x - last_pos[0]) ** 2 + (self.agent_y - last_pos[1]) ** 2)
            if dist < 0.5:
                loss = loss + (speed - 2.0) ** 2 * 3.0

        return loss

    def train_epoch(self, num_steps=200):

        terrain = self.terrain_gen.generate_random_track()
        sensor_model = Sensor(terrain, grid_size=(5, 4))

        self.reset_episode()
        epoch_loss = 0

        for step in range(num_steps):
            sensor_reading = sensor_model.read(self.agent_x, self.agent_y, self.agent_angle)

            grid_tensor = torch.from_numpy(sensor_reading.flatten()).long().unsqueeze(0).to(DEVICE)
            sensor_tensor = torch.from_numpy(sensor_reading.astype(np.float32)).unsqueeze(0).to(DEVICE)

            cnn_out = self.cnn(sensor_tensor)
            visual_tensor = self.visual(grid_tensor, cnn_out)  # [1, 22, D_MAIN] full tensor

            # Pool CLS token for temporal history (store as [1, 1, D_MAIN])
            visual_cls = visual_tensor[:, 0:1, :].detach()
            self.latent_history.append(visual_cls)

            if len(self.latent_history) < 5:
                pad = visual_cls.expand(1, 5 - len(self.latent_history), -1)
                latent_seq = torch.cat(list(self.latent_history) + [pad], dim=1)
            else:
                latent_seq = torch.cat(list(self.latent_history), dim=1)  # [1, 5, D_MAIN]

            pos_tensor = torch.tensor([self.agent_x, self.agent_y], dtype=torch.float32, device=DEVICE).unsqueeze(
                0).unsqueeze(0)
            pos_history = torch.cat([pos_tensor] * max(1, len(self.position_history)), dim=1)

            if len(self.action_history) > 0:
                action_history = torch.tensor(list(self.action_history), dtype=torch.float32, device=DEVICE).unsqueeze(
                    0)
            else:
                action_history = torch.zeros((1, 1, 2), dtype=torch.float32, device=DEVICE)

            memory_tensor = self.episodic(pos_history, action_history)  # [1, S, D_MEM] full tensor
            expert_out = self.moe(latent_seq)                          # [1, 2]
            output = self.controller(visual_tensor, expert_out, memory_tensor)  # [1, 2]
            speed, angle = output[0, 0], output[0, 1]

            loss = self.compute_loss(sensor_reading, speed, angle, step)

            self.optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                list(self.cnn.parameters()) +
                list(self.visual.parameters()) +
                list(self.episodic.parameters()) +
                list(self.moe.parameters()) +
                list(self.controller.parameters()),
                1.5
            )
            self.optimizer.step()

            epoch_loss += loss.item()

            speed_val = speed.detach().float().item()
            angle_val = angle.detach().float().item()

            self.agent_x += speed_val * 2.0 * np.cos(self.agent_angle)
            self.agent_y += speed_val * 2.0 * np.sin(self.agent_angle)
            self.agent_angle += angle_val * 0.1

            self.agent_x = self.agent_x % self.terrain_size
            self.agent_y = self.agent_y % self.terrain_size

            self.position_history.append((self.agent_x, self.agent_y))
            self.action_history.append([speed_val, angle_val])

        return epoch_loss / num_steps


def main():
    trainer = AgentTrainer(terrain_size=100, line_thickness=15)

    print(" Starting training with procedural terrain generation...\n")

    for epoch in range(100):
        avg_loss = trainer.train_epoch(num_steps=200)
        print(f" Epoch {epoch:3d} | Avg Loss: {avg_loss:8.2f}")

        if (epoch + 1) % 10 == 0:
            print(f"   Checkpoint at epoch {epoch}")

    # Save weights to JSON
    save_weights_to_json(trainer, 'agent_weights.json')
    print("\nTraining complete! Weights saved to agent_weights.json")


if __name__ == "__main__":
    main()