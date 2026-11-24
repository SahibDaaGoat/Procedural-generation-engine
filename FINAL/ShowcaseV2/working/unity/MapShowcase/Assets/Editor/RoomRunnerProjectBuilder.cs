#if UNITY_EDITOR
using System;
using ProceduralMapGenerator;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace RoomRunnerGame.Editor
{
    public static class RoomRunnerProjectBuilder
    {
        private const string ScenePath = "Assets/Scenes/RoomRunner.unity";
        private const string MapPath = "Assets/Maps/demo_building.json";
        private const string MaterialsPath = "Assets/GeneratedMapMaterials";

        private static readonly Color[] RoomPalette =
        {
            new Color(0.94f, 0.82f, 0.70f),
            new Color(0.90f, 0.86f, 0.76f),
            new Color(0.83f, 0.87f, 0.78f),
            new Color(0.94f, 0.88f, 0.79f),
            new Color(0.91f, 0.79f, 0.69f),
            new Color(0.87f, 0.84f, 0.77f),
        };

        [MenuItem("Tools/Room Runner/Create or Refresh Showcase Scene")]
        public static void CreateShowcaseScene()
        {
            try
            {
                TextAsset json = AssetDatabase.LoadAssetAtPath<TextAsset>(MapPath);
                if (json == null)
                    throw new InvalidOperationException($"Could not find the sample map at {MapPath}.");

                BuildingMapData building = BuildingMapJson.Parse(json.text);
                if (building == null || building.metadata == null || building.floors == null)
                    throw new InvalidOperationException("The sample building JSON could not be parsed.");

                EnsureMaterialFolder();
                Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                BuildScene(scene, building, json);
                if (!Application.isBatchMode)
                    EditorUtility.DisplayDialog("Room Runner ready",
                        "The sample building and playable graph-navigation game are ready. Press Play to run.", "OK");
            }
            catch (Exception error)
            {
                if (Application.isBatchMode)
                    throw;
                Debug.LogException(error);
                if (!Application.isBatchMode)
                    EditorUtility.DisplayDialog("Could not create Room Runner", error.Message, "OK");
            }
        }

        [MenuItem("Tools/Room Runner/Build Windows Game")]
        public static void BuildWindowsGame()
        {
            if (Application.isBatchMode || !System.IO.File.Exists(ScenePath))
                CreateShowcaseScene();

            PlayerSettings.SetScriptingBackend(
                UnityEditor.Build.NamedBuildTarget.Standalone,
                ScriptingImplementation.IL2CPP);

            string outputDirectory = "Build/ShowcaseV2";
            string[] arguments = Environment.GetCommandLineArgs();
            int outputIndex = Array.IndexOf(arguments, "-roomRunnerOutput");
            if (outputIndex >= 0 && outputIndex + 1 < arguments.Length)
                outputDirectory = arguments[outputIndex + 1];

            EnsureDirectory(outputDirectory);
            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = System.IO.Path.Combine(outputDirectory, "RoomRunner.exe"),
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.None,
            };
            BuildReport report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
                throw new InvalidOperationException($"Windows build failed: {report.summary.result}");
            Debug.Log($"Room Runner built to {options.locationPathName}");
        }

        private static void BuildScene(Scene scene, BuildingMapData building, TextAsset json)
        {
            var mapRoot = new GameObject($"Generated Building - Seed {building.metadata.seed}");
            var map = mapRoot.AddComponent<BuildingMapRenderer>();
            map.jsonAsset = json;
            map.mapUnitScale = 0.05f;
            map.unityFloorHeight = 3f;
            map.wallHeight = 2.5f;
            map.wallThickness = 0.16f;
            map.floorThickness = 0.12f;
            map.connectionLineWidth = 0.15f;
            map.lineAboveWalls = 0.12f;
            map.wallMaterial = MaterialAsset("Map Wall.mat", new Color(0.49f, 0.36f, 0.28f));
            map.stairLandingMaterial = MaterialAsset("Map Stair Landing.mat", new Color(0.67f, 0.34f, 0.20f));
            map.connectionLineMaterial = MaterialAsset("Map Connection Line.mat", new Color(0.78f, 0.16f, 0.10f), true);
            map.roomMaterials = new Material[RoomPalette.Length];
            for (int index = 0; index < RoomPalette.Length; index++)
                map.roomMaterials[index] = MaterialAsset($"Map Room {index + 1}.mat", RoomPalette[index]);
            AssignGraphMaterials(map);
            map.GenerateFromJson(json.text);
            map.ShowFloor(1);

            var game = mapRoot.AddComponent<RoomGraphRunner>();
            game.buildingJson = json;
            game.mapRenderer = map;
            game.moveSpeed = 16f;
            var controls = mapRoot.AddComponent<ShowcaseControls>();
            controls.runner = game;

            controls.keyLight = CreateLighting();
            CreateCamera(building.metadata.map_width, building.metadata.map_height, map.mapUnitScale);
            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            PlayerSettings.productName = "Room Runner - Procedural Map Showcase";
            PlayerSettings.companyName = "Procedural Map Generator";
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1360;
            PlayerSettings.defaultScreenHeight = 850;
            PlayerSettings.resizableWindow = true;
            AssetDatabase.SaveAssets();
            Selection.activeGameObject = mapRoot;
        }

        private static void AssignGraphMaterials(BuildingMapRenderer map)
        {
            map.floorSurfaceMaterial = MaterialAsset("Map Floor Surface.mat", new Color(0.82f, 0.80f, 0.75f));
            map.floorOutlineMaterial = MaterialAsset("Map Floor Outline.mat", new Color(0.05f, 0.46f, 0.79f), true);
            map.routeEdgeMaterial = MaterialAsset("Map Route Edge.mat", new Color(0.10f, 0.52f, 0.18f), true);
            map.routeNodeMaterial = MaterialAsset("Map Route Node.mat", new Color(0.76f, 0.08f, 0.14f), true);
            map.ladderMaterial = MaterialAsset("Map Ladder.mat", new Color(0.88f, 0.39f, 0.08f));
            map.stairNodeMaterial = MaterialAsset("Map Stair Node.mat", new Color(1f, 0.65f, 0.12f), true);
        }

        private static void CreateCamera(float mapWidth, float mapHeight, float scale)
        {
            var cameraObject = new GameObject("Map Overview Camera");
            var camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.95f, 0.92f, 0.86f);
            camera.orthographic = true;
            camera.renderingPath = RenderingPath.Forward;
            camera.nearClipPlane = 0.2f;
            camera.farClipPlane = 125f;

            float width = mapWidth * scale;
            float depth = mapHeight * scale;
            Vector3 focus = new Vector3(width / 2f, 3f, depth / 2f);
            Vector3 offset = new Vector3(depth * 0.45f, Mathf.Max(width, depth) * 0.9f, -depth * 0.55f);
            cameraObject.transform.position = focus + offset;
            cameraObject.transform.rotation = Quaternion.LookRotation(focus - cameraObject.transform.position, Vector3.up);
            camera.orthographicSize = Mathf.Max(depth / 2f, width / (2f * 1.65f)) * 1.85f;
            cameraObject.tag = "MainCamera";
        }

        private static Light CreateLighting()
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color32(111, 104, 95, 255);
            var lightObject = new GameObject("Warm Key Light");
            var light = lightObject.AddComponent<Light>();
            light.type = LightType.Directional;
            light.renderMode = LightRenderMode.ForcePixel;
            light.intensity = 0.78f;
            light.color = new Color32(255, 242, 221, 255);
            light.shadows = LightShadows.Soft;
            light.shadowResolution = UnityEngine.Rendering.LightShadowResolution.VeryHigh;
            light.shadowStrength = 0.84f;
            light.shadowBias = 0.04f;
            light.shadowNormalBias = 0.18f;
            lightObject.transform.rotation = Quaternion.Euler(49f, 103f, 0f);
            return light;
        }

        private static Material MaterialAsset(string name, Color color, bool unlit = false)
        {
            string path = $"{MaterialsPath}/{name}";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material == null)
            {
                Shader shader = unlit
                    ? Shader.Find("Sprites/Default") ?? Shader.Find("Unlit/Color")
                    : Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
                if (shader == null)
                    throw new InvalidOperationException("No supported Unity material shader was found.");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, path);
            }
            material.color = color;
            EditorUtility.SetDirty(material);
            return material;
        }

        private static void EnsureMaterialFolder()
        {
            if (!AssetDatabase.IsValidFolder(MaterialsPath))
                AssetDatabase.CreateFolder("Assets", "GeneratedMapMaterials");
        }

        private static void EnsureDirectory(string path)
        {
            if (!System.IO.Directory.Exists(path))
                System.IO.Directory.CreateDirectory(path);
        }
    }
}
#endif


