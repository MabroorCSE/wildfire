#!/usr/bin/env python3
"""
Generates a square NxN Cell-DEVS AsymmCell grid config (Moore neighborhood, 8 neighbors + self)
for the wildfire model. Flat terrain, uniform fuel/wind, single ignition point on one edge so
the fire has the whole grid to spread across.

Usage:
    python3 scripts/generate_grid.py <output.json> <size> <wind_speed_kmh> [wind_direction] [fuel_model]
"""

import json
import math
import sys

CELL_SIZE = 30.0  # meters
X0, Y0 = 500000, 5000000


def cell_id(i, j):
    return f"{X0 + i * int(CELL_SIZE)}_{Y0 + j * int(CELL_SIZE)}"


def build_config(size, wind_speed, wind_direction, fuel_model):
    cells = {
        "default": {
            "delay": "inertial",
            "eoc": ["cellStateOut"],
            "eic": [["cellCommandIn", "commandIn"]],
        }
    }

    ignition_j = size // 2

    for i in range(size):
        for j in range(size):
            x = X0 + i * int(CELL_SIZE)
            y = Y0 + j * int(CELL_SIZE)
            neighborhood = {cell_id(i, j): 0}
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    if di == 0 and dj == 0:
                        continue
                    ni, nj = i + di, j + dj
                    if 0 <= ni < size and 0 <= nj < size:
                        dist = CELL_SIZE * math.sqrt(di * di + dj * dj)
                        neighborhood[cell_id(ni, nj)] = dist

            cells[cell_id(i, j)] = {
                "neighborhood": neighborhood,
                "state": {
                    "fuelModelNumber": fuel_model,
                    "windDirection": wind_direction,
                    "windSpeed": wind_speed,
                    "x": float(x),
                    "y": float(y),
                    "elevation": 0.0,
                    "ignited": i == 0 and j == ignition_j,
                },
            }

    return {"cells": cells}


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)

    output_path = sys.argv[1]
    size = int(sys.argv[2])
    wind_speed = float(sys.argv[3])
    wind_direction = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
    fuel_model = int(sys.argv[5]) if len(sys.argv) > 5 else 9

    config = build_config(size, wind_speed, wind_direction, fuel_model)
    with open(output_path, "w") as f:
        json.dump(config, f)

    print(f"Wrote {output_path}: {size}x{size} grid, windSpeed={wind_speed}, windDirection={wind_direction}, fuelModel={fuel_model}")


if __name__ == "__main__":
    main()
