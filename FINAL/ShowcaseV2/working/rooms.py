"""Conversion from BSP regions to inset room rectangles."""

import random


def shrink_room(region, rng=random, required_points=()):
    x, y, width, height = region
    max_margin_x = max(0, min(width // 3, (width - 1) // 2))
    max_margin_y = max(0, min(height // 3, (height - 1) // 2))

    # Keep required map features inside the inset room.
    if required_points:
        safe_x = min(
            int(min(point_x - x, x + width - point_x))
            for point_x, _ in required_points
        )
        safe_y = min(
            int(min(point_y - y, y + height - point_y))
            for _, point_y in required_points
        )
        max_margin_x = min(max_margin_x, safe_x)
        max_margin_y = min(max_margin_y, safe_y)

    min_margin_x = min(width // 20, max_margin_x)
    min_margin_y = min(height // 20, max_margin_y)
    margin_x = rng.randint(min_margin_x, max_margin_x) if max_margin_x else 0
    margin_y = rng.randint(min_margin_y, max_margin_y) if max_margin_y else 0
    # Preserve free space along cell boundaries, including one-unit cells.
    # Legacy callers can still pin a point to a room boundary.
    if not required_points:
        margin_x = max(margin_x, width * 0.035)
        margin_y = max(margin_y, height * 0.035)
    return x + margin_x, y + margin_y, width - 2 * margin_x, height - 2 * margin_y
