"""Add a route graph along BSP cell boundaries, with explicit room doors."""

from collections import defaultdict


def add_route_graphs(building):
    stairs_by_floor = defaultdict(list)
    for stair in building["stairs"]:
        stairs_by_floor[stair["from"]["floor"]].append((stair["from"], stair["id"], "up"))
        stairs_by_floor[stair["to"]["floor"]].append((stair["to"], stair["id"], "down"))
    for floor in building["floors"]:
        floor["route_graph"] = _build_routes(floor["rooms"], stairs_by_floor[floor["id"]])


def _build_routes(rooms, stairs):
    nodes = []
    edges = set()
    node_by_point = {}
    lines = defaultdict(list)
    line_breaks = defaultdict(set)
    doors = []
    stairs_by_room = defaultdict(list)
    for endpoint, stair_id, direction in stairs:
        stairs_by_room[endpoint["room"]].append((endpoint, stair_id, direction))

    def node(point, kind="junction", room=0, stair=0, direction=""):
        if point not in node_by_point:
            node_id = len(nodes) + 1
            node_by_point[point] = node_id
            nodes.append({
                "id": node_id, "kind": kind, "position": {"x": point[0], "y": point[1]},
                "room": room, "stair": stair, "direction": direction,
            })
        return node_by_point[point]

    def connect(first, second):
        if first != second:
            edges.add(tuple(sorted((first, second))))

    for room in rooms:
        cell = room["region"]
        x, y = cell["x"], cell["y"]
        right, top = x + cell["width"], y + cell["height"]
        for axis, constant, start, end in (
            (0, y, x, right), (0, top, x, right),
            (1, x, y, top), (1, right, y, top),
        ):
            key = (axis, constant)
            lines[key].append((start, end))
            line_breaks[key].update((start, end))

        room_id = room["id"]
        cx, cy = room["center"]["x"], room["center"]["y"]
        center_id = node((cx, cy), "room", room_id)
        bounds = room["bounds"]
        room_x, room_y = bounds["x"], bounds["y"]
        positions = {
            "west": ((room_x, cy), (x, cy), (1, x), cy),
            "east": ((room_x + bounds["width"], cy), (right, cy), (1, right), cy),
            "south": ((cx, room_y), (cx, y), (0, y), cx),
            "north": ((cx, room_y + bounds["height"]), (cx, top), (0, top), cx),
        }
        endpoints = stairs_by_room[room_id]
        # A stair door can serve as the room's entrance. Rooms without stairs get one door.
        if not endpoints:
            side = min(positions, key=lambda side: sum(
                abs(a - b) for a, b in zip(positions[side][0], positions[side][1])))
            endpoints = [({"side": side, "width": 1.0}, 0, "")]
        for endpoint, stair_id, direction in endpoints:
            point, outside, key, along = positions[endpoint["side"]]
            line_breaks[key].add(along)
            door_id = node(point, "stair" if stair_id else "door", room_id, stair_id, direction)
            connect(center_id, door_id)
            connect(door_id, node(outside))
            doors.append({
                "room": room_id, "node": door_id, "side": endpoint["side"],
                "position": {"x": point[0], "y": point[1]}, "width": endpoint["width"],
            })

    # A corner of one cell can meet the middle of another cell's side.
    # Every crossing gets a node before intervals are joined.
    for (axis, fixed), points in list(line_breaks.items()):
        for along in list(points):
            other = (1 - axis, along)
            if any(start <= fixed <= end for start, end in lines.get(other, ())):
                line_breaks[other].add(fixed)

    for (axis, fixed), intervals in sorted(lines.items()):
        points = sorted(line_breaks[(axis, fixed)])
        for first, second in zip(points, points[1:]):
            if any(start <= first and second <= end for start, end in intervals):
                a = (first, fixed) if axis == 0 else (fixed, first)
                b = (second, fixed) if axis == 0 else (fixed, second)
                connect(node(a), node(b))

    return {"nodes": nodes, "edges": [
        {"from_node": first, "to_node": second} for first, second in sorted(edges)
    ], "doors": doors}
