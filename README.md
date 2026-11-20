# Procedural Generation Engine

A collection of Python experiments and tools for generating connected 2D maps and multi-floor buildings, with a browser interface and a Unity showcase.

## Project contents

- **Progressive 2D lessons** — numbered scripts introduce seeded randomness, geometry, binary space partitioning (BSP), rooms, map grids, graphs, pathfinding, and validation.
- **Multi-floor generator** — Python code creates connected room layouts, stair links, and JSON map exports.
- **Browser app** — a local web interface for configuring and previewing generated buildings.
- **Unity importer and showcase** — a Unity package that imports generated building JSON, plus a playable example project.
- **Early experiments** — standalone scripts in the project root and `FINAL/` preserve earlier versions and UI prototypes.

## Requirements

- Python 3.10 or newer
- NumPy and Matplotlib for the visualization lessons
- Unity 6.3 for the included showcase project

Install the Python visualization dependencies:

```powershell
python -m pip install numpy matplotlib
```

The multi-floor browser app uses only the Python standard library.

## Run the browser app

From the repository root:

```powershell
python FINAL/working/app.py
```

The app starts a local server and opens the interface in your browser. Use it to set the map dimensions, seed, floor count, and room distribution, then generate and export a building JSON file. Exports are saved under `FINAL/working/maps/`.

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

## Open the Unity showcase

In Unity Hub, open `FINAL/working/unity/MapShowcase/` as a project and open `Assets/Scenes/RoomRunner.unity`. Press **Play** to explore the generated room graph. The example uses **WASD** or the arrow keys to move, **E** to go up stairs, **Q** to go down, and **R** to restart.

The showcase uses the package in `FINAL/working/unity/ProceduralMapGenerator/`. Keep both folders together so the local package reference resolves. The Unity project can import other building JSON files through its Procedural Map menu.

## Map data

The Python generator exports JSON containing building dimensions, floors, rooms, graph connections, navigation information, and stair links. The Unity importer reads this format to create a blockout scene. Example map JSON files are included with the Python and Unity projects.

## Notes

The numbered lessons are educational prototypes. Their algorithms favor clarity over production features: corridor routing and validation are simple, and the Matplotlib plots are for inspection rather than real-time rendering. The Unity showcase demonstrates room graph navigation; it is not a complete collision-based game.
