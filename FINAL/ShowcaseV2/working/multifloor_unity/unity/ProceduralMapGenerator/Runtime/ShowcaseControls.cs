using System;
using System.Collections;
using System.IO;
using UnityEngine;

namespace ProceduralMapGenerator
{
    public sealed partial class ShowcaseControls : MonoBehaviour
    {
        public RoomGraphRunner runner;

        [Serializable]
        public sealed class Settings
        {
            public string width = "800";
            public string height = "600";
            public string seed = "20261116";
            public string floor_count = "3";
            public string total_rooms = "37";
            public string room_plan = "12,15,10";
            public string room_mode = "plan";
        }

        [Serializable]
        private sealed class BackendError { public string error; }

        private readonly Settings settings = new Settings();
        private Camera overview;
        private bool topDown = true;
        private bool busy;
        private string status;
        private string exportDirectory;
        private string generatedDirectory;
        private string jobDirectory;
        private WindowsGeneratorProcess process;
        private BuildingMapData generated;
        private Vector2 scroll;
        private void Awake()
        {
            runner.UseExternalHud = true;
            overview = Camera.main;
            if (keyLight == null)
                keyLight = GameObject.Find("Warm Key Light")?.GetComponent<Light>();
            SetTheme(PlayerPrefs.GetInt(DarkModePreference, 0) == 1);
            exportDirectory = Path.Combine(Application.persistentDataPath, "Maps");
            status = "Showing the sample map. Generate to export your own.";
        }

        private float PanelWidth => Mathf.Clamp(Screen.width * 0.31f, 245f, 340f);

        private void LateUpdate()
        {
            if (overview == null || runner.Building == null)
                return;

            var metadata = runner.Building.metadata;
            var renderer = runner.mapRenderer;
            renderer.SetLaddersVisible(!topDown);
            float width = metadata.map_width * renderer.mapUnitScale;
            float depth = metadata.map_height * renderer.mapUnitScale;
            float elevation = (renderer.ShownFloorId - 1) * renderer.unityFloorHeight;
            float left = Mathf.Min((PanelWidth + 14f) / Screen.width, 0.7f);
            overview.rect = new Rect(left, 0f, 1f - left, 1f);
            float aspect = Mathf.Max(0.1f, overview.pixelWidth / (float)Mathf.Max(1, overview.pixelHeight));
            Vector3 center = new Vector3(width / 2f, elevation, depth / 2f);
            if (topDown)
            {
                overview.transform.SetPositionAndRotation(center + Vector3.up * 70f, Quaternion.Euler(90, 0, 0));
                overview.orthographicSize = Mathf.Max(depth, width / aspect) * 0.57f + 0.4f;
            }
            else
            {
                Vector3 offset = new Vector3(24f, 54f, -38f);
                overview.transform.SetPositionAndRotation(center + offset, Quaternion.LookRotation(-offset));
                Bounds projected = new Bounds(Vector3.zero, Vector3.zero);
                for (int x = 0; x <= 1; x++)
                for (int z = 0; z <= 1; z++)
                for (int y = 0; y <= 1; y++)
                    projected.Encapsulate(Quaternion.Inverse(overview.transform.rotation) *
                        new Vector3((x - 0.5f) * width, y * Mathf.Max(renderer.wallHeight, renderer.unityFloorHeight + 0.25f), (z - 0.5f) * depth));
                overview.orthographicSize = Mathf.Max(projected.extents.y, projected.extents.x / aspect) * 1.15f + 0.4f;
                overview.transform.position += overview.transform.rotation *
                    new Vector3(projected.center.x, projected.center.y, 0f);
            }
            overview.ResetAspect();
        }

        private void OnGUI()
        {
            EnsureThemeStyles();
            GUILayout.BeginArea(new Rect(12, 12, PanelWidth, Screen.height - 24), panelStyle);
            scroll = GUILayout.BeginScrollView(scroll);
            GUILayout.Label("ROOM RUNNER", titleStyle);
            if (GUILayout.Button(darkMode ? "Use light mode" : "Use dark mode", GUILayout.Height(24)))
            {
                GUI.FocusControl(null);
                SetTheme(!darkMode);
                PlayerPrefs.SetInt(DarkModePreference, darkMode ? 1 : 0);
                PlayerPrefs.Save();
            }
            GUILayout.Space(7);
            bool enabled = GUI.enabled;
            GUI.enabled = !busy;
            settings.width = TextField("Width", settings.width);
            settings.height = TextField("Height", settings.height);
            settings.seed = TextField("Seed", settings.seed);
            settings.floor_count = TextField("Floors", settings.floor_count);
            settings.room_mode = GUILayout.Toolbar(settings.room_mode == "plan" ? 1 : 0,
                new[] { "Total rooms", "Rooms per floor" }) == 1 ? "plan" : "total";
            if (settings.room_mode == "plan")
                settings.room_plan = TextField("Floor counts", settings.room_plan);
            else
                settings.total_rooms = TextField("Total rooms", settings.total_rooms);
            if (GUILayout.Button(busy ? "Generating..." : "Generate map", GUILayout.Height(32)))
            {
                GUI.FocusControl(null);
                StartCoroutine(Generate(settings));
            }
            GUI.enabled = !busy && generated != null;
            if (GUILayout.Button("Save JSON + floor SVGs"))
                SaveExports();
            GUI.enabled = Directory.Exists(exportDirectory);
            if (GUILayout.Button("Open exports folder"))
                Application.OpenURL(new Uri(exportDirectory + Path.DirectorySeparatorChar).AbsoluteUri);
            GUI.enabled = enabled;
            GUILayout.Label(status, wrapStyle);

            if (runner.Building != null)
            {
                int floor = runner.mapRenderer.ShownFloorId;
                int total = runner.Building.floors.Length;
                GUILayout.Space(10);
                GUILayout.Label($"Floor {floor} / {total}  |  {runner.Building.floors[floor - 1].room_count} rooms", wrapStyle);
                GUILayout.BeginHorizontal();
                GUI.enabled = floor > 1;
                if (GUILayout.Button("Previous floor")) Inspect(floor - 1);
                GUI.enabled = floor < total;
                if (GUILayout.Button("Next floor")) Inspect(floor + 1);
                GUI.enabled = enabled;
                GUILayout.EndHorizontal();
                if (GUILayout.Button(topDown ? "Switch to 3D" : "Switch to 2D"))
                {
                    GUI.FocusControl(null);
                    topDown = !topDown;
                    ApplyViewLighting();
                }
                GUILayout.Space(8);
                GUILayout.Label("Red: node   Green: route", wrapStyle);
                GUILayout.Label("Gold diamond: stair (+ up, − down)\nBlue: floor boundary", wrapStyle);
                if (!topDown && floor < total)
                    GUILayout.Label($"Ladder to floor {floor + 1}", wrapStyle);
                GUILayout.Space(6);
                GUILayout.Label($"Player: floor {runner.CurrentFloor}, room {runner.CurrentRoom}", wrapStyle);
                GUILayout.Label("WASD / arrows: move\nE / Q: up / down stairs   R: restart", wrapStyle);
                GUILayout.Label(runner.Status, wrapStyle);
            }
            GUILayout.EndScrollView();
            GUILayout.EndArea();
            runner.InputPaused = busy || !string.IsNullOrEmpty(GUI.GetNameOfFocusedControl());
        }

        private string TextField(string label, string value)
        {
            GUILayout.BeginHorizontal();
            GUILayout.Label(label, wrapStyle, GUILayout.Width(86));
            GUI.SetNextControlName(label);
            string result = GUILayout.TextField(value, 96, GUILayout.Height(24));
            GUILayout.EndHorizontal();
            return result;
        }

        private void Inspect(int floor)
        {
            GUI.FocusControl(null);
            runner.mapRenderer.ShowFloor(floor);
        }

        public IEnumerator Generate(Settings request)
        {
            if (busy)
                yield break;
            busy = true;
            status = "Generating floors and connecting doors...";
            string resultPath = null;
            try
            {
                jobDirectory = Path.Combine(Application.temporaryCachePath, "RoomRunner-" + Guid.NewGuid().ToString("N"));
                Directory.CreateDirectory(jobDirectory);
                string requestPath = Path.Combine(jobDirectory, "request.json");
                resultPath = Path.Combine(jobDirectory, "map.json");
                File.WriteAllText(requestPath, JsonUtility.ToJson(request));
                string backend = Path.Combine(Application.streamingAssetsPath, "MapGenerator.exe");
                if (!File.Exists(backend))
                    throw new FileNotFoundException("The bundled Windows map generator is missing.");
                process = new WindowsGeneratorProcess(Path.GetFullPath(backend),
                    $"\"{requestPath}\" \"{resultPath}\"", jobDirectory);
            }
            catch (Exception error)
            {
                status = error.Message;
            }

            if (process != null)
            {
                float deadline = Time.realtimeSinceStartup + 60f;
                while (!process.HasExited && Time.realtimeSinceStartup < deadline)
                    yield return null;
                try
                {
                    if (!process.HasExited)
                        throw new TimeoutException("Generation timed out. Try a smaller map.");
                    if (!File.Exists(resultPath))
                        throw new IOException($"The generator stopped without a map (code {process.ExitCode}).");
                    string json = File.ReadAllText(resultPath);
                    if (process.ExitCode != 0)
                        throw new InvalidOperationException(JsonUtility.FromJson<BackendError>(json).error);

                    var next = BuildingMapJson.Parse(json);
                    runner.LoadMap(json);
                    DeleteJob(generatedDirectory);
                    generatedDirectory = jobDirectory;
                    jobDirectory = null;
                    generated = next;
                    status = $"Generated {next.metadata.total_room_count} rooms on {next.floors.Length} floors.";
                }
                catch (Exception error)
                {
                    status = error.Message;
                }
            }

            StopProcess();
            DeleteJob(jobDirectory);
            jobDirectory = null;
            busy = false;
        }

        public string SaveExports(string directory = null)
        {
            if (generated == null)
                return null;
            try
            {
                string target = directory ?? exportDirectory;
                Directory.CreateDirectory(target);
                BuildingMetadata m = generated.metadata;
                string name = $"building_seed-{m.seed}_floors-{m.floor_count}_rooms-{m.total_room_count}" +
                    $"_plan-{string.Join("-", m.rooms_per_floor)}_width-{m.map_width:0}_height-{m.map_height:0}";
                for (int id = 1; id <= m.floor_count; id++)
                    File.Copy(Path.Combine(generatedDirectory, $"map_floor-{id}.svg"), Path.Combine(target, $"{name}_floor-{id}.svg"), true);
                string path = Path.Combine(target, name + ".json");
                File.Copy(Path.Combine(generatedDirectory, "map.json"), path, true);
                status = $"Saved JSON and {m.floor_count} floor diagrams.";
                return path;
            }
            catch (Exception error)
            {
                status = "Could not save exports. " + error.Message;
                return null;
            }
        }

        private static void DeleteJob(string directory)
        {
            if (directory == null)
                return;
            try { Directory.Delete(directory, true); }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }

        private void StopProcess()
        {
            if (process == null)
                return;
            process.Dispose();
            process = null;
        }

        private void OnDestroy()
        {
            StopProcess();
            DeleteJob(jobDirectory);
            DeleteJob(generatedDirectory);
            if (panelTexture != null) Destroy(panelTexture);
        }
    }
}

