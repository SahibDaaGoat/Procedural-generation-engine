const form = document.getElementById("generator-form");
const modeRadios = [...document.querySelectorAll('input[name="room-mode"]')];
const errorBox = document.getElementById("form-error");
const statusLine = document.getElementById("form-status");
const generateButton = document.getElementById("generate-button");
const downloadButton = document.getElementById("download-json");
const emptyState = document.getElementById("empty-state");
const buildingView = document.getElementById("building-view");
const mapSvg = document.getElementById("map-svg");

let building = null;
let currentFloor = 0;

for (const radio of modeRadios) {
  radio.addEventListener("change", () => {
    const isPlan = document.querySelector('input[name="room-mode"]:checked').value === "plan";
    document.getElementById("total-control").hidden = isPlan;
    document.getElementById("plan-control").hidden = !isPlan;
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  errorBox.hidden = true;
  statusLine.textContent = "Generating floors and placing independent stair flights…";
  generateButton.disabled = true;
  generateButton.firstElementChild.textContent = "Generating…";
  const mode = document.querySelector('input[name="room-mode"]:checked').value;
  const payload = {
    width: document.getElementById("width").value,
    height: document.getElementById("height").value,
    seed: document.getElementById("seed").value,
    floor_count: document.getElementById("floor-count").value,
    room_mode: mode,
    total_rooms: document.getElementById("total-rooms").value,
    room_plan: document.getElementById("room-plan-input").value,
  };
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || "Generation failed.");
    building = result;
    currentFloor = 0;
    emptyState.hidden = true;
    buildingView.hidden = false;
    downloadButton.disabled = false;
    statusLine.textContent = `Saved ${result.export_file} beside the app.`;
    renderFloor();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
    statusLine.textContent = "The map was not generated.";
  } finally {
    generateButton.disabled = false;
    generateButton.firstElementChild.textContent = "Generate building";
  }
});

document.getElementById("floor-down").addEventListener("click", () => changeFloor(-1));
document.getElementById("floor-up").addEventListener("click", () => changeFloor(1));

function changeFloor(delta) {
  if (!building) return;
  currentFloor = Math.max(0, Math.min(building.floors.length - 1, currentFloor + delta));
  renderFloor();
}

function renderFloor() {
  const floor = building.floors[currentFloor];
  const { map_width: width, map_height: height } = building.metadata;
  const floorNumber = floor.id;
  const rooms = floor.rooms;
  const colors = ["#f4d6bf", "#e9dfc9", "#dfe7d6", "#f1e3d3", "#eed0bb", "#e8e2d5"];
  mapSvg.setAttribute("viewBox", `${-width * 0.02} ${-height * 0.02} ${width * 1.04} ${height * 1.04}`);
  mapSvg.setAttribute("preserveAspectRatio", "xMidYMid meet");

  const xy = (point) => [point.x, height - point.y];
  const parts = [];
  parts.push(`<rect x="0" y="0" width="${width}" height="${height}" fill="#fffaf3"/>`);

  for (const room of rooms) {
    const box = room.bounds;
    const top = height - box.y - box.height;
    parts.push(`<rect x="${box.x}" y="${top}" width="${box.width}" height="${box.height}" rx="${Math.max(2, Math.min(box.width, box.height) * 0.025)}" fill="${colors[(room.id - 1) % colors.length]}" stroke="#9f765c" stroke-width="${Math.max(width, height) * 0.002}"/>`);
    const [cx, cy] = xy(room.center);
    parts.push(`<text x="${cx}" y="${cy - Math.min(box.height * 0.19, height * 0.018)}" text-anchor="middle" dominant-baseline="central" fill="#392d26" font-size="${Math.min(box.width * 0.3, box.height * 0.28, Math.min(width, height) * 0.027)}" font-family="Segoe UI,Arial,sans-serif" font-weight="700">${room.id}</text>`);
  }

  const landings = building.stairs.flatMap((stair) => {
    const endpoint = [stair.from, stair.to].find((item) => item.floor === floorNumber);
    return endpoint ? [{ stair, endpoint }] : [];
  });
  const size = Math.min(width, height);
  const edgeWidth = size * 0.004;
  parts.push(`<rect x="0" y="0" width="${width}" height="${height}" fill="none" stroke="#137bc4" stroke-width="${edgeWidth * 4}"/>`);
  const graph = floor.route_graph;
  if (graph) {
    const nodes = new Map(graph.nodes.map((node) => [node.id, node]));
    for (const edge of graph.edges) {
      const [x1, y1] = xy(nodes.get(edge.from_node).position);
      const [x2, y2] = xy(nodes.get(edge.to_node).position);
      parts.push(`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#218441" stroke-width="${edgeWidth}" stroke-linecap="round"/>`);
    }
    for (const node of graph.nodes) {
      const [x, y] = xy(node.position);
      if (node.kind === "stair") {
        const radius = edgeWidth * 3;
        parts.push(`<path d="M ${x} ${y-radius} l ${radius} ${radius} ${-radius} ${radius} ${-radius} ${-radius} Z" fill="#f0ae39" stroke="#603919"/>`);
        parts.push(`<text x="${x}" y="${y}" text-anchor="middle" dominant-baseline="central" font-size="${radius * 1.3}">${node.direction === "up" ? "↑" : "↓"}</text>`);
      } else {
        parts.push(`<circle cx="${x}" cy="${y}" r="${edgeWidth * 1.3}" fill="#c72734"/>`);
      }
    }
  }

  mapSvg.innerHTML = parts.join("");
  mapSvg.setAttribute("aria-label", `Floor ${floorNumber} map with ${rooms.length} rooms and ${landings.length} independent stair landings`);
  document.getElementById("floor-kicker").textContent = `FLOOR ${floorNumber} OF ${building.floors.length}`;
  document.getElementById("floor-name").textContent = floorNumber === 1 ? "Ground floor" : `Floor ${floorNumber - 1}`;
  document.getElementById("floor-room-count").textContent = `${rooms.length} rooms`;
  document.getElementById("floor-seed").textContent = floor.seed;
  document.getElementById("room-plan-summary").textContent = building.metadata.rooms_per_floor.join(" · ");
  document.getElementById("viewer-subtitle").textContent = `${building.metadata.total_room_count} rooms across ${building.floors.length} floors`;
  document.getElementById("floor-down").disabled = currentFloor === 0;
  document.getElementById("floor-up").disabled = currentFloor === building.floors.length - 1;

  const currentStairs = building.stairs.filter((item) => item.from.floor === floorNumber || item.to.floor === floorNumber);
  if (!currentStairs.length) {
    document.getElementById("stair-summary").textContent = "Single-floor map";
  } else {
    const links = currentStairs.map((stair) => {
      const goingUp = stair.from.floor === floorNumber;
      const other = goingUp ? stair.to : stair.from;
      const landing = goingUp ? stair.from : stair.to;
      return `${goingUp ? "↑" : "↓"} Floor ${other.floor}, room ${other.room} · ${landing.side} door · run ${stair.flight.horizontal_run.toFixed(1)}`;
    });
    document.getElementById("stair-summary").textContent = links.join("\n");
  }
}

downloadButton.addEventListener("click", () => {
  if (!building) return;
  const { export_file, ...jsonData } = building;
  const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = building.export_file;
  link.click();
  URL.revokeObjectURL(link.href);
});

document.getElementById("close-app").addEventListener("click", async () => {
  try { await fetch("/api/shutdown", { method: "POST" }); } catch (_) { /* server is closing */ }
  document.body.innerHTML = "<main style='font:16px Segoe UI,Arial;padding:48px;color:#392d26;background:#fffaf3;min-height:100vh'><h1>Generator closed</h1><p>You can close this browser tab.</p></main>";
});
