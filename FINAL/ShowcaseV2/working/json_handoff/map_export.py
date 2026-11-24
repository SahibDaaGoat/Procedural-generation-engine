"""Serialize generated map geometry and navigation data to JSON."""

import json
from pathlib import Path
import sys

from bsp_generation.geometry import center
from graphs_navigation.graph import breadth_first_path


if getattr(sys, "frozen", False):
    # Store exports beside the executable, outside PyInstaller's temp folder.
    EXPORT_DIRECTORY = Path(sys.executable).resolve().parent / "maps"
else:
    EXPORT_DIRECTORY = Path(__file__).resolve().parent / "maps"
SCHEMA_VERSION = 2


def _rectangle(region):
    x, y, width, height = region
    return {
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def build_map_data(seed, width, height, regions, rooms, graph, start_room, target_room, dfs_path):
    """Return the complete, engine-friendly map representation."""
    room_records = []
    for index, (region, room) in enumerate(zip(regions, rooms)):
        cx, cy = center(room)
        room_records.append({
            "id": index + 1,
            "region": _rectangle(region),
            "bounds": _rectangle(room),
            "center": {"x": cx, "y": cy},
            "connections": [neighbour + 1 for neighbour in graph[index]],
        })

    connections = [
        {"from": room + 1, "to": neighbour + 1}
        for room, neighbours in graph.items()
        for neighbour in neighbours
        if neighbour > room
    ]
    bfs_path = breadth_first_path(graph, start_room - 1, target_room - 1)

    return {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "seed": seed,
            "room_count": len(rooms),
            "map_width": width,
            "map_height": height,
        },
        "coordinate_system": {
            "origin": "bottom_left",
            "units": "map_units",
            "bounds": {"x": 0, "y": 0, "width": width, "height": height},
        },
        "navigation": {
            "start_room": start_room,
            "target_room": target_room,
            "dfs_path": [room + 1 for room in dfs_path] if dfs_path is not None else None,
            "shortest_path": [room + 1 for room in bfs_path] if bfs_path is not None else None,
            "connections": connections,
        },
        "rooms": room_records,
    }


def export_map(seed, width, height, regions, rooms, graph, start_room, target_room, dfs_path):
    """Write one JSON file and return its path."""
    EXPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = (
        f"map_seed-{seed}_rooms-{len(rooms)}_"
        f"width-{width}_height-{height}.json"
    )
    output_path = EXPORT_DIRECTORY / filename
    map_data = build_map_data(
        seed, width, height, regions, rooms, graph,
        start_room, target_room, dfs_path,
    )
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(map_data, output_file, indent=2)
        output_file.write("\n")
    return output_path


def build_building_data(seed, width, height, floors, stairs, room_counts,
                        floor_height=3.0):
    """Create the versioned JSON-ready map structure for a whole building."""
    total_rooms = sum(room_counts)
    building_data = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "seed": seed,
            "floor_count": len(floors),
            "rooms_per_floor": room_counts,
            "total_room_count": total_rooms,
            "map_width": width,
            "map_height": height,
            "floor_height": floor_height,
        },
        "coordinate_system": {
            "origin": "bottom_left",
            "units": "map_units",
            "bounds": {"x": 0, "y": 0, "width": width, "height": height},
        },
        "floors": [],
        "stairs": stairs,
    }

    for floor_number, floor in enumerate(floors, start=1):
        room_stairs = {room_index: [] for room_index in range(1, len(floor["rooms"]) + 1)}
        for stair in stairs:
            for endpoint_name in ("from", "to"):
                endpoint = stair[endpoint_name]
                if endpoint["floor"] == floor_number:
                    room_stairs[endpoint["room"]].append(stair["id"])

        room_records = []
        for room_index, (region, room) in enumerate(zip(floor["regions"], floor["rooms"])):
            cx, cy = center(room)
            room_records.append({
                "id": room_index + 1,
                "region": _rectangle(region),
                "bounds": _rectangle(room),
                "center": {"x": cx, "y": cy},
                "connections": [neighbour + 1 for neighbour in floor["graph"][room_index]],
                "stairs": room_stairs[room_index + 1],
            })
        dfs_path = floor["dfs_path"]
        target_room = len(floor["rooms"])
        shortest_path = breadth_first_path(floor["graph"], 0, target_room - 1)
        building_data["floors"].append({
            "id": floor_number,
            "seed": seed + floor_number - 1,
            "room_count": target_room,
            "rooms": room_records,
            "navigation": {
                "start_room": 1,
                "target_room": target_room,
                "dfs_path": [room + 1 for room in dfs_path] if dfs_path is not None else None,
                "shortest_path": [room + 1 for room in shortest_path] if shortest_path is not None else None,
            },
        })

    return building_data


def export_building(seed, width, height, floors, stairs, room_counts):
    """Build and write a multi-floor JSON map."""
    building_data = build_building_data(seed, width, height, floors, stairs, room_counts)
    return save_building_data(seed, width, height, room_counts, building_data)


def save_building_data(seed, width, height, room_counts, building_data):
    """Write an already-serialized building structure and return its path."""
    EXPORT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    room_plan = "-".join(str(count) for count in room_counts)
    filename = (
        f"building_seed-{seed}_floors-{len(room_counts)}_rooms-{sum(room_counts)}_"
        f"plan-{room_plan}_width-{width}_height-{height}.json"
    )
    output_path = EXPORT_DIRECTORY / filename
    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(building_data, output_file, indent=2)
        output_file.write("\n")
    return output_path
