# BSP generation

This area owns the per-floor geometry and room-generation algorithms.

- `generator.py` validates floor inputs and coordinates region partitioning, room footprints, and graph construction.
- `geometry.py` splits regions and provides geometric helpers.
- `partitioning.py` adjusts a BSP layout to the requested room count.
- `rooms.py` creates inset room footprints inside the BSP regions.
- `visualization.py` provides optional Matplotlib inspection helpers.

The main interface is `build_floor(seed, width, height, room_count, ...)`. It returns regions, rooms, a room adjacency graph, and a DFS path. Building-level stair placement and final JSON serialization are handled by other role areas.
