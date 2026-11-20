# ROOM RUNNER // Procedural Map Showcase

A small Unity 6.3 LTS game project that imports and showcases a generated multi-floor map.

## Play

Open this folder in Unity Hub, open `Assets/Scenes/RoomRunner.unity`, then press **Play**.

- Move between connected rooms with **WASD** or the **arrow keys**.
- Use **E** at a stair room to go up; use **Q** to go down.
- Reach the exit room shown in the HUD. Press **R** to restart.

To rebuild the demo scene from the bundled JSON, choose **Tools → Room Runner → Create or Refresh Showcase Scene**. To make the IL2CPP Windows executable, choose **Tools → Room Runner → Build Windows Game** after Windows IL2CPP support is installed and Unity is licensed. The executable is written to `Build/IL2CPP/RoomRunner.exe`.

The player is a graph marker moving between room centers. It demonstrates the generated connectivity and stair links; movement does not yet use physical corridor meshes. The viewer follows the selected floor, and the camera keeps that entire floor in frame.

## Import a different generated map

Use **Tools → Procedural Map → Import Building JSON...** from the package. Select a JSON file exported by the Python generator. To use it in the game, assign the imported TextAsset to `RoomGraphRunner.buildingJson` and the `BuildingMapRenderer` on the generated root. The `Tools → Room Runner → Create or Refresh Showcase Scene` command restores the included demo scene.

The Unity package is loaded from `../ProceduralMapGenerator/package.json` in `Packages/manifest.json`, so keep the `MapShowcase` project next to the `ProceduralMapGenerator` package folder when moving these files.
