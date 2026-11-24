"""Regression checks for partitions, route geometry, stairs and export."""

from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from io import StringIO
import itertools
import json
import math
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree

from json_handoff.floor_diagrams import write_floor_diagrams
from json_handoff.web_server import generate_from_payload


def settings(seed=0, width=800, height=600, plan=(12, 15, 10)):
    return {
        "seed": str(seed), "width": str(width), "height": str(height),
        "floor_count": str(len(plan)), "room_mode": "plan",
        "room_plan": ",".join(map(str, plan)),
    }


def right(box):
    return box["x"] + box["width"]


def top(box):
    return box["y"] + box["height"]


def boxes_overlap(a, b):
    return (max(a["x"], b["x"]) < min(right(a), right(b)) - 1e-8
            and max(a["y"], b["y"]) < min(top(a), top(b)) - 1e-8)


class BuildingTests(unittest.TestCase):
    def assert_floor(self, floor, width, height):
        rooms = floor["rooms"]
        self.assertEqual(floor["room_count"], len(rooms))
        self.assertEqual(width * height, sum(r["region"]["width"] * r["region"]["height"] for r in rooms))
        for room in rooms:
            box, region = room["bounds"], room["region"]
            self.assertTrue(0 <= region["x"] < box["x"] < right(box) < right(region) <= width)
            self.assertTrue(0 <= region["y"] < box["y"] < top(box) < top(region) <= height)
        for a, b in itertools.combinations(rooms, 2):
            self.assertFalse(boxes_overlap(a["region"], b["region"]))
            self.assertFalse(boxes_overlap(a["bounds"], b["bounds"]))

        graph = floor["route_graph"]
        nodes = {node["id"]: node for node in graph["nodes"]}
        self.assertEqual(len(nodes), len(graph["nodes"]))
        neighbors = defaultdict(set)
        room_nodes = [node for node in nodes.values() if node["kind"] == "room"]
        self.assertEqual({node["room"] for node in room_nodes}, {room["id"] for room in rooms})
        for edge in graph["edges"]:
            first, second = edge["from_node"], edge["to_node"]
            a, b = nodes[first]["position"], nodes[second]["position"]
            self.assertNotEqual(first, second)
            self.assertNotIn(second, neighbors[first])
            neighbors[first].add(second)
            neighbors[second].add(first)
            self.assertTrue(math.isclose(a["x"], b["x"]) or math.isclose(a["y"], b["y"]))
            for room in rooms:
                if first in {node["id"] for node in room_nodes if node["room"] == room["id"]} or second in {
                    node["id"] for node in room_nodes if node["room"] == room["id"]
                }:
                    continue
                box = room["bounds"]
                if math.isclose(a["x"], b["x"]):
                    hit = (box["x"] + 1e-8 < a["x"] < right(box) - 1e-8
                           and max(min(a["y"], b["y"]), box["y"]) < min(max(a["y"], b["y"]), top(box)) - 1e-8)
                else:
                    hit = (box["y"] + 1e-8 < a["y"] < top(box) - 1e-8
                           and max(min(a["x"], b["x"]), box["x"]) < min(max(a["x"], b["x"]), right(box)) - 1e-8)
                self.assertFalse(hit, (edge, room["id"]))

        seen = {1}
        pending = deque([1])
        while pending:
            for candidate in neighbors[pending.popleft()] - seen:
                seen.add(candidate)
                pending.append(candidate)
        self.assertEqual(seen, set(nodes))
        for door in graph["doors"]:
            node = nodes[door["node"]]
            room = rooms[door["room"] - 1]
            box = room["bounds"]
            self.assertEqual(node["room"], room["id"])
            self.assertEqual(node["position"], door["position"])
            x, y = node["position"]["x"], node["position"]["y"]
            if door["side"] in ("west", "east"):
                self.assertAlmostEqual(x, box["x"] if door["side"] == "west" else right(box))
                self.assertTrue(box["y"] < y < top(box))
            else:
                self.assertAlmostEqual(y, box["y"] if door["side"] == "south" else top(box))
                self.assertTrue(box["x"] < x < right(box))

    def assert_building(self, building, width, height, plan):
        self.assertEqual(list(plan), building["metadata"]["rooms_per_floor"])
        self.assertEqual(len(plan)-1, len(building["stairs"]))
        for count, floor in zip(plan, building["floors"], strict=True):
            self.assertEqual(count, len(floor["rooms"]))
            self.assert_floor(floor, width, height)
        for stair_id, stair in enumerate(building["stairs"], 1):
            self.assertEqual(stair_id, stair["id"])
            a, b = stair["from"], stair["to"]
            self.assertEqual((stair_id, stair_id + 1), (a["floor"], b["floor"]))
            self.assertAlmostEqual(math.dist(list(a["position"].values()), list(b["position"].values())),
                                   stair["flight"]["horizontal_run"])
            self.assertGreater(stair["flight"]["vertical_rise"], 0)
            for endpoint, direction in ((a, "up"), (b, "down")):
                floor = building["floors"][endpoint["floor"] - 1]
                nodes = [n for n in floor["route_graph"]["nodes"] if n["stair"] == stair_id]
                self.assertEqual(1, len(nodes))
                node = nodes[0]
                self.assertEqual((endpoint["room"], direction), (node["room"], node["direction"]))
                for coord in ("x", "y"):
                    self.assertAlmostEqual(endpoint["position"][coord], node["position"][coord])
                self.assertIn(stair_id, floor["rooms"][node["room"] - 1]["stairs"])

    def test_many_seeds_and_edge_cases(self):
        cases = [(800, 600, (15, 25, 10)), (3, 3, (9, 8, 1)), (300, 3, (1, 42)),
                 (3, 300, (24, 7)), (60, 60, (1,)), (15, 20, (1,) * 12),
                 (100_000, 99_999, (150,))]
        count = 0
        with redirect_stdout(StringIO()):
            for seed in range(-7, 13):
                for width, height, plan in cases:
                    with self.subTest(seed=seed, width=width, height=height, plan=plan):
                        self.assert_building(generate_from_payload(settings(seed, width, height, plan)), width, height, plan)
                        count += 1
        print(f"Verified geometry, graph connectivity, and stairs on {count} buildings.")

    def test_total_mode_concurrent_determinism_and_exports(self):
        request = settings(20261116)
        request.update(room_mode="total", total_rooms="50")
        with redirect_stdout(StringIO()), ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(generate_from_payload, [request] * 12))
        first = results[0]
        self.assertTrue(all(result == first for result in results))
        self.assert_building(first, 800, 600, (17, 17, 16))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "export.json"
            path.write_text(json.dumps(first), encoding="utf-8")
            write_floor_diagrams(first, path)
            self.assertEqual(first, json.loads(path.read_text()))
            for index in range(1, 4):
                diagram = path.with_name(f"export_floor-{index}.svg")
                self.assertTrue(ElementTree.parse(diagram).getroot().tag.endswith("svg"))

    def test_invalid_settings(self):
        for changes in (
            {"width": 2}, {"height": "three"}, {"seed": 2**31},
            {"floor_count": 13}, {"room_plan": "15,25"}, {"room_plan": "15,0,10"},
            {"room_plan": "151,25,10"}, {"width": 3, "height": 3},
            {"room_mode": "total", "total_rooms": 2},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                generate_from_payload(settings() | changes)


if __name__ == "__main__":
    unittest.main()
