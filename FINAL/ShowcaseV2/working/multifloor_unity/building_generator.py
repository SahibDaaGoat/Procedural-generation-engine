"""Generate multi-floor buildings with independent, room-connected stair flights."""

import math
import random
from threading import Lock

from bsp_generation.generator import build_floor
from graphs_navigation.route_graph import add_route_graphs
from json_handoff.map_export import build_building_data


DEFAULT_FLOOR_HEIGHT = 3.0
DEFAULT_STAIR_WIDTH = 1.0
_floor_generation_lock = Lock()


def _door_candidates(floor):
    """Return deterministic room-wall door candidates in map coordinates."""
    candidates = []
    for room_number, (x, y, width, height) in enumerate(floor["rooms"], start=1):
        candidates.extend((
            {"floor": None, "room": room_number, "side": "west", "position": {"x": x, "y": y + height / 2}},
            {"floor": None, "room": room_number, "side": "east", "position": {"x": x + width, "y": y + height / 2}},
            {"floor": None, "room": room_number, "side": "south", "position": {"x": x + width / 2, "y": y}},
            {"floor": None, "room": room_number, "side": "north", "position": {"x": x + width / 2, "y": y + height}},
        ))
    return candidates


def _available_doors(floor, floor_number, used_doors):
    candidates = _door_candidates(floor)
    available = [candidate for candidate in candidates
                 if (candidate["room"], candidate["side"]) not in used_doors]
    if not available:
        available = candidates
    for candidate in available:
        candidate["floor"] = floor_number
        candidate["width"] = DEFAULT_STAIR_WIDTH
    return available


def _make_stairs(seed, floors, floor_height):
    """Create one independently positioned flight between each adjacent floor."""
    rng = random.Random(seed ^ 0x5A17C0DE)
    used_doors = [set() for _ in floors]
    stairs = []
    for lower_index in range(len(floors) - 1):
        lower_floor = lower_index + 1
        upper_floor = lower_floor + 1
        lower_doors = _available_doors(floors[lower_index], lower_floor, used_doors[lower_index])
        upper_doors = _available_doors(floors[lower_index + 1], upper_floor, used_doors[lower_index + 1])
        pairs = []
        target_run = floor_height * 1.5
        for lower_door in lower_doors:
            for upper_door in upper_doors:
                start_point = lower_door["position"]
                end_point = upper_door["position"]
                run = math.hypot(end_point["x"] - start_point["x"], end_point["y"] - start_point["y"])
                if run >= floor_height * 0.75:
                    pairs.append((abs(run - target_run), rng.random(), lower_door, upper_door))
        if not pairs:
            for lower_door in lower_doors:
                for upper_door in upper_doors:
                    start_point = lower_door["position"]
                    end_point = upper_door["position"]
                    run = math.hypot(end_point["x"] - start_point["x"], end_point["y"] - start_point["y"])
                    pairs.append((abs(run - target_run), rng.random(), lower_door, upper_door))
        _, _, start_door, end_door = min(pairs, key=lambda item: (item[0], item[1]))
        start_door = start_door.copy()
        end_door = end_door.copy()
        used_doors[lower_index].add((start_door["room"], start_door["side"]))
        used_doors[lower_index + 1].add((end_door["room"], end_door["side"]))
        start = start_door["position"]
        end = end_door["position"]
        delta_x = end["x"] - start["x"]
        delta_y = end["y"] - start["y"]
        stairs.append({
            "id": lower_index + 1,
            "type": "stairs",
            "connects_floors": [lower_floor, upper_floor],
            "from": start_door,
            "to": end_door,
            "flight": {
                "start": {"x": start["x"], "y": start["y"], "z": (lower_floor - 1) * floor_height},
                "end": {"x": end["x"], "y": end["y"], "z": (upper_floor - 1) * floor_height},
                "horizontal_run": math.hypot(delta_x, delta_y),
                "vertical_rise": floor_height,
                "clear_width": DEFAULT_STAIR_WIDTH,
            },
        })
    return stairs


def generate_building(seed, width, height, floor_count, room_counts):
    """Build floors, then attach a separately positioned stair flight per transition."""
    if floor_count < 1:
        raise ValueError("Number of floors must be at least 1.")
    if len(room_counts) != floor_count:
        raise ValueError("Provide exactly one room count for each floor.")
    if any(count < 1 for count in room_counts):
        raise ValueError("Each floor must have at least one room.")

    floors = []
    for floor_index, room_count in enumerate(room_counts):
        floor_seed = seed + floor_index
        print(f"Generating floor {floor_index + 1}/{floor_count}: {room_count} rooms")
        # build_floor uses the original module-wide PRNG.
        with _floor_generation_lock:
            floor = build_floor(
                floor_seed, width, height, room_count,
                start_room=1, target_room=room_count,
            )
        if floor is None:
            raise ValueError(f"Could not generate floor {floor_index + 1}.")
        floors.append(floor)

    floor_height = DEFAULT_FLOOR_HEIGHT
    stairs = _make_stairs(seed, floors, floor_height)
    building = build_building_data(
        seed, width, height, floors, stairs, room_counts, floor_height=floor_height,
    )
    _validate_stair_links(building)
    add_route_graphs(building)
    return building


def _validate_stair_links(building):
    """Fail generation if any landing is detached from its declared room or flight."""
    floors = {floor["id"]: floor for floor in building["floors"]}
    for stair in building["stairs"]:
        for endpoint_name in ("from", "to"):
            endpoint = stair[endpoint_name]
            floor = floors[endpoint["floor"]]
            if not 1 <= endpoint["room"] <= len(floor["rooms"]):
                raise RuntimeError(f"Stair {stair['id']} references a missing room.")
            room = floor["rooms"][endpoint["room"] - 1]["bounds"]
            point = endpoint["position"]
            tolerance = 1e-8
            on_declared_wall = (
                endpoint["side"] == "west" and abs(point["x"] - room["x"]) < tolerance
                or endpoint["side"] == "east" and abs(point["x"] - (room["x"] + room["width"])) < tolerance
                or endpoint["side"] == "south" and abs(point["y"] - room["y"]) < tolerance
                or endpoint["side"] == "north" and abs(point["y"] - (room["y"] + room["height"])) < tolerance
            )
            if not on_declared_wall:
                raise RuntimeError(f"Stair {stair['id']} landing is not on its room door wall.")
            if stair["id"] not in floor["rooms"][endpoint["room"] - 1]["stairs"]:
                raise RuntimeError(f"Stair {stair['id']} is missing from its room's stair references.")
        if stair["flight"]["horizontal_run"] < 0 or stair["flight"]["vertical_rise"] <= 0:
            raise RuntimeError(f"Stair {stair['id']} has invalid flight dimensions.")
