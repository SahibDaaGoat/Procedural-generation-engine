# Unity map import

The `unity/ProceduralMapGenerator` folder is a local Unity Package Manager package. It reads schema version 2 building JSON and generates a scene blockout with rectangular room floors, thick walls, numbered rooms, stair door openings/landing pads, and red room-graph connection overlays.

## Import into a game project

1. Open **Window → Package Manager → + → Add package from disk...** in Unity.
2. Select `unity/ProceduralMapGenerator/package.json` from this repository.
3. After compilation, choose **Tools → Procedural Map → Import Building JSON...**.
4. Select a JSON file from the app's `maps` folder and save the generated scene.

The importer stores the source JSON on the generated root, groups objects by floor and room, and creates reusable material assets in `Assets/GeneratedMapMaterials`. It uses Unity cube primitives for room floor/wall geometry, so the floor and walls have colliders. Stair endpoint data creates a wall opening and a landing pad at each connected room door.

The red lines are room graph edges drawn above the walls for visibility. The current JSON does not encode room-to-room corridor paths or door locations, so those lines are a connectivity overlay, not walkable corridor geometry. Stair links preserve independent room endpoints, door sides, landing coordinates, and flight measurements. The showcase game uses those links to move between floors; it is a room-graph runner rather than physical character movement on stair meshes.

## Coordinate system

JSON floorplan coordinates use a bottom-left origin: JSON X maps to Unity X, JSON Y maps to Unity Z, and floor elevation maps to Unity Y. The blockout defaults to `mapUnitScale = 0.05` and `unityFloorHeight = 3` Unity units; both can be adjusted in the renderer Inspector. The opening width gets a visual minimum because the current stair-door width is stored in abstract map units.

## Runtime use

Add `BuildingMapRenderer` to a scene GameObject, assign `jsonAsset` (or set `jsonText`), and call `GenerateFromSource()`. Enabling `generateOnStart` builds the map when the game starts. The Editor menu importer is recommended for a saved, editable scene.

The DTOs in `unity/ProceduralMapGenerator/Runtime/BuildingMapData.cs` match the exported JSON field names for Unity's built-in `JsonUtility`.
