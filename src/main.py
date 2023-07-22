import time
import sys
import argparse
from pathlib import Path
from Bot import Bot
from threading import Thread
from Failsafe import FailSafe
import mouse
import simulatedinput
import monitor
from logger import logger as log
import os
import win32gui
import subprocess
from winreg import *
import re
import json

def main(arg_parser):


    def no_gameplan_exception():
        raise Exception("No valid argument for directory.. 'python main.py --gameplan_path <directory to gameplan>'")

    args = vars(arg_parser.parse_args())

    # Retrives the gameplan from the command line and makes a Path object out of it
    gameplan_path = (Path(__file__).parent.parent.resolve() / Path(args["path"]) )
    print(gameplan_path, Path(__file__).parent.parent.resolve())
    # Verify directory exist.
    if not gameplan_path.exists():
        print("No directory found at: " + str(gameplan_path))
        no_gameplan_exception()
    # Verify that it is a directory
    if not gameplan_path.is_dir():
        print("Not a directory")
        no_gameplan_exception()
    
    bot = Bot(instruction_path=Path(args["path"]), 
            debug_mode=(args['debug']), 
            restart_mode=(args['restart']),
            sandbox_mode=(args['sandbox']),
        )
    os.system('cls' if os.name == 'nt' else 'clear')
    print("""
.______   .___________. _______    __                              
|   _  \  |           ||       \  / /                              
|  |_)  | `---|  |----`|  .--.  |/ /_                              
|   _  <      |  |     |  |  |  | '_ \                             
|  |_)  |     |  |     |  '--'  | (_) |                            
|______/      |__|     |_______/ \___/                             
 _______    ___      .______      .___  ___.  _______ .______      
|   ____|  /   \     |   _  \     |   \/   | |   ____||   _  \     
|  |__    /  ^  \    |  |_)  |    |  \  /  | |  |__   |  |_)  |    
|   __|  /  /_\  \   |      /     |  |\/|  | |   __|  |      /     
|  |    /  _____  \  |  |\  \----.|  |  |  | |  |____ |  |\  \----.
|__|   /__/     \__\ | _| `._____||__|  |__| |_______|| _| `._____|
Join the discord: https://discord.gg/qyKT6bzqZQ                    
""")
    print("Setting up Bot...")
    print("Using gameplan located in: " + str(gameplan_path))
    print("="*25)
    print("Hero:", bot.settings["HERO"].replace("_", " ").title())
    print("Map:", bot.settings["MAP"].replace("_", " ").title())
    print("Difficulty:", bot.settings["DIFFICULTY"].replace("_", " ").title())
    print("Gamemode:", bot.settings["GAMEMODE"].replace("_", " ").title())
    print("="*25)

    print("Finding game process.")

    # set mouse starting position to the bottom right corner
    simulatedinput.move_mouse((monitor.width,monitor.height))

    game_not_found = True
    hwnd = win32gui.FindWindow(None, 'BloonsTD6')

    # game process not found
    if not hwnd:
        print("Game process not found.")

        # check if game is installed on Steam (can also be used to check if game is a legit copy or cracked)
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
                    pass
            CloseKey(key)
        except WindowsError:
            pass
        CloseKey(reg)

        # if game is not installed on Steam check Epic Games
        if not game_on_Steam:
            reg = ConnectRegistry(None,HKEY_LOCAL_MACHINE)
            found_EpicGamesLauncher = False
            game_on_EpicGames = False
            try:
                key = OpenKey(reg, r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher")
                if key:
                    try:
                        isInstalled = QueryValueEx(key, "AppDataPath")[0]
                        if isInstalled:
                            found_EpicGamesLauncher = True
                    except WindowsError:
                        pass
                CloseKey(key)
            except WindowsError:
                pass
            CloseKey(reg)

            if found_EpicGamesLauncher:
                path = re.search(r".+Epic\\", isInstalled).group(0) + "UnrealEngineLauncher\LauncherInstalled.dat"
                try:
                    with open(path) as f:
                        data = json.load(f)
                    for x in data["InstallationList"]:
                        if x["NamespaceId"] == "6a8dfa6e441e4f2f9048a98776c6077d":
                            game_on_EpicGames = True
                            print("Detected Epic Games installation.")
                except:
                    # game is not installed on epic games
                    pass

        if game_on_Steam:
            # Steam
            print("Starting the game through Steam. Please wait...")
            subprocess.run("start steam://run/960090", shell=True, check=True)
        elif game_on_EpicGames:
            # Epic Games
            print("Starting the game through Epic Games. Please wait...")
            subprocess.run("start com.epicgames.launcher://apps/6a8dfa6e441e4f2f9048a98776c6077d%3A49c4bf5c6fd24259b87d0bcc96b6009f%3A7786b355a13b47a6b3915335117cd0b2?action=launch", shell=True, check=True)
        else:
            print("Please start the game manually.")

    while game_not_found:
        time.sleep(0.2)
        # game process found, focus its window
        hwnd = win32gui.FindWindow(None, 'BloonsTD6')
        if hwnd:
            game_not_found = False
            win32gui.SetForegroundWindow(hwnd)
            print("Game found. Switching to game window.")

    # Wait for btd6 home screen or startup screen
    waiting_for_home = False

    log.info("Waiting for home screen..")
    while waiting_for_home is False:
        time.sleep(0.2) # add a short timeout to avoid spamming the cpu
        waiting_for_startup, waiting_for_home = bot.checkFor(["startup","home_menu"], return_raw=True)
        if waiting_for_startup:
            log.info("Startup screen detected")
            simulatedinput.click("STARTUP")
    log.info("Home screen detected")
    
    print("Starting bot..\nIf you want to stop the bot, move your mouse to the upper left corner of your screen or press ctrl+c in the terminal")
    
    bot.initilize() # Initialize the bot (presses alt, etc)
    
    if bot.checkFor("english") is False:
        log.info("Setting game to english")
        simulatedinput.click("SETTINGS")
        simulatedinput.click("LANGUAGE")
        simulatedinput.click("ENGLISH")
        simulatedinput.send_key("esc", timeout=0.5, amount=2)

    # Check for obyn
    bot.hero_select()

    if bot.RESTART:
        log.info("Selecting map")
        bot.select_map()

    # Make sure we haven't exited by using the stop key.
    while bot.running:
        bot.check_for_collection_crates()

        if not bot.RESTART:
            log.info("Selecting map")
            
            # Choose map
            bot.select_map()   
        log.info("Game start")
        

        # main game loop
        bot.loop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A bot that plays the game bloons td 6')

    parser.add_argument('-p', '--path', '--gameplan_path', type=str, help='Path to the gameplan directory', required=True)
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-r', '--restart', action='store_true', help='automatically restarts the game when finished, instead of going to home screen \(games don\'t count towards event progression if you don\'t go back to home)')
    parser.add_argument('-s', '--sandbox', action='store_true', help='Try put gameplan in sandbox mode without waiting for specific rounds')
    
    # Start the bot on a seperate thread
    bot_thread = Thread(target=main, args=(parser,), daemon=True)
    bot_thread.start()

    # Failsafe option, move mouse to upper left corner (0,0) to instantly kill the bot
    try:
        while mouse.get_position() != (0,0) and bot_thread.is_alive():
            time.sleep(0.1)
        
        if mouse.get_position() == (0, 0):
            raise FailSafe()

    except FailSafe as exeption_message:
        print(exeption_message)
        sys.exit(1)
    