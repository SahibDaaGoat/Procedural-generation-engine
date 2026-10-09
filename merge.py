import random

import matplotlib.pyplot as plt

import navigation





def generate(seed, width1, height1, rooms, start_room, target_room):

    random.seed(seed)



    WIDTH = width1

    HEIGHT = height1

    NUMBER_OF_ROOMS = rooms



    # ------------------------------------------------------------

    # REGION FUNCTIONS

    # ------------------------------------------------------------

    def split_region(region):

        x, y, width, height = region



        # Split along the longer side.

        if width >= height:

            cut = random.randint(width // 3, (2 * width) // 3)

            first = (x, y, cut, height)

            second = (x + cut, y, width - cut, height)

        else:

            cut = random.randint(height // 3, (2 * height) // 3)

            first = (x, y, width, cut)

            second = (x, y + cut, width, height - cut)



        return [first, second]



    def center(region):

        x, y, width, height = region

        return x + width / 2, y + height / 2



    def area(region):

        return region[2] * region[3]



    # ------------------------------------------------------------

    # MERGING

    # ------------------------------------------------------------

    def can_merge(a, b):

        ax, ay, aw, ah = a

        bx, by, bw, bh = b



        # Side by side, sharing a full edge.

        if ah == bh and (ax + aw == bx or bx + bw == ax):

            return True



        # One above the other, sharing a full edge.

        if aw == bw and (ay + ah == by or by + bh == ay):

            return True



        return False



    def merge_regions(a, b):

        ax, ay, aw, ah = a

        bx, by, bw, bh = b



        x = min(ax, bx)

        y = min(ay, by)

        right = max(ax + aw, bx + bw)

        top = max(ay + ah, by + bh)



        return x, y, right - x, top - y



    # ------------------------------------------------------------

    # BSP GENERATION

    # ------------------------------------------------------------

    def choose_region(regions):

        return random.choices(regions, weights=[area(r) for r in regions], k=1)[0]



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

            regions.pop(j)  # Remove larger index first.

            regions.pop(i)

            regions.append(merged)



        return regions



    # ------------------------------------------------------------

    # NAVIGATION GRAPH

    # ------------------------------------------------------------

    def are_adjacent(a, b):

        ax, ay, aw, ah = a

        bx, by, bw, bh = b



        # a and b touch on a vertical edge and overlap vertically.

        if ax + aw == bx or bx + bw == ax:

            return max(ay, by) < min(ay + ah, by + bh)



        # a and b touch on a horizontal edge and overlap horizontally.

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



    # ------------------------------------------------------------

    # DFS ROUTING

    # ------------------------------------------------------------

    def dfs(graph, start, target):

        visited = set()

        path = []



        def search(node):

            visited.add(node)

            path.append(node)



            if node == target:

                return True



            for neighbour in graph[node]:

                if neighbour not in visited and search(neighbour):

                    return True



            path.pop()

            return False



        return path if search(start) else None



    # ------------------------------------------------------------

    # GENERATION

    # ------------------------------------------------------------

    print("\n       EXACT ROOM BSP GENERATOR\n")

    print("Requested rooms:", NUMBER_OF_ROOMS)



    # This algorithm uses an intermediate target of rooms // 2.

    if NUMBER_OF_ROOMS < 2 or NUMBER_OF_ROOMS % 2 != 0:

        print("ERROR: NUMBER_OF_ROOMS must be an even integer of at least 2.")

        return



    if WIDTH < 3 or HEIGHT < 3:

        print("ERROR: WIDTH and HEIGHT must both be at least 3.")

        return



    power = largest_power_of_two(NUMBER_OF_ROOMS)

    intermediate = NUMBER_OF_ROOMS // 2

    print("Largest power of 2 <= target:", power)

    print("Intermediate target:", intermediate)



    print("\nPHASE 1: BINARY PARTITIONING\n")

    regions = generate_power_regions(power)

    print("Generated", len(regions), "regions.")



    print("\nPHASE 2: MERGING\n")

    regions = merge_to_target(regions, intermediate)

    if regions is None:

        print("ERROR: The regions could not be merged to the target.")

        return

    print("Merged down to", len(regions), "regions.")



    print("\nPHASE 3: FINAL BINARY PARTITIONING\n")

    old_regions = regions.copy()

    for region in old_regions:

        regions.remove(region)

        regions.extend(split_region(region))

    print("Final number of regions:", len(regions))



    if len(regions) != NUMBER_OF_ROOMS:

        print("ERROR: Expected", NUMBER_OF_ROOMS, "rooms but generated", len(regions))

        return



    print("\nSUCCESS! Exactly", NUMBER_OF_ROOMS, "regions were generated.")



    # Build graph from the original regions, before shrinking the room rectangles.

    print("\nBUILDING NAVIGATION GRAPH...\n")

    graph = build_graph(regions)

    for room, neighbours in graph.items():

        print(f"Room {room + 1}:", [n + 1 for n in neighbours])



    print("\nDFS TEST\n")

    start_index = start_room - 1

    target_index = target_room - 1

    if not (1 <= start_room <= NUMBER_OF_ROOMS and 1 <= target_room <= NUMBER_OF_ROOMS):
        print(f"ERROR: Room numbers must be between 1 and {NUMBER_OF_ROOMS}.")
        return

    path = dfs(graph, start_index, target_index)

    if path is not None:

        print("Path:", [room + 1 for room in path])

    else:

        print("No path found.")



    # ------------------------------------------------------------

    # SHRINK ROOMS

    # ------------------------------------------------------------

    print("\nSHRINKING ROOMS...\n")



    def shrink_room(region):

        x, y, width, height = region



        # Keep margins small enough that the resulting room stays positive.

        max_margin_x = max(0, min(width // 3, (width - 1) // 2))

        max_margin_y = max(0, min(height // 3, (height - 1) // 2))

        min_margin_x = min(width // 20, max_margin_x)

        min_margin_y = min(height // 20, max_margin_y)

        margin_x = random.randint(min_margin_x, max_margin_x) if max_margin_x else 0

        margin_y = random.randint(min_margin_y, max_margin_y) if max_margin_y else 0



        return (

            x + margin_x,

            y + margin_y,

            width - 2 * margin_x,

            height - 2 * margin_y,

        )



    rooms_list = [shrink_room(region) for region in regions]

    print("Rooms created:", len(rooms_list))

    fig, ax = plt.subplots()

    print("\nOPENING VISUALIZATION...\n")

    for number, room in enumerate(rooms_list, start=1):
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
        ax.add_patch(rectangle)

        cx, cy = center(room)
        ax.text(
            cx,
            cy,
            str(number),
            ha="center",
            va="center",
            fontsize=7,
            zorder=4,
        )

    # Draw the graph and the selected route on the same axes.
    # navigation.py should use the signature:
    # draw_navigation(ax, rooms_list, graph, start_room, target_room)
    navigation.draw_navigation(ax, rooms_list, graph, start_room, target_room)

    ax.set_xlim(0, WIDTH)

    ax.set_ylim(0, HEIGHT)

    ax.set_aspect("equal")

    ax.set_title(f"BSP Procedural Generation - {NUMBER_OF_ROOMS} Rooms")

    ax.set_xlabel("x")

    ax.set_ylabel("y")

    ax.grid(True, zorder=0)



    fig.patch.set_facecolor("white")

    ax.set_facecolor("white")

    plt.show()

    plt.close(fig)





if __name__ == "__main__":

    generate(1000000, 1000000, 1000000, 10,2,8)
