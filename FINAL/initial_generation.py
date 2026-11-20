import random
import matplotlib.pyplot as plt

random.seed(4285865)

def split(x, y, width, height, depth):

    if depth == 0:
        return [(x, y, width, height)]

    if width > height:
        cut = random.randint(width // 3, 2 * width // 3)

        left = (x, y, cut, height)
        right = (x + cut, y, width - cut, height)

        return split(*left, depth - 1) + split(*right, depth - 1)

    else:
        cut = random.randint(height // 3, 2 * height // 3)

        bottom = (x, y, width, cut)
        top = (x, y + cut, width, height - cut)

        return split(*bottom, depth - 1) + split(*top, depth - 1)

def shrink_room(x, y, width, height):
    max_margin_x = min(width // 4, (width - 1) // 2)
    max_margin_y = min(height // 4, (height - 1) // 2)

    left = random.randint(0, max_margin_x)
    right = random.randint(0, max_margin_x)
    bottom = random.randint(0, max_margin_y)
    top = random.randint(0, max_margin_y)

    room_x = x + left
    room_y = y + bottom
    room_width = width - left - right
    room_height = height - bottom - top

    return room_x, room_y, room_width, room_height

def BSPshrink(x1,y1,width1,height1,depth1):
    regions = split(x1,y1,width1,height1,depth1)

    for x, y, width, height in regions:
        room_x, room_y, room_width, room_height = shrink_room(x,y,width, height)
        rectangle = plt.Rectangle(
            (room_x, room_y),
            room_width,
            room_height,
            fill=False
        )

        plt.gca().add_patch(rectangle)

    plt.xlim(0, width1)
    plt.ylim(0, height1)
    plt.gca().set_aspect("equal")

    plt.title(f"Binary Space Partitioning - depth {depth1}")
    plt.grid()

    plt.show()

def BSPnoshrink(x1, y1, width1, height1, depth1):
    regions = split(x1, y1, width1, height1, depth1)

    # Store the generated BSP partitions
    global current_regions
    current_regions = regions

    fig, ax = plt.subplots()

    for x, y, width, height in regions:
        rectangle = plt.Rectangle(
            (x, y),
            width,
            height,
            fill=False,
            edgecolor="black"
        )
        ax.add_patch(rectangle)

    ax.set_xlim(x1, x1 + width1)
    ax.set_ylim(y1, y1 + height1)
    ax.set_aspect("equal")
    ax.set_title(f"BSP Partitions - Depth {depth1}")
    ax.grid()

    plt.show()


def BSPshrink():
    # Ensure partitions have already been generated
    if not current_regions:
        print("Generate BSP partitions first!")
        return

    fig, ax = plt.subplots()

    for x, y, width, height in current_regions:
        room_x, room_y, room_width, room_height = shrink_room(
            x, y, width, height
        )

        rectangle = plt.Rectangle(
            (room_x, room_y),
            room_width,
            room_height,
            fill=False,
            edgecolor="blue"
        )
        ax.add_patch(rectangle)

    # Recover the overall map boundaries
    min_x = min(x for x, y, w, h in current_regions)
    min_y = min(y for x, y, w, h in current_regions)
    max_x = max(x + w for x, y, w, h in current_regions)
    max_y = max(y + h for x, y, w, h in current_regions)

    ax.set_xlim(min_x, max_x)
    ax.set_ylim(min_y, max_y)
    ax.set_aspect("equal")
    ax.set_title("BSP Partitions Converted to Rooms")
    ax.grid()

    plt.show()


current_regions = []

