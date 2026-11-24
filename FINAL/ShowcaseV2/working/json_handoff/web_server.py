"""Local HTTP interface for multi-floor map generation."""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from json_handoff.floor_diagrams import write_floor_diagrams
from json_handoff.map_export import save_building_data
from multifloor_unity.building_generator import generate_building


def _asset_directory():
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "web"
    return Path(__file__).resolve().parent / "web"


def distribute_rooms(total_rooms, floor_count):
    """Spread a total as evenly as possible, putting remainders on early floors."""
    if total_rooms < floor_count:
        raise ValueError("Total rooms must be at least the number of floors.")
    base, remainder = divmod(total_rooms, floor_count)
    return [base + (1 if floor < remainder else 0) for floor in range(floor_count)]


def _integer(payload, field, minimum=None):
    try:
        value = int(payload[field])
    except (KeyError, TypeError, ValueError):
        raise ValueError(f"{field.replace('_', ' ').title()} must be a whole number.")
    if minimum is not None and value < minimum:
        raise ValueError(f"{field.replace('_', ' ').title()} must be at least {minimum}.")
    return value


def generate_from_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("Expected a map settings object.")
    width = _integer(payload, "width", 3)
    height = _integer(payload, "height", 3)
    seed = _integer(payload, "seed")
    floor_count = _integer(payload, "floor_count", 1)
    if max(width, height) > 100_000 or not -(2**31) <= seed <= 2**31 - floor_count:
        raise ValueError("Use dimensions up to 100,000 and a signed 32-bit seed.")
    if floor_count > 12:
        raise ValueError("Use at most 12 floors.")
    if payload.get("room_mode") == "plan":
        try:
            room_counts = [int(value.strip()) for value in str(payload.get("room_plan", "")).split(",")]
        except ValueError:
            raise ValueError("Enter one whole room count per floor, separated by commas.") from None
        if len(room_counts) != floor_count or min(room_counts) < 1:
            raise ValueError("Enter one positive room count per floor.")
    else:
        room_counts = distribute_rooms(_integer(payload, "total_rooms", 1), floor_count)
    if max(room_counts) > min(150, width * height) or sum(room_counts) > 600:
        raise ValueError("Use up to 150 rooms per floor (limited by map area) and 600 per building.")
    return generate_building(seed, width, height, floor_count, room_counts)


class MapRequestHandler(BaseHTTPRequestHandler):
    server_version = "MapGenerator/1.0"

    def _write(self, status, body, content_type="application/json; charset=utf-8"):
        encoded = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        path = urlparse(self.path).path
        asset_names = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}
        filename = asset_names.get(path)
        if filename is None:
            self._write(404, json.dumps({"error": "Not found."}))
            return
        asset_path = _asset_directory() / filename
        try:
            self._write(200, asset_path.read_bytes(), self._content_type(filename))
        except OSError:
            self._write(500, json.dumps({"error": "The web app files could not be loaded."}))

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/shutdown":
            self._write(200, json.dumps({"ok": True}))
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if path != "/api/generate":
            self._write(404, json.dumps({"error": "Not found."}))
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            building = generate_from_payload(payload)
            metadata = building["metadata"]
            export_path = save_building_data(
                metadata["seed"], metadata["map_width"], metadata["map_height"],
                metadata["rooms_per_floor"], building,
            )
            write_floor_diagrams(building, export_path)
            building["export_file"] = export_path.name
            self._write(200, json.dumps(building, separators=(",", ":")))
        except (ValueError, TypeError, json.JSONDecodeError) as error:
            self._write(400, json.dumps({"error": str(error)}))
        except Exception as error:
            print("Map generation error:", repr(error))
            self._write(500, json.dumps({"error": "Map generation failed. Check the inputs and try again."}))

    @staticmethod
    def _content_type(filename):
        return {
            "index.html": "text/html; charset=utf-8",
            "app.js": "text/javascript; charset=utf-8",
            "style.css": "text/css; charset=utf-8",
        }[filename]

    def log_message(self, format_string, *args):
        print("Web app:", format_string % args)


def run():
    server = ThreadingHTTPServer(("127.0.0.1", 0), MapRequestHandler)
    address, port = server.server_address
    url = f"http://{address}:{port}/"
    print("Map generator web app:", url)
    threading.Timer(0.8, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
