from AI_Goal import ParametricGridEngine, AI_CONFIG
import math
import random

engine = ParametricGridEngine(AI_CONFIG)


sensor = [

[1, 0, 0, 0, 0],
[0, 1, 1, 0, 0],
[0, 0, 0, 1, 1],
[0, 0, 0, 0, 1],
]

def convert(inp):
    return [[bool(col) for col in row] for row in inp]


def native(lines):
    p1 = None
    p2 = None
    if not lines:
        return [0, 0]
    p1, p2 = lines[0]
    return [p2[0] - p1[0], p2[1] - p1[1]]


def process_sensor_data(inp):

    data = []
    pattern = ""
    lines = []

    speed = 1.0
    angle = 0.0

    r1 = 0.0;
    r2 = 0.0
    c1 = 0.0;
    c2 = 0.0
    dx = 0.0;
    dy = 0.0
    chosen = None
    # -----------------------------------------------

    data = convert(inp)
    pattern = engine.classify(data)
    lines = engine.extract_lines(data)

    if pattern == "empty":
        speed = 0.0
        angle = 0.0
        return "case6", speed, angle

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
                dx = -dx;
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
                dx = -dx;
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
                dx = -dx;
                dy = -dy
            elif dy == 0:
                if random.choice([True, False]): dx = -dx

            angle = math.degrees(math.atan2(dx, dy))
        return "case5", speed, angle

    else:
        return "case7", speed, 0.0


detected_case = ""
robot_speed = 0.0
robot_angle = 0.0
raw_vector = [0, 0]
turn_direction = ""

# Execute core logic
detected_case, robot_speed, robot_angle = process_sensor_data(sensor)
raw_vector = native(engine.extract_lines(convert(sensor)))


if robot_angle > 0:
    turn_direction = "(Right)"
elif robot_angle < 0:
    turn_direction = "(Left)"
else:
    turn_direction = "(Straight)"

print(f"Case: {detected_case}")
print(f"Robot Speed: {robot_speed}")
print(f"Target Angle: {robot_angle:+0.2f} degrees {turn_direction}")
print(f"Native Vector: {raw_vector}")