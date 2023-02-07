import mouse, time
import tkinter
import static
import keyboard
import os
tk = tkinter.Tk()
width, height = tk.winfo_screenwidth(), tk.winfo_screenheight()
tk.destroy()
step = """
{{
    "INSTRUCTION_TYPE": "PLACE_TOWER",
    "ARGUMENTS": {{
        "MONKEY": "{0}",
        "LOCATION": [
            {1},
            {2}
        ]
    }}
}}
        """
def find_tower(letter):
    for tower in static.tower_keybinds:
        if static.tower_keybinds[tower] == letter:
            return tower
    return None # Not Possible

while True:
    for tower in static.tower_keybinds:
        print(static.tower_keybinds[tower].upper() + ". " +tower )

    print("Press the key of the tower you want the coords for or press O to quit")
    while True:
        if keyboard.read_key().lower() in static.tower_keybinds.values():
            letter = keyboard.read_key().lower()
            break
        elif keyboard.read_key().lower() == 'o':
            exit()
    tower = find_tower(letter)
    if tower:
        print("Press P to get the coords")
        while True:
            if keyboard.is_pressed('p'):
                os.system('cls')
                x, y = mouse.get_position()
                w_norm, h_norm = x / width, y / height
                print("Step:")
                print(step.format(tower, w_norm, h_norm))
                print("Press O to quit or P to continue")
                while True:
                    if keyboard.read_key().lower() == 'o':
                        exit()
                    elif keyboard.read_key().lower() == 'p':
                        os.system('cls')
                        break
                break
