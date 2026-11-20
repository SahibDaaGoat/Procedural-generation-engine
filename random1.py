import random
import matplotlib.pyplot as plt

x = []
y = []

for i in range(30):
    x.append(random.randint(0, 100))
    y.append(random.randint(0, 100))

plt.scatter(x, y)
plt.xlim(0, 100)
plt.ylim(0, 100)
plt.title("Random Points")
plt.show()