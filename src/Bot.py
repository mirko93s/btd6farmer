import time
import static
import json
import copy
import re
import time
import concurrent.futures
from pathlib import Path

# Local imports
import recognition
import simulatedinput
import monitor
import gameplan
from winreg import *

# Definently fix this 
class Bot():
    def __init__(self):
        self.game_plan = gameplan.get()        
        self.running = True
        self.fast_forward = True

    def loop(self):
        
        rounds = list(self.game_plan.keys())
        r = 1
        current_round = 6
        ability_one_timer = time.time()
        ability_two_timer = time.time()
        
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
                
                win_or_lose = True if did_win else False # is this correct logic?

                self.exit_level(won=win_or_lose)

                finished = True
                self.game_plan = gameplan.get()
                break
            
            # check for next round using images
            if self.checkFor("rounds/" + str(rounds[r]), confidence=0.99):
                current_round = int(rounds[r])
                if r < len(rounds)-1:
                    r+=1

            if current_round != None:
                # Saftey net; use abilites
                cooldowns = static.obyn["COOLDOWNS"]

                if current_round >= 7 and self.abilityAvaliabe(ability_one_timer, cooldowns[0]):
                    simulatedinput.send_key("1")
                    ability_one_timer = time.time()
                
                if current_round >= 31 and self.abilityAvaliabe(ability_two_timer, cooldowns[1]):
                    simulatedinput.send_key("2")
                    ability_two_timer = time.time()

                # Is this necessary?
                # Check for round in game plan
                if current_round in self.game_plan:
                    for x, instruction in enumerate(self.game_plan[current_round]):
                        if instruction:
                            self.execute_instruction(instruction)
                            self.game_plan[current_round][x] = None

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

    def execute_instruction(self, instruction):
        """Handles instructions from the gameplan"""

        instruction = instruction.split()
        instruction_type = instruction[0]

        if instruction_type == "PLACE":
            tower = instruction[1]
            position = float(instruction[2]), float(instruction[3])

            keybind = static.tower_keybinds[tower]

            self.place_tower(position, keybind)
            
        elif instruction_type == "SELL":
            self.remove_tower(instruction[1], instruction[2])
        
        # Upgrade tower
        elif instruction_type == "UPGRADE":
            position = float(instruction[1]), float(instruction[2])

            upgrade_path = list(map(int, [*instruction[3]]))

            self.upgrade_tower(position, upgrade_path)
        
        # Change tower target
        elif instruction_type == "TARGET":
            target_type = instruction[4]
            position = position = float(instruction[1]), float(instruction[2])
            target = instruction[3].split("-")

            if len(instruction) > 5:
                delay = int(instruction[5])
                self.change_target(target_type, position, target, delay)
            else:
                self.change_target(target_type, position, target)
            

        # Set static target of a tower
        elif instruction_type == "STATIC_TARGET":
            position = float(instruction[1]), float(instruction[2])
            target_position = float(instruction[3]), float(instruction[4])

            self.set_static_target(position, target_position)
        
        # Start game
        elif instruction_type == "START":
            if len(instruction) > 1:
                self.fast_forward = True if instruction[1] == "FAST" else False
                
            self.start_first_round()

        # Wait a given time
        elif instruction_type == "WAIT":
            time.sleep(int(instruction[1]))
        
        else:
            # Maybe raise exception or just ignore?
            raise Exception("Instruction type {} is not a valid type".format(instruction_type))

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

    def check_for_collection_crates(self):
        # Can this be done better?
        if self.checkFor("diamond_case"):
            #c lick collect button
            simulatedinput.click("EVENT_COLLECTION", timeout=1.5)
            # collect instas
            simulatedinput.click("LEFT_INSTA", amount=2, timeout=1.5)
            simulatedinput.click("RIGHT_INSTA", amount=2, timeout=1.5)
            simulatedinput.click("F_LEFT_INSTA", amount=2, timeout=1.5)
            simulatedinput.click("MID_INSTA", amount=2, timeout=1.5)
            simulatedinput.click("F_RIGHT_INSTA", amount=2, timeout=1.5)
            # click continue and exit to main menu
            time.sleep(1)
            simulatedinput.click("EVENT_CONTINUE",timeout=1)
            simulatedinput.send_key("esc")
            
    # select hero if not selected
    def hero_select(self):
        hero_variants = [f"OBYN_{i}" for i in range(1, 4)]

        if not self.checkFor(hero_variants):
            simulatedinput.click("HERO_SELECT")
            simulatedinput.click(static.obyn["POSITION"], move_timeout=0.2)
            simulatedinput.click("CONFIRM_HERO")
            simulatedinput.send_key("esc")

    def exit_level(self, won=True):
        if won:
            simulatedinput.click("VICTORY_CONTINUE")
            time.sleep(2)
            simulatedinput.click("VICTORY_HOME")
        else: # lost
            simulatedinput.click("DEFEAT_HOME_NO_CONTINUE")
            time.sleep(2)
        
        self.wait_for_loading() # wait for loading screen

    def select_map(self):
        
        time.sleep(1)

        simulatedinput.click("HOME_MENU_START")
        # reset map page
        simulatedinput.click("EXPERT_SELECTION", timeout=0.25)
        simulatedinput.click("BEGINNER_SELECTION")

        # loop expert map pages until we find dark castle and click it
        self.findDarkCastle()

        simulatedinput.click("HARD_MODE")
        simulatedinput.click("CHIMPS_MODE")

        simulatedinput.click("OVERWRITE_SAVE")

        self.wait_for_loading() # wait for loading screen
        # Only need to press confirm button if we play chimps or impoppable
        time.sleep(1)
        simulatedinput.send_key("esc", timeout=1)

    def findDarkCastle(self):
        mapFound = False
        while not mapFound:
            simulatedinput.click("EXPERT_SELECTION", timeout=0.25)
            mapFound = self.checkFor("dark_castle", return_cords=True, center_on_found=True)
        x, y = mapFound
        simulatedinput.click((x/monitor.width, y/monitor.height))

    def wait_for_loading(self):
        still_loading = True

        while still_loading:
            
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            still_loading = self.checkFor("loading_screen")

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
        
    def findStore(self):
        # check if game is installed on Steam
        reg = ConnectRegistry(None,HKEY_CURRENT_USER)
        game_on_Steam = False
        try:
            key = OpenKey(reg, r"SOFTWARE\Valve\Steam\Apps\960090")
            if key:
                try:
                    isInstalled = QueryValueEx(key, "Installed")[0]
                    # Other useful values are "Running" and "Updating"
                    if isInstalled == 1:
                        game_on_Steam = True
                        print("Detected Steam installation.")
                except WindowsError:
                    # game is not installed but in the Steam library ???
                    pass
            CloseKey(key)
        except WindowsError:
            # game is not installed on Steam
            pass
        CloseKey(reg)

        # if game is not installed on Steam check Epic Games
        reg = ConnectRegistry(None,HKEY_LOCAL_MACHINE)
        game_on_EpicGames = False
        try:
            key = OpenKey(reg, r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher")
            if key:
                try:
                    epicgamesLauncherPath = QueryValueEx(key, "AppDataPath")[0]
                    if epicgamesLauncherPath:
                        path = re.search(r".+Epic\\", epicgamesLauncherPath).group(0) + "UnrealEngineLauncher\LauncherInstalled.dat"
                        try:
                            with open(path) as f:
                                data = json.load(f)
                            for x in data["InstallationList"]:
                                if x["NamespaceId"] == "6a8dfa6e441e4f2f9048a98776c6077d":
                                    game_on_EpicGames = True
                                    print("Detected Epic Games installation.")
                        except:
                            # game is not installed on Epic Games
                            pass
                except WindowsError:
                    # couldn't find Epic Games launcher path
                    pass
            CloseKey(key)
        except WindowsError:
            # Epic Games launcher is not installed
            pass
        CloseKey(reg)
        
        return(game_on_Steam,game_on_EpicGames)

if __name__ == "__main__":
    import time
    time.sleep(2)
    bot = Bot()
