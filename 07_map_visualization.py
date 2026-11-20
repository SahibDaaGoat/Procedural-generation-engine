"""Experiment 07 — rasterize rooms and corridors into a 2D NumPy map."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from map_utils import (
    Partition,
    Rect,
    build_grid,
    collect_leaves,
    graph_from_edges,
    make_rooms,
    plot_map,
    room_edges,
    split_partition,
)


def generate_map(seed: int, width: int, height: int, minimum_size: int, depth: int):
    rng = np.random.default_rng(seed)
    root = Partition(Rect(0, 0, width, height), depth=0)
    split_partition(root, rng, minimum_size, depth)
    rooms = make_rooms(collect_leaves(root), rng, margin=2, minimum_room_size=5)
    edges = room_edges(rooms)
    return rooms, edges, build_grid(width, height, rooms, edges)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--width", type=int, default=100)
    parser.add_argument("--height", type=int, default=70)
    parser.add_argument("--minimum-size", type=int, default=14)
    parser.add_argument("--depth", type=int, default=4)
    args = parser.parse_args()

    rooms, edges, grid = generate_map(args.seed, args.width, args.height, args.minimum_size, args.depth)
    print(f"Seed: {args.seed}")
    print(f"Rooms: {len(rooms)}")
    print(f"Connections: {len(edges)}")
    print(f"Playable cells: {int(np.count_nonzero(grid))}")

    fig, ax = plt.subplots(figsize=(11, 7))
    plot_map(ax, grid, rooms, edges, title="Experiment 07 — 2D Procedural Map Representation")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

