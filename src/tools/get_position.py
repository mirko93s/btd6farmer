"""
    Cordinates with this bot are normalized to work on all resolutions.
"""

import mouse, time
import tkinter

tk = tkinter.Tk()
width, height = tk.winfo_screenwidth(), tk.winfo_screenheight()
while True:
    
    x, y = mouse.get_position()
    w_norm, h_norm = x / width, y / height
    print(f"x: {w_norm} y: {h_norm}")
    time.sleep(0.1)

