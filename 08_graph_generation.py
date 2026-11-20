"""Experiment 08 — represent generated rooms as nodes in a graph."""

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    width, height = 100, 70
    rng = np.random.default_rng(args.seed)
    root = Partition(Rect(0, 0, width, height), depth=0)
    split_partition(root, rng, minimum_size=14, maximum_depth=4)
    rooms = make_rooms(collect_leaves(root), rng, margin=2, minimum_room_size=5)
    edges = room_edges(rooms, extra_edges=2)
    graph = graph_from_edges(len(rooms), edges)
    grid = build_grid(width, height, rooms, edges)

    print(f"Seed: {args.seed}")
    print(f"Graph nodes: {len(graph)}")
    print(f"Graph edges: {len(edges)}")
    print(f"Room 0 neighbors: {graph.get(0, [])}")

    fig, ax = plt.subplots(figsize=(11, 7))
    plot_map(ax, grid, rooms, edges, title="Experiment 08 — Physical Map and Logical Room Graph")
    ax.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

