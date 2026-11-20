using System;
using UnityEngine;

namespace ProceduralMapGenerator
{
    // Field names match the exported JSON so Unity's built-in JsonUtility can read it.
    [Serializable]
    public class BuildingMapData
    {
        public int schema_version;
        public BuildingMetadata metadata;
        public CoordinateSystem coordinate_system;
        public FloorMap[] floors;
        public StairLink[] stairs;
    }

    [Serializable]
    public class BuildingMetadata
    {
        public int seed;
        public int floor_count;
        public int[] rooms_per_floor;
        public int total_room_count;
        public float map_width;
        public float map_height;
        public float floor_height;
    }

    [Serializable]
    public class CoordinateSystem
    {
        public string origin;
        public string units;
        public MapRectangle bounds;
    }

    [Serializable]
    public class FloorMap
    {
        public int id;
        public int seed;
        public int room_count;
        public MapRoom[] rooms;
        public FloorNavigation navigation;
    }

    [Serializable]
    public class MapRoom
    {
        public int id;
        public MapRectangle region;
        public MapRectangle bounds;
        public MapPoint center;
        public int[] connections;
        public int[] stairs;
    }

    [Serializable]
    public class FloorNavigation
    {
        public int start_room;
        public int target_room;
        public int[] dfs_path;
        public int[] shortest_path;
    }

    [Serializable]
    public class StairLink
    {
        public int id;
        public string type;
        public int[] connects_floors;
        public StairEndpoint from;
        public StairEndpoint to;
        public StairFlight flight;
    }

    [Serializable]
    public class StairEndpoint
    {
        public int floor;
        public int room;
        public string side;
        public MapPoint position;
        public float width;
    }

    [Serializable]
    public class StairFlight
    {
        public MapPoint3 start;
        public MapPoint3 end;
        public float horizontal_run;
        public float vertical_rise;
        public float clear_width;
    }

    [Serializable]
    public class MapPoint
    {
        public float x;
        public float y;
    }

    [Serializable]
    public class MapPoint3
    {
        public float x;
        public float y;
        public float z;
    }

    [Serializable]
    public class MapRectangle
    {
        public float x;
        public float y;
        public float width;
        public float height;
    }

    public static class BuildingMapJson
    {
        public static BuildingMapData Parse(string json)
        {
            return JsonUtility.FromJson<BuildingMapData>(json);
        }
    }
}
