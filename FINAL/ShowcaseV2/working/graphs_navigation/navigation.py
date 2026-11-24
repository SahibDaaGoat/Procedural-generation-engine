"""Drawing helpers for room links and the selected shortest route."""

from bsp_generation.geometry import center
from graphs_navigation.graph import breadth_first_path


def draw_navigation(ax, rooms, graph, start_room, target_room):
    centres = [center(room) for room in rooms]
    start = start_room - 1
    target = target_room - 1

    if not 0 <= start < len(rooms):
        print("Invalid starting room number.")
        return None
    if not 0 <= target < len(rooms):
        print("Invalid target room number.")
        return None

    path = breadth_first_path(graph, start, target)
    if path is None:
        print(f"No path exists from room {start_room} to room {target_room}.")
        return None

    for room, neighbours in graph.items():
        x1, y1 = centres[room]
        for neighbour in neighbours:
            if neighbour > room:
                x2, y2 = centres[neighbour]
                ax.plot([x1, x2], [y1, y2], color="darkkhaki", linewidth=2, zorder=1)

    for first, second in zip(path, path[1:]):
        x1, y1 = centres[first]
        x2, y2 = centres[second]
        ax.plot([x1, x2], [y1, y2], color="red", linewidth=3, zorder=3)

    print(f"Path from room {start_room} to room {target_room}:", [room + 1 for room in path])
    return path
