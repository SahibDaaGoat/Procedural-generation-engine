# Graphs and navigation

This area owns room connectivity, route geometry, and graph-based navigation helpers.

- `graph.py` builds adjacency from BSP region boundaries and provides depth-first and breadth-first path searches.
- `route_graph.py` adds room, door, junction, and stair nodes plus navigable edges along open boundaries.
- `navigation.py` draws room links and a selected route for plotting.
- `merge.py` preserves the earlier `merge.generate` entry point.

`bsp_generation.generator` uses `graph.py` to summarize room adjacency. `multifloor_unity.building_generator` uses `route_graph.py` after it has placed stairs. Both graph layers are exported through `json_handoff.map_export`.
