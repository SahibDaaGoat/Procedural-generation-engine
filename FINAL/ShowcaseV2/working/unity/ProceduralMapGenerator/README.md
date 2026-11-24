# Procedural Map Generator Unity Package

This local package imports version 2 building JSON into a Unity scene as a warm-toned 3D blockout.

## Add the package to a Unity project

1. In Unity, open **Window → Package Manager**.
2. Select **+ → Add package from disk...**.
3. Choose this folder's `package.json`.
4. Wait for the package scripts to compile.
5. Run **Tools → Procedural Map → Import Building JSON...** and select a JSON file exported by the Python app.
6. Save the scene.

The importer creates one group per floor, room floor slabs, thick walls, room-number labels, stair-door openings/landing pads, and red room-connection graph lines. Room geometry and the red graph overlay are separate in the hierarchy. The red lines are lifted above the wall tops so they remain visible; they show graph connectivity, not a walkable corridor mesh.

The importer creates persistent warm-pastel materials under `Assets/GeneratedMapMaterials`. The generated scene uses Unity cube colliders on room floors and walls. Stair endpoints create visible door openings and landing pads. The JSON currently defines no corridor centerlines or room-to-room door coordinates, so those red edges are intentionally visual guides rather than physical paths.

## Use the renderer at runtime

Add `BuildingMapRenderer` to a GameObject, assign the exported JSON as `jsonAsset`, and enable `generateOnStart`; or paste the JSON in `jsonText` and call `GenerateFromSource()`. You can adjust map-unit scale, wall height/thickness, and connection-line appearance in the Inspector.

## Coordinate mapping

JSON uses a bottom-left floorplan origin, with X horizontal and Y depth. Unity maps these to X and Z; Unity Y is elevation. The blockout defaults to 0.05 Unity units per map unit and 3 Unity units between floors; adjust both values in the renderer Inspector to set the real-world scale for a particular map. The chosen horizontal scale also scales the imported stair-door width, subject to a visual minimum so openings remain visible.
