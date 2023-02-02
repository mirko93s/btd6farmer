import time
import static
import json
import copy
from pathlib import Path

import sys
import time
import keyboard
import mouse
import static
import tkinter
from pathlib import Path

import numpy as np
import cv2
import pytesseract

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

    def log_stats(self, did_win: bool = None, match_time: int | float = 0):
        # Standard dict which will be used if json loads nothing
        data = {"wins": 0, "loses": 0, "winrate": "0%", "average_matchtime": "0 s", "total_time": 0, "average_matchtime_seconds": 0}
        
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
        if self.settings["GAMEMODE"] == "CHIMPS_MODE" or \
           self.settings["GAMEMODE"] == "IMPOPPABLE"  or \
           self.settings["GAMEMODE"] == "DEFLATION"   or \
           self.settings["GAMEMODE"] == "APOPALYPSE"  or \
           self.settings["GAMEMODE"] == "HALF_CASH":
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
        monitor = {'top': self.round_area["top"], 'left': self.round_area["left"], 'width': self.round_area["width"], 'height': self.round_area["height"]}
        # print("region", monitor)

        # Take Screenshot
        with mss.mss() as sct:
            sct_image = sct.grab(monitor)
            screenshot = np.array(sct_image, dtype=np.uint8)
            # Get local maximum:
            kernelSize = 5
            maxKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernelSize, kernelSize))
            localMax = cv2.morphologyEx(screenshot, cv2.MORPH_CLOSE, maxKernel, None, None, 1, cv2.BORDER_REFLECT101)
            # Perform gain division
            gainDivision = np.where(localMax == 0, 0, (screenshot/localMax))
            # Clip the values to [0,255]
            gainDivision = np.clip((255 * gainDivision), 0, 255)
            # Convert the mat type from float to uint8:
            gainDivision = gainDivision.astype("uint8")
            # Convert RGB to grayscale:
            grayscaleImage = cv2.cvtColor(gainDivision, cv2.COLOR_BGR2GRAY)
            # Resize image to improve the quality
            grayscaleImage = cv2.resize(grayscaleImage,(0,0), fx=3.0, fy=3.0)
            # Get binary image via Otsu:
            _, final_image = cv2.threshold(grayscaleImage, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # Set kernel (structuring element) size:
            kernelSize = 3
            # Set morph operation iterations:
            opIterations = 1
            # Get the structuring element:
            morphKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernelSize, kernelSize))
            # Perform closing:
            final_image = cv2.morphologyEx( final_image, cv2.MORPH_CLOSE, morphKernel, None, None, opIterations, cv2.BORDER_REFLECT101 )
            # Flood fill (white + black):
            cv2.floodFill(final_image, mask=None, seedPoint=(int(0), int(0)), newVal=(255))
            # Invert image so target blobs are colored in white:
            final_image = 255 - final_image
            # Find the blobs on the binary image:
            contours, hierarchy = cv2.findContours(final_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # Process the contours:
            for i, c in enumerate(contours):
                # Get contour hierarchy:
                currentHierarchy = hierarchy[0][i][3]
                # Look only for children contours (the holes):
                if currentHierarchy != -1:
                    # Get the contour bounding rectangle:
                    boundRect = cv2.boundingRect(c)
                    # Get the dimensions of the bounding rect:
                    rectX = boundRect[0]
                    rectY = boundRect[1]
                    rectWidth = boundRect[2]
                    rectHeight = boundRect[3]
                    # Get the center of the contour the will act as
                    # seed point to the Flood-Filling:
                    fx = rectX + 0.5 * rectWidth
                    fy = rectY + 0.5 * rectHeight
                    # Fill the hole:
                    cv2.floodFill(final_image, mask=None, seedPoint=(int(fx), int(fy)), newVal=(0))
            # Write result to disk:
            if self.DEBUG:
                cv2.imwrite("./DEBUG/round.png", final_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

            # Get current round from screenshot with tesseract
            found_text = pytesseract.image_to_string(final_image,  config='--psm 7').replace("\n", "")

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

    def _move_mouse(self, location, move_timeout=0.1):
        mouse.move(x=location[0], y=location[1])
        time.sleep(move_timeout)

    def click(self, location: tuple | tuple, amount=1, timeout=0.5, move_timeout=0.1, press_time=0.075):        
        """
            Method to click on a specific location on the screen
            @param location: The location to click on
            @param amount: amount of clicks to be performed
            @param timeout: time to wait between clicks
            @param move_timeout: time to wait between move and click
            @param press_time: time to wait between press and release
        """

        # If location is a string then assume that its a static button
        if isinstance(location, str):
            location = static.button_positions[location]
        
        # Move mouse to location
        self._move_mouse(self._scaling(location), move_timeout)

        for _ in range(amount):
            mouse.press(button='left')
            time.sleep(press_time) # https://www.reddit.com/r/AskTechnology/comments/4ne2tv/how_long_does_a_mouse_click_last/ TLDR; dont click too fast otherwise shit will break
            mouse.release(button='left')
            
            """
                We don't need to apply cooldown and slow down the bot on single clicks
                So we only apply the .1 delay if the bot has to click on the same spot multiple times
                This is currently used for level selection and levelup screen
            """
            if amount > 1:
                time.sleep(timeout)
        
        time.sleep(timeout)

    def press_key(self, key, timeout=0.1, amount=1):
        for _ in range(amount):
            keyboard.send(key)
            time.sleep(timeout)

    # Different methods for different checks all wraps over _find()
    def menu_check(self):
        return self._find( self._image_path("menu") )

    def insta_monkey_check(self):
        return self._find( self._image_path("instamonkey") )

    def monkey_knowledge_check(self):
        return self._find( self._image_path("monkey_knowledge") )

    def victory_check(self):
        return self._find( self._image_path("victory") )

    def defeat_check(self):
        return self._find( self._image_path("defeat") )

    def levelup_check(self):
        return self._find( self._image_path("levelup") )

    def hero_check(self, heroString):
        return self._find( self._image_path(heroString) ) or \
            self._find( self._image_path(heroString + "_2") ) or \
            self._find( self._image_path(heroString + "_3") )

    def loading_screen_check(self):
        return self._find( self._image_path("loading_screen") )

    def home_menu_check(self):
        return self._find( self._image_path("play") )

    def language_check(self):
        return self._find( self._image_path("english") )

    def collection_event_check(self):
        return self._find(self._image_path("diamond_case") )

    def locate_static_target_button(self):
        return self._find(self._image_path("set_target_button"), return_cords=True)
    
    def locate_round_area(self):
        return self._find(self._image_path("round_area"), return_cords=True, center_on_found=False)

    # Generic function to see if something is present on the screen
    def _find(self, path, confidence=0.9, return_cords=False, center_on_found=True):

        try:
            if return_cords:
                cords = self._locate(path, confidence=confidence)
                if self.DEBUG:
                    self.log(cords)
                if cords is not None:
                    left, top, width, height = cords
                    if center_on_found:
                        return (left + width // 2, top + height // 2) # Return middle of found image   
                    else:
                        return (left, top, width, height)
                else:
                    return None
            return True if self._locate(path, confidence=confidence) is not None else False

        except Exception as e:
            raise Exception(e)

    # Scaling functions for different resolutions support
    def _scaling(self, pos_list):
        """
            This function will dynamically calculate the differance between current resolution and designed for 2560x1440
            it will also add any padding needed to positions to account for 21:9 

            do_padding -- this is used during start 
        """

        reso_21 = False
        for x in self.reso_16: 
            if self.height == x['height']:
                if self.width != x['width']:
                    reso_21 = True
                    x = pos_list[0]
                    break

        if reso_21 != True:
            x = pos_list[0] * self.width
        
        y = pos_list[1] * self.height
        x = x + self._padding() # Add's the pad to to the curent x position variable

        if self.DEBUG:
            self.log("Scaling: {} -> {}".format(pos_list, (int(x), int(y))))

        return (int(x), int(y))
        # return (x,y)


    def _padding(self):
        """
            Get's width and height of current resolution
            we iterate through reso_16 for heights, if current resolution height matches one of the entires 
            then it will calulate the difference of the width's between current resolution and 16:9 (reso_16) resolution
            divides by 2 for each side of padding

            Variables Used
            width -- used to referance current resolution width
            height -- used to referance current resolution height
            pad -- used to output how much padding we expect in different resolutions
            reso_16 -- list that  
        """

        padding = 0
        for x in self.reso_16: 
            if self.height == x['height']:
                padding = (self.width - x['width'])/2

        return padding

    def _load_img(self, img):
        """
        TODO
        """
        # load images if given Path, or convert as needed to opencv
        # Alpha layer just causes failures at this point, so flatten to RGB.
        # RGBA: load with -1 * cv2.CV_LOAD_IMAGE_COLOR to preserve alpha
        # to matchTemplate, need template and image to be the same wrt having alpha
        
        if isinstance(img, Path):
            # The function imread loads an image from the specified file and
            # returns it. If the image cannot be read (because of missing
            # file, improper permissions, unsupported or invalid format),
            # the function returns an empty matrix
            # http://docs.opencv.org/3.0-beta/modules/imgcodecs/doc/reading_and_writing_images.html
            img_cv = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE)
            if img_cv is None:
                raise IOError(f"Failed to read {img} because file is missing, has improper permissions, or is an unsupported or invalid format")
        elif isinstance(img, np.ndarray):
            img_cv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # don't try to convert an already-gray image to gray
            # if grayscale and len(img.shape) == 3:  # and img.shape[2] == 3:
            # else:
            #     img_cv = img
        elif hasattr(img, 'convert'):
            # assume its a PIL.Image, convert to cv format
            img_array = np.array(img.convert('RGB'))
            img_cv = img_array[:, :, ::-1].copy()  # -1 does RGB -> BGR
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        else:
            raise TypeError('expected an image filename, OpenCV numpy array, or PIL image')
        
        return img_cv


    def _locate_all(self, template_path, confidence=0.9, limit=100, region=None):
        """
            Template matching a method to match a template to a screenshot taken with mss.
            
            @template_path - Path to the template image
            @confidence - A threshold value between {> 0.0f & < 1.0f} (Defaults to 0.9f)

            credit: https://github.com/asweigart/pyscreeze/blob/b693ca9b2c964988a7e924a52f73e15db38511a8/pyscreeze/__init__.py#L184

            Returns a list of cordinates to where openCV found matches of the template on the screenshot taken
        """

        monitor = {'top': 0, 'left': 0, 'width': self.width, 'height': self.height} if region is None else region

        if  0.0 > confidence <= 1.0:
            raise ValueError("Confidence must be a value between 0.0 and 1.0")

        with mss.mss() as sct:

            # Load the taken screenshot into a opencv img object
            img = np.array(sct.grab(monitor))
            screenshot = self._load_img(img) 

            if region:
                screenshot = screenshot[region[1]:region[1]+region[3],
                                        region[0]:region[0]+region[2]
                                        ]
            else:
                region = (0, 0)
            # Load the template image
            template = self._load_img(template_path)

            confidence = float(confidence)

            # width & height of the template
            templateHeight, templateWidth = template.shape[:2]

            # scale template
            if self.width != 2560 or self.height != 1440:
                template = cv2.resize(template, dsize=(int(templateWidth/(2560/self.width)), int(templateHeight/(1440/self.height))), interpolation=cv2.INTER_CUBIC)

            # Find all the matches
            # https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image/9253805#9253805
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)    # heatmap of the template and the screenshot"
            match_indices = np.arange(result.size)[(result > confidence).flatten()]
            matches = np.unravel_index(match_indices[:limit], result.shape)
            
            # Defining the coordinates of the matched region
            matchesX = matches[1] * 1 + region[0]
            matchesY = matches[0] * 1 + region[1]

            if len(matches[0]) == 0:
                return None
            else:
                return [ (x, y, templateWidth, templateHeight) for x, y in zip(matchesX, matchesY) ]

    def _locate(self, template_path, confidence=0.9, tries=1):
        """
            Locates a template on the screen.

            Note: @tries does not do anything at the moment
        """
        result = self._locate_all(template_path, confidence)
        return result[0] if result is not None else None


    