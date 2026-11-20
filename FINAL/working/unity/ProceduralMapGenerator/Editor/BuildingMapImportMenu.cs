#if UNITY_EDITOR
using System;
using System.IO;
using ProceduralMapGenerator;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace ProceduralMapGenerator.Editor
{
    public static class BuildingMapImportMenu
    {
        private const string MaterialFolder = "Assets/GeneratedMapMaterials";

        private static readonly Color[] RoomPalette =
        {
            new Color(0.94f, 0.82f, 0.70f),
            new Color(0.90f, 0.86f, 0.76f),
            new Color(0.83f, 0.87f, 0.78f),
            new Color(0.94f, 0.88f, 0.79f),
            new Color(0.91f, 0.79f, 0.69f),
            new Color(0.87f, 0.84f, 0.77f),
        };

        [MenuItem("Tools/Procedural Map/Import Building JSON...")]
        public static void ImportBuildingJson()
        {
            string jsonPath = EditorUtility.OpenFilePanel("Select a generated building JSON", "", "json");
            if (string.IsNullOrEmpty(jsonPath))
                return;

            GameObject root = null;
            try
            {
                string json = File.ReadAllText(jsonPath);
                BuildingMapData building = BuildingMapJson.Parse(json);
                if (building == null || building.metadata == null || building.schema_version != 2)
                    throw new InvalidDataException("Select a valid version 2 building map JSON export.");

                EnsureMaterialFolder();
                root = new GameObject($"Generated Building - Seed {building.metadata.seed}");
                Undo.RegisterCreatedObjectUndo(root, "Import Procedural Building");
                var renderer = Undo.AddComponent<BuildingMapRenderer>(root);
                renderer.jsonText = json;
                renderer.generateOnStart = false;
                renderer.wallMaterial = GetOrCreateMaterial("Map Wall.mat",
                    "Universal Render Pipeline/Lit", "Standard", new Color(0.49f, 0.36f, 0.28f));
                renderer.stairLandingMaterial = GetOrCreateMaterial("Map Stair Landing.mat",
                    "Universal Render Pipeline/Lit", "Standard", new Color(0.67f, 0.34f, 0.20f));
                renderer.connectionLineMaterial = GetOrCreateMaterial("Map Connection Line.mat",
                    "Sprites/Default", "Unlit/Color", new Color(0.78f, 0.16f, 0.10f));
                renderer.roomMaterials = new Material[RoomPalette.Length];
                for (int index = 0; index < RoomPalette.Length; index++)
                    renderer.roomMaterials[index] = GetOrCreateMaterial(
                        $"Map Room {index + 1}.mat", "Universal Render Pipeline/Lit", "Standard", RoomPalette[index]);

                renderer.GenerateFromJson(json);
                EditorUtility.SetDirty(renderer);
                Selection.activeGameObject = root;
                EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
                EditorUtility.DisplayDialog("Building imported",
                    $"Created {building.floors.Length} floor(s) and {building.metadata.total_room_count} rooms.\n\n" +
                    "Save the current Unity scene to keep the generated map.", "OK");
            }
            catch (Exception error)
            {
                if (root != null)
                    Undo.DestroyObjectImmediate(root);
                Debug.LogException(error);
                EditorUtility.DisplayDialog("Could not import building", error.Message, "OK");
            }
        }

        private static void EnsureMaterialFolder()
        {
            if (!AssetDatabase.IsValidFolder("Assets/GeneratedMapMaterials"))
                AssetDatabase.CreateFolder("Assets", "GeneratedMapMaterials");
        }

        private static Material GetOrCreateMaterial(string fileName, string preferredShader,
            string fallbackShader, Color color)
        {
            string assetPath = $"{MaterialFolder}/{fileName}";
            Material material = AssetDatabase.LoadAssetAtPath<Material>(assetPath);
            if (material == null)
            {
                Shader shader = Shader.Find(preferredShader) ?? Shader.Find(fallbackShader);
                if (shader == null)
                    throw new InvalidOperationException($"Could not find Unity shader '{preferredShader}' or '{fallbackShader}'.");
                material = new Material(shader);
                AssetDatabase.CreateAsset(material, assetPath);
            }
            material.color = color;
            EditorUtility.SetDirty(material);
            return material;
        }
    }
}
#endif
