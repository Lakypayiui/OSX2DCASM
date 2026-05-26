import numpy as np
import json

rule = np.zeros(512, dtype=np.uint8)

for idx in range(512):

    # Extraer bits
    bits = [(idx >> i) & 1 for i in range(9)]

    center = bits[4]

    neighbors = (
        bits[0] + bits[1] + bits[2] +
        bits[3] + bits[5] +
        bits[6] + bits[7] + bits[8]
    )

    alive = 0

    # Conway's Game of Life
    if center == 1:
        if neighbors == 2 or neighbors == 3:
            alive = 1
    else:
        if neighbors == 3:
            alive = 1

    rule[idx] = alive

print(rule.tolist())

data = {
    "Game of Life": {
        "rule": rule.tolist()
    }
}

with open("presets/rules.json", "w") as f:
    json.dump(data, f, indent=4)