# Procedural Map Generation Project Report

## 1. Project purpose

This project turns reproducible random input into connected 2D room layouts and multi-floor building maps. It combines a Python generation pipeline, a browser-based configuration and preview tool, versioned JSON/SVG exports, and a Unity importer/showcase. The main V2 project lives in `ShowcaseV2/working/`. Earlier scripts and the first browser/Unity implementation are preserved in sibling folders under `FINAL/` and at the parent project root.

The map is an abstract blockout and navigation model. It describes room regions, room footprints, graph routes, doors, and stair connections; it is not a building-code-compliant architectural plan or a full collision-ready corridor mesh.

## 2. How generation works

### 2.1 Inputs and deterministic behavior

The browser accepts map width and height, a seed, a floor count, and either a total room count to distribute or one room count per floor. The server validates integer inputs, minimum dimensions, positive floor and room counts, and matching plan length. A fixed seed produces a repeatable layout for the same inputs and implementation version.

Each floor receives `seed + floor_index`, making floors reproducible while changing their partition choices. The current floor builder seeds Python's module-level PRNG, so `building_generator.py` serializes calls with a lock when handling concurrent requests. Stair selection uses a separate PRNG derived from the building seed.

### 2.2 BSP partition and room generation

`generator.build_floor` validates the requested dimensions and room count, then asks `partitioning.py` and `geometry.py` to divide the integer map rectangle into exactly the requested number of non-overlapping regions. The partition implementation starts with a power-of-two partition layout, merges/splits for even counts, and adds splits for odd counts. `rooms.py` shrinks each region to form an inset room, preserving margins and preventing adjacent footprints from overlapping. The result includes regions, rooms, an adjacency graph, and a depth-first route between selected rooms.

`graph.py` builds room adjacency from shared partition boundaries and supplies traversal routines. The classic single-floor export path also computes a breadth-first shortest path for comparison. The multi-floor generator builds every floor first, then attaches one stair flight to each adjacent floor pair.

### 2.3 Stairs and walkable route graph

`building_generator.py` evaluates candidate wall positions on rooms in each adjacent floor pair. It selects a deterministic pair with a useful horizontal run, avoids reusing the same wall where alternatives exist, and records floor, room, side, position, width, run, and rise. Validation checks that each landing is on the declared room wall, points to a valid room, and appears in the room's stair references.

`route_graph.py` adds a finer route representation to every floor. It places room center nodes, explicit door nodes, stair nodes, and junction nodes along BSP-cell boundaries; connects those points while splitting geometric crossings; and returns nodes, edges, and door metadata. This representation is designed to express paths through the open space between inset room footprints. The older room adjacency graph remains in the export for compatibility and as a simpler overview.

### 2.4 Export format

`map_export.py` assembles schema-version-2 JSON. Building metadata records the seed, map size, floor height, floor/room counts, and coordinate convention. Floors contain room IDs, partition regions, inset bounds, centers, room connections, and route graphs. Stairs pair landings on adjacent floors and define a 3D flight. JSON coordinates use a bottom-left origin; Unity maps map X/Y to Unity X/Z and elevation to Unity Y.

`building_schema.json` documents the building-level contract; `map_schema.json` documents the single-floor shape. The server saves JSON under `maps/`, while `floor_diagrams.py` creates a standalone SVG overview for each floor beside the JSON file. These SVGs show room rectangles, route edges, room labels, and stair direction markers.

### 2.5 Browser application

`app.py` launches `web_server.run`. The server uses Python's standard-library HTTP server, serves `web/index.html`, `web/app.js`, and `web/style.css`, and exposes `/api/generate`. It validates and normalizes the request, runs generation, writes JSON and SVG files, and returns the generated data to the page. The server binds to localhost on an available port and opens the UI in the default browser. This is a local desktop-style tool, not a remotely hosted service.

### 2.6 Unity integration and game showcase

`unity/ProceduralMapGenerator/` is a local Unity package. Its editor importer reads exported building JSON and creates floor groups and map geometry. The runtime renderer and graph/navigation components support interactive use. `unity/MapShowcase/` is the Unity sample project: its scene and materials provide a Room Runner experience with 2D/3D views, floor navigation, stair movement, lighting, and appearance controls. The V2 showcase can launch a bundled generator worker; the worker uses the same Python modules to generate JSON and floor diagrams without requiring a separately installed Python runtime.

The showcase guides describe controls, import steps, coordinate mapping, and build commands. Unity's `Library`, `Temp`, `Obj`, `Logs`, and player build output are generated locally and should not be versioned.

## 3. Repository and file structure

The table focuses on the V2 repository under `ShowcaseV2/working/`.

| Path | Role |
| --- | --- |
| `app.py` | Browser app entry point. |
| `web_server.py` | Local HTTP server, request validation, generation orchestration, export response. |
| `building_generator.py` | Multi-floor orchestration, stair placement, stair-link validation. |
| `generator.py` | Single-floor BSP/room/graph generation. |
| `geometry.py` | Rectangle splitting and coordinate helpers. |
| `partitioning.py` | Region selection, power-of-two partitioning, merge-to-target logic. |
| `rooms.py` | Inset room footprint generation. |
| `graph.py` | Room adjacency and graph traversal/pathfinding. |
| `route_graph.py` | Door-aware geometric route graph construction. |
| `map_export.py` | Single-floor and building JSON serialization and file output. |
| `floor_diagrams.py` | SVG rendering for each generated floor. |
| `building_schema.json`, `map_schema.json` | JSON schema descriptions of exported data. |
| `web/` | HTML, CSS, and JavaScript for input, preview, floor stepping, export, and visual controls. |
| `tests/test_showcase.py` | Regression tests for partition geometry, graph connectivity, stairs, payload validation, export, SVG, and concurrent requests. |
| `unity/ProceduralMapGenerator/` | Reusable Unity package with import/editor and runtime rendering code. |
| `unity/MapShowcase/` | Unity sample project assets, scene, settings, materials, and demo map. |
| `maps/ShowcaseV2/` | Curated example building JSON and per-floor SVG outputs. |
| `showcase_backend.py` | Command-line worker entry point used by the bundled desktop/Unity flow. |
| `app.spec` | PyInstaller configuration for packaging the browser application. |
| `SHOWCASE_V2.md`, `UNITY_IMPORT.md` | User instructions for the showcase, build, and package import. |
| `.gitignore` | Excludes caches, builds, generated outputs, and Unity-generated directories. |

### Earlier project directories

The enclosing project also contains numbered teaching scripts (`01`–`11`) for seeded randomness, shape generation, BSP, visualization, graph creation, pathfinding, constraints, and a complete 2D generator. `FINAL/working/` is the earlier multi-floor implementation; `FINAL/ShowcaseV2/working/` is the newer version described above. Top-level files in `FINAL/` retain initial BSP and Tkinter/Matplotlib experiments. The parent `README.md` gives the broad run instructions for these tracks.

## 4. Evolution of the implementation

The codebase shows a progression from isolated algorithm experiments to a packaged, engine-facing generator:

1. **Algorithm learning prototypes:** the numbered scripts and early `FINAL` scripts explore seeded randomness, recursive region splitting, inset rooms, plotting, room adjacency, path search, and basic validity constraints. The Tkinter prototype exposes BSP parameters through a small desktop form.
2. **Composable single-floor generator:** geometry, partitioning, room shrinking, and graph operations are separated into modules. A seed and dimensions can produce a room layout plus JSON navigation data instead of only a Matplotlib drawing.
3. **Multi-floor browser workflow:** the first `FINAL/working/` implementation adds floors, room-count distribution/plans, stairs, browser interaction, and a building JSON export.
4. **V2 route and showcase expansion:** V2 adds explicit doors and route graphs, improved stair metadata and checks, SVG floor files, regression coverage, a bundled worker path, and a more interactive Unity Room Runner showcase with visual modes and lighting.

Git history in this checkout is shallow: the V2 repository currently has only the baseline commit `a71321d` (`initial_commit`). Therefore the stages above are reconstructed from the present directory structure and documentation; they are not a commit-by-commit chronology. The sibling `FINAL/working/` repository shares the GitHub URL but is a separate checkout with the same baseline commit.

## 5. Running and maintaining the project

Run the local browser application from the V2 project directory:

```powershell
python app.py
```

Run the regression suite from that same directory:

```powershell
python -m unittest discover -s tests -v
```

The suite is intended to protect key geometric and data invariants, including exact room counts, non-overlapping partitions/rooms, connected route graphs, valid door positions, adjacent-floor stair pairing, and reproducible export behavior. Unity build and import instructions are in `SHOWCASE_V2.md` and `UNITY_IMPORT.md`.

When changing exported fields, update both the serializers and schema files, then check the browser and Unity consumers. Preserve the bottom-left coordinate convention and schema version expectations or add an explicit migration/version change. Generated maps, executable bundles, Python bytecode, and Unity caches should stay outside source control; the curated example map is retained for inspection and importer/demo use.

## 6. Current boundaries and future work

- The generator is intended for procedural game layouts and visualization. Its simple BSP and stair heuristics do not guarantee architectural suitability.
- The room graph, route graph, and rendered Unity geometry are distinct abstractions; a visible graph edge is not automatically a physically carved corridor.
- A seed provides repeatability under the current algorithm, but algorithm changes can change layouts for the same seed.
- The app is a localhost tool and does not include authentication, a hosted API, or multi-user storage.
- The V2 regression suite is substantial, but Unity editor/player behavior still depends on the Unity version and build environment documented by the project.
