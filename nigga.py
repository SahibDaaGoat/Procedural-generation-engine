import random
import matplotlib.pyplot as plt


random.seed(42)

WIDTH = 100
HEIGHT = 70

FIRST_TARGET = 16

FINAL_TARGET = 7
MERGE_TARGET = FINAL_TARGET//2


def split_region(region):

    x, y, width, height = region

    if width >= height:

        cut = random.randint(
            width // 3,
            2 * width // 3
        )

        left = (x, y, cut, height)

        right = (
            x + cut,
            y,
            width - cut,
            height
        )

        return [left, right]

    else:

        cut = random.randint(
            height // 3,
            2 * height // 3
        )

        bottom = (
            x,
            y,
            width,
            cut
        )

        top = (
            x,
            y + cut,
            width,
            height - cut
        )

        return [bottom, top]


def center(region):

    x, y, width, height = region

    return (
        x + width / 2,
        y + height / 2
    )


def area(region):

    width = region[2]
    height = region[3]

    return width * height


def can_merge(a, b):

    ax, ay, aw, ah = a
    bx, by, bw, bh = b

    # Side by side
    if ah == bh:

        if ax + aw == bx or bx + bw == ax:
            return True

    # One above the other
    if aw == bw:

        if ay + ah == by or by + bh == ay:
            return True

    return False


def merge(a, b):

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

    width = right - x
    height = top - y

    return (
        x,
        y,
        width,
        height
    )


def choose_split_region(regions):

    average_x = sum(
        center(region)[0]
        for region in regions
    ) / len(regions)

    average_y = sum(
        center(region)[1]
        for region in regions
    ) / len(regions)

    scores = []

    for region in regions:

        x, y = center(region)

        size_score = area(region)

        spread_score = (
            (x - average_x) ** 2
            +
            (y - average_y) ** 2
        ) ** 0.5

        score = (
            size_score
            +
            spread_score * 2
        )

        scores.append(score)

    return random.choices(
        regions,
        weights=scores,
        k=1
    )[0]


# ============================================================
# START
# ============================================================

regions = [
    (0, 0, WIDTH, HEIGHT)
]


print()
print("======================================")
print("       BSP PROCEDURAL GENERATOR")
print("======================================")
print()

print("Map size:", WIDTH, "x", HEIGHT)
print("Seed:", 42)

print()
print("Generation plan:")
print("1. Split to 32 regions")
print("2. Merge to 25 regions")
print("3. Split to 50 regions")

print()
print("Starting with 1 region...")


# ============================================================
# PHASE 1
# 1 -> 32
# ============================================================

print()
print("======================================")
print("PHASE 1: SPLITTING")
print("======================================")

while len(regions) < FIRST_TARGET:

    region = choose_split_region(regions)

    regions.remove(region)

    new_regions = split_region(region)

    regions.extend(new_regions)

    print(
        "Split:",
        len(regions) - 1,
        "->",
        len(regions)
    )


print()
print("Phase 1 complete.")
print("Regions:", len(regions))


# ============================================================
# PHASE 2
# 32 -> 25
# ============================================================

print()
print("======================================")
print("PHASE 2: MERGING")
print("======================================")

while len(regions) > MERGE_TARGET:

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

        print(
            "No more compatible regions to merge."
        )

        break

    i, j = random.choice(
        possible_pairs
    )

    region_a = regions[i]
    region_b = regions[j]

    merged_region = merge(
        region_a,
        region_b
    )

    regions.pop(j)
    regions.pop(i)

    regions.append(
        merged_region
    )

    print(
        "Merged:",
        len(regions) + 1,
        "->",
        len(regions)
    )


print()
print("Phase 2 complete.")
print("Regions:", len(regions))


# ============================================================
# PHASE 3
# 25 -> 50
# ============================================================

print()
print("======================================")
print("PHASE 3: FINAL SPLITTING")
print("======================================")

while len(regions) < FINAL_TARGET:

    region = choose_split_region(regions)

    regions.remove(region)

    new_regions = split_region(
        region
    )

    regions.extend(
        new_regions
    )

    print(
        "Split:",
        len(regions) - 1,
        "->",
        len(regions)
    )


print()
print("======================================")
print("GENERATION COMPLETE")
print("======================================")

print(
    "Final number of regions:",
    len(regions)
)

print()
print("Opening final visualization...")


# ============================================================
# MATPLOTLIB VISUALIZATION
# ============================================================

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
    f"Generated {FINAL_TARGET} rooms"
)

plt.xlabel("x")
plt.ylabel("y")

plt.grid()

plt.show()