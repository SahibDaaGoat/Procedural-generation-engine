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


regions = split(0, 0, 100, 70,5)

for x, y, width, height in regions:

    rectangle = plt.Rectangle(
        (x, y),
        width,
        height,
        fill=False
    )

    plt.gca().add_patch(rectangle)

plt.xlim(0, 100)
plt.ylim(0, 70)
plt.gca().set_aspect("equal")

plt.title("Recursive Spatial Partitioning")
plt.grid()

plt.show()