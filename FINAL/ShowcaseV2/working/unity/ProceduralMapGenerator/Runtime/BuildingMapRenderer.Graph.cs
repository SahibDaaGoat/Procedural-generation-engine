using System.Collections.Generic;
using UnityEngine;

namespace ProceduralMapGenerator
{
    public sealed partial class BuildingMapRenderer
    {
        public Material floorSurfaceMaterial;
        public Material floorOutlineMaterial;
        public Material routeEdgeMaterial;
        public Material routeNodeMaterial;
        public Material stairNodeMaterial;

        private static readonly Color Surface = new Color(0.82f, 0.80f, 0.75f);
        private static readonly Color Outline = new Color(0.05f, 0.46f, 0.79f);
        private static readonly Color Edge = new Color(0.10f, 0.52f, 0.18f);
        private static readonly Color Node = new Color(0.76f, 0.08f, 0.14f);
        private static readonly Color Stair = new Color(1f, 0.65f, 0.12f);

        private static Dictionary<int, List<StairEndpoint>> GetRouteDoors(FloorMap floor)
        {
            var result = new Dictionary<int, List<StairEndpoint>>();
            foreach (RouteDoor door in floor.route_graph.doors)
            {
                AddEndpoint(new StairEndpoint
                {
                    floor = floor.id, room = door.room, side = door.side,
                    position = door.position, width = door.width,
                }, floor.id, result);
            }
            return result;
        }

        private void RenderFloorSurface(Transform parent, BuildingMetadata metadata, float y)
        {
            float width = metadata.map_width * mapUnitScale;
            float depth = metadata.map_height * mapUnitScale;
            CreateBox("Floor surface", parent, new Vector3(width / 2, y - floorThickness * 1.5f - 0.02f, depth / 2),
                new Vector3(width, floorThickness * 3, depth), floorSurfaceMaterial ?? GetColorMaterial(Surface, false));

            var material = floorOutlineMaterial ?? GetColorMaterial(Outline, true);
            var points = new[] {
                new Vector3(0, y + 0.012f, 0), new Vector3(width, y + 0.012f, 0),
                new Vector3(width, y + 0.012f, depth), new Vector3(0, y + 0.012f, depth)
            };
            float thickness = connectionLineWidth * 3.2f;
            for (int i = 0; i < points.Length; i++)
                DrawStrip("Blue floor boundary", parent, points[i], points[(i + 1) % points.Length], thickness, material);
        }

        private void RenderRouteGraph(Transform parent, FloorRouteGraph graph, float floorY)
        {
            var group = CreateGroup("Floor Route Graph", parent);
            var positions = new Dictionary<int, Vector3>();
            float routeY = floorY + 0.085f;
            foreach (RouteNode node in graph.nodes)
                positions.Add(node.id, new Vector3(node.position.x * mapUnitScale, routeY, node.position.y * mapUnitScale));

            var edgeMaterial = routeEdgeMaterial ?? GetColorMaterial(Edge, true);
            foreach (RouteEdge edge in graph.edges)
                DrawStrip("Green route", group, positions[edge.from_node], positions[edge.to_node], connectionLineWidth, edgeMaterial);

            var dotMaterial = routeNodeMaterial ?? GetColorMaterial(Node, true);
            var landingMaterial = stairNodeMaterial ?? GetColorMaterial(Stair, true);
            foreach (RouteNode node in graph.nodes)
            {
                bool stair = node.kind == "stair";
                var marker = GameObject.CreatePrimitive(stair ? PrimitiveType.Cube : PrimitiveType.Cylinder);
                marker.transform.SetParent(group, false);
                marker.transform.position = positions[node.id] + Vector3.up * 0.035f;
                float size = stair ? connectionLineWidth * 4.4f : connectionLineWidth * 2.7f;
                marker.transform.localScale = new Vector3(size, 0.025f, size);
                marker.name = stair ? $"Stair {node.stair} {node.direction}" : $"Node {node.id} {node.kind}";
                Renderer markerRenderer = marker.GetComponent<Renderer>();
                markerRenderer.sharedMaterial = stair ? landingMaterial : dotMaterial;
                DisableOverlayShadows(markerRenderer);
                marker.GetComponent<Collider>().enabled = false;
                if (stair)
                {
                    marker.transform.rotation = Quaternion.Euler(0, 45, 0);
                    CreateStairLabel(group, node, positions[node.id]);
                }
            }
        }

        private void CreateStairLabel(Transform parent, RouteNode node, Vector3 position)
        {
            var label = CreateGroup($"Stair {node.stair} label", parent);
            label.position = position + Vector3.up * 0.085f;
            label.rotation = Quaternion.Euler(90, 0, 0);
            var text = label.gameObject.AddComponent<TextMesh>();
            text.text = (node.direction == "up" ? "+" : "-") + node.stair;
            text.anchor = TextAnchor.MiddleCenter;
            text.fontSize = 48;
            text.characterSize = connectionLineWidth * 0.60f;
            text.color = Color.black;
            DisableOverlayShadows(text.GetComponent<MeshRenderer>());
        }

        private void DrawStrip(string name, Transform parent, Vector3 from, Vector3 to, float width, Material material)
        {
            var delta = to - from;
            if (delta.sqrMagnitude < 0.00000001f)
                return;
            var strip = CreateBox(name, parent, (from + to) / 2,
                new Vector3(width, 0.013f, delta.magnitude), material);
            strip.transform.rotation = Quaternion.LookRotation(delta);
            strip.GetComponent<Collider>().enabled = false;
            DisableOverlayShadows(strip.GetComponent<Renderer>());
        }
    }
}
