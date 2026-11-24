"""BSP partition creation and region merging."""

from bsp_generation.geometry import area, split_region


def largest_power_of_two(number):
    power = 1
    while power * 2 <= number:
        power *= 2
    return power


def choose_region(regions, rng):
    splittable = [region for region in regions if region[2] > 1 or region[3] > 1]
    return rng.choices(splittable, weights=[area(region) for region in splittable], k=1)[0]


def generate_power_regions(width, height, target, rng):
    regions = [(0, 0, width, height)]
    while len(regions) < target:
        region = choose_region(regions, rng)
        regions.remove(region)
        regions.extend(split_region(region, rng))
    return regions


def can_merge(first, second):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    side_by_side = ay == by and ah == bh and (ax + aw == bx or bx + bw == ax)
    stacked = ax == bx and aw == bw and (ay + ah == by or by + bh == ay)
    return side_by_side or stacked


def merge_regions(first, second):
    ax, ay, aw, ah = first
    bx, by, bw, bh = second
    x = min(ax, bx)
    y = min(ay, by)
    right = max(ax + aw, bx + bw)
    top = max(ay + ah, by + bh)
    return x, y, right - x, top - y


def merge_to_target(regions, target, rng):
    while len(regions) > target:
        possible_pairs = [
            (i, j)
            for i in range(len(regions))
            for j in range(i + 1, len(regions))
            if can_merge(regions[i], regions[j])
        ]
        if not possible_pairs:
            return None

        i, j = rng.choice(possible_pairs)
        merged = merge_regions(regions[i], regions[j])
        regions.pop(j)
        regions.pop(i)
        regions.append(merged)

    return regions
