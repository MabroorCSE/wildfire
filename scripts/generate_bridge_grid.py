#!/usr/bin/env python3
"""
Generates a two-zone Cell-DEVS grid: a left block and a right block of flammable cells,
connected only through a narrow "bridge" corridor. Cells in the gap outside the bridge simply
don't exist, so fire can only reach the right block by crossing the bridge. Ignition starts on
the left block's far edge.

Usage:
    python3 scripts/generate_bridge_grid.py <output.json> <block_size> <gap_width> <bridge_width> <wind_speed_kmh> [fuel_model]
"""

import json
import math
import sys

CELL_SIZE = 30.0
X0, Y0 = 500000, 5000000


def cell_id(col, row):
    return f"{X0 + col * int(CELL_SIZE)}_{Y0 + row * int(CELL_SIZE)}"


def build_config(block_size, gap_width, bridge_width, wind_speed, fuel_model):
    left_cols = range(0, block_size)
    gap_cols = range(block_size, block_size + gap_width)
    right_cols = range(block_size + gap_width, 2 * block_size + gap_width)

    bridge_row_start = block_size // 2 - bridge_width // 2
    bridge_rows = set(range(bridge_row_start, bridge_row_start + bridge_width))

    existing = set()
    for col in left_cols:
        for row in range(block_size):
            existing.add((col, row))
    for col in right_cols:
        for row in range(block_size):
            existing.add((col, row))
    for col in gap_cols:
        for row in bridge_rows:
            existing.add((col, row))

    cells = {
        "default": {
            "delay": "inertial",
            "eoc": ["cellStateOut"],
            "eic": [["cellCommandIn", "commandIn"]],
        }
    }

    ignition_col, ignition_row = max(block_size - 4, 0), block_size // 2

    for (col, row) in existing:
        neighborhood = {cell_id(col, row): 0}
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = col + dc, row + dr
                if (nc, nr) in existing:
                    dist = CELL_SIZE * math.sqrt(dc * dc + dr * dr)
                    neighborhood[cell_id(nc, nr)] = dist

        x = X0 + col * int(CELL_SIZE)
        y = Y0 + row * int(CELL_SIZE)
        cells[cell_id(col, row)] = {
            "neighborhood": neighborhood,
            "state": {
                "fuelModelNumber": fuel_model,
                "windDirection": 0,
                "windSpeed": wind_speed,
                "x": float(x),
                "y": float(y),
                "elevation": 0.0,
                "ignited": col == ignition_col and row == ignition_row,
            },
        }

    return {"cells": cells}, bridge_rows, list(gap_cols)


def main():
    if len(sys.argv) < 6:
        print(__doc__)
        sys.exit(1)

    output_path = sys.argv[1]
    block_size = int(sys.argv[2])
    gap_width = int(sys.argv[3])
    bridge_width = int(sys.argv[4])
    wind_speed = float(sys.argv[5])
    fuel_model = int(sys.argv[6]) if len(sys.argv) > 6 else 9

    config, bridge_rows, gap_cols = build_config(block_size, gap_width, bridge_width, wind_speed, fuel_model)
    with open(output_path, "w") as f:
        json.dump(config, f)

    bridge_cell_ids = [cell_id(c, r) for c in gap_cols for r in sorted(bridge_rows)]
    print(f"Wrote {output_path}: {len(config['cells']) - 1} cells")
    print(f"Bridge cell ids ({len(bridge_cell_ids)}): {bridge_cell_ids}")


if __name__ == "__main__":
    main()
