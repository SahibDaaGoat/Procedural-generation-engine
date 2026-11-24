# Procedural Map Generator: Technical Report

## Purpose

The V2 project turns seeded map settings into connected 2D room layouts and multi-floor buildings. A local browser app collects the settings; Python creates rooms, graphs, routes, and stairs; JSON and SVG files capture the output; and a Unity package imports the JSON for a 3D showcase.

The four source areas below align with the four project roles. Small shared entry points, integration tests, and project documentation remain at the project root.

## Input-to-output flow

1. The user enters map width and height, seed, floor count, and either a total room count or a per-floor room plan in `json_handoff/web/`.
2. The root `app.py` launches `json_handoff/web_server.py`. The server validates values, normalizes room counts, and calls the building generator.
3. `multifloor_unity/building_generator.py` assigns `seed + floor_index` to each floor and invokes the BSP floor builder. It then selects stair endpoints between adjacent floors and validates each link.
4. `bsp_generation/` divides each floor into regions and creates inset room footprints. `graphs_navigation/` calculates room adjacency and traversal paths; the building generator then attaches a door-aware geometric route graph to each floor.
5. `json_handoff/map_export.py` serializes the generated data as schema-versioned JSON. `json_handoff/floor_diagrams.py` creates a separate SVG for every floor. Source-run output is stored under `json_handoff/maps/`; the browser receives the generated building data for its preview.
6. The Unity importer in `multifloor_unity/unity/` reads the selected JSON export and creates a 3D blockout. The browser generation request does not depend on Unity being open.

## Four role-based source areas

### 1. Multi-floor logic and Unity representation — `multifloor_unity/`

- `building_generator.py` validates floor plans, calls the floor builder, derives per-floor seeds, and creates one stair flight for each adjacent floor pair.
- Stair candidate selection considers room wall positions, favors unused walls and useful horizontal runs, and records landing floor, room, side, position, width, rise, and run. Validation checks that endpoints land on the declared wall and appear in the room’s stair references.
- `unity/ProceduralMapGenerator/` contains the reusable Unity package: editor JSON import, runtime data types, map rendering, route display, stair ladders, and Room Runner controls.
- `unity/MapShowcase/` contains the Unity sample project, scene, materials, settings, and demo building data. It renders each floor in 3D and supports movement and floor switching.
- Unity uses map X/Y as Unity X/Z and floor elevation as Unity Y.

### 2. JSON exports and Python-to-Unity handoff — `json_handoff/`

- `map_export.py` serializes single-floor and building data. The schema-version-2 building object includes metadata, coordinate convention, floors, rooms, connections, navigation graphs, and stairs.
- `building_schema.json` and `map_schema.json` describe the building and single-floor data contracts.
- `web_server.py` serves the local interface, validates `/api/generate` requests, calls generation, writes exports, and returns building data to the browser.
- `web/` contains the HTML form, JavaScript preview and controls, and CSS theme.
- `floor_diagrams.py` renders per-floor SVG previews. `maps/ShowcaseV2/` keeps a curated JSON/SVG sample; newly generated source outputs go to `maps/`.
- `showcase_backend.py` provides the headless worker. The root `showcase_backend.py` wrapper is the PyInstaller entry point.

### 3. BSP generation algorithms — `bsp_generation/`

- `generator.py` implements `build_floor`: input checks, region partitioning, room creation, adjacency assembly, and selected start-to-target traversal.
- `geometry.py` contains rectangle splitting and coordinate helpers.
- `partitioning.py` starts from a power-of-two region layout and adjusts it to the requested room count. Even and odd targets use different merge/split paths.
- `rooms.py` shrinks each partition region to create an inset room footprint while preserving the overall map bounds.
- `visualization.py` provides Matplotlib inspection tools for generated rooms and graph paths.

### 4. Graphs and navigation — `graphs_navigation/`

- `graph.py` determines adjacency between partition regions and provides depth-first and breadth-first path searches. The breadth-first search returns a shortest path in the unweighted room graph.
- `route_graph.py` builds a more detailed per-floor graph with room-center nodes, door nodes, stair nodes, junction nodes, and edges along open partition boundaries. It inserts nodes where route segments cross.
- `navigation.py` draws room links and a selected route for the earlier plotting flow.
- `merge.py` remains as a compatibility entry point for earlier code that imported `merge.generate`.

## Shared project files

| Path | Responsibility |
| --- | --- |
| `app.py` | Stable root launcher for the browser app. |
| `app.spec` | PyInstaller configuration for the browser app bundle. |
| `tests/test_showcase.py` | Cross-area checks for geometry, graph connectivity, stairs, request handling, exports, SVGs, and concurrency. |
| `PROJECT_DIAGRAMS.md` | UML component/sequence views and DFD context/detail views. |
| `SHOWCASE_V2.md`, `UNITY_IMPORT.md` | Run, build, and import instructions. |
| `PROJECT_REPORT.md` | This technical overview and role/file map. |
| `.gitignore` | Excludes caches, generated output, and Unity build/cache folders. |

## Data and validation

The generator uses integer map coordinates with a bottom-left origin. A fixed seed produces repeatable output for the same algorithm version. The floor builder checks map dimensions and requested room counts; the building generator checks floor plans and stair references; tests cover region coverage, room bounds and overlap, route connectivity, door positions, stair pairing, and serialized output.

The room adjacency graph, route graph, and rendered Unity geometry are distinct layers. A graph edge describes logical or navigational connectivity; it does not itself carve a physical corridor mesh. The project is intended as a procedural game-map blockout, not an architectural safety or code-compliance tool.

## Run from source

From the V2 project root:

```sh
python app.py
```

The browser app uses Python’s standard library. Optional Matplotlib inspection requires NumPy and Matplotlib. Unity import and showcase steps are in `SHOWCASE_V2.md` and `UNITY_IMPORT.md`.
