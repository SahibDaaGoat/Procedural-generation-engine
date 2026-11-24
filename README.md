# Procedural Generation Engine

A collection of Python experiments and tools for generating connected 2D maps and multi-floor buildings, with a browser interface and a Unity showcase.

## Project contents

- **Progressive 2D lessons** — numbered scripts introduce seeded randomness, geometry, binary space partitioning (BSP), rooms, map grids, graphs, pathfinding, and validation.
- **Multi-floor generator** — Python code creates connected room layouts, stair links, and JSON map exports.
- **Browser app** — a local web interface for configuring and previewing generated buildings.
- **Unity importer and showcase** — a Unity package that imports generated building JSON, plus a playable example project.
- **Earlier experiments** — the original lessons and prototypes remain available in the `legacy` branch.

## Install and run the V2 browser app

You need Git and Python 3.10 or newer. The V2 browser app uses Python's standard library, so it does not need third-party packages.

Clone the repository and create a virtual environment from a terminal:

```sh
git clone https://github.com/SahibDaaGoat/Procedural-generation-engine.git
cd Procedural-generation-engine
python -m venv .venv
```

Activate the environment, then start the app from the V2 project directory.

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
cd FINAL\ShowcaseV2\working
python app.py
```

**macOS / Linux:**

```sh
source .venv/bin/activate
cd FINAL/ShowcaseV2/working
python app.py
```

The app opens in your browser. Enter map dimensions, a seed, floor count, and room counts, then generate a building. JSON and a standalone SVG for each floor are saved under `FINAL/ShowcaseV2/working/json_handoff/maps/`.

If PowerShell prevents environment activation, run the app with the environment's interpreter directly:

```powershell
cd FINAL\ShowcaseV2\working
..\..\..\.venv\Scripts\python.exe app.py
```

## Optional: install lesson dependencies

The earlier Matplotlib visualization lessons need NumPy and Matplotlib. Install them from the repository root with:

```sh
python -m pip install numpy matplotlib
```

## Optional: open the Unity showcase

Install Unity Hub and Unity Editor 6.3, then open `FINAL/ShowcaseV2/working/multifloor_unity/unity/MapShowcase/` as a project in Unity Hub. Open `Assets/Scenes/RoomRunner.unity` and press **Play**. To import generated JSON into another Unity project, add `FINAL/ShowcaseV2/working/multifloor_unity/unity/ProceduralMapGenerator/package.json` through Package Manager using **Add package from disk**. See the V2 guide and Unity import guide under `FINAL/ShowcaseV2/working/` for controls and build steps.

## V2 code ownership areas

The V2 source is grouped into four role-based areas:

| Folder | Responsibility |
| --- | --- |
| `multifloor_unity/` | Multi-floor generation and the Unity package/showcase. |
| `json_handoff/` | JSON schemas and exports, browser API and UI, floor SVGs, and the Python-to-Unity worker. |
| `bsp_generation/` | BSP partitioning, room footprints, geometry helpers, and visual inspection. |
| `graphs_navigation/` | Room adjacency, door-aware route graphs, pathfinding, and navigation helpers. |

Shared entry points, tests, and project documentation stay at the V2 project root. See `FINAL/ShowcaseV2/working/PROJECT_REPORT.md` for the detailed pipeline and file map.

## Run the 2D lessons

The numbered scripts cover spatial partitioning through a complete connected map. For example:

```powershell
python 05_spatial_partitioning.py
python 06_bsp_rooms.py
python 07_map_visualization.py --seed 42
python 08_graph_generation.py --seed 42
python 09_pathfinding.py --seed 42
python 10_constraints.py --seed 42
python 11_complete_2d_generator.py --seed 42
```

Earlier experiments are also kept in the root scripts and `FINAL/`. `05_spatial_partitioning.py` runs with its built-in settings, and `06_bsp_rooms.py` asks for a seed, dimensions, and room count. Most visualization scripts open a Matplotlib window; close it before launching the next script. A fixed seed makes a run reproducible where the script exposes a seed option.

## Map data

The Python generator exports JSON containing building dimensions, floors, rooms, graph connections, navigation information, and stair links. The Unity importer reads this format to create a blockout scene. Example map JSON files are included with the Python and Unity projects.

## Notes

The generator is a procedural game-map blockout, not an architectural design tool or a complete collision-based game. The Unity scene demonstrates room-graph navigation; the route representation and rendered geometry remain separate abstractions.
