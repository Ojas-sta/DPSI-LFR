import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

class ConvolutionalEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        # Layer 1
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=8, kernel_size=3, stride=2, padding=1)
        # Layer 2
        self.conv2 = nn.Conv2d(in_channels=8, out_channels=16, kernel_size=3, stride=2, padding=1)
        # Layer 3
        self.conv3 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, stride=2, padding=1)
        # Layer 4
        self.conv4 = nn.Conv2d(in_channels=32, out_channels=64, kernel_size=3, stride=2, padding=1)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)

        x = self.conv2(x)
        x = F.relu(x)

        x = self.conv3(x)
        x = F.relu(x)

        x = self.conv4(x)
        x = F.relu(x)
        return x

def image_to_tensor(image_np): # Renamed parameter for clarity
    if image_np is None:
        return None
    
    if isinstance(image_np, Image.Image):
        import numpy as np
        image_np = np.array(image_np)
        
    tensor = torch.from_numpy(image_np).permute(2, 0, 1).float().div_(255.0)
    return tensor.unsqueeze(0) # Add batch dimension

if __name__ == '__main__':
    model = ConvolutionalEncoder()
    # Create a dummy input tensor for shape calculation
    dummy_input = torch.randn(1, 3, 720, 1080) # Batch size, channels, height, width

    print(f"Input Shape: {tuple(dummy_input.shape)}")

    x = model.conv1(dummy_input)
    print(f"After Conv1: {tuple(x.shape)}")
    x = F.relu(x)

    x = model.conv2(x)
    print(f"After Conv2: {tuple(x.shape)}")
    x = F.relu(x)

    x = model.conv3(x)
    print(f"After Conv3: {tuple(x.shape)}")
    x = F.relu(x)

    x = model.conv4(x)
    print(f"After Conv4: {tuple(x.shape)}")
    x = F.relu(x)
