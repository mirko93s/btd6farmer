import time
import static
import json
import copy
from pathlib import Path

import time
import static
from pathlib import Path

import re
import mss

# 
import cv2
import time


import sys
# Local imports
import ocr
import recognition
import simulatedinput
import monitor
import gameplan
from logger import logger as log

# Definently fix this 
class Bot():
    def __init__(self, 
        instruction_path, 
        debug_mode=False, 
        verbose_mode=False, 
        restart_mode=False, 
        sandbox_mode=False,
        game_plan_filename="instructions.json",
        game_settings_filename="setup.json"
    ):
        is_url_regex = re.compile(r"https?://(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
        if (re.search(is_url_regex, str(instruction_path))):
            self.settings = gameplan.load_from_url(instruction_path)
            self.game_plan = gameplan.load_from_url(instruction_path)
        else:
            self.settings = gameplan.load_from_file(instruction_path / game_settings_filename)
            self.game_plan = gameplan.load_from_file(instruction_path / game_plan_filename)

        # Something to do with how python handles copying objects
        self._game_plan_copy = copy.deepcopy(self.game_plan)
        self._game_plan_version = self.settings.pop("VERSION")
        ####

        self.round_area = None
        
        self.DEBUG = debug_mode
        self.VERBOSE = verbose_mode
        self.RESTART = restart_mode
        self.SANDBOX = sandbox_mode

        if self.SANDBOX and self.RESTART:
            raise Exception("Sandbox mode and restart mode cannot be used at the same time")
        
        self.start_time = time.time()
        self.game_start_time = time.time()
        
        self.running = True
        self.fast_forward = True

        self.statDict = {
            "Current_Round": None,
            "Last_Upgraded": None,
            "Last_Target_Change": None,
            "Last_Placement": None,
            "Uptime": 0
        }

        self.support_dir = self.get_resource_dir("assets")

        # Defing a lamda function that can be used to get a path to a specific image
        # In essence this is dumb
        self.image_path = lambda image, root_dir=self.support_dir : root_dir/f"{image}.png"


    def handle_time(self, ttime):
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
                    log.error("invalid stats file while logging stats")
        # Catch if the file does not exist
        except IOError:
            log.error("stats file does not exist")


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
        average_converted, unit = self.handle_time(data["average_matchtime_seconds"])
        
        # Push average to dictionary
        data["average_matchtime"] = f"{round(average_converted, 3)} {unit}"


        # Open as write
        with open("stats.json", "w") as outfile:        
            outfile.write(json.dumps(data, indent=4)) # write stats to file
        
        return data

    def reset_game_plan(self):
        self.game_plan = copy.deepcopy(self._game_plan_copy)


    def initilize(self):
        if self.DEBUG:
            log.debug("RUNNING IN DEBUG MODE, DEBUG FILES WILL BE GENERATED")
        simulatedinput.send_key("alt")


    def loop(self):

        current_round = -1
        ability_one_timer = time.time()
        ability_two_timer = time.time()
        ability_three_timer = time.time()
        
        finished = False

        middle_of_screen = (0.5, 0.5)

        if self.SANDBOX:
            print("Sandbox mode started")
            for instructionGroup in self.game_plan.keys():
                for instruction in self.game_plan.get(instructionGroup):
                    if self._game_plan_version == "1":
                        # print(instruction)
                        self.v1_handleInstruction(instruction)
                        
                    else:
                        raise Exception("Game plan version {} not supported".format(self._game_plan_version))
            
            print("Sandbox mode finished")
            
            self.running = False
            return

        # main ingame loop
        while not finished:
            # Check for levelup or insta monkey (level 100)
            if self.levelup_check() or self.insta_monkey_check():
                simulatedinput.click(middle_of_screen, amount=3)
            elif self.monkey_knowledge_check():
                simulatedinput.click(middle_of_screen, amount=1)

            # Check for finished or failed game
            if self.defeat_check():
                
                log.info("Defeat detected on round {}; exiting level".format(current_round))
                self.log_stats(did_win=False, match_time=(time.time()-self.game_start_time))

                if self.RESTART:
                    self.restart_level(won=False)
                else:
                    self.exit_level(won=False)
                finished = True
                self.reset_game_plan()
                continue

            elif self.victory_check():

                log.info("Victory detected; exiting level")

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
                        simulatedinput.send_key("1")
                        ability_one_timer = time.time()
                    
                    # skip if ezili or adora, their lvl 7 ability is useless
                    if current_round >= 31 and self.abilityAvaliabe(ability_two_timer, cooldowns[1]) and (self.settings["HERO"] != "EZILI" and "ADORA"):
                        simulatedinput.send_key("2")
                        ability_two_timer = time.time()
                    
                    if len(cooldowns) == 3:
                        if current_round >= 53 and self.abilityAvaliabe(ability_three_timer, cooldowns[2]):
                            simulatedinput.send_key("3")
                            ability_three_timer = time.time()

                # Is this necessary?
                # Check for round in game plan
                if str(current_round) in self.game_plan:
                    
                    # Handle all instructions in current round
                    for instruction in self.game_plan[str(current_round)]:
                        if not "DONE" in instruction:

                            if self._game_plan_version == "1":
                                # print(instruction)
                                self.v1_handleInstruction(instruction)
                                
                            else:
                                raise Exception("Game plan version {} not supported".format(self._game_plan_version))

                            instruction["DONE"] = True

                            log.debug(f"Current round {current_round}") # Only print current round once

    def exit_bot(self): 
        self.running = False

    def place_tower(self, tower_position, keybind):
        simulatedinput.send_key(keybind) # press keybind
        simulatedinput.click(tower_position) # click on decired location


    def upgrade_tower(self, tower_position, upgrade_path):
        if not any(isinstance(path, int) for path in upgrade_path) or len(upgrade_path) != 3:
            raise Exception("Upgrade path must be a list of integers", upgrade_path)

        simulatedinput.click(tower_position)

        # Convert upgrade_path to something usable
        top, middle, bottom = upgrade_path
        
        for _ in range(top):
            simulatedinput.send_key("top")

        for _ in range(middle):
            simulatedinput.send_key("middle")

        for _ in range(bottom):
            simulatedinput.send_key("bottom")
        
        simulatedinput.send_key("esc")

    def change_target(self, tower_type, tower_position, targets: str | list, delay: int | float | list | tuple = 3):
        if not isinstance(targets, (tuple, list)):
            targets = [targets]

        if isinstance(targets, (list, tuple)) and isinstance(delay, (tuple, list)):
            # check if delay and targets are the same length
            if len(targets) != len(delay):
                raise Exception("Number of targets and number of delays needs to be the same")

        simulatedinput.click(tower_position)

        if "SPIKE" in tower_type:
            target_order = static.target_order_spike
        else:
            target_order = static.target_order_regular

        current_target_index = 0

        # for each target in target list
        for i in targets:

            while current_target_index != target_order.index(i):
                simulatedinput.send_key("tab")
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
            

        simulatedinput.send_key("esc")

    def set_static_target(self, tower_position, target_pos):
        simulatedinput.click(tower_position)
        
        simulatedinput.send_key("tab")

        simulatedinput.click(target_pos)

        simulatedinput.send_key("esc")

    def remove_tower(self, position):
        simulatedinput.click(position)
        simulatedinput.send_key("backspace")
        simulatedinput.send_key("esc")

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

            log.debug(f"Tower placed: {tower}")
            
        elif instruction_type == "REMOVE_TOWER":
            self.remove_tower(instruction["ARGUMENTS"]["LOCATION"])
            log.debug(f"Tower removed on: {instruction['ARGUMENTS']['LOCATION']}")
        
        # Upgrade tower
        elif instruction_type == "UPGRADE_TOWER":
            position = instruction["ARGUMENTS"]["LOCATION"]
            upgrade_path = instruction["ARGUMENTS"]["UPGRADE_PATH"]

            self.upgrade_tower(position, upgrade_path)

            log.debug(f"Tower upgraded at position: {instruction['ARGUMENTS']['LOCATION']} with the upgrade path {instruction['ARGUMENTS']['UPGRADE_PATH']}")
        
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

            log.debug("First Round Started")

        # Wait a given time
        elif instruction_type == "WAIT":
            time.sleep(instruction["ARGUMENTS"]["TIME"])

            log.debug(f"Waiting for {instruction['ARGUMENTS']['TIME']} second(s)")
        
        else:
            # Maybe raise exception or just ignore?
            raise Exception("Instruction type {} is not a valid type".format(instruction_type))

        log.debug(f"executed instruction:\n{instruction}")


    def abilityAvaliabe(self, last_used, cooldown):
        # TODO: Store if the game is speeded up or not. If it is use the constant (true by default)
        m = 1

        if self.fast_forward:
            m = 3

        return (time.time() - last_used) >= (cooldown / m)

    def start_first_round(self):
        if self.fast_forward:
            simulatedinput.send_key("space", amount=2)
        else:
            simulatedinput.send_key("space", amount=1)

        self.game_start_time = time.time()

    def check_for_collection_crates(self):
        # Can this be done better?
        if self.collection_event_check():
            log.debug("easter collection detected")

            simulatedinput.click("EASTER_COLLECTION") #DUE TO EASTER EVENT:
            time.sleep(1)
            simulatedinput.click("LEFT_INSTA") # unlock insta
            time.sleep(1)
            simulatedinput.click("LEFT_INSTA") # collect insta
            time.sleep(1)
            simulatedinput.click("RIGHT_INSTA") # unlock r insta
            time.sleep(1)
            simulatedinput.click("RIGHT_INSTA") # collect r insta
            time.sleep(1)
            simulatedinput.click("F_LEFT_INSTA")
            time.sleep(1)
            simulatedinput.click("F_LEFT_INSTA")
            time.sleep(1)
            simulatedinput.click("MID_INSTA") # unlock insta
            time.sleep(1)
            simulatedinput.click("MID_INSTA") # collect insta
            time.sleep(1)
            simulatedinput.click("F_RIGHT_INSTA")
            time.sleep(1)
            simulatedinput.click("F_RIGHT_INSTA")
            time.sleep(1)

            time.sleep(1)
            simulatedinput.click("EASTER_CONTINUE")

            simulatedinput.send_key("esc")
            
    # select hero if not selected
    def hero_select(self):
        if not self.hero_check(self.settings["HERO"]):
            log.debug(f"Selecting {self.settings['HERO']}")

            simulatedinput.click("HERO_SELECT")
            simulatedinput.click(static.hero_positions[self.settings["HERO"]], move_timeout=0.2)
            simulatedinput.click("CONFIRM_HERO")
            simulatedinput.send_key("esc")

    def exit_level(self, won=True):
        if won:
            simulatedinput.click("VICTORY_CONTINUE")
            time.sleep(2)
            simulatedinput.click("VICTORY_HOME")
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE":
            simulatedinput.click("DEFEAT_HOME_CHIMPS")
            time.sleep(2)
        else:
            simulatedinput.click("DEFEAT_HOME")
            time.sleep(2)
        
        self.wait_for_loading() # wait for loading screen
    
    def restart_level(self, won=True):
        if won:
            simulatedinput.click("VICTORY_CONTINUE")
            time.sleep(2)
            simulatedinput.click("FREEPLAY")
            simulatedinput.click("OK_MIDDLE")
            time.sleep(1)
            simulatedinput.send_key("esc")
            time.sleep(1)
            simulatedinput.click("RESTART_WIN")
            simulatedinput.click("RESTART_CONFIRM")
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE":
            simulatedinput.click("RESTART_DEFEAT_CHIMPS")
            simulatedinput.click("RESTART_CONFIRM")
            time.sleep(2)
        else:
            simulatedinput.click("RESTART_DEFEAT")
            simulatedinput.click("RESTART_CONFIRM")
            time.sleep(2)
        
        self.wait_for_loading() # wait for loading screen

    def select_map(self):
        map_page = static.maps[self.settings["MAP"]][0]
        map_index = static.maps[self.settings["MAP"]][1]
        
        time.sleep(1)

        simulatedinput.click("HOME_MENU_START")
        simulatedinput.click("EXPERT_SELECTION")
        
        simulatedinput.click("BEGINNER_SELECTION") # goto first page

        # click to the right page
        simulatedinput.click("RIGHT_ARROW_SELECTION", amount=(map_page - 1), timeout=0.1)

        simulatedinput.click("MAP_INDEX_" + str(map_index)) # Click correct map

        if self.SANDBOX:
            simulatedinput.click("EASY_MODE") # Select Difficulty
            simulatedinput.click("SANDBOX_EASY") # Select Gamemode
        else:
            simulatedinput.click(self.settings["DIFFICULTY"]) # Select Difficulty
            simulatedinput.click(self.settings["GAMEMODE"]) # Select Gamemode

            simulatedinput.click("OVERWRITE_SAVE")

        self.wait_for_loading() # wait for loading screen
        # Only need to press confirm button if we play chimps or impoppable
        confirm_list = ["CHIMPS_MODE", "IMPOPPABLE", "DEFLATION", "APOPALYPSE", "HALF_CASH", ]
        if self.settings["GAMEMODE"] in confirm_list or self.SANDBOX:
            simulatedinput.send_key("esc", timeout=2)

    
    def wait_for_loading(self):
        still_loading = True

        log.debug("Waiting for loading screen..")
        while still_loading:
            
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            still_loading = self.loading_screen_check()

        log.debug("Out of loading screen, continuing..")
        

    def get_resource_dir(self, path):
        return Path(__file__).resolve().parent/path

    def getRoundArea(self):
        # Init round area dict with width and height of the round area
        round_area = {
            "width": 200,
            "height": 42
        }

        area = self.locate_round_area() # Search for round text, returns (1484,13) on 1080p
        log.debug("this should be only printed once, getting round area")
        log.debug(f"Round area found at {area}, applying offsetts")
        
        if area:
            log.info("Found round area!")

            # set round area to the found area + offset
            x, y, roundwidth, roundheight = area
            
            # Fiddled offset, do not tuch
            # Offset from ROUND text to round number
            xOffset = roundwidth + 10
            yOffset = int(roundheight * 3) - 40

            round_area["top"] = y + yOffset
            round_area["left"] = x - xOffset

            return round_area

        # If it cant find anything
        log.warning("Could not find round area, setting default values")
        default_round_area_scaled = monitor.scaling([0.7083333333333333, 0.0277777777777778]) # Use default values, (1360,30) on 1080p

        # left = x, top = y
        round_area["left"] = default_round_area_scaled[0]
        round_area["top"] = default_round_area_scaled[1]
        return round_area
    

    def getRound(self):


        # If round area is not located yet
        if self.round_area is None:
            self.round_area = self.getRoundArea()
        
        # Setting up screen capture area
        # The screen part to capture
        screenshot_dimensions = {
            'top': self.round_area["top"], 
            'left': self.round_area["left"], 
            'width': self.round_area["width"], 
            'height': self.round_area["height"] + 50
        }

        # Take Screenshot
        with mss.mss() as screenshotter:
            screenshot = screenshotter.grab(screenshot_dimensions)
            found_text, _ocrImage = ocr.getTextFromImage(screenshot)
            
            if self.DEBUG:
                def get_valid_filename(s):
                    s = str(s).strip().replace(' ', '_')
                    return re.sub(r'(?u)[^-\w.]', '', s)
                cv2.imwrite(f"./DEBUG/OCR_DONE_FOUND_{get_valid_filename(found_text)}_{str(time.time())}.png", _ocrImage, [cv2.IMWRITE_PNG_COMPRESSION, 0])

            # Get only the first number/group so we don't need to replace anything in the string
            if re.search(r"(\d+/\d+)", found_text):
                found_text = re.search(r"(\d+)", found_text)
                return int(found_text.group(0))
            else:
                # If the found text does not match the regex requirements, Debug and save image
                log.warning("Found text '{}' does not match regex requirements".format(found_text))
                
                try:
                    file_path =  Path(__file__).resolve().parent.parent/ "DEBUG"
                    if not file_path.exists():
                        Path.mkdir(file_path)

                    with open(file_path/f"GETROUND_IMAGE_{str(time.time())}.png", "wb") as output_file:
                        output_file.write(mss.tools.to_png(screenshot.rgb, screenshot.size))
                    
                    log.warning("Saved screenshot of what was found")

                except Exception as e:
                    log.error(e)
                    log.warning("Could not save screenshot of what was found")

                return None
    
    # Different methods for different checks all wraps over _find()
    # Can this be done better?
    def menu_check(self):
        return recognition.find( self.image_path("menu"))

    def insta_monkey_check(self):
        return recognition.find( self.image_path("instamonkey"))

    def monkey_knowledge_check(self):
        return recognition.find( self.image_path("monkey_knowledge"))

    def victory_check(self):
        return recognition.find( self.image_path("victory"))

    def defeat_check(self):
        return recognition.find( self.image_path("defeat"))

    def levelup_check(self):
        return recognition.find( self.image_path("levelup"))

    def hero_check(self, heroString):
        return recognition.find( self.image_path(heroString)) or \
                recognition.find( self.image_path(f"{heroString}_2" ) ) or \
                recognition.find( self.image_path(f"{heroString}_3" ) )

    def loading_screen_check(self):
        return recognition.find( self.image_path("loading_screen"))

    def home_menu_check(self):
        return recognition.find( self.image_path("play"))

    def language_check(self):
        return recognition.find( self.image_path("english"))

    def collection_event_check(self):
        return recognition.find(self.image_path("diamond_case"))

    def locate_round_area(self):
        return recognition.find(self.image_path("round"), return_cords=True, center_on_found=False)


if __name__ == "__main__":
    import time
    time.sleep(2)
    bot = Bot(instruction_path="")
    print(bot.getRound())
