"""Room adjacency and graph path-finding algorithms."""

from collections import deque


def are_adjacent(first, second):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second

    vertical_touch = ax + aw == bx or bx + bw == ax
    if vertical_touch and max(ay, by) < min(ay + ah, by + bh):
        return True

    horizontal_touch = ay + ah == by or by + bh == ay
    return horizontal_touch and max(ax, bx) < min(ax + aw, bx + bw)


def build_graph(regions):
    graph = {i: [] for i in range(len(regions))}
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            if are_adjacent(regions[i], regions[j]):
                graph[i].append(j)
                graph[j].append(i)
    return graph


def depth_first_path(graph, start, target):
    visited = set()
    path = []

    def search(node):
        visited.add(node)
        path.append(node)
        if node == target:
            return True
        for neighbour in graph[node]:
            if neighbour not in visited and search(neighbour):
                return True
        path.pop()
        return False

    return path if search(start) else None


def breadth_first_path(graph, start, target):
    queue = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        node = path[-1]
        if node == target:
            return path
        for neighbour in graph[node]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(path + [neighbour])
    return None
