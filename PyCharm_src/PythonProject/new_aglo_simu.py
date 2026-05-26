import numpy as np
import torch
import torch.nn as nn
import json
import pygame
import sys
from typing import Tuple

pygame.init()

DEVICE = torch.device(
    "cuda" if torch.cuda.is_available()
    else "mps" if torch.backends.mps.is_available()
    else "cpu"
)


CANVAS_SIZE = 600
SENSOR_SIZE = 80
SCREEN_WIDTH = CANVAS_SIZE + SENSOR_SIZE + 40
SCREEN_HEIGHT = CANVAS_SIZE + 80

FPS = 60
BRUSH_SIZE = 15

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
DARK_GRAY = (30, 30, 30)


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
        x = torch.cat([cls, c, g], dim=1)
        x = self.transformer(x)
        return x  # full tensor [B, 22, d_model]


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
        return x


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
        return x


class EpisodicMemory(nn.Module):
    def __init__(self, d_model=D_MEM):
        super().__init__()
        self.spatial = SpatialMemoryTransformer(d_model)
        self.vector = VectorMemoryTransformer(d_model)
        self.cross_attn = CrossAttentionBridge(d_model, d_model, nhead=N_HEADS)

    def forward(self, positions, vectors):
        spatial_tensor = self.spatial(positions)
        vector_tensor = self.vector(vectors)
        fused = self.cross_attn(spatial_tensor, vector_tensor)
        return fused


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
        self.mem_proj = nn.Linear(d_memory, d_visual)
        self.cross_attn = CrossAttentionBridge(d_visual, d_visual, nhead=N_HEADS)
        self.pool_query = nn.Parameter(torch.randn(1, 1, d_visual))
        self.pool_attn = nn.MultiheadAttention(d_visual, N_HEADS, batch_first=True)
        self.pool_norm = nn.LayerNorm(d_visual)
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


class Sensor:


    def __init__(self, terrain: np.ndarray, grid_size: Tuple[int, int] = (5, 4)):
        self.terrain = terrain
        self.grid_h, self.grid_w = grid_size
        self.terrain_h, self.terrain_w = terrain.shape

    def read(self, agent_x: float, agent_y: float, agent_angle: float = 0) -> np.ndarray:
        """Read sensor at agent position facing agent_angle."""
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



def load_weights_from_json(trainer, filepath='agent_weights.json'):

    try:
        with open(filepath, 'r') as f:
            weights = json.load(f)

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

        return True
    except FileNotFoundError:
        return False



class AgentController:


    def __init__(self, cnn, visual, episodic, moe, controller):
        self.cnn = cnn
        self.visual = visual
        self.episodic = episodic
        self.moe = moe
        self.controller = controller

        # Agent state
        self.x = CANVAS_SIZE / 2
        self.y = CANVAS_SIZE / 2
        self.angle = 0.0

        # History
        self.position_history = []
        self.action_history = []
        self.latent_history = []

    def reset(self):

        self.x = CANVAS_SIZE / 2
        self.y = CANVAS_SIZE / 2
        self.angle = 0.0
        self.position_history.clear()
        self.action_history.clear()
        self.latent_history.clear()

    def step(self, sensor_reading):

        with torch.no_grad():
            # CNN
            grid_tensor = torch.from_numpy(sensor_reading.flatten()).long().unsqueeze(0).to(DEVICE)
            sensor_tensor = torch.from_numpy(sensor_reading.astype(np.float32)).unsqueeze(0).to(DEVICE)

            cnn_out = self.cnn(sensor_tensor)
            visual_tensor = self.visual(grid_tensor, cnn_out)  # [1, 22, D_MAIN] full tensor

            # Pool CLS token for temporal history
            visual_cls = visual_tensor[:, 0:1, :].detach()
            self.latent_history.append(visual_cls)
            if len(self.latent_history) > 5:
                self.latent_history.pop(0)

            # Temporal
            if len(self.latent_history) < 5:
                pad = visual_cls.expand(1, 5 - len(self.latent_history), -1)
                latent_seq = torch.cat(list(self.latent_history) + [pad], dim=1)
            else:
                latent_seq = torch.cat(list(self.latent_history), dim=1)  # [1, 5, D_MAIN]

            # Memory
            if len(self.position_history) > 0:
                pos_history = torch.tensor(self.position_history[-50:], dtype=torch.float32, device=DEVICE).unsqueeze(0)
                action_history = torch.tensor(self.action_history[-50:], dtype=torch.float32, device=DEVICE).unsqueeze(
                    0)
            else:
                pos_history = torch.tensor([[self.x, self.y]], dtype=torch.float32, device=DEVICE).unsqueeze(0)
                action_history = torch.zeros((1, 1, 2), dtype=torch.float32, device=DEVICE)

            memory_tensor = self.episodic(pos_history, action_history)  # [1, S, D_MEM] full tensor
            expert_out = self.moe(latent_seq)                          # [1, 2]
            output = self.controller(visual_tensor, expert_out, memory_tensor)  # [1, 2]

            speed = float(output[0, 0])
            angle = float(output[0, 1])

        # Update position
        self.x += speed * 2.0 * np.cos(self.angle)
        self.y += speed * 2.0 * np.sin(self.angle)
        self.angle += angle * 0.1

        # Clamp to canvas
        self.x = max(0, min(CANVAS_SIZE - 1, self.x))
        self.y = max(0, min(CANVAS_SIZE - 1, self.y))

        # Record history
        self.position_history.append([self.x, self.y])
        self.action_history.append([speed, angle])

        return speed, angle



class AgentSimulator:


    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("🤖 Autonomous Agent Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)

        # Canvas
        self.canvas = np.zeros((CANVAS_SIZE, CANVAS_SIZE), dtype=np.float32)
        self.drawing = True
        self.running = True
        self.simulating = False

        # Agent — upgraded dimensions
        self.cnn = VisualCNN().to(DEVICE)
        self.visual = VisualTransformer(d_model=D_MAIN).to(DEVICE)
        self.episodic = EpisodicMemory(d_model=D_MEM).to(DEVICE)
        self.moe = FractalMoE(d_model=D_MAIN).to(DEVICE)
        self.controller = Controller(d_visual=D_MAIN, d_memory=D_MEM).to(DEVICE)

        self.agent = AgentController(self.cnn, self.visual, self.episodic, self.moe, self.controller)
        self.sensor = Sensor(self.canvas)

        # Load weights
        self.weights_loaded = load_weights_from_json(self, 'agent_weights.json')
        if not self.weights_loaded:
            print("⚠️  Warning: agent_weights.json not found. Using random weights.")
            print("    Run autonomous_agent_train.py first to train the model.")
        else:
            print("✅ Weights loaded successfully")

    def load_weights_from_json(self, filepath='agent_weights.json'):

        try:
            with open(filepath, 'r') as f:
                weights = json.load(f)

            cnn_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['cnn'].items()}
            self.cnn.load_state_dict(cnn_state)

            visual_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['visual'].items()}
            self.visual.load_state_dict(visual_state)

            episodic_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['episodic'].items()}
            self.episodic.load_state_dict(episodic_state)

            moe_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['moe'].items()}
            self.moe.load_state_dict(moe_state)

            controller_state = {k: torch.tensor(v, dtype=torch.float32) for k, v in weights['controller'].items()}
            self.controller.load_state_dict(controller_state)

            return True
        except:
            return False

    def handle_events(self):

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                elif event.key == pygame.K_SPACE:
                    self.simulating = not self.simulating
                    if self.simulating:
                        self.drawing = False
                        self.agent.reset()
                    else:
                        self.drawing = True

                elif event.key == pygame.K_c:
                    self.canvas.fill(0)
                    self.agent.reset()
                    self.simulating = False
                    self.drawing = True

                elif event.key == pygame.K_r:
                    self.agent.reset()
                    self.simulating = False


        if self.drawing and pygame.mouse.get_pressed()[0]:
            mx, my = pygame.mouse.get_pos()
            if mx < CANVAS_SIZE and my < CANVAS_SIZE:
                if hasattr(self, 'last_mouse_pos') and self.last_mouse_pos is not None:
                    x0, y0 = self.last_mouse_pos
                    dist = max(abs(mx - x0), abs(my - y0))
                    if dist == 0:
                        dist = 1
                    for i in range(dist + 1):
                        x = int(x0 + i * (mx - x0) / dist)
                        y = int(y0 + i * (my - y0) / dist)
                        y_start = max(0, y - BRUSH_SIZE // 2)
                        y_end = min(CANVAS_SIZE, y + BRUSH_SIZE // 2)
                        x_start = max(0, x - BRUSH_SIZE // 2)
                        x_end = min(CANVAS_SIZE, x + BRUSH_SIZE // 2)
                        self.canvas[y_start:y_end, x_start:x_end] = 1.0
                else:
                    y_start = max(0, int(my) - BRUSH_SIZE // 2)
                    y_end = min(CANVAS_SIZE, int(my) + BRUSH_SIZE // 2)
                    x_start = max(0, int(mx) - BRUSH_SIZE // 2)
                    x_end = min(CANVAS_SIZE, int(mx) + BRUSH_SIZE // 2)
                    self.canvas[y_start:y_end, x_start:x_end] = 1.0
                
                self.last_mouse_pos = (mx, my)
        else:
            self.last_mouse_pos = None

    def update(self):

        if self.simulating:
            sensor_reading = self.sensor.read(self.agent.x, self.agent.y, self.agent.angle)
            self.agent.step(sensor_reading)

    def draw(self):

        self.screen.fill(DARK_GRAY)

        # Draw canvas area using fast surfarray (replaces slow pixel-by-pixel loop)
        canvas_rgb = np.zeros((CANVAS_SIZE, CANVAS_SIZE, 3), dtype=np.uint8)
        canvas_rgb[self.canvas > 0] = 255
        canvas_surface = pygame.surfarray.make_surface(canvas_rgb.transpose(1, 0, 2))
        self.screen.blit(canvas_surface, (10, 10))

        agent_x = int(self.agent.x)
        agent_y = int(self.agent.y)
        pygame.draw.circle(self.screen, RED, (agent_x + 10, agent_y + 10), 20)

        arrow_len = 50
        end_x = agent_x + 10 + arrow_len * np.cos(self.agent.angle)
        end_y = agent_y + 10 + arrow_len * np.sin(self.agent.angle)
        pygame.draw.line(self.screen, RED, (agent_x + 10, agent_y + 10), (end_x, end_y), 4)


        sensor_reading = self.sensor.read(self.agent.x, self.agent.y, self.agent.angle)
        
        # Draw sensor grid points directly on canvas
        look_ahead = 60
        spacing = 15
        for i in range(5):
            for j in range(4):
                px = self.agent.x + (j - 4 // 2) * spacing + look_ahead * np.cos(self.agent.angle)
                py = self.agent.y + (i - 5 // 2) * spacing + look_ahead * np.sin(self.agent.angle)
                
                draw_x = int(px) + 10
                draw_y = int(py) + 10
                
                if 10 <= draw_x <= CANVAS_SIZE + 10 and 10 <= draw_y <= CANVAS_SIZE + 10:
                    color = GREEN if sensor_reading[i, j] > 0 else GRAY
                    pygame.draw.circle(self.screen, color, (draw_x, draw_y), 5)
        sensor_x = CANVAS_SIZE + 20
        sensor_y = 10


        title = self.small_font.render("Sensor (5x4)", True, WHITE)
        self.screen.blit(title, (sensor_x, sensor_y))


        grid_scale = SENSOR_SIZE // 4
        for i in range(5):
            for j in range(4):
                rect = pygame.Rect(sensor_x + j * grid_scale, sensor_y + 25 + i * grid_scale,
                                   grid_scale, grid_scale)
                color = GREEN if sensor_reading[i, j] > 0 else GRAY
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, WHITE, rect, 1)

        # Status text
        status_y = CANVAS_SIZE + 20

        if self.drawing:
            status_text = "Status: DRAWING | Press SPACE to start"
            color = YELLOW
        elif self.simulating:
            status_text = "Status: SIMULATING | Press SPACE to stop"
            color = GREEN
        else:
            status_text = "Status: PAUSED | Press SPACE to resume"
            color = BLUE

        status_surface = self.font.render(status_text, True, color)
        self.screen.blit(status_surface, (10, status_y))

        # Controls
        controls = [
            "Controls:",
            "  Draw: Left Mouse",
            "  Start: SPACE",
            "  Clear: C",
            "  Reset: R",
            "  Quit: ESC"
        ]

        for i, ctrl in enumerate(controls):
            text = self.small_font.render(ctrl, True, WHITE)
            self.screen.blit(text, (CANVAS_SIZE + 20, status_y + i * 25))

        pygame.display.flip()

    def run(self):
        """Main loop."""
        print("\n🎮 Simulator started!")
        print("   - Draw a line on the canvas")
        print("   - Press SPACE to start simulation")
        print("   - Watch the robot follow your line!\n")

        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        print("\n👋 Simulator closed")


if __name__ == "__main__":
    simulator = AgentSimulator()
    simulator.run()