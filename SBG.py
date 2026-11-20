import numpy as np
import matplotlib.pyplot as plt


def generate_points(seed, count):
    rng = np.random.default_rng(seed)
    return rng.uniform(0, 100, size=(count, 2))


seed = 42
count = 60

run_a = generate_points(seed, count)
run_b = generate_points(seed + 1, count)
run_c = generate_points(seed + 2, count)
run_d = generate_points(seed + 1, count)


fig, axes = plt.subplots(1,5, figsize=(12,4))

axes[0].scatter(run_a[:, 0], run_a[:, 1])
axes[0].set_title("Seed 42")

axes[1].scatter(run_b[:, 0], run_b[:, 1])
axes[1].set_title("Seed 43")

axes[2].scatter(run_c[:, 0], run_c[:, 1])
axes[2].set_title("Seed 44")

axes[3].scatter(run_d[:, 0], run_d[:, 1])
axes[3].set_title("""Seed 43 (to show that seed can
 be reused for same map)""")

axes[4].scatter(run_d[:, 0], run_d[:, 1])
axes[4].set_title("""Seed 43 (to show that seed can
 be reused for same map)""")

for ax in axes:
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal")

plt.tight_layout()
plt.show()