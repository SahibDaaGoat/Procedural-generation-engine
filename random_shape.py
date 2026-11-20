import random
import matplotlib.pyplot as plt

random.seed(3345312)

for i in range(60):

    width = random.randint(5, 20)
    height = random.randint(5, 15)

    x = random.randint(0, 100 - width)
    y = random.randint(0, 70 - height)

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

plt.title("Random Rectangles")
plt.xlabel("x")
plt.ylabel("y")
plt.grid()

plt.show()