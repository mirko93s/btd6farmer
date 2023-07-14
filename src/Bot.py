import time
import static
import json
import copy
import re
import mss
import time
import concurrent.futures
from pathlib import Path

# Local imports
import ocr
import recognition
import simulatedinput
import monitor
import gameplan
from logger import logger as log
import pymem

# Definently fix this 
class Bot():
    def __init__(self, 
        instruction_path, 
        debug_mode=False, 
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
        ####

        self.round_area = None
        
        self.DEBUG = debug_mode
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
        if self.SANDBOX:
            print("Sandbox mode started")
            for instructionGroup in self.game_plan.keys():
                for instruction in self.game_plan.get(instructionGroup):
                    self.execute_instruction(instruction)
            print("Sandbox mode finished")
            
            self.running = False
            return

        current_round = -1
        ability_one_timer = time.time()
        ability_two_timer = time.time()
        ability_three_timer = time.time()
        
        finished = False

        middle_of_screen = (0.5, 0.5)

        # main ingame loop
        while not finished:
            # Check for levelup or insta monkey (level 100)
            if self.checkFor(["levelup", "instamonkey"]):
                simulatedinput.click(middle_of_screen, amount=3)
            elif self.checkFor("monkey_knowledge"):
                simulatedinput.click(middle_of_screen, amount=1)

            # Check for finished or failed game
            did_win, did_fail = self.checkFor(["victory", "defeat"], return_raw=True)
            if did_win or did_fail:
                if did_win:
                    print("We won")
                    log.info("Victory detected; exiting level")
                else:
                    print("We lost")
                    log.info("Defeat detected on round {}; exiting level".format(current_round))
                
                win_or_lose = True if did_win else False # is this correct logic?
                print(win_or_lose)
                self.log_stats(did_win=win_or_lose, match_time=(time.time()-self.game_start_time))

                if self.RESTART:
                    self.restart_level(won=win_or_lose)
                else:
                    self.exit_level(won=win_or_lose)

                finished = True
                self.reset_game_plan()
                break

            current_round = self.getRound()

            if current_round != None:
                # Saftey net; use abilites
                # TODO: Calculate round dynamically, based on which round hero has been placed.
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
                            self.execute_instruction(instruction)
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

    def change_target(self, tower_type, tower_position, targets: list[str] | str, delay: int | float | list | tuple = 3):
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

    def execute_instruction(self, instruction):
        """Handles instructions from the gameplan"""

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
        if self.checkFor("diamond_case"):
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
        hero_vaiants = [f"{self.settings['HERO']}_{i}" for i in range(1, 4)]

        if not self.checkFor(hero_vaiants):
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
        # Some Chimps and Deflation doesn't have continue button
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE" or self.settings["GAMEMODE"] == "DEFLATION":
            simulatedinput.click("DEFEAT_HOME_NO_CONTINUE")
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
            # simulatedinput.click("OK_MIDDLE")
            simulatedinput.send_key("esc")

            time.sleep(2)
            simulatedinput.send_key("esc")
            time.sleep(1)
            simulatedinput.click("RESTART_WIN")
            simulatedinput.click("RESTART_CONFIRM")
        elif self.settings["GAMEMODE"] == "CHIMPS_MODE" or self.settings["GAMEMODE"] == "DEFLATION":
            simulatedinput.click("RESTART_DEFEAT_NO_CONTINUE")
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
        simulatedinput.click("EXPERT_SELECTION", timeout=0.25)
        
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
        time.sleep(1)
        confirm_list = ["CHIMPS_MODE", "IMPOPPABLE", "DEFLATION", "APOPALYPSE", "HALF_CASH", ]
        if self.settings["GAMEMODE"] in confirm_list or self.SANDBOX:
            simulatedinput.send_key("esc", timeout=1)

    
    def wait_for_loading(self):
        still_loading = True

        log.debug("Waiting for loading screen..")
        while still_loading:
            
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            still_loading = self.checkFor("loading_screen")

        log.debug("Out of loading screen, continuing..")
           

    def getRound(self):
        add = 0x03096928
        offsets = [0x40, 0xB8, 0x0, 0xC0, 0x120, 0x20, 0x20]

        pm = pymem.Pymem('BloonsTD6.exe')
        gameModule = pymem.process.module_from_name(pm.process_handle, "GameAssembly.dll").lpBaseOfDll
        address = pm.read_longlong(gameModule+add)

        for offset in offsets:
            try:
                address = pm.read_longlong(address + offset)
            except Exception as e:
                print(e)

        return address + offsets[-1] -32

    def waitForRound(self, round) -> None:
        """Wait for a specific round to start, use this to wait until to execute a gameplan instruction"""
        pass

    def waitFor(self, images: list[str] | str, confidence: float = 0.9, timeout: int = 10) -> None:
        """Wait for a image to appear on screen, generic function for multiple things"""
        pass

    def checkFor(self, 
            images: list[str] | str, 
            confidence: float = 0.9, 
            return_cords: bool = False, 
            center_on_found: bool = True,
            return_raw: bool = False
        ) -> bool:
        """Generic function to check for images on screen"""

        assets_directory = Path(__file__).resolve().parent/"assets"
        image_path = lambda image : assets_directory/f"{image}.png"
        if isinstance(images, list):
            
            output = [None]*len(images)
            
            # Could this be done the find function?
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit the template matching function to the thread pool
                futures= {
                    executor.submit(recognition.find, image_path(image)): idx for idx, image in enumerate(images)
                }
                
                # When all the tasks are done, return the results in the same order as the input
                for future in concurrent.futures.as_completed(futures):
                    output[futures[future]] = future.result()
            
            # Return the raw output if return_raw is true
            if return_raw:
                return output

            # Return true if any of the images are found
            return any(output)
        else:
            return recognition.find(
                image_path(images), 
                confidence, 
                return_cords, 
                center_on_found
            )

if __name__ == "__main__":
    import time
    time.sleep(2)
    bot = Bot(instruction_path="")
    print(bot.getRound())
