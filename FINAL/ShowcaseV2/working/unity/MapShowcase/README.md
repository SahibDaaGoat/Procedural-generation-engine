# Room Runner Unity project

Open `Assets/Scenes/RoomRunner.unity` and press **Play**. The panel lets you generate a building, inspect each floor in 2D or 3D, and save JSON and SVGs. Use WASD or arrow keys to move, E or Q to use a stair from its room, and R to restart.

The Windows IL2CPP build is in `Build/ShowcaseV2`. See [the showcase guide](../../SHOWCASE_V2.md) for input limits, build commands, and test instructions.

To import exported geometry into a scene, use **Tools → Procedural Map → Import Building JSON…**. The importer and the runtime controls come from the adjacent local `ProceduralMapGenerator` package.
