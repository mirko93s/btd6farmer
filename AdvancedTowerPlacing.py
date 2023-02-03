import mouse
import tkinter
import static
import keyboard
import os
import logging
import json
from BotUtils import BotUtils

if not os.path.isdir("DEBUG"):
    os.mkdir("DEBUG")

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename='DEBUG/ATP_log.txt', filemode='a+')

tk = tkinter.Tk()
width, height = tk.winfo_screenwidth(), tk.winfo_screenheight()
tk.destroy()

inst = BotUtils()
inst.log = logging.debug
inst.DEBUG = True

result = {}
last_round = "1"

def find_tower(letter):
    for tower in static.tower_keybinds:
        if static.tower_keybinds[tower] == letter:
            return tower
    return None

def add_tower_step(step_args, round):
    global result, last_round
    step = {}
    step["INSTRUCTION_TYPE"] = "PLACE_TOWER"
    step["ARGUMENTS"] = {}
    step["ARGUMENTS"]["MONKEY"] = step_args[0]
    step["ARGUMENTS"]["LOCATION"] = [step_args[1], step_args[2]]

    if round is None:
        round = last_round
    else:
        last_round = round = str(round)
        
    if round in result:
        result[round].append(step)
    else:
        result[round] = [step]
    

while True:
    os.system('cls') # if os.name == 'nt' else 'clear' -- Add this if you want to clear the console on linux
    for tower in static.tower_keybinds:
        print(static.tower_keybinds[tower].upper() + ". " +tower)

    print("Press the key of the tower you want the coords for or press O to quit")
    while True:
        if keyboard.read_key().lower() in static.tower_keybinds.values():
            letter = keyboard.read_key().lower()
            break
        elif keyboard.read_key().lower() == 'o':
            with open('DEBUG/ATP_result.json', 'w') as f:
                json.dump(result, f, indent=3)
            exit()

    tower = find_tower(letter)
    if tower:
        print("Click on the map where you want to place the tower, or esc to cancel")
        while True:
            if mouse.is_pressed(button='left'):
                round = inst.getRound()
                x, y = mouse.get_position()
                w_norm, h_norm = x / width, y / height
                add_tower_step((tower, w_norm, h_norm), round)
                break
            elif keyboard.is_pressed("esc"):
                break