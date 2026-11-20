import matplotlib.pyplot as plt

x = 10
y = 30
width = 50
height = 20

print("Area:", width * height)

plt.gca().add_patch(
    plt.Rectangle((x, y), width, height, fill=False)
)

plt.xlim(0, 100)
plt.ylim(0, 100)
plt.grid()
plt.show()