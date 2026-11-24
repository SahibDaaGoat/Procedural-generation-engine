using UnityEngine;
using UnityEngine.Rendering;

namespace ProceduralMapGenerator
{
    public sealed partial class ShowcaseControls
    {
        public Light keyLight;

        private const string DarkModePreference = "RoomRunner.DarkMode";
        private bool darkMode;
        private GUIStyle titleStyle;
        private GUIStyle panelStyle;
        private GUIStyle wrapStyle;
        private Texture2D panelTexture;
        private static readonly Color Ink = new Color32(50, 37, 30, 255);
        private static readonly Color LightBackground = new Color32(242, 235, 220, 255);
        private static readonly Color DarkBackground = new Color32(21, 22, 26, 255);

        private void SetTheme(bool enabled)
        {
            darkMode = enabled;
            runner.mapRenderer.SetDarkPalette(enabled);
            if (overview != null)
                overview.backgroundColor = enabled ? DarkBackground : LightBackground;

            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = enabled ? new Color32(89, 86, 94, 255)
                : new Color32(111, 104, 95, 255);
            if (keyLight != null)
            {
                keyLight.color = enabled ? new Color32(255, 235, 211, 255)
                    : new Color32(255, 242, 221, 255);
                keyLight.intensity = enabled ? 0.84f : 0.78f;
                keyLight.shadowStrength = enabled ? 0.88f : 0.84f;
            }
            RefreshThemeStyles();
            ApplyViewLighting();
        }

        private void ApplyViewLighting()
        {
            if (keyLight == null)
                return;

            QualitySettings.shadows = topDown ? ShadowQuality.Disable : ShadowQuality.All;
            QualitySettings.shadowDistance = 115f;
            QualitySettings.shadowCascades = 2;
            QualitySettings.shadowProjection = ShadowProjection.CloseFit;
        }

        private void EnsureThemeStyles()
        {
            if (titleStyle != null)
                return;

            panelTexture = new Texture2D(1, 1);
            panelStyle = new GUIStyle(GUI.skin.box)
                { normal = { background = panelTexture }, padding = new RectOffset(15, 15, 16, 16) };
            titleStyle = new GUIStyle(GUI.skin.label) { fontSize = 24, fontStyle = FontStyle.Bold };
            wrapStyle = new GUIStyle(GUI.skin.label) { fontSize = 15, wordWrap = true };
            RefreshThemeStyles();
        }

        private void RefreshThemeStyles()
        {
            if (panelTexture == null)
                return;

            panelTexture.SetPixel(0, 0, darkMode ? new Color32(36, 37, 42, 255)
                : new Color32(250, 239, 223, 255));
            panelTexture.Apply();
            Color ink = darkMode ? new Color32(249, 233, 214, 255) : Ink;
            titleStyle.normal.textColor = ink;
            wrapStyle.normal.textColor = ink;
        }
    }
}
