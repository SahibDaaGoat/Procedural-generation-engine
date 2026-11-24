using UnityEngine;
using UnityEngine.Rendering;

namespace ProceduralMapGenerator
{
    public sealed partial class BuildingMapRenderer
    {
        private bool darkPalette;
        private static readonly int ColorProperty = Shader.PropertyToID("_Color");
        private static readonly int BaseColorProperty = Shader.PropertyToID("_BaseColor");
        private static readonly Color[] DarkRoomColors =
        {
            new Color32(100, 70, 58, 255),
            new Color32(92, 83, 61, 255),
            new Color32(62, 85, 77, 255),
            new Color32(94, 77, 67, 255),
            new Color32(103, 68, 58, 255),
            new Color32(85, 80, 73, 255),
        };

        public void SetDarkPalette(bool enabled)
        {
            if (darkPalette == enabled)
                return;

            darkPalette = enabled;
            Transform root = transform.Find("Generated Geometry");
            if (root != null)
                ApplyPalette(root);
        }

        private void ApplyPalette(Transform root)
        {
            var properties = new MaterialPropertyBlock();
            foreach (MeshRenderer mesh in root.GetComponentsInChildren<MeshRenderer>(true))
            {
                if (mesh.TryGetComponent(out TextMesh label))
                {
                    if (label.name.StartsWith("Room Number "))
                        label.color = darkPalette ? new Color32(255, 236, 210, 255) : LabelColor;
                    continue;
                }

                Material material = mesh.sharedMaterial;
                if (material == null || !TryGetPaletteColor(material, out Color color))
                    continue;

                mesh.GetPropertyBlock(properties);
                if (material.HasProperty(BaseColorProperty))
                    properties.SetColor(BaseColorProperty, color);
                if (material.HasProperty(ColorProperty))
                    properties.SetColor(ColorProperty, color);
                mesh.SetPropertyBlock(properties);
            }
        }

        private bool TryGetPaletteColor(Material material, out Color color)
        {
            color = material.color;
            if (material == floorSurfaceMaterial)
                color = darkPalette ? new Color32(49, 49, 55, 255) : color;
            else if (material == wallMaterial)
                color = darkPalette ? new Color32(121, 104, 93, 255) : color;
            else if (material == floorOutlineMaterial)
                color = darkPalette ? new Color32(77, 180, 232, 255) : color;
            else if (material == routeEdgeMaterial)
                color = darkPalette ? new Color32(102, 216, 145, 255) : color;
            else if (material == routeNodeMaterial)
                color = darkPalette ? new Color32(255, 117, 122, 255) : color;
            else if (roomMaterials != null)
            {
                int index = System.Array.IndexOf(roomMaterials, material);
                if (index < 0)
                    return false;
                if (darkPalette)
                    color = DarkRoomColors[index % DarkRoomColors.Length];
            }
            else
                return false;

            return true;
        }

        private static void DisableOverlayShadows(Renderer renderer)
        {
            renderer.shadowCastingMode = ShadowCastingMode.Off;
            renderer.receiveShadows = false;
        }
    }
}
