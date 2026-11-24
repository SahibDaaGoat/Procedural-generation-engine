# Project UML and Data Flow Diagrams

These diagrams describe the V2 application in this folder. The browser generator runs locally. Unity is a downstream consumer of exported JSON and is not part of the browser request path.

## 1. UML component diagram

```mermaid
flowchart LR
    User[User]
    Browser[Browser UI\njson_handoff/web]
    Entry[App entry point\napp.py]
    HTTP[Local HTTP/API\njson_handoff/web_server.py]
    Building[Building orchestrator\nmultifloor_unity/building_generator.py]
    Floor[Floor builder\nbsp_generation/generator.py]
    Partition[Partitioning\nbsp_generation/partitioning.py, geometry.py]
    Room[Room footprints\nbsp_generation/rooms.py]
    Graph[Room adjacency\ngraphs_navigation/graph.py]
    Routes[Door-aware route graph\ngraphs_navigation/route_graph.py]
    Export[Serializer\njson_handoff/map_export.py]
    SVG[Floor diagrams\njson_handoff/floor_diagrams.py]
    JSON[(Building JSON\njson_handoff/maps/*.json)]
    SVGFiles[(Floor SVGs\njson_handoff/maps/*_floor-N.svg)]
    Schema[JSON schemas\njson_handoff/*.json]
    Unity[Unity package and showcase\nmultifloor_unity/unity]

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
    participant Server as json_handoff/web_server.py
    participant BG as multifloor_unity/building_generator.py
    participant Floor as bsp_generation/generator.py and floor modules
    participant Route as graphs_navigation/route_graph.py
    participant Export as json_handoff/map_export.py
    participant Diagram as json_handoff/floor_diagrams.py
    participant Disk as json_handoff/maps/ output directory

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
    Floors((3. Generate floors\nbsp_generation/generator.py))
    BSP((3a. Partition regions\nbsp_generation/geometry.py, partitioning.py))
    Rooms((3b. Create inset rooms\nbsp_generation/rooms.py))
    Graph((3c. Build adjacency and paths\ngraphs_navigation/graph.py))
    Building((4. Connect floors\nmultifloor_unity/building_generator.py))
    Routes((5. Build door-aware routes\ngraphs_navigation/route_graph.py))
    Serialize((6. Serialize building\njson_handoff/map_export.py))
    SVG((7. Draw floor diagrams\njson_handoff/floor_diagrams.py))
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
- JSON and SVG files are written under `json_handoff/maps/`; the browser preview is returned directly by the API.
- The Unity flow starts after export/import. It consumes the building JSON; it does not call the browser server during ordinary map generation.
