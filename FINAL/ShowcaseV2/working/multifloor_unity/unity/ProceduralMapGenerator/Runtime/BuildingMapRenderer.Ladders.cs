using System;
using UnityEngine;

namespace ProceduralMapGenerator
{
    public sealed partial class BuildingMapRenderer
    {
        public Material ladderMaterial;
        public bool LaddersVisible { get; private set; } = true;

        public void SetLaddersVisible(bool visible)
        {
            if (LaddersVisible == visible)
                return;

            LaddersVisible = visible;
            Transform ladders = transform.Find("Generated Geometry/Stair Ladders");
            if (ladders != null)
                ladders.gameObject.SetActive(visible);
        }

        private void RenderStairLadders(Transform geometryRoot, BuildingMapData building)
        {
            Transform ladders = CreateGroup("Stair Ladders", geometryRoot);
            foreach (StairLink stair in building.stairs ?? Array.Empty<StairLink>())
            {
                StairEndpoint lower = stair.from;
                StairEndpoint upper = stair.to;
                if (lower?.position == null || upper?.position == null || upper.floor <= lower.floor)
                    continue;

                Transform ladder = CreateGroup(LadderName(lower.floor), ladders);
                BuildLadder(ladder, building, lower, upper);
            }
            ladders.gameObject.SetActive(LaddersVisible);
        }

        private void RefreshLaddersForFloor(Transform geometryRoot, int floorId)
        {
            Transform ladders = geometryRoot.Find("Stair Ladders");
            if (ladders == null)
                return;

            foreach (Transform ladder in ladders)
                ladder.gameObject.SetActive(ladder.name == LadderName(floorId));
        }

        private static string LadderName(int lowerFloor) => $"Up from Floor {lowerFloor}";

        private void BuildLadder(Transform ladder, BuildingMapData building, StairEndpoint lower, StairEndpoint upper)
        {
            Vector3 start = LandingPosition(lower);
            Vector3 end = LandingPosition(upper);
            Vector3 axis = (end - start).normalized;
            Vector3 across = Vector3.Cross(Vector3.up, axis);
            // Aligned landings produce a vertical ladder. Match the door's orientation.
            if (across.sqrMagnitude < 0.0001f)
                across = lower.side == "east" || lower.side == "west" ? Vector3.forward : Vector3.right;
            across.Normalize();

            float width = Mathf.Min(0.84f, DoorWidth(building, lower) * 0.95f, DoorWidth(building, upper) * 0.95f);
            float railThickness = Mathf.Min(0.13f, width * 0.18f);
            var railOffset = across * (width * 0.5f);
            Material material = ladderMaterial ?? stairLandingMaterial ??
                GetColorMaterial(new Color(0.9f, 0.42f, 0.07f), false);
            DrawLadderBeam("Left rail", ladder, start - railOffset, end - railOffset, railThickness, material);
            DrawLadderBeam("Right rail", ladder, start + railOffset, end + railOffset, railThickness, material);

            int intervals = Mathf.Clamp(Mathf.RoundToInt(Vector3.Distance(start, end) / 0.32f), 5, 24);
            for (int index = 1; index < intervals; index++)
            {
                Vector3 rung = Vector3.Lerp(start, end, index / (float)intervals);
                DrawLadderBeam("Rung", ladder, rung - railOffset, rung + railOffset, railThickness * 0.75f, material);
            }

            // Show the destination threshold while the next floor is hidden in the cutaway.
            bool eastWest = upper.side == "east" || upper.side == "west";
            Vector3 padSize = eastWest ? new Vector3(0.32f, 0.08f, width * 1.12f)
                : new Vector3(width * 1.12f, 0.08f, 0.32f);
            CreateBox("Upper landing", ladder, end, padSize, material).GetComponent<Collider>().enabled = false;
        }

        private Vector3 LandingPosition(StairEndpoint endpoint) =>
            new Vector3(endpoint.position.x * mapUnitScale, (endpoint.floor - 1) * unityFloorHeight + 0.065f,
                endpoint.position.y * mapUnitScale);

        private float DoorWidth(BuildingMapData building, StairEndpoint endpoint)
        {
            MapRectangle bounds = building.floors[endpoint.floor - 1].rooms[endpoint.room - 1].bounds;
            float wallLength = endpoint.side == "east" || endpoint.side == "west" ? bounds.height : bounds.width;
            return Mathf.Min(Mathf.Max(endpoint.width * mapUnitScale, minimumStairDoorWidth),
                wallLength * mapUnitScale * 0.9f);
        }

        private void DrawLadderBeam(string name, Transform parent, Vector3 start, Vector3 end,
            float thickness, Material material)
        {
            Vector3 delta = end - start;
            GameObject beam = CreateBox(name, parent, (start + end) / 2f,
                new Vector3(thickness, thickness, delta.magnitude), material);
            beam.transform.rotation = Quaternion.FromToRotation(Vector3.forward, delta.normalized);
            beam.GetComponent<Collider>().enabled = false;
        }
    }
}
