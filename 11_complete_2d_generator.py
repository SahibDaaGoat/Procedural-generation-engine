"""Experiment 11 — combine BSP, rooms, corridors, graphs, routing, and validation."""

from __future__ import annotations

import argparse

import matplotlib.pyplot as plt
import numpy as np

from map_utils import (
    Partition,
    Rect,
    bfs_path,
    build_grid,
    collect_leaves,
    collect_partitions,
    graph_from_edges,
    make_rooms,
    plot_map,
    plot_partitions,
    plot_rooms,
    room_edges,
    split_partition,
    validate_map,
)


SEED = 42
MAP_WIDTH = 120
MAP_HEIGHT = 80
MIN_PARTITION_SIZE = 16
MAX_DEPTH = 4
MIN_ROOMS = 4
MIN_PLAYABLE_AREA = 100


def generate_complete_map(
    seed: int,
    map_width: int,
    map_height: int,
    minimum_partition_size: int,
    maximum_depth: int,
):
    """Run the complete educational 2D generation pipeline."""

    rng = np.random.default_rng(seed)
    root = Partition(Rect(0, 0, map_width, map_height), depth=0)

    # First create spatial structure, then fill the leaf regions with rooms.
    split_partition(root, rng, minimum_partition_size, maximum_depth)
    partitions = collect_partitions(root)
    rooms = make_rooms(collect_leaves(root), rng, margin=2, minimum_room_size=5)

    # The nearest-region tree guarantees connectivity; extra edges add variety.
    edges = room_edges(rooms, extra_edges=2)
    graph = graph_from_edges(len(rooms), edges)
    grid = build_grid(map_width, map_height, rooms, edges)
    start = 0
    goal = len(rooms) - 1
    path = bfs_path(graph, start, goal) if rooms else []
    valid, reasons = validate_map(
        rooms,
        graph,
        grid,
        start=start,
        goal=goal if rooms else None,
        minimum_rooms=MIN_ROOMS,
        minimum_playable_area=MIN_PLAYABLE_AREA,
    )
    return partitions, rooms, edges, graph, grid, path, valid, reasons


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--width", type=int, default=MAP_WIDTH)
    parser.add_argument("--height", type=int, default=MAP_HEIGHT)
    parser.add_argument("--minimum-partition-size", type=int, default=MIN_PARTITION_SIZE)
    parser.add_argument("--depth", type=int, default=MAX_DEPTH)
    args = parser.parse_args()

    partitions, rooms, edges, graph, grid, path, valid, reasons = generate_complete_map(
        args.seed, args.width, args.height, args.minimum_partition_size, args.depth
    )
    print(f"Seed: {args.seed}")
    print(f"Partitions: {len(partitions)}")
    print(f"Rooms: {len(rooms)}")
    print(f"Connections: {len(edges)}")
    print(f"Graph path length: {max(0, len(path) - 1)}")
    print(f"Validation: {'VALID' if valid else 'INVALID'}")
    if reasons:
        print("Reasons: " + "; ".join(reasons))

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    plot_partitions(axes[0], partitions)
    plot_rooms(axes[0], rooms)
    axes[0].set_title("BSP partitions and generated rooms")
    axes[0].set_xlim(0, args.width)
    axes[0].set_ylim(0, args.height)
    axes[0].set_aspect("equal")
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")

    status = "VALID" if valid else "INVALID"
    detail = status if valid else status + "\n" + "\n".join(reasons)
    plot_map(
        axes[1],
        grid,
        rooms,
        edges,
        graph_path=path,
        start=0 if rooms else None,
        goal=len(rooms) - 1 if rooms else None,
        title="Complete 2D procedural map",
        validation_text=detail,
    )
    axes[1].legend(loc="upper right")
    fig.suptitle("Experiment 11 — Complete 2D Procedural Generator", fontsize=15)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

