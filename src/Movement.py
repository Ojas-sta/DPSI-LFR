from AI_Goal import ParametricGridEngine
from AI_Goal import AI_CONFIG
import numpy as np
import math

engine = ParametricGridEngine(AI_CONFIG)

body = {
    "velocity": [0, 0],
    "angle": 0,
}

sensor = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
def convert(inp):
    return[[col != 0 for col in row]for row in inp]

data = convert(sensor)

def casanal(inp):
    if engine.classify(inp) == "vertical_line":
        return "case1"
    elif engine.classify(inp) == "horizontal_line":
        return "case2"
    elif engine.classify(inp) == "diagonal_line":
        return "case3"
    elif engine.classify(inp) == "intersection/cross":
        return "case4"
    elif engine.classify(inp) == "curve":
        return "case5"
    elif engine.classify(inp) == "empty":
        return "case6"
    else:
        return "case7"

def native(inp):
    c = np.array(inp)
    x = c.tolist()
    return [x[0][0][0]-x[0][1][0], x[0][0][1]-x[0][1][1]]

def movement(inp):
    if engine.classify(inp) == "vertical_line":
        vele



