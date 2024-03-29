import time
import static
import json
import re
import time
import concurrent.futures
from pathlib import Path

# Local imports
import recognition
import simulatedinput
import gameplan
from winreg import *

# Definently fix this 
class Bot():
    def __init__(self):
        self.game_plan = gameplan.get()
        self.running = True

    def loop(self):
        
        # TODO do we want to check for round 6 also???
        # if so r should be 0, current_round anything < 6 (ideally None or -1)
        rounds = list(self.game_plan.keys())
        r = 1
        current_round = 6
        ability_one_timer = time.time()
        ability_two_timer = time.time()

        # main ingame loop
        while True:
            # Check for levelup or insta monkey (level 100)
            if self.checkFor(["levelup", "instamonkey"]):
                simulatedinput.click(amount=3)
            elif self.checkFor("monkey_knowledge"):
                simulatedinput.click()

            # Check for finished game
            win, lose = self.checkFor(["victory", "defeat"], return_raw=True)
            if win or lose:
                self.exit_level(won=win)
                self.game_plan = gameplan.get()
                break
            
            # check for next round using images
            if self.checkFor(str(rounds[r]), confidence=0.95):
                current_round = int(rounds[r])
                if r < len(rounds)-1:
                    r+=1

            if current_round != None:
                # TODO we shouldn't spam abilities. We should use ability on demand using a gameplan instruction
                cooldowns = [35, 90]

                if current_round >= 7 and self.abilityAvaliabe(ability_one_timer, cooldowns[0]):
                    simulatedinput.send_key("1")
                    ability_one_timer = time.time()
                
                if current_round >= 31 and self.abilityAvaliabe(ability_two_timer, cooldowns[1]):
                    simulatedinput.send_key("2")
                    ability_two_timer = time.time()

                # Check for round in game plan and execute instructions
                if current_round in self.game_plan:
                    for instruction in self.game_plan[current_round]:
                        self.execute_instruction(instruction)
                    self.game_plan.pop(current_round)

    def place_tower(self, tower_position, keybind):
        simulatedinput.send_key(keybind) # press keybind
        simulatedinput.click(tower_position) # click on decired location


    def upgrade_tower(self, tower_position, upgrade_path):
 
        top, middle, bottom = upgrade_path
        simulatedinput.click(tower_position)
        
        if top:
            simulatedinput.send_key("top", amount=top)
        if middle:
            simulatedinput.send_key("middle", amount=middle)
        if bottom:
            simulatedinput.send_key("bottom", amount=bottom)
        
        simulatedinput.send_key("esc")

    # TODO this needs a way to remember the old target, we can't always assume it's 0/FIRST
    def change_target(self, tower_type, tower_position, targets: list[str] | str, delay: int | float | list | tuple = 3):
        if not isinstance(targets, (tuple, list)):
            targets = [targets]

        if isinstance(targets, (list, tuple)) and isinstance(delay, (tuple, list)):
            # check if delay and targets are the same length
            if len(targets) != len(delay):
                raise Exception("Number of targets and number of delays needs to be the same")

        simulatedinput.click(tower_position)

        if "SPIKE" in tower_type:
            target_order = [ "NORMAL", "CLOSE", "FAR", "SMART" ]
        else:
            target_order = [ "FIRST", "LAST", "CLOSE", "STRONG" ]

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

    # TODO: this doesn't work, many towers have different ways to set static targets
    # examples: ace "centered path" button, wizrd "aim" button, mortar "set target" button, etc.......
    # we don't really need it for dark castle atm...
    def set_static_target(self, tower_position, target_pos):
        pass

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
            
        # TODO change this together with set_static_target() function
        # Set static target of a tower
        elif instruction_type == "STATIC_TARGET":
            position = float(instruction[1]), float(instruction[2])
            target_position = float(instruction[3]), float(instruction[4])

            self.set_static_target(position, target_position)
        
        # Start game
        elif instruction_type == "START":
            self.start_first_round()

        # Wait a given time
        elif instruction_type == "WAIT":
            time.sleep(int(instruction[1]))

    def abilityAvaliabe(self, last_used, cooldown):
        return (time.time() - last_used) >= (cooldown / 3) # fast-forward is x3

    def start_first_round(self):
        simulatedinput.send_key("space", amount=2)

    def check_for_collection_crates(self):
        # TODO: this whole function can be optimized
        # first check every matched template and save their coords
        # then redeem them one by one
        # so we don't loop over and over again unnecessarily checking many templates (in the for loop)

        # double check for home or event screen as a way to wait for the loading screen to go away after a game ended
        found = False
        while not found:
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            found = self.checkFor(["event_collect","home_menu"], confidence=0.85)
        # sleep here because when you end a game and go back to home the main menu is briefly displayed before the game forces you to the event screen
        time.sleep(1)

        # wait for either the event screen or the main menu to be sure we don't skip this function while loading
        home = event = False
        while not home:
            time.sleep(0.2) # add a short timeout to avoid spamming the cpu
            event, home = self.checkFor(["event_collect","home_menu"], return_raw=True, confidence=0.85)
            # if we find the event screen (aka event collect button) redeem the crates
            if event:
                # click collect button
                self.findClick("event_collect")
                _continue = False
                # loop until the continue button appears on the bottom, so we know we are done redeeming insta monkeys
                while not _continue:
                    # loop
                    for tier in ["common", "uncommon", "rare", "epic", "legendary"]:
                        found = self.checkFor(f"event_insta_{tier}", return_cords=True, center_on_found=True, confidence=0.85)
                        if found:
                            simulatedinput.click(found, ui=True, amount=2, timeout=1)
                            # we break if we find an insta so we can loop again all tiers, there may be duplicate tiers (up to 3)
                            break
                    # check if the continue button appeared if so we can try to exit to main menu
                    _continue = self.checkFor("event_continue", return_cords=True, center_on_found=True, confidence=0.85)
                # click continue to go back to the event screen and press esc to go back to the main menu
                simulatedinput.click(_continue, ui=True, timeout=1)
                simulatedinput.send_key("esc", timeout=1)
                # after pressing esc if we didn't exit to main menu it means we have other crates to redeem so we run the main while loop again
            
    # select hero if not selected
    def hero_select(self):
        hero_variants = ["OBYN_1", "OBYN_2", "OBYN_3"]
        if not self.checkFor(hero_variants):
            self.findClick("heroes")
            hero_variants = ["heroes_obyn_1", "heroes_obyn_2", "heroes_obyn_3"]
            found = False
            while not found:
                time.sleep(0.2)
                found = self.checkFor(hero_variants, return_raw=True)
            self.findClick("heroes_obyn_"+str(list.index(found, True)+1))
            self.findClick("select")
            simulatedinput.send_key("esc")

    def exit_level(self, won=True):
        if won:
            self.findClick("next")
        self.findClick("home")

    def select_map(self):
        self.findClick("play")
        # loop expert map pages until we find dark castle and click it
        self.findDarkCastle()
        # select gamemode
        self.findClick("hard")
        self.findClick("chimps")
        # checks for overwrite save game
        self.findClickTimed("ok")
        # confirm chimps
        self.findClick("ok")

    def findDarkCastle(self):
        mapFound = False
        while not mapFound:
            self.findClick("expert")
            mapFound = self.checkFor("dark_castle", return_cords=True, center_on_found=True)
        simulatedinput.click(mapFound, ui=True)

    def findClickTimed(self, image, confidence = 0.9, timeout = 1):
        """Generic function to check for an image on screen and click it, with a timeout"""
        found = False
        _time = time.time() + timeout
        while not found:
            if time.time() > _time:
                break
            time.sleep(0.2) # avoid spamming the cpu
            found = self.checkFor(image, confidence, return_cords = True, center_on_found = True)
        if found: 
            simulatedinput.click(found, ui=True)

    # TODO clean this?!
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

    def findClick(self, image, confidence = 0.85):
        """Generic function to check for an image on screen and click it"""
        found = False
        while not found:
            time.sleep(0.2) # avoid spamming the cpu
            found = self.checkFor(image, confidence, return_cords = True, center_on_found = True)
        simulatedinput.click(found, ui=True)
        
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
