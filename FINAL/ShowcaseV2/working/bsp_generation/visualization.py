"""Matplotlib rendering for generated maps."""

import matplotlib.pyplot as plt

from bsp_generation.geometry import center
from graphs_navigation.navigation import draw_navigation


def show_map(width, height, rooms, graph, start_room, target_room, stairs=None, floor_number=None):
    fig, ax = plt.subplots()
    for number, room in enumerate(rooms, start=1):
        x, y, room_width, room_height = room
        rectangle = plt.Rectangle(
            (x, y), room_width, room_height,
            fill=True, edgecolor="black", facecolor="silver",
            linewidth=1.5, zorder=2,
        )
        ax.add_patch(rectangle)
        cx, cy = center(room)
        ax.text(cx, cy, str(number), ha="center", va="center", fontsize=7, zorder=4)

    draw_navigation(ax, rooms, graph, start_room, target_room)
    for stair in stairs or []:
        for endpoint_name, label in (("from", "UP"), ("to", "DOWN")):
            endpoint = stair[endpoint_name]
            if endpoint["floor"] != floor_number:
                continue
            position = endpoint["position"]
            ax.scatter(position["x"], position["y"], color="purple", marker="^", s=55, zorder=5)
            ax.annotate(
                label, (position["x"], position["y"]),
                xytext=(5, 5), textcoords="offset points",
                color="purple", fontsize=8, zorder=6,
            )
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    title = f"BSP Procedural Generation - {len(rooms)} Rooms"
    if floor_number is not None:
        title += f" - Floor {floor_number}"
    ax.set_title(title)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True, zorder=0)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    plt.show()
    plt.close(fig)
