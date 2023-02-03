import time
import static
import json
import copy
from pathlib import Path

import sys
import time
import static
import tkinter
from pathlib import Path

import numpy as np
import pytesseract
import processing

if sys.platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import re
import mss

import ctypes
from collections import defaultdict

# Definently fix this 
class Bot():
    def __init__(self, instruction_path, debug_mode=False, verbose_mode=False, restart_mode=False):
        # wtf fix this
        instruction_path=Path.cwd()/"Instructions"/"Dark_Castle_Hard_Standard"
        game_plan_filename="instructions.json"
        game_settings_filename="setup.json"
        self.settings = self._load_json(instruction_path / game_settings_filename)
        self.game_plan = self._load_json(instruction_path / game_plan_filename)
        ####
        
        self._game_plan_copy = copy.deepcopy(self.game_plan)

        self._game_plan_version = self.settings.pop("VERSION")
        
        self.start_time = time.time()
        self.running = True
        self.DEBUG = debug_mode
        self.VERBOSE = verbose_mode
        self.RESTART = restart_mode
        self.game_start_time = time.time()
        self.fast_forward = True

        self.statDict = {
            "Current_Round": None,
            "Last_Upgraded": None,
            "Last_Target_Change": None,
            "Last_Placement": None,
            "Uptime": 0
        }

        try:
            if sys.platform == "win32":
                ctypes.windll.shcore.SetProcessDpiAwareness(2) # DPI indipendent
            tk = tkinter.Tk()
            self.width, self.height = tk.winfo_screenwidth(), tk.winfo_screenheight()
        except Exception as e:
            raise Exception("Could not retrieve monitor resolution")

        self.support_dir = self.get_resource_dir("assets")

        # Defing a lamda function that can be used to get a path to a specific image
        # self._image_path = lambda image, root_dir=self.support_dir, height=self.height : root_dir/f"{height}_{image}.png"
        # In essence this is dumb
        self._image_path = lambda image, root_dir=self.support_dir : root_dir/f"{image}.png"


        # Resolutions for for padding
        self.reso_16 = [
            { "width": 1280, "height": 720  },
            { "width": 1920, "height": 1080 },
            { "width": 2560, "height": 1440 },
            { "width": 3840, "height": 2160 }
        ]
        self.round_area = None


    def _handle_time(self, ttime):
        """
            Converts seconds to appropriate unit
        """
        if ttime >= 60: # Minutes
            return (ttime / 60, "min")
        elif (ttime / 60) >= 60: # Hours
            return (ttime / 3600, "hrs")
        elif (ttime / 3600) >= 24: # days
            return (ttime / 86400, "d")
        elif (ttime / 86400) >= 7: # Weeks
            return (ttime / 604800, "w")
        else: # No sane person will run this bokk for a week
            return (ttime, "s")

    # Put this somewhere else
    def log_stats(self, did_win: bool = None, match_time: int | float = 0):
        # Standard dict which will be used if json loads nothing
        data = {
            "wins": 0, 
            "loses": 0, 
            "winrate": "0%", 
            "average_matchtime": "0 s", 
            "total_time": 0, 
            "average_matchtime_seconds": 0
        }
        
        # Try to read the file
        try:
            with open("stats.json", "r") as infile:
                try:
                    # Read json file
                    str_file = "".join(infile.readlines())
                    data = json.loads(str_file)
                # Catch if file format is invalid for json (eg empty file)
                except json.decoder.JSONDecodeError:
                    print("invalid stats file")
        # Catch if the file does not exist
        except IOError:
            print("file does not exist")


        if did_win:
            data["wins"] += 1
        else:
            data["loses"] += 1
        
        total_matches = (data["wins"] + data["loses"])
        # winrate = total wins / total matches
        winrate = data["wins"] / total_matches

        # Convert to procent
        procentage = round(winrate * 100, 4)
        
        # Push procentage to winrate
        data["winrate"] = f"{procentage}%"

        data["average_matchtime_seconds"] = (data["total_time"]  + match_time) / total_matches
        
        # new_total_time = old_total_time + current_match_time in seconds
        data["total_time"] += match_time
        
        # average = total_time / total_matches_played
        average_converted, unit = self._handle_time(data["average_matchtime_seconds"])
        
        # Push average to dictionary
        data["average_matchtime"] = f"{round(average_converted, 3)} {unit}"


        # Open as write
        with open("stats.json", "w") as outfile:        
            outfile.write(json.dumps(data, indent=4)) # write stats to file
        
        return data

    def log(self, *kargs):
        print(*kargs)

    def _load_json(self, path):
        """
            Will read the @path as a json file load into a dictionary.
        """
        data = {}
        with path.open('r', encoding="utf-8") as f:
            data = json.load(f)
        return data
    
    def reset_game_plan(self):
        self.game_plan = copy.deepcopy(self._game_plan_copy)


    def initilize(self):
        if self.DEBUG:
            self.log("RUNNING IN DEBUG MODE, DEBUG FILES WILL BE GENERATED")

        self.press_key("alt")


    def loop(self):

        current_round = -1
        ability_one_timer = time.time()
        ability_two_timer = time.time()
        ability_three_timer = time.time()
        
        finished = False

        middle_of_screen = (0.5, 0.5)

        # main ingame loop
        while not finished:

            # Check for levelup or insta monkey (level 100)
            if self.levelup_check() or self.insta_monkey_check():
                self.click(middle_of_screen, amount=3)
            elif self.monkey_knowledge_check():
                self.click(middle_of_screen, amount=1)

            # Check for finished or failed game
            if self.defeat_check():
                
                if self.DEBUG:
                    print("Defeat detected on round {}; exiting level".format(current_round))
                    self.log_stats(did_win=False, match_time=(time.time()-self.game_start_time))
                if self.RESTART:
                    self.restart_level(won=False)
                else:
                    self.exit_level(won=False)
                finished = True
                self.reset_game_plan()
                continue

            elif self.victory_check():

                if self.DEBUG:
                    print("Victory detected; exiting level") 
                    self.log_stats(did_win=True, match_time=(time.time()-self.game_start_time))
                if self.RESTART:
                    self.restart_level(won=True)
                else:
                    self.exit_level(won=True)
                finished = True
                self.reset_game_plan()
                continue
            
            current_round = self.getRound()

            if current_round != None:
                # Saftey net; use abilites
                # TODO: Calculate round dynamically, base on which round hero has been placed.
                if self.settings["HERO"] != "GERALDO": # geraldo doesn't any ability
                    cooldowns = static.hero_cooldowns[self.settings["HERO"]]

                    if current_round >= 7 and self.abilityAvaliabe(ability_one_timer, cooldowns[0]):
                        self.press_key("1")
                        ability_one_timer = time.time()
                    
                    # skip if ezili or adora, their lvl 7 ability is useless
                    if current_round >= 31 and self.abilityAvaliabe(ability_two_timer, cooldowns[1]) and (self.settings["HERO"] != "EZILI" and "ADORA"):
                        self.press_key("2")
                        ability_two_timer = time.time()
                    
                    if len(cooldowns) == 3:
                        if current_round >= 53 and self.abilityAvaliabe(ability_three_timer, cooldowns[2]):
                            self.press_key("3")
                            ability_three_timer = time.time()

                # Check for round in game plan
                if str(current_round) in self.game_plan:
                    
                    # Handle all instructions in current round
                    for instruction in self.game_plan[str(current_round)]:
                        if not "DONE" in instruction:

                            if self._game_plan_version == "1":
                                print(instruction)
                                self.v1_handleInstruction(instruction)
                                
                            else:
                                raise Exception("Game plan version {} not supported".format(self._game_plan_version))

                            instruction["DONE"] = True

                            if self.DEBUG:
                                self.log("Current round", current_round) # Only print current round once

    def exit_bot(self): 
        self.running = False

    def place_tower(self, tower_position, keybind):
        self.press_key(keybind) # press keybind
        self.click(tower_position) # click on decired location


    def upgrade_tower(self, tower_position, upgrade_path):
        if not any(isinstance(path, int) for path in upgrade_path) or len(upgrade_path) != 3:
            raise Exception("Upgrade path must be a list of integers", upgrade_path)

        self.click(tower_position)

        # Convert upgrade_path to something usable
        top, middle, bottom = upgrade_path
        
        for _ in range(top):
            self.press_key(static.upgrade_keybinds["top"])

        for _ in range(middle):
            self.press_key(static.upgrade_keybinds["middle"])

        for _ in range(bottom):
            self.press_key(static.upgrade_keybinds["bottom"])
        
        self.press_key("esc")

    def change_target(self, tower_type, tower_position, targets: str | list, delay: int | float | list | tuple = 3):
        if not isinstance(targets, (tuple, list)):
            targets = [targets]

        if isinstance(targets, (list, tuple)) and isinstance(delay, (tuple, list)):
            # check if delay and targets are the same length
            if len(targets) != len(delay):
                raise Exception("Number of targets and number of delays needs to be the same")

        self.click(tower_position)

        if "SPIKE" in tower_type:
            target_order = static.target_order_spike
        else:
            target_order = static.target_order_regular

        current_target_index = 0

        # for each target in target list
        for i in targets:

            while current_target_index != target_order.index(i):
                self.press_key("tab")
                current_target_index+=1
                if current_target_index > 3:
                    current_target_index = 0

            # If delay is an int sleep for delay for each target
            if isinstance(delay, (int, float)):
                # If the bot is on the last target  in targets list, dont sleep
                if targets[-1] != i: # 
                    time.sleep(delay)   
            # If delay is a list sleep for respective delay for each target
            elif isinstance(delay, (list, tuple)):
                time.sleep(delay.pop(-1))
            

        self.press_key("esc")

    def set_static_target(self, tower_position, target_pos):
        self.click(tower_position)
        
        target_button = self.locate_static_target_button()
        self.click(target_button)

        self.click(target_pos)

        self.press_key("esc")

    def remove_tower(self, position):
        self.click(position)
        self.press_key("backspace")
        self.press_key("esc")

    def v1_handleInstruction(self, instruction):
        """
            Handles instructions for version 1 of the game plan 
        """

        instruction_type = instruction["INSTRUCTION_TYPE"]

        if instruction_type == "PLACE_TOWER":
            tower = instruction["ARGUMENTS"]["MONKEY"]
            position = instruction["ARGUMENTS"]["LOCATION"]

            keybind = static.tower_keybinds[tower]

            self.place_tower(position, keybind)

            if self.DEBUG or self.VERBOSE:
                self.log("Tower placed:", tower)
            
        elif instruction_type == "REMOVE_TOWER":
            self.remove_tower(instruction["ARGUMENTS"]["LOCATION"])
            
            if self.DEBUG or self.VERBOSE:
                self.log("Tower removed on:", instruction["ARGUMENTS"]["LOCATION"])
        
        # Upgrade tower
        elif instruction_type == "UPGRADE_TOWER":
            position = instruction["ARGUMENTS"]["LOCATION"]
            upgrade_path = instruction["ARGUMENTS"]["UPGRADE_PATH"]

            self.upgrade_tower(position, upgrade_path)

            if self.DEBUG or self.VERBOSE:
                self.log("Tower upgraded at position:", instruction["ARGUMENTS"]["LOCATION"], "with the upgrade path:", instruction["ARGUMENTS"]["UPGRADE_PATH"])
        
        # Change tower target
        elif instruction_type == "CHANGE_TARGET":
            target_type = instruction["ARGUMENTS"]["TYPE"]
            position = instruction["ARGUMENTS"]["LOCATION"]
            target = instruction["ARGUMENTS"]["TARGET"]

            if "DELAY" in instruction["ARGUMENTS"]:
                delay = instruction["ARGUMENTS"]["DELAY"] 
                self.change_target(target_type, position, target, delay)
            else:
                self.change_target(target_type, position, target)
            

        # Set static target of a tower
        elif instruction_type == "SET_STATIC_TARGET":
            position = instruction["ARGUMENTS"]["LOCATION"]
            target_position = instruction["ARGUMENTS"]["TARGET"]

            self.set_static_target(position, target_position)
        
        # Start game
        elif instruction_type == "START":
            if "ARGUMENTS" in instruction and "FAST_FORWARD " in instruction["ARGUMENTS"]:
                self.fast_forward = instruction["ARGUMENTS"]["FASTFORWARD"]
                
            self.start_first_round()

            if self.DEBUG or self.VERBOSE:
                self.log("First Round Started")

        # Wait a given time
        elif instruction_type == "WAIT":
            time.sleep(instruction["ARGUMENTS"]["TIME"])

            if self.DEBUG or self.VERBOSE:
                self.log("Waiting for ", instruction["ARGUMENTS"]["TIME"], "second(s)")
        
        else:
            # Maybe raise exception or just ignore?
            raise Exception("Instruction type {} is not a valid type".format(instruction_type))

        if self.DEBUG or self.VERBOSE:
            self.log(f"executed instruction:\n{instruction}")


    def abilityAvaliabe(self, last_used, cooldown):
        # TODO: Store if the game is speeded up or not. If it is use the constant (true by default)
        m = 1

        if self.fast_forward:
            m = 3

        return (time.time() - last_used) >= (cooldown / m)

    def start_first_round(self):
        if self.fast_forward:
            self.press_key("space", amount=2)
        else:
            self.press_key("space", amount=1)

        self.game_start_time = time.time()

    def check_for_collection_crates(self):
        if self.collection_event_check():
            if self.DEBUG:
                self.log("easter collection detected")
                # take screenshot of loc and save it to the folder

            self.click("EASTER_COLLECTION") #DUE TO EASTER EVENT:
            time.sleep(1)
            self.click("LEFT_INSTA") # unlock insta
            time.sleep(1)
            self.click("LEFT_INSTA") # collect insta
            time.sleep(1)
            self.click("RIGHT_INSTA") # unlock r insta
            time.sleep(1)
            self.click("RIGHT_INSTA") # collect r insta
            time.sleep(1)
            self.click("F_LEFT_INSTA")
            time.sleep(1)
            self.click("F_LEFT_INSTA")
            time.sleep(1)
            self.click("MID_INSTA") # unlock insta
            time.sleep(1)
            self.click("MID_INSTA") # collect insta
            time.sleep(1)
            self.click("F_RIGHT_INSTA")
            time.sleep(1)
            self.click("F_RIGHT_INSTA")
            time.sleep(1)

            time.sleep(1)
            self.click("EASTER_CONTINUE")

            self.press_key("esc")
            
    # select hero if not selected
    def hero_select(self):
        if not self.hero_check(self.settings["HERO"]):
            self.log(f"Selecting {self.settings['HERO']}")
            self.click("HERO_SELECT")
            self.click(static.hero_positions[self.settings["HERO"]], move_timeout=0.2)
            self.click("CONFIRM_HERO")
            self.press_key("esc")

    def exit_level(self, won=True):
        if won:
            self.click("VICTORY_CONTINUE")
            time.sleep(2)
            self.click("VICTORY_HOME")
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE":
            self.click("DEFEAT_HOME_CHIMPS")
            time.sleep(2)
        else:
            self.click("DEFEAT_HOME")
            time.sleep(2)
        
        self.wait_for_loading() # wait for loading screen
    
    def restart_level(self, won=True):
        if won:
            self.click("VICTORY_CONTINUE")
            time.sleep(2)
            self.click("FREEPLAY")
            self.click("OK_MIDDLE")
            time.sleep(1)
            self.press_key("esc")
            time.sleep(1)
            self.click("RESTART_WIN")
            self.click("RESTART_CONFIRM")
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE":
            self.click("RESTART_DEFEAT_CHIMPS")
            self.click("RESTART_CONFIRM")
            time.sleep(2)
        else:
            self.click("RESTART_DEFEAT")
            self.click("RESTART_CONFIRM")
            time.sleep(2)
        
        self.wait_for_loading() # wait for loading screen

    def select_map(self):
        map_page = static.maps[self.settings["MAP"]][0]
        map_index = static.maps[self.settings["MAP"]][1]
        
        time.sleep(1)

        self.click("HOME_MENU_START")
        self.click("EXPERT_SELECTION")
        
        self.click("BEGINNER_SELECTION") # goto first page

        # click to the right page
        self.click("RIGHT_ARROW_SELECTION", amount=(map_page - 1), timeout=0.1)

        self.click("MAP_INDEX_" + str(map_index)) # Click correct map
        self.click(self.settings["DIFFICULTY"]) # Select Difficulty
        self.click(self.settings["GAMEMODE"]) # Select Gamemode
        self.click("OVERWRITE_SAVE")

        self.wait_for_loading() # wait for loading screen

        # Only need to press confirm button if we play chimps or impoppable
        confirm_list = ["CHIMPS_MODE", "IMPOPPABLE", "DEFLATION", "APOPALYPSE", "HALF_CASH"]
        if self.settings["GAMEMODE"] in confirm_list:
            self.press_key("esc", timeout=1)
            # self.click(self.settings["DIFFICULTY"])
            # self.click("CONFIRM_CHIMPS")
    
    def wait_for_loading(self):
        still_loading = True

        while still_loading:
            if self.DEBUG:
                self.log("Waiting for loading screen..")
            
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            still_loading = self.loading_screen_check()

    def get_resource_dir(self, path):
        return Path(__file__).resolve().parent/path

    def getRound(self):
        # Change to https://stackoverflow.com/questions/66334737/pytesseract-is-very-slow-for-real-time-ocr-any-way-to-optimise-my-code 
        # or https://www.reddit.com/r/learnpython/comments/kt5zzw/how_to_speed_up_pytesseract_ocr_processing/

        # The screen part to capture

        # If round area is not located yet
        if self.round_area is None:
    
            self.round_area = defaultdict()
            self.round_area["width"] = 200
            self.round_area["height"] = 42

            area = self.locate_round_area() # Search for round text, returns (1484,13) on 1080p
            
            # If it cant find anything
            if area == None:
                if self.DEBUG:
                    self.log("Could not find round area, setting default values")
                scaled_values = self._scaling([0.7083333333333333, 0.0277777777777778]) # Use default values, (1360,30) on 1080p

                # left = x
                # top = y
                self.round_area["left"] = scaled_values[0]
                self.round_area["top"] = scaled_values[1]
            else:
                # set round area to the found area + offset
                x, y, roundwidth, roundheight = area
                
                xOffset, yOffset = ((roundwidth + 55), int(roundheight * 2) - 5)
                self.round_area["top"] = y + yOffset
                self.round_area["left"] = x - xOffset
        
        # Setting up screen capture area
        screenshot_dimensions = {
            'top': self.round_area["top"], 
            'left': self.round_area["left"], 
            'width': self.round_area["width"], 
            'height': self.round_area["height"]
        }

        # Take Screenshot
        with mss.mss() as sct:
            sct_image = sct.grab(screenshot_dimensions)

            
            found_text = processing.getTextFromImage(sct_image)

            # Get only the first number/group so we don't need to replace anything in the string
            if re.search(r"(\d+/\d+)", found_text):
                found_text = re.search(r"(\d+)", found_text)
                return int(found_text.group(0))

            else:
                if self.DEBUG:
                    self.log("Found text '{}' does not match regex requirements".format(found_text))
                    self.save_file(data=mss.tools.to_png(sct_image.rgb, sct_image.size), _file_name="get_current_round_failed.png")
                    self.log("Saved screenshot of what was found")

                return None
                    
            


    
    def save_file(self, data=format(0, 'b'), _file_name="noname", folder="DEBUG", ):
        directory = Path(__file__).resolve().parent/folder
        
        if not directory.exists():
            Path.mkdir(directory)

        with open(directory/_file_name, "wb") as output_file:
            output_file.write(data)

    # Different methods for different checks all wraps over _find()
    # Can this be done better?
    def menu_check(self):
        return processing.find( self._image_path("menu"), self.width, self.height )

    def insta_monkey_check(self):
        return processing.find( self._image_path("instamonkey"), self.width, self.height )

    def monkey_knowledge_check(self):
        return processing.find( self._image_path("monkey_knowledge"), self.width, self.height )

    def victory_check(self):
        return processing.find( self._image_path("victory"), self.width, self.height )

    def defeat_check(self):
        return processing.find( self._image_path("defeat"), self.width, self.height )

    def levelup_check(self):
        return processing.find( self._image_path("levelup"), self.width, self.height )

    def hero_check(self, heroString):
        return processing.find( self._image_path(heroString), self.width, self.height ) or \
                processing.find( self._image_path(f"{heroString}_2" , self.width, self.height) ) or \
                processing.find( self._image_path(f"{heroString}_3" , self.width, self.height) )

    def loading_screen_check(self):
        return processing.find( self._image_path("loading_screen"), self.width, self.height )

    def home_menu_check(self):
        return processing.find( self._image_path("play"), self.width, self.height )

    def language_check(self):
        return processing.find( self._image_path("english"), self.width, self.height )

    def collection_event_check(self):
        return processing.find(self._image_path("diamond_case"), self.width, self.height )

    def locate_static_target_button(self):
        return processing.find(self._image_path("set_target_button"), self.width, self.height, return_cords=True)
    
    def locate_round_area(self):
        return processing.find(self._image_path("round_area"), self.width, self.height, return_cords=True, center_on_found=False)


    