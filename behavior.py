"""Small deterministic movement and web helpers, independent of Qt."""
import math

def turn_towards(angle, target, blend=0.16):
    return angle + ((target - angle + 180) % 360 - 180) * blend

def step_towards(x, y, tx, ty, speed):
    distance = math.hypot(tx-x, ty-y)
    if distance == 0:
        return x, y
    step = min(speed, distance)
    return x + (tx-x)/distance*step, y + (ty-y)/distance*step

def edge_key(start, end):
    return frozenset((start['name'], end['name']))
