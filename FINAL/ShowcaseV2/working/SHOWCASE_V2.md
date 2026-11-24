# Room Runner Showcase V2

## Run the demo

Open `unity/MapShowcase/Build/ShowcaseV2-Lighting/RoomRunner.exe`. Keep the executable with the rest of that build folder. In the Unity Editor, open `unity/MapShowcase/Assets/Scenes/RoomRunner.unity` and press Play. The project uses Editor 6000.3.28f1.

Enter width, height, seed, and number of floors. Choose either a building-wide room count or a comma-separated count for each floor. Generate a map, step through the floors, and switch between the 2D overview and angled 3D view. Use **Use dark mode** to change the panel and map palette. The choice is saved for the next launch. The angled 3D view uses soft shadows from the walls and ladders. Click **Save JSON + floor SVGs** and **Open exports folder** to find the files.

Red circles mark route nodes. Green edges follow the gaps between room footprints and enter rooms at their doors. Gold diamonds mark the stair landings, with matching numbers on adjacent floors. The blue outline marks the edge of each floor slab.

Use WASD or arrows to move between nearby rooms along the displayed routes. Use E or Q in a stair room to change floors, and R to restart. In 3D, orange ladders join the paired landings. The marker climbs along the ladder before the view switches to the destination floor.

The bundled Windows generator uses the same Python source as the desktop app. A separate Python installation is unnecessary for the Unity build. Input supports 1–12 floors, 1–150 rooms per floor (bounded by integer map area), up to 600 rooms per building, and width/height from 3 to 100,000.

## Desktop generator

Open `dist/app.exe` for the browser-based version. It writes JSON and a standalone SVG for every floor to `dist/maps`.

## Build and verify

From the project root, run the regression tests with:

```powershell
python -m unittest discover -s tests -v
```

Rebuild the Windows generator worker and desktop app after editing Python or web assets:

```powershell
pyinstaller --noconfirm --onefile --name MapGenerator --distpath unity/MapShowcase/Assets/StreamingAssets --workpath build/backend --specpath build showcase_backend.py
pyinstaller --noconfirm app.spec
```

In Unity, use **Tools → Room Runner → Create or Refresh Showcase Scene**, then **Tools → Room Runner → Build Windows Game** to create the IL2CPP player. Keep the Unity project next to the local `ProceduralMapGenerator` package folder.
