import merge
import tkinter as tk


def generate_map():
    width = int(width_entry.get())
    height = int(height_entry.get())
    seed = int(seed_entry.get())
    rooms = int(rooms_entry.get())
    start_room = int(start_entry.get())
    target_room = int(target_entry.get())

    print("Width:", width)
    print("Height:", height)
    print("Seed:", seed)
    print("Rooms:", rooms)

    merge.generate(
        seed,
        width,
        height,
        rooms,
        start_room,
        target_room
    )


window = tk.Tk()

window.title("Map Generator")
window.geometry("550x500")


tk.Label(window, text="Width").pack()
width_entry = tk.Entry(window)
width_entry.pack()


tk.Label(window, text="Height").pack()
height_entry = tk.Entry(window)
height_entry.pack()


tk.Label(window, text="Seed").pack()
seed_entry = tk.Entry(window)
seed_entry.pack()


tk.Label(window, text="Number of Rooms").pack()
rooms_entry = tk.Entry(window)
rooms_entry.pack()

tk.Label(window, text="Starting Room - ").pack()
start_entry = tk.Entry(window)
start_entry.pack()

tk.Label(window, text="Ending Room - ").pack()
target_entry = tk.Entry(window)
target_entry.pack()


generate_button = tk.Button(
    window,
    text="Generate Map",
    command=generate_map
)

generate_button.pack(pady=20)


window.mainloop()