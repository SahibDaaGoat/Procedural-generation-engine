using System;
using System.Collections.Generic;
using UnityEngine;

namespace ProceduralMapGenerator
{
    /// <summary>
    /// Creates a Unity blockout from a building JSON export. Room bounds become
    /// floor slabs and wall boxes; room graph edges are red overview lines.
    /// </summary>
    public sealed class BuildingMapRenderer : MonoBehaviour
    {
        [Header("Source")]
        [TextArea(3, 12)] public string jsonText;
        public TextAsset jsonAsset;
        public bool generateOnStart;

        [Header("Map scale and room geometry")]
        [Min(0.001f)] public float mapUnitScale = 0.05f;
        [Min(0.1f)] public float unityFloorHeight = 3f;
        [Min(0.01f)] public float wallHeight = 2.5f;
        [Min(0.01f)] public float wallThickness = 0.18f;
        [Min(0.01f)] public float floorThickness = 0.12f;
        [Min(0.1f)] public float minimumStairDoorWidth = 0.8f;

        [Header("Optional persistent Unity materials")]
        public Material wallMaterial;
        public Material[] roomMaterials;
        public Material connectionLineMaterial;
        public Material stairLandingMaterial;

        [Header("Connectivity overlay")]
        [Min(0.001f)] public float connectionLineWidth = 0.08f;
        [Min(0f)] public float lineAboveWalls = 0.12f;
        public Color connectionColor = new Color(0.78f, 0.16f, 0.10f);

        private static readonly Color[] RoomColors =
        {
            new Color(0.94f, 0.82f, 0.70f),
            new Color(0.90f, 0.86f, 0.76f),
            new Color(0.83f, 0.87f, 0.78f),
            new Color(0.94f, 0.88f, 0.79f),
            new Color(0.91f, 0.79f, 0.69f),
            new Color(0.87f, 0.84f, 0.77f),
        };

        private static readonly Color WallColor = new Color(0.49f, 0.36f, 0.28f);
        private static readonly Color LabelColor = new Color(0.17f, 0.13f, 0.10f);
        private static readonly Color StairDoorColor = new Color(0.67f, 0.34f, 0.20f);
        private readonly Dictionary<string, Material> materialCache = new Dictionary<string, Material>();
        private int shownFloorId = 1;
        public bool HasGeneratedGeometry => transform.Find("Generated Geometry") != null;

        private void Start()
        {
            if (generateOnStart)
                GenerateFromSource();
        }

        [ContextMenu("Generate Building Map")]
        public void GenerateFromSource()
        {
            string source = !string.IsNullOrWhiteSpace(jsonText)
                ? jsonText
                : jsonAsset != null ? jsonAsset.text : null;

            if (string.IsNullOrWhiteSpace(source))
                throw new InvalidOperationException("Assign a JSON TextAsset or paste building JSON into jsonText.");

            GenerateFromJson(source);
        }

        public void GenerateFromJson(string source)
        {
            BuildingMapData building = BuildingMapJson.Parse(source);
            Validate(building);
            jsonText = source;
            ClearGeneratedChildren();

            Transform geometryRoot = CreateGroup("Generated Geometry");
            foreach (FloorMap floor in building.floors)
            {
                float floorY = (floor.id - 1) * unityFloorHeight;
                Transform floorRoot = CreateGroup($"Floor {floor.id}", geometryRoot);
                var stairDoorsByRoom = GetStairDoorEndpoints(building, floor.id);

                foreach (MapRoom room in floor.rooms)
                {
                    Transform roomRoot = CreateGroup($"Room {room.id}", floorRoot);
                    RenderRoom(roomRoot, room, floorY,
                        stairDoorsByRoom.TryGetValue(room.id, out List<StairEndpoint> doors) ? doors : null);
                }

                RenderConnections(floorRoot, floor, floorY);
            }
        }

        public void ShowFloor(int floorId)
        {
            Transform geometryRoot = transform.Find("Generated Geometry");
            if (geometryRoot == null)
                return;
            foreach (Transform floorRoot in geometryRoot)
            {
                if (floorRoot.name.StartsWith("Floor "))
                    floorRoot.gameObject.SetActive(floorRoot.name == $"Floor {floorId}");
            }

            int floorDelta = floorId - shownFloorId;
            Camera mapCamera = Camera.main;
            if (floorDelta != 0 && mapCamera != null)
                mapCamera.transform.position += Vector3.up * floorDelta * unityFloorHeight;
            shownFloorId = floorId;
        }

        private void RenderRoom(Transform parent, MapRoom room, float floorY,
            List<StairEndpoint> stairDoors)
        {
            float x = room.bounds.x * mapUnitScale;
            float z = room.bounds.y * mapUnitScale;
            float width = room.bounds.width * mapUnitScale;
            float depth = room.bounds.height * mapUnitScale;
            if (width <= 0f || depth <= 0f)
                return;

            Color roomColor = RoomColors[(room.id - 1) % RoomColors.Length];
            CreateBox("Floor", parent,
                new Vector3(x + width / 2f, floorY - floorThickness / 2f, z + depth / 2f),
                new Vector3(width, floorThickness, depth), GetRoomMaterial(room.id, roomColor));

            var doorOpenings = IndexDoorOpenings(stairDoors);
            RenderWallWithOpening(parent, "West Wall", x, z, width, depth, floorY,
                "west", doorOpenings);
            RenderWallWithOpening(parent, "East Wall", x + width, z, width, depth, floorY,
                "east", doorOpenings);
            RenderWallWithOpening(parent, "South Wall", x, z, width, depth, floorY,
                "south", doorOpenings);
            RenderWallWithOpening(parent, "North Wall", x, z + depth, width, depth, floorY,
                "north", doorOpenings);

            RenderStairLandingMarkers(parent, stairDoors, x, z, width, depth, floorY);
            CreateRoomLabel(parent, room.id, room.center, floorY);
        }

        private void RenderStairLandingMarkers(Transform parent, List<StairEndpoint> endpoints,
            float x, float z, float roomWidth, float roomDepth, float floorY)
        {
            if (endpoints == null)
                return;

            foreach (StairEndpoint endpoint in endpoints)
            {
                float doorX = endpoint.position.x * mapUnitScale;
                float doorZ = endpoint.position.y * mapUnitScale;
                bool sideWall = endpoint.side == "east" || endpoint.side == "west";
                float padDepth = Mathf.Min(0.4f, sideWall ? roomWidth : roomDepth);
                float halfPad = padDepth / 2f;
                Vector3 center;
                if (endpoint.side == "west")
                    center = new Vector3(x + halfPad, floorY + 0.02f, doorZ);
                else if (endpoint.side == "east")
                    center = new Vector3(x + roomWidth - halfPad, floorY + 0.02f, doorZ);
                else if (endpoint.side == "south")
                    center = new Vector3(doorX, floorY + 0.02f, z + halfPad);
                else
                    center = new Vector3(doorX, floorY + 0.02f, z + roomDepth - halfPad);

                float wallLength = sideWall ? roomDepth : roomWidth;
                float doorWidth = Mathf.Min(
                    Mathf.Max(endpoint.width * mapUnitScale, minimumStairDoorWidth),
                    wallLength * 0.9f);
                Vector3 size = sideWall
                    ? new Vector3(padDepth, 0.025f, doorWidth)
                    : new Vector3(doorWidth, 0.025f, padDepth);
                CreateBox($"Stair {endpoint.floor}F Room {endpoint.room} Landing",
                    parent, center, size,
                    stairLandingMaterial ?? GetColorMaterial(StairDoorColor, false));
            }
        }

        private void RenderWallWithOpening(Transform parent, string wallName, float edgeX, float edgeZ,
            float roomWidth, float roomDepth, float floorY, string side,
            Dictionary<string, List<StairEndpoint>> openings)
        {
            float horizontalLength = side == "north" || side == "south" ? roomWidth : roomDepth;
            float edgeStart = side == "north" || side == "south"
                ? edgeX
                : edgeZ;
            float edgeCoordinate = side == "north" || side == "south" ? edgeZ : edgeX;
            if (!openings.TryGetValue(side, out List<StairEndpoint> sideOpenings) || sideOpenings.Count == 0)
            {
                CreateWallSegment(wallName, parent, side, edgeStart, horizontalLength,
                    edgeCoordinate, floorY);
                return;
            }

            var intervals = new List<Vector2>();
            foreach (StairEndpoint opening in sideOpenings)
            {
                float mapCoordinate = side == "north" || side == "south"
                    ? opening.position.x
                    : opening.position.y;
                float center = mapCoordinate * mapUnitScale - edgeStart;
                float doorWidth = Mathf.Min(
                    Mathf.Max(opening.width * mapUnitScale, minimumStairDoorWidth),
                    horizontalLength * 0.9f);
                float halfOpening = doorWidth / 2f;
                intervals.Add(new Vector2(
                    Mathf.Clamp(center - halfOpening, 0f, horizontalLength),
                    Mathf.Clamp(center + halfOpening, 0f, horizontalLength)));
            }
            intervals.Sort((a, b) => a.x.CompareTo(b.x));

            float cursor = 0f;
            int segment = 1;
            foreach (Vector2 interval in intervals)
            {
                float start = Mathf.Max(cursor, interval.x);
                if (start > cursor + 0.01f)
                    CreateWallSegment($"{wallName} Segment {segment++}", parent, side,
                        edgeStart + cursor, start - cursor, edgeCoordinate, floorY);
                cursor = Mathf.Max(cursor, interval.y);
            }
            if (cursor < horizontalLength - 0.01f)
                CreateWallSegment($"{wallName} Segment {segment}", parent, side,
                    edgeStart + cursor, horizontalLength - cursor, edgeCoordinate, floorY);
        }

        private void CreateWallSegment(string name, Transform parent, string side, float alongStart,
            float segmentLength, float edgeCoordinate, float floorY)
        {
            if (segmentLength <= 0.01f)
                return;

            Vector3 position;
            Vector3 size;
            if (side == "north" || side == "south")
            {
                position = new Vector3(alongStart + segmentLength / 2f,
                    floorY + wallHeight / 2f, edgeCoordinate);
                size = new Vector3(segmentLength, wallHeight, wallThickness);
            }
            else
            {
                position = new Vector3(edgeCoordinate, floorY + wallHeight / 2f,
                    alongStart + segmentLength / 2f);
                size = new Vector3(wallThickness, wallHeight, segmentLength);
            }
            CreateBox(name, parent, position, size,
                wallMaterial ?? GetColorMaterial(WallColor, false));
        }

        private void CreateRoomLabel(Transform parent, int roomId, MapPoint center, float floorY)
        {
            var labelObject = new GameObject($"Room Number {roomId}");
            labelObject.transform.SetParent(parent, false);
            labelObject.transform.position = new Vector3(
                center.x * mapUnitScale,
                floorY + 0.025f,
                center.y * mapUnitScale);
            labelObject.transform.rotation = Quaternion.Euler(-90f, 0f, 0f);

            TextMesh label = labelObject.AddComponent<TextMesh>();
            label.text = roomId.ToString();
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.characterSize = Mathf.Max(0.25f, 0.5f * mapUnitScale);
            label.fontSize = 64;
            label.color = LabelColor;
            label.richText = false;
            label.GetComponent<MeshRenderer>().sortingOrder = 5;
        }

        private void RenderConnections(Transform parent, FloorMap floor, float floorY)
        {
            foreach (MapRoom room in floor.rooms)
            {
                foreach (int neighbourId in room.connections)
                {
                    if (neighbourId <= room.id || neighbourId > floor.rooms.Length)
                        continue;

                    MapRoom neighbour = floor.rooms[neighbourId - 1];
                    var lineObject = new GameObject($"F{floor.id} Room {room.id} to Room {neighbour.id}");
                    lineObject.transform.SetParent(parent, false);
                    var line = lineObject.AddComponent<LineRenderer>();
                    line.useWorldSpace = true;
                    line.positionCount = 2;
                    line.SetPosition(0, new Vector3(
                        room.center.x * mapUnitScale,
                        floorY + wallHeight + lineAboveWalls,
                        room.center.y * mapUnitScale));
                    line.SetPosition(1, new Vector3(
                        neighbour.center.x * mapUnitScale,
                        floorY + wallHeight + lineAboveWalls,
                        neighbour.center.y * mapUnitScale));
                    line.startWidth = connectionLineWidth;
                    line.endWidth = connectionLineWidth;
                    line.numCapVertices = 4;
                    line.numCornerVertices = 2;
                    line.sharedMaterial = connectionLineMaterial ?? GetColorMaterial(connectionColor, true);
                    line.startColor = connectionColor;
                    line.endColor = connectionColor;
                }
            }
        }

        private static Dictionary<int, List<StairEndpoint>> GetStairDoorEndpoints(
            BuildingMapData building, int floorId)
        {
            var byRoom = new Dictionary<int, List<StairEndpoint>>();
            foreach (StairLink stair in building.stairs ?? Array.Empty<StairLink>())
            {
                AddEndpoint(stair.from, floorId, byRoom);
                AddEndpoint(stair.to, floorId, byRoom);
            }
            return byRoom;
        }

        private static void AddEndpoint(StairEndpoint endpoint, int floorId,
            Dictionary<int, List<StairEndpoint>> byRoom)
        {
            if (endpoint == null || endpoint.floor != floorId)
                return;
            if (!byRoom.TryGetValue(endpoint.room, out List<StairEndpoint> endpoints))
            {
                endpoints = new List<StairEndpoint>();
                byRoom.Add(endpoint.room, endpoints);
            }
            endpoints.Add(endpoint);
        }

        private static Dictionary<string, List<StairEndpoint>> IndexDoorOpenings(
            List<StairEndpoint> endpoints)
        {
            var indexed = new Dictionary<string, List<StairEndpoint>>();
            if (endpoints == null)
                return indexed;
            foreach (StairEndpoint endpoint in endpoints)
            {
                if (endpoint == null || string.IsNullOrEmpty(endpoint.side))
                    continue;
                if (!indexed.TryGetValue(endpoint.side, out List<StairEndpoint> list))
                {
                    list = new List<StairEndpoint>();
                    indexed.Add(endpoint.side, list);
                }
                list.Add(endpoint);
            }
            return indexed;
        }

        private Transform CreateGroup(string groupName, Transform parent = null)
        {
            var group = new GameObject(groupName);
            group.transform.SetParent(parent != null ? parent : transform, false);
            return group.transform;
        }

        private Material GetRoomMaterial(int roomId, Color fallbackColor)
        {
            if (roomMaterials != null && roomMaterials.Length > 0)
                return roomMaterials[(roomId - 1) % roomMaterials.Length];
            return GetColorMaterial(fallbackColor, false);
        }

        private GameObject CreateBox(string objectName, Transform parent,
            Vector3 position, Vector3 size, Material material)
        {
            GameObject box = GameObject.CreatePrimitive(PrimitiveType.Cube);
            box.name = objectName;
            box.transform.SetParent(parent, false);
            box.transform.position = position;
            box.transform.localScale = size;
            box.GetComponent<Renderer>().sharedMaterial = material;
            return box;
        }

        private Material GetColorMaterial(Color color, bool unlit)
        {
            string key = $"{color.r:F3}_{color.g:F3}_{color.b:F3}_{color.a:F3}_{unlit}";
            if (materialCache.TryGetValue(key, out Material existing))
                return existing;

            Shader shader = unlit
                ? Shader.Find("Sprites/Default")
                : Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (shader == null)
                shader = Shader.Find("Unlit/Color");
            var material = new Material(shader)
            {
                color = color,
                name = $"Generated {key}",
                hideFlags = HideFlags.DontSave,
            };
            materialCache.Add(key, material);
            return material;
        }

        private void OnDestroy()
        {
            foreach (Material material in materialCache.Values)
            {
                if (material == null)
                    continue;
                if (Application.isPlaying)
                    Destroy(material);
                else
                    DestroyImmediate(material);
            }
            materialCache.Clear();
        }

        private void ClearGeneratedChildren()
        {
            for (int index = transform.childCount - 1; index >= 0; index--)
            {
                GameObject child = transform.GetChild(index).gameObject;
                if (Application.isPlaying)
                    Destroy(child);
                else
                    DestroyImmediate(child);
            }
        }

        private static void Validate(BuildingMapData building)
        {
            if (building == null || building.schema_version != 2)
                throw new InvalidOperationException("Expected a version 2 building map JSON export.");
            if (building.metadata == null || building.floors == null || building.floors.Length == 0)
                throw new InvalidOperationException("The building JSON must contain metadata and at least one floor.");
            foreach (FloorMap floor in building.floors)
            {
                if (floor.rooms == null || floor.rooms.Length == 0)
                    throw new InvalidOperationException($"Floor {floor.id} has no rooms.");
                foreach (MapRoom room in floor.rooms)
                {
                    if (room.bounds == null || room.center == null)
                        throw new InvalidOperationException($"Floor {floor.id}, room {room.id} is missing geometry.");
                }
            }
        }
    }
}
