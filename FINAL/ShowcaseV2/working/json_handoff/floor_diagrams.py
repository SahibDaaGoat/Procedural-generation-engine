"""Write standalone floor diagrams from building JSON."""

from pathlib import Path


def write_floor_diagrams(building, json_path):
    base = Path(json_path)
    for floor in building["floors"]:
        path = base.with_name(f"{base.stem}_floor-{floor['id']}.svg")
        path.write_text(floor_svg(building["metadata"], floor), encoding="utf-8")


def floor_svg(metadata, floor):
    width, height = metadata["map_width"], metadata["map_height"]
    scale = 900 / max(width, height)
    w, h = width * scale, height * scale
    def xy(point):
        return point["x"] * scale + 12, (height - point["y"]) * scale + 12
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w+24:g} {h+56:g}" role="img">',
        f'<title>Floor {floor["id"]} | Seed {metadata["seed"]}</title>',
        f'<rect width="{w+24:g}" height="{h+56:g}" fill="#fffaf1"/>',
        f'<rect x="12" y="12" width="{w:g}" height="{h:g}" fill="#e8e4da" stroke="#137bc4" stroke-width="3"/>',
    ]
    for room in floor["rooms"]:
        b = room["bounds"]
        x, y = xy({"x": b["x"], "y": b["y"] + b["height"]})
        parts.append(f'<rect x="{x:g}" y="{y:g}" width="{b["width"]*scale:g}" height="{b["height"]*scale:g}" fill="#f5dcc2" stroke="#805c44"/>')
    graph = floor["route_graph"]
    nodes = {node["id"]: node for node in graph["nodes"]}
    for edge in graph["edges"]:
        a, b = (xy(nodes[edge[key]]["position"]) for key in ("from_node", "to_node"))
        parts.append(f'<path d="M {a[0]:g} {a[1]:g} L {b[0]:g} {b[1]:g}" stroke="#218441" stroke-width="2" stroke-linecap="round"/>')
    for node in graph["nodes"]:
        x, y = xy(node["position"])
        if node["kind"] == "stair":
            arrow = "↑" if node["direction"] == "up" else "↓"
            parts.append(f'<path d="M {x:g} {y-8:g} l 8 8 -8 8 -8 -8 Z" fill="#f0ae39" stroke="#603919"/><text x="{x:g}" y="{y+4:g}" text-anchor="middle" font-size="12">{arrow}</text>')
        else:
            parts.append(f'<circle cx="{x:g}" cy="{y:g}" r="3" fill="#c72734"/>')
            if node["kind"] == "room":
                parts.append(f'<text x="{x+6:g}" y="{y-5:g}" font-size="12" fill="#301e18">{node["room"]}</text>')
    parts.append(f'<text x="12" y="{h+42:g}" font-family="sans-serif" font-size="13">Floor {floor["id"]} · {len(floor["rooms"])} rooms · ◆ Stair landing</text></svg>')
    return "\n".join(parts)
