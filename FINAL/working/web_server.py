"""Local HTTP interface for multi-floor map generation."""

import json
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from building_generator import generate_building
from map_export import save_building_data


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
            width = _integer(payload, "width", 3)
            height = _integer(payload, "height", 3)
            seed = _integer(payload, "seed")
            floor_count = _integer(payload, "floor_count", 1)

            if payload.get("room_mode") == "plan":
                room_counts = [int(value.strip()) for value in payload.get("room_plan", "").split(",")]
                if len(room_counts) != floor_count:
                    raise ValueError("Enter one room count for each floor, separated by commas.")
                if any(count < 1 for count in room_counts):
                    raise ValueError("Every floor must have at least one room.")
            else:
                total_rooms = _integer(payload, "total_rooms", 1)
                room_counts = distribute_rooms(total_rooms, floor_count)

            building = generate_building(seed, width, height, floor_count, room_counts)
            export_path = save_building_data(seed, width, height, room_counts, building)
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
