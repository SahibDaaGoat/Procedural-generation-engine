import initial_generation
import tkinter as tk


def BSPshrink():
    width = int(width_entry.get())
    height = int(height_entry.get())
    x = int(x_entry.get())
    y = int(y_entry.get())
    depth = int(depth_entry.get())

    initial_generation.BSPshrink(
        
    )

def BSPnoshrink():
    width = int(width_entry.get())
    height = int(height_entry.get())
    x = int(x_entry.get())
    y = int(y_entry.get())
    depth = int(depth_entry.get())

    initial_generation.BSPnoshrink(
        x,y,width, height, depth
    )

window = tk.Tk()

window.title("Binary space partitioning")
window.geometry("550x500")


tk.Label(window, text="X value").pack()
x_entry = tk.Entry(window)
x_entry.pack()

tk.Label(window, text="Y value").pack()
y_entry = tk.Entry(window)
y_entry.pack()

tk.Label(window, text="Width").pack()
width_entry = tk.Entry(window)
width_entry.pack()


tk.Label(window, text="Height").pack()
height_entry = tk.Entry(window)
height_entry.pack()


tk.Label(window, text="Depth").pack()
depth_entry = tk.Entry(window)
depth_entry.pack()

generate_button = tk.Button(
    window,
    text="Generate partitions",
    command=BSPnoshrink
)

generate_button.pack(pady=20)

generate_button_shrink = tk.Button(
    window,
    text="Generate rooms (shrinked partitions)",
    command=BSPshrink
)

generate_button_shrink.pack(pady=10)


window.mainloop()