using System;
using System.Collections.Generic;
using UnityEngine;

namespace ProceduralMapGenerator
{
    /// <summary>
    /// Tiny graph-navigation game for demonstrating imported building maps.
    /// The player marker moves between room nodes; it does not simulate walking
    /// through physical corridor meshes.
    /// </summary>
    public sealed class RoomGraphRunner : MonoBehaviour
    {
        public TextAsset buildingJson;
        public BuildingMapRenderer mapRenderer;
        [Min(0.1f)] public float moveSpeed = 5f;

        private BuildingMapData building;
        private GameObject playerToken;
        private GameObject goalToken;
        private Material playerMaterial;
        private Material goalMaterial;
        private int currentFloor = 1;
        private int currentRoom = 1;
        private readonly Queue<Waypoint> waypoints = new Queue<Waypoint>();
        private readonly struct Waypoint
        {
            public readonly Vector3 position;
            public readonly int visibleFloor;
            public readonly bool climb;

            public Waypoint(Vector3 position, int visibleFloor = 0, bool climb = false)
            {
                this.position = position;
                this.visibleFloor = visibleFloor;
                this.climb = climb;
            }
        }
        public bool InputPaused { get; set; }
        public bool UseExternalHud { get; set; }
        public string Status => message;
        public BuildingMapData Building => building;
        public int CurrentFloor => currentFloor;
        public int CurrentRoom => currentRoom;
        private Waypoint moveTarget;
        private bool isMoving;
        private bool hasWon;
        private string message = "Find the exit. Follow the room graph.";
        private GUIStyle panelStyle;
        private GUIStyle headingStyle;
        private GUIStyle bodyStyle;
        private Texture2D panelTexture;

        private int GoalFloor => building.floors.Length;
        private int GoalRoom => building.floors[GoalFloor - 1].room_count;

        private void Start()
        {
            if (mapRenderer == null)
                mapRenderer = FindObjectOfType<BuildingMapRenderer>();
            if (building == null && buildingJson != null && mapRenderer != null)
                LoadMap(buildingJson.text);
        }

        public void LoadMap(string json)
        {
            BuildingMapData next = BuildingMapJson.Parse(json);
            if (next == null || next.floors == null || next.floors.Length == 0)
                throw new InvalidOperationException("The selected JSON does not contain a building.");
            // Fit the longest map dimension into 40 Unity units.
            mapRenderer.mapUnitScale = 40f / Mathf.Max(next.metadata.map_width, next.metadata.map_height);
            mapRenderer.GenerateFromJson(json);
            building = next;
            if (playerToken == null)
                CreateTokens();
            goalToken.transform.position = RoomMarkerPosition(GoalFloor, GetRoom(GoalFloor, GoalRoom));
            RestartRun();
        }

        private void Update()
        {
            if (building == null)
                return;

            if (isMoving)
            {
                playerToken.transform.position = Vector3.MoveTowards(
                    playerToken.transform.position, moveTarget.position,
                    (moveTarget.climb ? 2.5f : moveSpeed) * Time.deltaTime);
                if ((playerToken.transform.position - moveTarget.position).sqrMagnitude < 0.0025f)
                {
                    playerToken.transform.position = moveTarget.position;
                    if (waypoints.Count > 0)
                    {
                        BeginWaypoint();
                        return;
                    }
                    isMoving = false;
                    mapRenderer.ShowFloor(currentFloor);
                    UpdateGoalState();
                }
                return;
            }

            if (InputPaused)
                return;

            if (hasWon)
            {
                if (Input.GetKeyDown(KeyCode.R))
                    RestartRun();
                return;
            }

            if (Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow))
                TryMoveInDirection(Vector2.up);
            else if (Input.GetKeyDown(KeyCode.S) || Input.GetKeyDown(KeyCode.DownArrow))
                TryMoveInDirection(Vector2.down);
            else if (Input.GetKeyDown(KeyCode.A) || Input.GetKeyDown(KeyCode.LeftArrow))
                TryMoveInDirection(Vector2.left);
            else if (Input.GetKeyDown(KeyCode.D) || Input.GetKeyDown(KeyCode.RightArrow))
                TryMoveInDirection(Vector2.right);
            else if (Input.GetKeyDown(KeyCode.E))
                TryUseStairs(true);
            else if (Input.GetKeyDown(KeyCode.Q))
                TryUseStairs(false);
            else if (Input.GetKeyDown(KeyCode.R))
                RestartRun();
        }

        private void TryMoveInDirection(Vector2 direction)
        {
            MapRoom current = GetRoom(currentFloor, currentRoom);
            int chosenRoom = 0;
            float bestScore = 0.08f;
            foreach (int candidateId in current.connections ?? Array.Empty<int>())
            {
                if (candidateId < 1 || candidateId > building.floors[currentFloor - 1].rooms.Length)
                    continue;
                MapRoom candidate = GetRoom(currentFloor, candidateId);
                Vector2 offset = new Vector2(
                    candidate.center.x - current.center.x,
                    candidate.center.y - current.center.y);
                if (offset.sqrMagnitude < 0.0001f)
                    continue;
                float score = Vector2.Dot(offset.normalized, direction);
                if (score > bestScore)
                {
                    bestScore = score;
                    chosenRoom = candidateId;
                }
            }

            if (chosenRoom == 0)
            {
                message = "No room connection in that direction.";
                return;
            }

            mapRenderer.ShowFloor(currentFloor);
            QueueRoomRoute(current, GetRoom(currentFloor, chosenRoom));
            currentRoom = chosenRoom;
            message = $"Moving to room {currentRoom} on floor {currentFloor}.";
            BeginMoveToCurrentRoom();
        }

        private void TryUseStairs(bool goingUp)
        {
            foreach (StairLink stair in building.stairs ?? Array.Empty<StairLink>())
            {
                StairEndpoint source = goingUp ? stair.from : stair.to;
                StairEndpoint destination = goingUp ? stair.to : stair.from;
                if (source.floor != currentFloor || source.room != currentRoom)
                    continue;

                mapRenderer.ShowFloor(currentFloor);
                waypoints.Enqueue(new Waypoint(MarkerPosition(source.floor, source.position)));
                waypoints.Enqueue(new Waypoint(MarkerPosition(destination.floor, destination.position),
                    Mathf.Min(source.floor, destination.floor), climb: true));
                currentFloor = destination.floor;
                currentRoom = destination.room;
                message = $"Taking ladder {stair.id} to floor {currentFloor}, room {currentRoom}.";
                BeginMoveToCurrentRoom(revealDestination: true);
                return;
            }

            message = goingUp
                ? "There is no stair going up from this room."
                : "There is no stair going down from this room.";
        }

        private void BeginMoveToCurrentRoom(bool revealDestination = false)
        {
            waypoints.Enqueue(new Waypoint(RoomMarkerPosition(currentFloor, GetRoom(currentFloor, currentRoom)),
                revealDestination ? currentFloor : 0));
            BeginWaypoint();
            isMoving = true;
        }

        private void BeginWaypoint()
        {
            moveTarget = waypoints.Dequeue();
            if (moveTarget.visibleFloor != 0 && (!moveTarget.climb || mapRenderer.LaddersVisible))
                mapRenderer.ShowFloor(moveTarget.visibleFloor);
        }

        private Vector3 RoomMarkerPosition(int floorNumber, MapRoom room)
        {
            return MarkerPosition(floorNumber, room.center);
        }

        private Vector3 MarkerPosition(int floorNumber, MapPoint point)
        {
            float elevation = (floorNumber - 1) * mapRenderer.unityFloorHeight;
            return new Vector3(
                point.x * mapRenderer.mapUnitScale,
                elevation + 0.32f,
                point.y * mapRenderer.mapUnitScale);
        }

        private void QueueRoomRoute(MapRoom from, MapRoom to)
        {
            FloorRouteGraph graph = building.floors[currentFloor - 1].route_graph;
            if (graph == null)
                return;

            RouteNode start = Array.Find(graph.nodes, node => node.kind == "room" && node.room == from.id);
            RouteNode end = Array.Find(graph.nodes, node => node.kind == "room" && node.room == to.id);
            var neighbors = new Dictionary<int, List<int>>();
            var nodes = new Dictionary<int, RouteNode>();
            foreach (RouteNode node in graph.nodes)
            {
                nodes.Add(node.id, node);
                neighbors.Add(node.id, new List<int>());
            }
            foreach (RouteEdge edge in graph.edges)
            {
                neighbors[edge.from_node].Add(edge.to_node);
                neighbors[edge.to_node].Add(edge.from_node);
            }
            var front = new Queue<int>();
            var previous = new Dictionary<int, int> { [start.id] = 0 };
            front.Enqueue(start.id);
            while (front.Count > 0 && !previous.ContainsKey(end.id))
            {
                int current = front.Dequeue();
                foreach (int next in neighbors[current])
                {
                    int room = nodes[next].room;
                    if (previous.ContainsKey(next) || (room != 0 && room != from.id && room != to.id))
                        continue;
                    previous.Add(next, current);
                    front.Enqueue(next);
                }
            }
            if (!previous.ContainsKey(end.id))
                return;
            var path = new Stack<int>();
            for (int id = previous[end.id]; id != 0 && id != start.id; id = previous[id])
                path.Push(id);
            foreach (int id in path)
                waypoints.Enqueue(new Waypoint(MarkerPosition(currentFloor, nodes[id].position)));
        }

        private MapRoom GetRoom(int floorNumber, int roomNumber)
        {
            return building.floors[floorNumber - 1].rooms[roomNumber - 1];
        }

        private void CreateTokens()
        {
            playerToken = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            playerToken.name = "Player - Graph Explorer";
            playerToken.transform.SetParent(transform, false);
            playerToken.transform.localScale = Vector3.one * 0.55f;
            Destroy(playerToken.GetComponent<Collider>());
            playerMaterial = CreateTokenMaterial(new Color(0.05f, 0.45f, 0.52f));
            playerToken.GetComponent<Renderer>().sharedMaterial = playerMaterial;

            goalToken = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            goalToken.name = "Exit - Goal Room";
            goalToken.transform.SetParent(transform, false);
            goalToken.transform.localScale = new Vector3(0.42f, 0.06f, 0.42f);
            Destroy(goalToken.GetComponent<Collider>());
            goalMaterial = CreateTokenMaterial(new Color(0.91f, 0.64f, 0.21f));
            goalToken.GetComponent<Renderer>().sharedMaterial = goalMaterial;
            goalToken.transform.position = RoomMarkerPosition(GoalFloor, GetRoom(GoalFloor, GoalRoom));
        }

        private static Material CreateTokenMaterial(Color color)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit") ?? Shader.Find("Standard");
            if (shader == null)
                shader = Shader.Find("Unlit/Color");
            return new Material(shader) { color = color, name = "Map Runner Token" };
        }

        private void SnapTokensToMap()
        {
            playerToken.transform.position = RoomMarkerPosition(currentFloor, GetRoom(currentFloor, currentRoom));
            goalToken.SetActive(currentFloor == GoalFloor);
            hasWon = currentFloor == GoalFloor && currentRoom == GoalRoom;
            if (hasWon)
                message = "Exit reached! Press R to run the map again.";
        }

        private void UpdateGoalState()
        {
            goalToken.SetActive(currentFloor == GoalFloor);
            if (currentFloor == GoalFloor && currentRoom == GoalRoom)
            {
                hasWon = true;
                message = "Exit reached! Press R to run the map again.";
            }
            else
            {
                message = "Room reached. Find the stair or follow the graph onward.";
            }
        }

        private void RestartRun()
        {
            currentFloor = 1;
            currentRoom = 1;
            isMoving = false;
            waypoints.Clear();
            hasWon = false;
            mapRenderer.ShowFloor(currentFloor);
            message = "Find the exit. Follow the room graph.";
            SnapTokensToMap();
        }

        private void OnGUI()
        {
            if (UseExternalHud)
                return;
            EnsureGuiStyles();
            GUI.Box(new Rect(22f, 22f, 330f, 196f), GUIContent.none, panelStyle);
            GUI.Label(new Rect(42f, 38f, 290f, 30f), "ROOM RUNNER // MAP 01", headingStyle);
            if (building != null)
            {
                GUI.Label(new Rect(42f, 75f, 290f, 26f),
                    $"FLOOR {currentFloor:00}   ROOM {currentRoom:00}", bodyStyle);
                GUI.Label(new Rect(42f, 103f, 290f, 26f),
                    $"EXIT: FLOOR {GoalFloor:00} / ROOM {GoalRoom:00}", bodyStyle);
            }
            GUI.Label(new Rect(42f, 137f, 290f, 42f), message, bodyStyle);
            GUI.Label(new Rect(24f, Screen.height - 46f, 660f, 28f),
                "MOVE  WASD / ARROWS     UP STAIRS  E     DOWN STAIRS  Q     RESTART  R",
                headingStyle);
        }

        private void EnsureGuiStyles()
        {
            if (panelStyle != null)
                return;

            panelTexture = new Texture2D(1, 1);
            panelTexture.SetPixel(0, 0, new Color(0.98f, 0.93f, 0.84f, 0.94f));
            panelTexture.Apply();
            panelStyle = new GUIStyle(GUI.skin.box)
            {
                normal = { background = panelTexture, textColor = new Color(0.19f, 0.14f, 0.10f) },
                border = new RectOffset(3, 3, 3, 3),
                padding = new RectOffset(12, 12, 10, 10),
            };
            headingStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 15,
                fontStyle = FontStyle.Bold,
                normal = { textColor = new Color(0.52f, 0.25f, 0.13f) },
            };
            bodyStyle = new GUIStyle(GUI.skin.label)
            {
                fontSize = 14,
                normal = { textColor = new Color(0.22f, 0.17f, 0.13f) },
                wordWrap = true,
            };
        }

        private void OnDestroy()
        {
            if (playerMaterial != null)
                Destroy(playerMaterial);
            if (goalMaterial != null)
                Destroy(goalMaterial);
            if (panelTexture != null)
                Destroy(panelTexture);
        }
    }
}
