"""Small geometry helpers used by the map generator."""


def split_region(region, rng):
    """Split a region along its longer side using the existing BSP rule."""
    x, y, width, height = region

    if width >= height:
        minimum = max(1, width // 3)
        maximum = min(width - 1, (2 * width) // 3)
        cut = rng.randint(minimum, maximum)
        return [(x, y, cut, height), (x + cut, y, width - cut, height)]

    minimum = max(1, height // 3)
    maximum = min(height - 1, (2 * height) // 3)
    cut = rng.randint(minimum, maximum)
    return [(x, y, width, cut), (x, y + cut, width, height - cut)]


def center(region):
    x, y, width, height = region
    return x + width / 2, y + height / 2


def area(region):
    return region[2] * region[3]
