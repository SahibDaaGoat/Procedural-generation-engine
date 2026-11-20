"""Small shared helpers for the 2D procedural-generation experiments.

The helpers are deliberately simple. They keep the later experiments readable
without turning the examples into a production framework.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle as RectanglePatch


@dataclass
class Rect:
    """A small axis-aligned rectangle used for partitions and rooms."""

    x: int
    y: int
    width: int
    height: int
    label: str = ""

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x + self.width <= other.x
            or other.x + other.width <= self.x
            or self.y + self.height <= other.y
            or other.y + other.height <= self.y
        )

    def contains_point(self, x: float, y: float) -> bool:
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


@dataclass
class Partition:
    """A node in a very small binary space partition tree."""

    rect: Rect
    depth: int
    left: "Partition | None" = None
    right: "Partition | None" = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


def split_partition(
    node: Partition,
    rng: np.random.Generator,
    minimum_size: int,
    maximum_depth: int,
) -> None:
    """Recursively split a partition while both children can remain useful."""

    if node.depth >= maximum_depth:
        return

    rect = node.rect
    possible_directions: list[str] = []
    if rect.width >= minimum_size * 2:
        possible_directions.append("vertical")
    if rect.height >= minimum_size * 2:
        possible_directions.append("horizontal")
    if not possible_directions:
        return

    direction = str(rng.choice(possible_directions))
    if direction == "vertical":
        split_at = int(rng.integers(minimum_size, rect.width - minimum_size + 1))
        first = Rect(rect.x, rect.y, split_at, rect.height)
        second = Rect(rect.x + split_at, rect.y, rect.width - split_at, rect.height)
    else:
        split_at = int(rng.integers(minimum_size, rect.height - minimum_size + 1))
        first = Rect(rect.x, rect.y, rect.width, split_at)
        second = Rect(rect.x, rect.y + split_at, rect.width, rect.height - split_at)

    node.left = Partition(first, node.depth + 1)
    node.right = Partition(second, node.depth + 1)
    split_partition(node.left, rng, minimum_size, maximum_depth)
    split_partition(node.right, rng, minimum_size, maximum_depth)


def collect_partitions(node: Partition) -> list[Partition]:
    """Return every partition node in tree order."""

    result = [node]
    if node.left is not None:
        result.extend(collect_partitions(node.left))
    if node.right is not None:
        result.extend(collect_partitions(node.right))
    return result


def collect_leaves(node: Partition) -> list[Partition]:
    """Return only the final regions of a partition tree."""

    if node.is_leaf:
        return [node]
    leaves: list[Partition] = []
    if node.left is not None:
        leaves.extend(collect_leaves(node.left))
    if node.right is not None:
        leaves.extend(collect_leaves(node.right))
    return leaves


def make_rooms(
    leaves: Iterable[Partition],
    rng: np.random.Generator,
    margin: int = 2,
    minimum_room_size: int = 4,
) -> list[Rect]:
    """Create one smaller random room inside each leaf partition."""

    rooms: list[Rect] = []
    for index, leaf in enumerate(leaves):
        region = leaf.rect
        available_width = region.width - margin * 2
        available_height = region.height - margin * 2
        if available_width < minimum_room_size or available_height < minimum_room_size:
            continue

        room_width = int(rng.integers(minimum_room_size, available_width + 1))
        room_height = int(rng.integers(minimum_room_size, available_height + 1))
        offset_x = margin + int(rng.integers(0, available_width - room_width + 1))
        offset_y = margin + int(rng.integers(0, available_height - room_height + 1))
        rooms.append(
            Rect(
                region.x + offset_x,
                region.y + offset_y,
                room_width,
                room_height,
                label=f"R{index}",
            )
        )
    return rooms


def room_edges(rooms: list[Rect], extra_edges: int = 0) -> list[tuple[int, int]]:
    """Connect rooms with a simple nearest-region tree plus optional shortcuts."""

    if len(rooms) < 2:
        return []

    connected = {0}
    remaining = set(range(1, len(rooms)))
    edges: list[tuple[int, int]] = []

    while remaining:
        best_pair: tuple[int, int] | None = None
        best_distance = float("inf")
        for source in connected:
            sx, sy = rooms[source].center
            for target in remaining:
                tx, ty = rooms[target].center
                distance = (sx - tx) ** 2 + (sy - ty) ** 2
                if distance < best_distance:
                    best_distance = distance
                    best_pair = (source, target)
        assert best_pair is not None
        edges.append(best_pair)
        connected.add(best_pair[1])
        remaining.remove(best_pair[1])

    candidates = [
        (i, j)
        for i in range(len(rooms))
        for j in range(i + 1, len(rooms))
        if (i, j) not in edges and (j, i) not in edges
    ]
    candidates.sort(
        key=lambda pair: (
            (rooms[pair[0]].center[0] - rooms[pair[1]].center[0]) ** 2
            + (rooms[pair[0]].center[1] - rooms[pair[1]].center[1]) ** 2
        )
    )
    edges.extend(candidates[: max(0, extra_edges)])
    return edges


def graph_from_edges(room_count: int, edges: Iterable[tuple[int, int]]) -> dict[int, list[int]]:
    """Build an undirected adjacency-list graph."""

    graph = {index: [] for index in range(room_count)}
    for first, second in edges:
        graph[first].append(second)
        graph[second].append(first)
    return graph


def bfs_path(graph: dict[int, list[int]], start: int, goal: int) -> list[int]:
    """Return a shortest unweighted graph path, or an empty list."""

    queue: deque[int] = deque([start])
    previous: dict[int, int | None] = {start: None}
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbor in graph.get(current, []):
            if neighbor not in previous:
                previous[neighbor] = current
                queue.append(neighbor)

    if goal not in previous:
        return []
    path: list[int] = []
    current: int | None = goal
    while current is not None:
        path.append(current)
        current = previous[current]
    return path[::-1]


def carve_corridor(
    grid: np.ndarray,
    first: Rect,
    second: Rect,
    corridor_width: int = 1,
) -> None:
    """Carve a simple L-shaped corridor between two room centers."""

    x1, y1 = (int(round(value)) for value in first.center)
    x2, y2 = (int(round(value)) for value in second.center)
    points: list[tuple[int, int]] = []
    for x in range(min(x1, x2), max(x1, x2) + 1):
        points.append((x, y1))
    for y in range(min(y1, y2), max(y1, y2) + 1):
        points.append((x2, y))

    radius = max(0, corridor_width // 2)
    for x, y in points:
        x_start = max(0, x - radius)
        x_end = min(grid.shape[1], x + radius + 1)
        y_start = max(0, y - radius)
        y_end = min(grid.shape[0], y + radius + 1)
        grid[y_start:y_end, x_start:x_end] = 2


def build_grid(width: int, height: int, rooms: list[Rect], edges: Iterable[tuple[int, int]]) -> np.ndarray:
    """Rasterize rooms as 1 and corridors as 2 in a NumPy grid."""

    grid = np.zeros((height, width), dtype=np.int8)
    for room in rooms:
        grid[room.y : room.y + room.height, room.x : room.x + room.width] = 1
    for first, second in edges:
        carve_corridor(grid, rooms[first], rooms[second])
    return grid


def plot_partitions(ax: plt.Axes, partitions: Iterable[Partition]) -> None:
    """Draw partition boundaries without hiding the spatial hierarchy."""

    for partition in partitions:
        rect = partition.rect
        alpha = max(0.15, 0.65 - partition.depth * 0.08)
        ax.add_patch(
            RectanglePatch(
                (rect.x, rect.y),
                rect.width,
                rect.height,
                fill=False,
                edgecolor="#8c6b43",
                linewidth=1.0,
                alpha=alpha,
            )
        )


def plot_rooms(ax: plt.Axes, rooms: Iterable[Rect], color: str = "#d7b878", alpha: float = 0.65) -> None:
    """Draw room boundaries and optional labels."""

    for index, room in enumerate(rooms):
        ax.add_patch(
            RectanglePatch(
                (room.x, room.y),
                room.width,
                room.height,
                facecolor=color,
                edgecolor="#3d2a1b",
                linewidth=1.4,
                alpha=alpha,
            )
        )
        ax.text(*room.center, room.label or f"R{index}", ha="center", va="center", fontsize=8)


def plot_map(
    ax: plt.Axes,
    grid: np.ndarray,
    rooms: list[Rect],
    edges: list[tuple[int, int]],
    graph_path: list[int] | None = None,
    start: int | None = None,
    goal: int | None = None,
    title: str = "",
    validation_text: str | None = None,
) -> None:
    """Render a dungeon-like NumPy grid and optional graph overlays."""

    cmap = ListedColormap(["#242932", "#d9be82", "#9b784b"])
    ax.imshow(grid, origin="lower", cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
    for first, second in edges:
        x1, y1 = rooms[first].center
        x2, y2 = rooms[second].center
        ax.plot([x1, x2], [y1, y2], color="#6b4f2d", linewidth=1, alpha=0.45)

    if graph_path:
        xs = [rooms[index].center[0] for index in graph_path]
        ys = [rooms[index].center[1] for index in graph_path]
        ax.plot(xs, ys, color="#b33a2b", linewidth=3, marker="o", label="BFS route")

    centers_x = [room.center[0] for room in rooms]
    centers_y = [room.center[1] for room in rooms]
    ax.scatter(centers_x, centers_y, color="#2f4f3a", s=22, zorder=4, label="Room nodes")
    if start is not None:
        ax.scatter(*rooms[start].center, color="#4c8bf5", s=90, marker="*", zorder=5, label="Start")
    if goal is not None:
        ax.scatter(*rooms[goal].center, color="#9c2f2f", s=75, marker="X", zorder=5, label="Goal")

    if validation_text:
        ax.text(
            0.02,
            0.98,
            validation_text,
            transform=ax.transAxes,
            va="top",
            bbox={"facecolor": "#f4e6c8", "edgecolor": "#6b4f2d", "alpha": 0.9},
        )
    ax.set_title(title)
    ax.set_aspect("equal")
    ax.set_xlim(0, grid.shape[1])
    ax.set_ylim(0, grid.shape[0])
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(False)


def validate_map(
    rooms: list[Rect],
    graph: dict[int, list[int]],
    grid: np.ndarray,
    start: int = 0,
    goal: int | None = None,
    minimum_rooms: int = 4,
    minimum_playable_area: int = 100,
) -> tuple[bool, list[str]]:
    """Apply simple constraints and return a status plus human-readable reasons."""

    goal = len(rooms) - 1 if goal is None and rooms else goal
    reasons: list[str] = []
    if len(rooms) < minimum_rooms:
        reasons.append(f"requires at least {minimum_rooms} rooms")
    if any(room.width <= 0 or room.height <= 0 for room in rooms):
        reasons.append("contains a room with invalid dimensions")
    playable_area = int(np.count_nonzero(grid))
    if playable_area < minimum_playable_area:
        reasons.append(f"playable area is {playable_area}, below {minimum_playable_area}")
    if rooms and goal is not None and not bfs_path(graph, start, goal):
        reasons.append("start and goal are not connected")
    return not reasons, reasons
