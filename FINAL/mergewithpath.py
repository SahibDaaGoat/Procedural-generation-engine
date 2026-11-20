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

            cut = random.randint(
                width // 3,
                2 * width // 3
            )

            first = (x, y, cut, height)
            second = (
                x + cut,
                y,
                width - cut,
                height
            )

        else:

            cut = random.randint(
                height // 3,
                2 * height // 3
            )

            first = (x, y, width, cut)
            second = (
                x,
                y + cut,
                width,
                height - cut
            )

        return [first, second]


    def center(region):

        x, y, width, height = region

        return (
            x + width / 2,
            y + height / 2
        )


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

        right = max(
            ax + aw,
            bx + bw
        )

        top = max(
            ay + ah,
            by + bh
        )

        return (
            x,
            y,
            right - x,
            top - y
        )


    # ============================================================
    # BSP GENERATION
    # ============================================================

    def choose_region(regions):

        weights = []

        for region in regions:
            weights.append(area(region))

        return random.choices(
            regions,
            weights=weights,
            k=1
        )[0]


    def largest_power_of_two(number):

        power = 1

        while power * 2 <= number:
            power *= 2

        return power


    def generate_power_regions(target):

        regions = [
            (0, 0, WIDTH, HEIGHT)
        ]

        while len(regions) < target:

            region = choose_region(regions)

            regions.remove(region)

            regions.extend(
                split_region(region)
            )

        return regions


    def merge_to_target(regions, target):

        while len(regions) > target:

            possible_pairs = []

            for i in range(len(regions)):

                for j in range(i + 1, len(regions)):

                    if can_merge(
                        regions[i],
                        regions[j]
                    ):

                        possible_pairs.append(
                            (i, j)
                        )

            if not possible_pairs:
                return None

            i, j = random.choice(
                possible_pairs
            )

            merged = merge_regions(
                regions[i],
                regions[j]
            )

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

        # --------------------------------------------------------
        # a is directly left/right of b
        # --------------------------------------------------------

        if ax + aw == bx or bx + bw == ax:

            # Their vertical ranges must overlap.
            return (
                max(ay, by)
                <
                min(ay + ah, by + bh)
            )

        # --------------------------------------------------------
        # a is directly above/below b
        # --------------------------------------------------------

        if ay + ah == by or by + bh == ay:

            # Their horizontal ranges must overlap.
            return (
                max(ax, bx)
                <
                min(ax + aw, bx + bw)
            )

        return False


    def build_graph(regions):

        graph = {
            i: []
            for i in range(len(regions))
        }

        for i in range(len(regions)):

            for j in range(i + 1, len(regions)):

                if are_adjacent(
                    regions[i],
                    regions[j]
                ):

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

    print(
        "Requested rooms:",
        NUMBER_OF_ROOMS
    )

    # This version uses the X/2 intermediate step,
    # so the requested number must be even.

    if NUMBER_OF_ROOMS % 2 != 0:

        print()
        print("ERROR:")
        print("NUMBER_OF_ROOMS must be even.")
        print()

        return

    # ------------------------------------------------------------
    # Find 2^k.
    # ------------------------------------------------------------

    power = largest_power_of_two(
        NUMBER_OF_ROOMS
    )

    intermediate = NUMBER_OF_ROOMS // 2

    print(
        "Largest power of 2 <= target:",
        power
    )

    print(
        "Intermediate target:",
        intermediate
    )

    # ============================================================
    # PHASE 1
    # ============================================================

    print()
    print("PHASE 1: BINARY PARTITIONING")
    print()

    regions = generate_power_regions(
        power
    )

    print(
        "Generated",
        len(regions),
        "regions."
    )

    # ============================================================
    # PHASE 2
    # ============================================================

    print()
    print("PHASE 2: MERGING")
    print()

    regions = merge_to_target(
        regions,
        intermediate
    )

    if regions is None:

        print()
        print("ERROR:")
        print(
            "The regions could not be merged to the target."
        )
        print()

        return

    print(
        "Merged down to",
        len(regions),
        "regions."
    )

    # ============================================================
    # PHASE 3
    # ============================================================

    print()
    print("PHASE 3: FINAL BINARY PARTITIONING")
    print()

    old_regions = regions.copy()

    for region in old_regions:

        regions.remove(region)

        new_regions = split_region(
            region
        )

        regions.extend(
            new_regions
        )

    print(
        "Final number of regions:",
        len(regions)
    )

    # ============================================================
    # VERIFY RESULT
    # ============================================================

    if len(regions) == NUMBER_OF_ROOMS:

        print()
        print("SUCCESS!")

        print(
            "Exactly",
            NUMBER_OF_ROOMS,
            "regions were generated."
        )

    else:

        print()
        print("ERROR!")

        print(
            "Expected:",
            NUMBER_OF_ROOMS
        )

        print(
            "Generated:",
            len(regions)
        )

        return

    # ============================================================
    # BUILD NAVIGATION GRAPH
    # ============================================================

    print()
    print("BUILDING NAVIGATION GRAPH...")
    print()

    graph = build_graph(regions)

    for room, neighbours in graph.items():

        print(
            f"Room {room + 1}:",
            [
                neighbour + 1
                for neighbour in neighbours
            ]
        )

    # ============================================================
    # TEST DFS
    # ============================================================

    print()
    print("DFS TEST")
    print()

    start_room = 0
    target_room = NUMBER_OF_ROOMS - 1

    path = dfs(
        graph,
        start_room,
        target_room
    )

    if path is not None:

        print(
            "Path:",
            [
                room + 1
                for room in path
            ]
        )

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

        margin_x = random.randint(
            width // 20,
            width // 3
        )

        margin_y = random.randint(
            height // 20,
            height // 3
        )

        x = x + margin_x
        y = y + margin_y

        width = width - 2 * margin_x
        height = height - 2 * margin_y

        return (
            x,
            y,
            width,
            height
        )


    rooms_list = []

    for region in regions:

        room = shrink_room(region)

        rooms_list.append(room)

    print(
        "Rooms created:",
        len(rooms_list)
    )

    # ============================================================
    # VISUALIZATION
    # ============================================================

    print()
    print("OPENING VISUALIZATION...")
    print()

    for number, room in enumerate(
        rooms_list,
        start=1
    ):

        # Draw each navigation-graph edge once, from the center of one room
        # to the center of its adjacent room.  The graph was built from
        # `regions`, and `rooms_list` preserves the same room indices.
        room_index = number - 1

        for neighbour_index in graph[room_index]:

            # The graph is undirected, so only draw the lower-indexed side.
            if room_index < neighbour_index:

                start_x, start_y = center(rooms_list[room_index])
                end_x, end_y = center(rooms_list[neighbour_index])

                plt.plot(
                    [start_x, end_x],
                    [start_y, end_y],
                    color="darkkhaki",
                    linewidth=4,
                    alpha=1,
                    zorder=1,
                )

        x, y, width, height = room
     
        rectangle = plt.Rectangle(
            (x, y),
            width,
            height,
            fill=True,
            edgecolor="black",
            facecolor="silver",
            linewidth=1.5,
            zorder=2,
        )
    
        plt.gca().add_patch(
            rectangle
        )

        cx, cy = center(room)

        plt.text(
            cx,
            cy,
            str(number),
            ha="center",
            va="center",
            fontsize=7,
            zorder=3,
        )

    plt.xlim(
        0,
        WIDTH
    )

    plt.ylim(
        0,
        HEIGHT
    )

    plt.gca().set_aspect(
        "equal"
    )

    plt.title(
        f"BSP Procedural Generation - "
        f"{NUMBER_OF_ROOMS} Rooms"
    )

    plt.xlabel("x")
    plt.ylabel("y")

    plt.grid()

    plt.show()

generate(67,1000,1000,6)