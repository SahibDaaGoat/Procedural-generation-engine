"""Experiment 10 — validate procedural maps instead of accepting every random result."""

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
    validate_map,
)


def create_example(seed: int, width: int, height: int, depth: int, room_limit: int | None = None):
    rng = np.random.default_rng(seed)
    root = Partition(Rect(0, 0, width, height), depth=0)
    split_partition(root, rng, minimum_size=14, maximum_depth=depth)
    rooms = make_rooms(collect_leaves(root), rng, margin=2, minimum_room_size=5)
    if room_limit is not None:
        rooms = rooms[:room_limit]
    edges = room_edges(rooms)
    graph = graph_from_edges(len(rooms), edges)
    grid = build_grid(width, height, rooms, edges)
    return rooms, edges, graph, grid


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    accepted_rooms, accepted_edges, accepted_graph, accepted_grid = create_example(args.seed, 100, 70, 4)
    accepted, accepted_reasons = validate_map(
        accepted_rooms,
        accepted_graph,
        accepted_grid,
        minimum_rooms=4,
        minimum_playable_area=100,
    )

    rejected_rooms, rejected_edges, rejected_graph, rejected_grid = create_example(
        args.seed + 1, 100, 70, 2, room_limit=3
    )
    rejected, rejected_reasons = validate_map(
        rejected_rooms,
        rejected_graph,
        rejected_grid,
        minimum_rooms=5,
        minimum_playable_area=2500,
    )

    print(f"Accepted example: {accepted}")
    print(f"Accepted reasons: {accepted_reasons or ['all constraints passed']}")
    print(f"Rejected example: {rejected}")
    print(f"Rejected reasons: {rejected_reasons or ['all constraints passed']}")

    accepted_text = "VALID\n" + ("All constraints passed" if accepted else "\n".join(accepted_reasons))
    rejected_text = "VALID\n" + ("All constraints passed" if rejected else "\n".join(rejected_reasons))
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    plot_map(
        axes[0],
        accepted_grid,
        accepted_rooms,
        accepted_edges,
        title="Accepted generated map",
        validation_text=accepted_text,
    )
    plot_map(
        axes[1],
        rejected_grid,
        rejected_rooms,
        rejected_edges,
        title="Rejected generated map",
        validation_text=rejected_text.replace("VALID", "INVALID", 1),
    )
    fig.suptitle("Experiment 10 — Constraint Validation", fontsize=14)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()

