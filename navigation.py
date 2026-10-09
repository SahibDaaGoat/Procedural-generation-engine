
from collections import deque


def draw_navigation(ax, rooms_list, graph, start_room, target_room):
    # Calculate the centre of each room.
    centres = []

    for x, y, width, height in rooms_list:
        centres.append((
            x + width / 2,
            y + height / 2
        ))

    # Convert room numbers from 1-based to 0-based indices.
    start = start_room - 1
    target = target_room - 1

    # Validate room numbers.
    if not (0 <= start < len(rooms_list)):
        print("Invalid starting room number.")
        return None

    if not (0 <= target < len(rooms_list)):
        print("Invalid target room number.")
        return None

    # Find the shortest path using BFS.
    def bfs(graph, start, target):
        queue = deque([[start]])
        visited = {start}

        while queue:
            current_path = queue.popleft()
            node = current_path[-1]

            if node == target:
                return current_path

            for neighbour in graph[node]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    queue.append(current_path + [neighbour])

        return None

    path = bfs(graph, start, target)

    if path is None:
        print(
            f"No path exists from room {start_room} "
            f"to room {target_room}."
        )
        return None

    # Draw every graph connection once.
    for room, neighbours in graph.items():
        x1, y1 = centres[room]

        for neighbour in neighbours:
            if neighbour > room:
                x2, y2 = centres[neighbour]

                ax.plot(
                    [x1, x2],
                    [y1, y2],
                    color="darkkhaki",
                    linewidth=2,
                    zorder=1
                )

    # Highlight the selected shortest path in red.
    for i in range(len(path) - 1):
        x1, y1 = centres[path[i]]
        x2, y2 = centres[path[i + 1]]

        ax.plot(
            [x1, x2],
            [y1, y2],
            color="red",
            linewidth=3,
            zorder=3
        )

    print(
        f"Path from room {start_room} to room {target_room}:",
        [room + 1 for room in path]
    )

    return path
