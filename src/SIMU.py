import pygame
import math
import sys
import random
from AI_Goal import ParametricGridEngine, AI_CONFIG

# ==========================================
# 1. Initialize AI Engine
# ==========================================
print("Loading Neural Network Weights...")
engine = ParametricGridEngine(AI_CONFIG)


def convert(inp):
    return [[bool(col) for col in row] for row in inp]


def process_sensor_data(inp):
    speed = 1.0
    angle = 0.0
    dx = 0.0
    dy = 0.0

    data = convert(inp)
    pattern = engine.classify(data)
    lines = engine.extract_lines(data)

    if pattern == "empty":
        return "case6", 0.0, 0.0

    if pattern == "vertical_line":
        if lines:
            c1 = lines[0][0][1]
            c2 = lines[0][1][1]
            angle = (((c1 + c2) / 2.0) - 2.0) * 25.0
        return "case1", speed, angle

    elif pattern == "horizontal_line":
        if lines:
            r1 = lines[0][0][0]
            r2 = lines[0][1][0]
            dy = 1.5 - ((r1 + r2) / 2.0)
            if dy > 0:
                angle = 0.0
            else:
                angle = random.choice([90.0, -90.0])
        return "case2", speed, angle

    elif pattern == "diagonal_line":
        if lines:
            r1, c1 = lines[0][0]
            r2, c2 = lines[0][1]
            dx = c2 - c1
            dy = -(r2 - r1)
            if dy < 0:
                dx = -dx
                dy = -dy
            elif dy == 0:
                if random.choice([True, False]): dx = -dx
            angle = math.degrees(math.atan2(dx, dy))
        return "case3", speed, angle

    elif pattern == "intersection/cross":
        if lines:
            chosen = random.choice(lines)
            dx = chosen[1][1] - chosen[0][1]
            dy = -(chosen[1][0] - chosen[0][0])
            if dy < 0:
                dx = -dx
                dy = -dy
            elif dy == 0:
                if random.choice([True, False]): dx = -dx
            angle = math.degrees(math.atan2(dx, dy))
        return "case4", speed, angle

    elif pattern == "curve":
        if lines:
            dx = lines[0][1][1] - lines[0][0][1]
            dy = -(lines[0][1][0] - lines[0][0][0])
            if dy < 0:
                dx = -dx
                dy = -dy
            elif dy == 0:
                if random.choice([True, False]): dx = -dx
            angle = math.degrees(math.atan2(dx, dy))
        return "case5", speed, angle

    else:
        return "case7", speed, 0.0


# ==========================================
# 2. Pygame Setup & State
# ==========================================
pygame.init()
screen = pygame.display.set_mode((800, 800))
pygame.display.set_caption("Grid CNN Line Follower - Smooth Steering & Centered Sensor")
clock = pygame.time.Clock()

mode = "draw"
paths = []
last_pos = None

# Robot Physical State
rx, ry = 400.0, 600.0  # Start near bottom middle
heading = 90.0  # 90 degrees = Pointing Up (North)
smooth_steering = 0.0  # Tracks the continuous steering momentum


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    """Calculates the shortest distance from a point to a line segment."""
    l2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    if l2 == 0: return math.hypot(px - x1, py - y1)
    t = max(0, min(1, ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / l2))
    proj_x = x1 + t * (x2 - x1)
    proj_y = y1 + t * (y2 - y1)
    return math.hypot(px - proj_x, py - proj_y)


# ==========================================
# 3. Main Game Loop
# ==========================================
print("\nCONTROLS:")
print("- Click and drag to draw a thick path (start on top of the blue robot).")
print("- Press [SPACEBAR] to release the robot.")

running = True
while running:
    screen.fill((255, 255, 255))

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and mode == "draw":
                print("\n--- SWITCHING TO AUTONOMOUS TRACKING ---")
                mode = "follow"

    # --- Draw Mode Logic ---
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

    # --- Render the Track ---
    LINE_THICKNESS = 16
    for (x1, y1, x2, y2) in paths:
        pygame.draw.line(screen, (0, 0, 0), (x1, y1), (x2, y2), LINE_THICKNESS)
        pygame.draw.circle(screen, (0, 0, 0), (x1, y1), LINE_THICKNESS // 2)
        pygame.draw.circle(screen, (0, 0, 0), (x2, y2), LINE_THICKNESS // 2)

    # --- Vector Math for Local Frame ---
    H_rad = math.radians(heading)
    f_x = math.cos(H_rad)
    f_y = -math.sin(H_rad)  # Inverted Y for Pygame coordinate space

    l_x = math.cos(H_rad + math.pi / 2)
    l_y = -math.sin(H_rad + math.pi / 2)

    # --- Area Sensor Grid Detection ---
    CELL_SIZE = 14
    SENSOR_RADIUS = 6

    sensor_data = [[0] * 5 for _ in range(4)]

    for r in range(4):
        for c in range(5):
            # NEW: Offset the rows so the grid rests exactly in the middle of the robot.
            # (1.5 - r) means rows 0 to 3 range mathematically from +1.5 to -1.5
            forward_dist = (1.5 - r) * CELL_SIZE
            left_dist = (2 - c) * CELL_SIZE

            # Map grid node to screen coordinates
            sx = rx + (f_x * forward_dist) + (l_x * left_dist)
            sy = ry + (f_y * forward_dist) + (l_y * left_dist)

            # Collision Detection
            hit = False
            for (x1, y1, x2, y2) in paths:
                if point_to_segment_dist(sx, sy, x1, y1, x2, y2) <= (LINE_THICKNESS / 2 + SENSOR_RADIUS):
                    hit = True
                    break

            if hit:
                sensor_data[r][c] = 1
                color = (0, 200, 0)  # Green = Triggered
            else:
                color = (255, 0, 0)  # Red = Empty

            pygame.draw.circle(screen, color, (int(sx), int(sy)), SENSOR_RADIUS)

    # --- Follow Mode & Centering AI Logic ---
    if mode == "follow":
        case, speed, slope_angle = process_sensor_data(sensor_data)

        if speed > 0:
            active_cols = [c for r in range(4) for c in range(5) if sensor_data[r][c] == 1]

            offset_angle = 0.0
            if active_cols:
                avg_c = sum(active_cols) / len(active_cols)
                offset_error = avg_c - 2.0
                offset_angle = offset_error * 25.0

                # Combine base slope with the centering correction
            target_steering_angle = slope_angle + offset_angle

            # NEW: Apply Low-Pass Filter for smooth, continuous turning momentum
            # The smaller the multiplier (e.g., 0.15), the smoother and heavier the steering feels.
            smooth_steering += (target_steering_angle - smooth_steering) * 0.65

            STEERING_SENSITIVITY = 0.15
            heading -= (smooth_steering * STEERING_SENSITIVITY)

            # Drive forward
            rx += f_x * (speed * 4.0)
            ry += f_y * (speed * 4.0)

    # --- Render Robot ---
    p1 = (rx + f_x * 20, ry + f_y * 20)  # Nose
    p2 = (rx - f_x * 10 + l_x * 14, ry - f_y * 10 + l_y * 14)  # Back Left
    p3 = (rx - f_x * 10 - l_x * 14, ry - f_y * 10 - l_y * 14)  # Back Right
    pygame.draw.polygon(screen, (0, 50, 255), [p1, p2, p3])

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()