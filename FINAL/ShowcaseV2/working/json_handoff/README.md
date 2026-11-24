# JSON handoff and browser app

This area owns the user-facing browser flow and the data contract shared with Unity.

- `web_server.py` validates browser requests and coordinates the generation call.
- `map_export.py` serializes single-floor and building JSON using schema version 2.
- `building_schema.json` and `map_schema.json` document the exported data.
- `floor_diagrams.py` writes per-floor SVG diagrams.
- `showcase_backend.py` is the headless worker used by the Unity build; the project-root `showcase_backend.py` is its packaging entry point.
- `web/` contains the browser interface. `maps/` contains a curated sample and source-run exports.

The server calls `multifloor_unity.building_generator.generate_building`, returns generated building data to the browser, and saves JSON/SVG files under `maps/`.
