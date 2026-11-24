# Unity map import

The local package at `unity/ProceduralMapGenerator/package.json` reads building JSON version 2. Open **Window → Package Manager → Add package from disk** if using another project, then select the package manifest. The supplied MapShowcase project already includes it.

Choose **Tools → Procedural Map → Import Building JSON…**, select an exported building JSON file, and save the scene. The generated root contains separate objects for each floor. Floors have a blue boundary, rooms have numbered labels and thick walls, and stair landings appear as gold diamonds.

New exports include a `route_graph` on each floor. Its `nodes` are positioned in map coordinates, `edges` connect node IDs, and `doors` map room wall openings to graph nodes. The `stairs` array pairs landings across adjacent floors. Older building exports remain importable and display their original room connection overlay.

JSON coordinates use a bottom-left origin. Map X maps to Unity X, map Y to Unity Z, and floor elevation to Unity Y. In the Editor, you can set `mapUnitScale` and `unityFloorHeight` in the renderer Inspector. The showcase fits its longest map dimension to 40 Unity units.

The runtime renderer can read a `TextAsset` or a JSON string. Call `GenerateFromSource()` or enable `generateOnStart`.
