# Project UML and Data Flow Diagrams

These diagrams describe the V2 application in this folder. The browser generator runs locally. Unity is a downstream consumer of exported JSON and is not part of the browser request path.

## 1. UML component diagram

```mermaid
flowchart LR
    User[User]
    Browser[Browser UI\nweb/index.html, app.js, style.css]
    Entry[App entry point\napp.py]
    HTTP[Local HTTP/API\nweb_server.py]
    Building[Building orchestrator\nbuilding_generator.py]
    Floor[Floor builder\ngenerator.py]
    Partition[Partitioning\npartitioning.py, geometry.py]
    Room[Room footprints\nrooms.py]
    Graph[Room adjacency\ngraph.py]
    Routes[Door-aware route graph\nroute_graph.py]
    Export[Serializer\nmap_export.py]
    SVG[Floor diagrams\nfloor_diagrams.py]
    JSON[(Building JSON\nmaps/*.json)]
    SVGFiles[(Floor SVGs\nmaps/*_floor-N.svg)]
    Schema[JSON schemas\nmap_schema.json, building_schema.json]
    Unity[Unity package and showcase]

    User --> Browser
    Browser -->|HTTP request and response| HTTP
    Entry -->|starts| HTTP
    HTTP -->|validated parameters| Building
    Building -->|build each floor| Floor
    Floor --> Partition
    Floor --> Room
    Floor --> Graph
    Building -->|stairs and floor metadata| Export
    Floor -->|regions, rooms, graph| Export
    Building --> Routes
    Routes --> Export
    Export --> JSON
    Export -. validates/documented by .-> Schema
    JSON --> SVG
    SVG --> SVGFiles
    HTTP -->|generated building response| Browser
    JSON -. imported separately .-> Unity
```

## 2. UML sequence diagram: generate a building

```mermaid
sequenceDiagram
    actor User
    participant UI as Browser UI
    participant Server as web_server.py
    participant BG as building_generator.py
    participant Floor as generator.py and floor modules
    participant Route as route_graph.py
    participant Export as map_export.py
    participant Diagram as floor_diagrams.py
    participant Disk as maps/ output directory

    User->>UI: Enter dimensions, seed, floors, room counts
    UI->>Server: POST /api/generate with settings
    Server->>Server: Parse and validate values
    Server->>BG: generate building(seed, size, floors, room plan)
    loop For each floor
        BG->>Floor: build_floor(floor seed, size, room count)
        Floor->>Floor: Partition map into exact-count regions
        Floor->>Floor: Shrink regions to room footprints
        Floor->>Floor: Build room adjacency and traversal paths
        Floor-->>BG: Regions, rooms, graph, DFS path
    end
    BG->>BG: Select and validate stair landings between floors
    BG->>Route: Add door-aware route graph to each floor
    Route-->>BG: Nodes, edges, door and stair-node metadata
    BG-->>Server: Complete building data
    Server->>Export: Serialize versioned building JSON
    Export->>Disk: Write building JSON
    Server->>Diagram: Render one SVG per floor
    Diagram->>Disk: Write floor SVG files
    Server-->>UI: Return building data and export filename
    UI-->>User: Preview floors and routes; show export result
```

## 3. DFD context diagram (Level 0)

```mermaid
flowchart LR
    U[External entity: User]
    G((Process 0:\nProcedural building generator))
    J[(Data store:\nBuilding JSON exports)]
    S[(Data store:\nFloor SVG exports)]
    Unity[External system:\nUnity showcase/importer]

    U -->|Generation settings| G
    G -->|Generated building JSON| U
    G -->|Save building data| J
    G -->|Save per-floor diagrams| S
    J -->|Selected JSON file| Unity
    Unity -->|3D scene display| U
```

## 4. DFD detailed diagram (Level 1)

```mermaid
flowchart LR
    User[External entity: User]
    UI((1. Configure and preview\nweb UI))
    API((2. Validate request\nweb_server.py))
    Floors((3. Generate floors\ngenerator.py))
    BSP((3a. Partition regions\ngeometry.py, partitioning.py))
    Rooms((3b. Create inset rooms\nrooms.py))
    Graph((3c. Build adjacency and paths\ngraph.py))
    Building((4. Connect floors\nbuilding_generator.py))
    Routes((5. Build door-aware routes\nroute_graph.py))
    Serialize((6. Serialize building\nmap_export.py))
    SVG((7. Draw floor diagrams\nfloor_diagrams.py))
    D1[(D1: Building JSON files)]
    D2[(D2: Floor SVG files)]
    Unity[External entity: Unity importer/showcase]

    User -->|Dimensions, seed, floor count, room mode/counts| UI
    UI -->|JSON request| API
    API -->|Validated settings| Floors
    Floors -->|Map bounds and requested room count| BSP
    BSP -->|Non-overlapping regions| Rooms
    BSP -->|Region adjacency input| Graph
    Rooms -->|Inset room bounds| Graph
    Floors -->|Floor geometry and graph| Building
    Building -->|Adjacent-floor stair endpoints| Routes
    Graph -->|Adjacency and traversal metadata| Serialize
    Rooms -->|Room geometry| Serialize
    Routes -->|Nodes, edges, doors, stair nodes| Serialize
    Building -->|Metadata, floors, stairs| Serialize
    Serialize -->|Versioned building data| D1
    D1 -->|Building data| SVG
    SVG -->|One diagram per floor| D2
    Serialize -->|Generated data for preview| API
    API -->|Building response and export name| UI
    UI -->|Interactive floor preview| User
    D1 -->|User-selected export file| Unity
    Unity -->|Rendered 3D map| User
```

### Diagram notes

- A fixed seed and identical inputs reproduce a layout under the same generator version.
- A building with *N* floors has *N−1* stair transitions.
- JSON and SVG files are written under `maps/`; the browser preview is returned directly by the API.
- The Unity flow starts after export/import. It consumes the building JSON; it does not call the browser server during ordinary map generation.
