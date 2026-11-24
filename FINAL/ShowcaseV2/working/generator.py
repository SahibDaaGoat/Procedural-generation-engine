"""Build one floor of the procedural map."""

import random

from geometry import split_region
from graph import build_graph, depth_first_path
from map_export import export_map
from partitioning import (
    choose_region,
    generate_power_regions,
    largest_power_of_two,
    merge_to_target,
)
from rooms import shrink_room


def build_floor(seed, width, height, room_count, start_room=1, target_room=None,
                required_points=()):
    """Return one floor's partition geometry, inset rooms, and graph."""
    random.seed(seed)
    target_room = room_count if target_room is None else target_room

    if room_count < 1:
        print("ERROR: ROOM_COUNT must be at least 1.")
        return None
    if width < 3 or height < 3:
        print("ERROR: WIDTH and HEIGHT must both be at least 3.")
        return None
    if room_count > width * height:
        print("ERROR: ROOM_COUNT cannot exceed the map's integer area.")
        return None

    print("\n       EXACT ROOM BSP GENERATOR\n")
    print("Requested rooms:", room_count)
    regions = _partition_regions(width, height, room_count, random)
    if regions is None:
        print("ERROR: The map could not be partitioned to the requested room count.")
        return None

    graph = build_graph(regions)
    if not (1 <= start_room <= room_count and 1 <= target_room <= room_count):
        print(f"ERROR: Room numbers must be between 1 and {room_count}.")
        return None
    path = depth_first_path(graph, start_room - 1, target_room - 1)

    rooms = []
    for region in regions:
        x, y, region_width, region_height = region
        points_in_region = [
            point for point in required_points
            if x <= point[0] < x + region_width and y <= point[1] < y + region_height
        ]
        rooms.append(shrink_room(region, random, points_in_region))

    print(f"Generated {len(regions)} rooms for seed {seed}.")
    return {"regions": regions, "rooms": rooms, "graph": graph, "dfs_path": path}


def _partition_regions(width, height, room_count, rng):
    """Use the original merge-and-split method for even counts.

    Odd counts start with the largest lower power of two and keep splitting
    regions until the requested count is reached.
    """
    power = largest_power_of_two(room_count)
    regions = generate_power_regions(width, height, power, rng)

    if room_count % 2 == 0:
        intermediate = room_count // 2
        merged = merge_to_target(regions.copy(), intermediate, rng)
        if merged is not None and all(w > 1 or h > 1 for _, _, w, h in merged):
            return [child for region in merged for child in split_region(region, rng)]
        # Some rectangular partitions cannot be merged back to the target.
        # Keep the valid cells and continue with the same BSP split rule.

    while len(regions) < room_count:
        region = choose_region(regions, rng)
        regions.remove(region)
        regions.extend(split_region(region, rng))
    return regions


def generate(seed, width, height, room_count, start_room, target_room):
    """Generate and export a single-floor JSON map (legacy entry point)."""
    floor = build_floor(seed, width, height, room_count, start_room, target_room)
    if floor is None:
        return
    export_path = export_map(
        seed, width, height, floor["regions"], floor["rooms"], floor["graph"],
        start_room, target_room, floor["dfs_path"],
    )
    print("JSON map exported to:", export_path)


if __name__ == "__main__":
    generate(1000000, 1000000, 1000000, 10, 2, 8)
