import random
import matplotlib.pyplot as plt


# ============================================================
# SETTINGS
# ============================================================
seed = int(input("seed -  "))
random.seed()

WIDTH = int(input("width :- "))
HEIGHT = int(input("height :- "))

NUMBER_OF_ROOMS = int(input("How many rooms are required :- "))


# ============================================================
# SPLIT ONE RECTANGLE
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


# ============================================================
# REGION INFORMATION
# ============================================================

def center(region):
    x, y, width, height = region

    return (
        x + width / 2,
        y + height / 2
    )


def area(region):
    return region[2] * region[3]


# ============================================================
# CHECK WHETHER TWO REGIONS CAN BE MERGED
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


# ============================================================
# MERGE TWO REGIONS
# ============================================================

def merge_regions(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    x = min(ax, bx)
    y = min(ay, by)

    right = max(ax + aw, bx + bw)
    top = max(ay + ah, by + bh)

    return (
        x,
        y,
        right - x,
        top - y
    )


# ============================================================
# CHOOSE A REGION TO SPLIT
#
# Larger regions are preferred.
# This helps avoid repeatedly splitting tiny regions.
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


# ============================================================
# FIND THE LARGEST POWER OF 2 <= X
# ============================================================

def largest_power_of_two(number):
    power = 1

    while power * 2 <= number:
        power *= 2

    return power


# ============================================================
# PHASE 1
#
# Generate the largest power of 2 before X.
# ============================================================

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


# ============================================================
# PHASE 2
#
# Merge neighbouring regions until the target is reached.
# ============================================================

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

        # Remove the larger index first.
        regions.pop(j)
        regions.pop(i)

        regions.append(merged)

    return regions


# ============================================================
# MAIN
# ============================================================

print()
print("==========================================")
print("       EXACT ROOM BSP GENERATOR")
print("==========================================")
print()

print("Requested rooms:", NUMBER_OF_ROOMS)


# This version uses the X/2 intermediate step,
# so the requested number must be even.

if NUMBER_OF_ROOMS % 2 != 0:

    print()
    print("ERROR:")
    print("NUMBER_OF_ROOMS must be even.")
    print()

else:

    # --------------------------------------------------------
    # Find 2^k.
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # PHASE 1
    # --------------------------------------------------------

    print()
    print("==========================================")
    print("PHASE 1: BINARY PARTITIONING")
    print("==========================================")

    regions = generate_power_regions(
        power
    )

    print(
        "Generated",
        len(regions),
        "regions."
    )


    # --------------------------------------------------------
    # PHASE 2
    # --------------------------------------------------------

    print()
    print("==========================================")
    print("PHASE 2: MERGING")
    print("==========================================")

    regions = merge_to_target(
        regions,
        intermediate
    )

    if regions is None:

        print()
        print("ERROR:")
        print("The regions could not be merged to the target.")
        print()

    else:

        print(
            "Merged down to",
            len(regions),
            "regions."
        )


        # ----------------------------------------------------
        # PHASE 3
        #
        # Split every remaining region once.
        # ----------------------------------------------------

        print()
        print("==========================================")
        print("PHASE 3: FINAL BINARY PARTITIONING")
        print("==========================================")

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


        # ----------------------------------------------------
        # Verify the result.
        # ----------------------------------------------------

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


        # ====================================================
        # VISUALIZATION
        # ====================================================

        print()
        print("Opening visualization...")

        for number, region in enumerate(
            regions,
            start=1
        ):

            x, y, width, height = region

            rectangle = plt.Rectangle(
                (x, y),
                width,
                height,
                fill=False
            )

            plt.gca().add_patch(
                rectangle
            )

            cx, cy = center(region)

            plt.text(
                cx,
                cy,
                str(number),
                ha="center",
                va="center",
                fontsize=7
            )


        plt.xlim(0, WIDTH)
        plt.ylim(0, HEIGHT)

        plt.gca().set_aspect(
            "equal"
        )

        plt.title(
            f"BSP Procedural Generation - {NUMBER_OF_ROOMS} Regions"
        )

        plt.xlabel("x")
        plt.ylabel("y")

        plt.grid()

        plt.show()
