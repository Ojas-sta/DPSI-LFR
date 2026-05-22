from AI_Goal import ParametricGridEngine, AI_CONFIG
import numpy as np
import math
import random
import torch
import torch.nn as nn
import torch.optim as optim
import json
import os

TRANSFORMER_WEIGHTS_FILE = "transformer_weights_v2.json"
MAX_HISTORY = 5


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
        last_out = out[:, -1, :]
        return self.fc_out(last_out)


def save_transformer_weights(model, filepath):
    state_dict = model.state_dict()
    serializable_dict = {k: v.cpu().numpy().tolist() for k, v in state_dict.items()}
    with open(filepath, 'w') as f:
        json.dump(serializable_dict, f)


def load_transformer_weights(model, filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            loaded_dict = json.load(f)
        state_dict = {k: torch.tensor(v) for k, v in loaded_dict.items()}
        model.load_state_dict(state_dict)
        return True
    return False


def train_transformer_memory(model, epochs=200):
    print("--- Initiating Transformer Attention Training ---")
    optimizer = optim.Adam(model.parameters(), lr=0.005)
    criterion = nn.MSELoss()

    X_seqs = []
    y_targets = []

    for _ in range(1500):
        seq = []
        base_dx = random.choice([-2.0, 0.0, 2.0])
        base_dy = 2.0
        base_angle = math.degrees(math.atan2(base_dx, base_dy))

        for step in range(MAX_HISTORY):
            is_empty = (step == (MAX_HISTORY - 1) and random.random() < 0.5)

            if is_empty:
                grid_flat = [0.0] * 20
                vector = [0.0, 0.0]
            else:
                grid_flat = [random.choice([0.0, 1.0]) for _ in range(20)]
                vector = [base_dx, base_dy]

            seq.append(grid_flat + vector)

        X_seqs.append(seq)
        y_targets.append([1.0, base_angle])

    X_tensor = torch.tensor(X_seqs, dtype=torch.float32)
    y_tensor = torch.tensor(y_targets, dtype=torch.float32)

    model.train()
    for epoch in range(epochs):
        optimizer.zero_grad()
        predictions = model(X_tensor)
        loss = criterion(predictions, y_tensor)
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 10 == 0:
            print(f"Training Step [{epoch + 1:03d}/{epochs}] | Error Rate (MSE): {loss.item():.6f}")

    print("--- Training Complete ---\n")
    return model


engine = ParametricGridEngine(AI_CONFIG)
transformer_model = RobotTransformer()

if not load_transformer_weights(transformer_model, TRANSFORMER_WEIGHTS_FILE):
    transformer_model = train_transformer_memory(transformer_model)
    save_transformer_weights(transformer_model, TRANSFORMER_WEIGHTS_FILE)

transformer_model.eval()

history_buffer = []


def convert(inp):
    return [[bool(col) for col in row] for row in inp]


def extract_native_vector(lines):
    if not lines:
        return [0.0, 0.0]
    p1, p2 = lines[0]

    dx = p2[1] - p1[1]
    dy = -(p2[0] - p1[0])

    if dy < 0:
        dx = -dx;
        dy = -dy
    elif dy == 0 and dx < 0:
        dx = -dx

    return [float(dx), float(dy)]


d

sensor_sequence = [
    [
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1],
    ],
    [
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1],
    ],
    [
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1],
    ],
    [
        [1, 0, 0, 0, 0],
        [0, 1, 1, 0, 0],
        [0, 0, 0, 1, 1],
        [0, 0, 0, 0, 1],
    ],
    [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
]

for i, sensor_frame in enumerate(sensor_sequence):
    spd, ang, vec = process_with_transformer(sensor_frame)
    direction = "(Right)" if ang > 0 else "(Left)" if ang < 0 else "(Straight)"
    print(f"--- Frame {i + 1} ---")
    print(f"Native Vector : {vec}")
    print(f"Trans. Speed  : {spd:.2f}")
    print(f"Trans. Angle  : {ang:+0.2f} degrees {direction}\n")