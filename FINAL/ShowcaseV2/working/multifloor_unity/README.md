# Multi-floor and Unity

This area owns building-level generation and the Unity representation.

- `building_generator.py` builds floors, assigns deterministic floor seeds, places stair connections, and validates stair references.
- `unity/ProceduralMapGenerator/` contains the reusable importer and runtime renderer.
- `unity/MapShowcase/` contains the sample Unity project and Room Runner scene.

The building generator calls `bsp_generation.generator.build_floor`, then adds stairs and asks `graphs_navigation.route_graph` to attach detailed route data. The completed building object is passed to `json_handoff.map_export` for serialization.

Open the Unity project at `unity/MapShowcase/`. Keep it beside `unity/ProceduralMapGenerator/`; the Unity package manifest uses a local relative path.
