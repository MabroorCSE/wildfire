"""Find cells that become fully surrounded by fire, and when.

For each cell, its "surround time" is the latest first-ignition time among
the cell itself and its 8 neighbours. Edge cells (fewer than 8 neighbours
in the map) are skipped.

Usage:
    python3 python/find_surrounded.py output_1.csv
"""

import csv
import sys

CELL_SIZE = 30  # metres between cell centres on the training map


def load_first_ignitions(csv_path):
    """Return a dict {(x, y): first simtime where ignited == 1}.

    Every cell in the CSV should appear as a key, even if it never ignites
    (use float("inf") for those), so later we can tell "never burned" apart
    from "not on the map".
    """
    first_ignition = {}
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)   # each row is a dict: row["x"], row["ignited"], ...
        for row in reader:
            x = int(row["x"])
            y = int(row["y"])
            # 1: the CSV gives strings, so convert them
            simtime = float(row["simtime"])
            ignited = row["ignited"] == "1"

            # 2: first time we see this cell, mark it "never ignited" for now
            if (x, y) not in first_ignition:
                first_ignition[(x, y)] = float("inf")

            # 3: on an ignited row, keep the earliest time seen so far
            if ignited:
                first_ignition[(x, y)] = min(first_ignition[(x, y)], simtime)
    return first_ignition


def neighbours(x, y, cell_size):
    """Return a list of the 8 (x, y) positions around (x, y)."""
    # TODO 4: loop dx and dy over (-cell_size, 0, +cell_size),
    #         skip dx == dy == 0, and collect (x + dx, y + dy)
    return []


def surround_time(cell, first_ignition, cell_size):
    """Return when `cell` and all 8 neighbours have ignited, or None
    if `cell` is on the edge (a neighbour is not in the map)."""
    # TODO 5: build the list of 9 positions (the cell + its neighbours)
    # TODO 6: if any position is not a key in first_ignition, return None
    # TODO 7: return the max of their first-ignition times
    return None


def earliest_surrounded(first_ignition, cell_size, n):
    """Return the n (time, cell) pairs with the smallest finite surround time."""
    results = []
    # TODO 8: for each cell, compute surround_time; keep it if it is not
    #         None and not inf; append (time, cell)
    # TODO 9: sort results and return the first n
    return results


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "output_1.csv"
    first_ignition = load_first_ignitions(csv_path)
    print(f"{len(first_ignition)} cells loaded")

    for time, (x, y) in earliest_surrounded(first_ignition, CELL_SIZE, 5):
        print(f"{x}_{y}  surrounded at {time:.1f} s")


if __name__ == "__main__":
    main()
