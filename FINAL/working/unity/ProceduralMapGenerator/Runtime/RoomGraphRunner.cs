using System;
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
        private Vector3 moveTarget;
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
            if (buildingJson == null)
            {
                message = "Assign a building JSON TextAsset to RoomGraphRunner.";
                enabled = false;
                return;
            }

            building = BuildingMapJson.Parse(buildingJson.text);
            if (building == null || building.floors == null || building.floors.Length == 0)
            {
                message = "The selected JSON does not contain a building.";
                enabled = false;
                return;
            }

            if (mapRenderer == null)
            {
                message = "Add BuildingMapRenderer to the scene and assign it here.";
                enabled = false;
                return;
            }

            if (!mapRenderer.HasGeneratedGeometry)
                mapRenderer.GenerateFromJson(buildingJson.text);
            currentFloor = 1;
            currentRoom = 1;
            CreateTokens();
            mapRenderer.ShowFloor(currentFloor);
            SnapTokensToMap();
        }

        private void Update()
        {
            if (building == null)
                return;

            if (isMoving)
            {
                playerToken.transform.position = Vector3.MoveTowards(
                    playerToken.transform.position, moveTarget, moveSpeed * Time.deltaTime);
                if ((playerToken.transform.position - moveTarget).sqrMagnitude < 0.0025f)
                {
                    playerToken.transform.position = moveTarget;
                    isMoving = false;
                    mapRenderer.ShowFloor(currentFloor);
                    UpdateGoalState();
                }
                return;
            }

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
                    current.center.y - candidate.center.y);
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

                currentFloor = destination.floor;
                currentRoom = destination.room;
                message = $"Taking stair {stair.id} to floor {currentFloor}, room {currentRoom}.";
                BeginMoveToCurrentRoom();
                return;
            }

            message = goingUp
                ? "There is no stair going up from this room."
                : "There is no stair going down from this room.";
        }

        private void BeginMoveToCurrentRoom()
        {
            moveTarget = RoomMarkerPosition(currentFloor, GetRoom(currentFloor, currentRoom));
            isMoving = true;
        }

        private Vector3 RoomMarkerPosition(int floorNumber, MapRoom room)
        {
            float elevation = (floorNumber - 1) * mapRenderer.unityFloorHeight;
            return new Vector3(
                room.center.x * mapRenderer.mapUnitScale,
                elevation + mapRenderer.wallHeight + mapRenderer.lineAboveWalls + 0.22f,
                room.center.y * mapRenderer.mapUnitScale);
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
            playerToken.transform.localScale = Vector3.one * 0.34f;
            Destroy(playerToken.GetComponent<Collider>());
            playerMaterial = CreateTokenMaterial(new Color(0.81f, 0.27f, 0.12f));
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
            hasWon = false;
            mapRenderer.ShowFloor(currentFloor);
            message = "Find the exit. Follow the room graph.";
            SnapTokensToMap();
        }

        private void OnGUI()
        {
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
