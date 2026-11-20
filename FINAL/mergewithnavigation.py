import random
import matplotlib.pyplot as plt


def generate(seed, width1, height1, rooms):
    random.seed(seed)

    WIDTH = width1
    HEIGHT = height1
    NUMBER_OF_ROOMS = rooms

    # ============================================================
    # REGION FUNCTIONS
    # ============================================================

    def split_region(region):
        x, y, width, height = region

        # Split along the longer side.
        if width >= height:
            cut = random.randint(width // 3, 2 * width // 3)
            first = (x, y, cut, height)
            second = (x + cut, y, width - cut, height)
        else:
            cut = random.randint(height // 3, 2 * height // 3)
            first = (x, y, width, cut)
            second = (x, y + cut, width, height - cut)

        return [first, second]

    def center(region):
        x, y, width, height = region
        return (x + width / 2, y + height / 2)

    def area(region):
        return region[2] * region[3]

    # ============================================================
    # MERGING
    # ============================================================

    def can_merge(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b

        # Side by side.
        if ah == bh:
            if ax + aw == bx or bx + bw == ax:
                return True

        # One above the other.
        if aw == bw:
            if ay + ah == by or by + bh == ay:
                return True

        return False

    def merge_regions(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b

        x = min(ax, bx)
        y = min(ay, by)
        right = max(ax + aw, bx + bw)
        top = max(ay + ah, by + bh)

        return (x, y, right - x, top - y)

    # ============================================================
    # BSP GENERATION
    # ============================================================

    def choose_region(regions):
        weights = [area(region) for region in regions]
        return random.choices(regions, weights=weights, k=1)[0]

    def largest_power_of_two(number):
        power = 1
        while power * 2 <= number:
            power *= 2
        return power

    def generate_power_regions(target):
        regions = [(0, 0, WIDTH, HEIGHT)]

        while len(regions) < target:
            region = choose_region(regions)
            regions.remove(region)
            regions.extend(split_region(region))

        return regions

    def merge_to_target(regions, target):
        while len(regions) > target:
            possible_pairs = []

            for i in range(len(regions)):
                for j in range(i + 1, len(regions)):
                    if can_merge(regions[i], regions[j]):
                        possible_pairs.append((i, j))

            if not possible_pairs:
                return None

            i, j = random.choice(possible_pairs)
            merged = merge_regions(regions[i], regions[j])

            # Remove larger index first.
            regions.pop(j)
            regions.pop(i)
            regions.append(merged)

        return regions

    # ============================================================
    # NAVIGATION GRAPH
    # ============================================================

    def are_adjacent(a, b):
        ax, ay, aw, ah = a
        bx, by, bw, bh = b

        # a is directly left/right of b.
        if ax + aw == bx or bx + bw == ax:
            return max(ay, by) < min(ay + ah, by + bh)

        # a is directly above/below b.
        if ay + ah == by or by + bh == ay:
            return max(ax, bx) < min(ax + aw, bx + bw)

        return False

    def build_graph(regions):
        graph = {i: [] for i in range(len(regions))}

        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                if are_adjacent(regions[i], regions[j]):
                    graph[i].append(j)
                    graph[j].append(i)

        return graph

    # ============================================================
    # DFS ROUTING
    # ============================================================

    def dfs(graph, start, target):
        visited = set()
        path = []

        def search(node):
            if node == target:
                path.append(node)
                return True

            visited.add(node)
            path.append(node)

            for neighbour in graph[node]:
                if neighbour not in visited:
                    if search(neighbour):
                        return True

            path.pop()
            return False

        if search(start):
            return path

        return None

    # ============================================================
    # GENERATION
    # ============================================================

    print()
    print("       EXACT ROOM BSP GENERATOR")
    print()
    print("Requested rooms:", NUMBER_OF_ROOMS)

    # This version uses the X/2 intermediate step,
    # so the requested number must be even.
    if NUMBER_OF_ROOMS % 2 != 0:
        print()
        print("ERROR:")
        print("NUMBER_OF_ROOMS must be even.")
        print()
        return

    power = largest_power_of_two(NUMBER_OF_ROOMS)
    intermediate = NUMBER_OF_ROOMS // 2

    print("Largest power of 2 <= target:", power)
    print("Intermediate target:", intermediate)

    # Phase 1: binary partitioning.
    print()
    print("PHASE 1: BINARY PARTITIONING")
    print()

    regions = generate_power_regions(power)
    print("Generated", len(regions), "regions.")

    # Phase 2: merging.
    print()
    print("PHASE 2: MERGING")
    print()

    regions = merge_to_target(regions, intermediate)

    if regions is None:
        print()
        print("ERROR:")
        print("The regions could not be merged to the target.")
        print()
        return

    print("Merged down to", len(regions), "regions.")

    # Phase 3: split each remaining region once.
    print()
    print("PHASE 3: FINAL BINARY PARTITIONING")
    print()

    old_regions = regions.copy()
    for region in old_regions:
        regions.remove(region)
        regions.extend(split_region(region))

    print("Final number of regions:", len(regions))

    # Verify result.
    if len(regions) == NUMBER_OF_ROOMS:
        print()
        print("SUCCESS!")
        print("Exactly", NUMBER_OF_ROOMS, "regions were generated.")
    else:
        print()
        print("ERROR!")
        print("Expected:", NUMBER_OF_ROOMS)
        print("Generated:", len(regions))
        return

    # Build graph using the original, unshrunk regions.
    print()
    print("BUILDING NAVIGATION GRAPH...")
    print()

    graph = build_graph(regions)

    for room, neighbours in graph.items():
        print(f"Room {room + 1}:", [n + 1 for n in neighbours])

    # Test DFS from first room to last room.
    print()
    print("DFS TEST")
    print()

    path = dfs(graph, 0, NUMBER_OF_ROOMS - 1)

    if path is not None:
        print("Path:", [room + 1 for room in path])
    else:
        print("No path found.")

    # ============================================================
    # SHRINK ROOMS
    # ============================================================

    print()
    print("SHRINKING ROOMS...")
    print()

    def shrink_room(region):
        x, y, width, height = region

        margin_x = random.randint(width // 20, width // 3)
        margin_y = random.randint(height // 20, height // 3)

        x += margin_x
        y += margin_y
        width -= 2 * margin_x
        height -= 2 * margin_y

        return (x, y, width, height)

    rooms_list = [shrink_room(region) for region in regions]
    print("Rooms created:", len(rooms_list))

    # ============================================================
    # VISUALIZATION: ROOMS, CENTRE POINTS, AND NAVIGATION LINES
    # ============================================================

    fig, ax = plt.subplots()

    # Draw room rectangles and labels.
    for number, room in enumerate(rooms_list, start=1):
        x, y, width, height = room

        rectangle = plt.Rectangle(
            (x, y),
            width,
            height,
            fill=False,
            edgecolor="black",
            linewidth=1.5
        )
        ax.add_patch(rectangle)

        cx, cy = center(room)
        ax.text(
            cx,
            cy,
            str(number),
            ha="center",
            va="center",
            fontsize=8,
            zorder=3
        )

    # Centre point for each visible room.
    room_centres = [center(room) for room in rooms_list]

    # Draw one line for every graph edge. Since the graph is
    # undirected, j > i prevents drawing each connection twice.
    for i, neighbours in graph.items():
        x1, y1 = room_centres[i]

        for j in neighbours:
            if j > i:
                x2, y2 = room_centres[j]
                ax.plot(
                    [x1, x2],
                    [y1, y2],
                    color="tab:blue",
                    linewidth=1.2,
                    zorder=1
                )

    # Draw a visible point at the centre of every room.
    centre_x = [point[0] for point in room_centres]
    centre_y = [point[1] for point in room_centres]

    ax.scatter(
        centre_x,
        centre_y,
        color="red",
        s=22,
        zorder=4,
        label="Room centre"
    )

    # Optional: highlight the DFS route in orange.
    if path:
        for i in range(len(path) - 1):
            x1, y1 = room_centres[path[i]]
            x2, y2 = room_centres[path[i + 1]]
            ax.plot(
                [x1, x2],
                [y1, y2],
                color="orange",
                linewidth=3,
                zorder=2,
                label="DFS path" if i == 0 else None
            )

    ax.set_xlim(0, WIDTH)
    ax.set_ylim(0, HEIGHT)
    ax.set_aspect("equal")
    ax.set_title(f"BSP Map - {NUMBER_OF_ROOMS} Rooms")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.grid(True)
    ax.legend()
    plt.show()

