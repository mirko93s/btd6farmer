import time
import sys
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

def main():

    def no_gameplan_exception():
        raise Exception("No valid argument for directory.. 'python main.py --gameplan_path <directory to gameplan>'")

    # Retrives the gameplan from the command line and makes a Path object out of it
    gameplan_path = (Path(__file__).parent.parent.resolve() / Path("gameplans/Dark_Castle_Hard_Chimps") )
    print(gameplan_path, Path(__file__).parent.parent.resolve())
    # Verify directory exist.
    if not gameplan_path.exists():
        print("No directory found at: " + str(gameplan_path))
        no_gameplan_exception()
    # Verify that it is a directory
    if not gameplan_path.is_dir():
        print("Not a directory")
        no_gameplan_exception()
    
    bot = Bot(instruction_path=Path("gameplans/Dark_Castle_Hard_Chimps"))
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

    waiting_for_game = True
    hwnd = win32gui.FindWindow(None, 'BloonsTD6') or win32gui.FindWindow(None, 'BloonsTD6-Epic')

    # game is not open
    if not hwnd:
        print("Game process not found. Finding game installations.")

        Steam, EpicGames = bot.findStore()

        if Steam:
            print("Starting the game through Steam. Please wait...")
            subprocess.run("start steam://run/960090", shell=True, check=True)

        elif EpicGames:
            print("Starting the game through Epic Games. Please wait...")
            subprocess.run("start com.epicgames.launcher://apps/6a8dfa6e441e4f2f9048a98776c6077d%3A49c4bf5c6fd24259b87d0bcc96b6009f%3A7786b355a13b47a6b3915335117cd0b2?action=launch", shell=True, check=True)

        else:
            # We can exit the program here if we don't want cracked users to use the bot
            # sys.exit(1)
            print("Please start the game manually.")

    while waiting_for_game:
        time.sleep(0.2)
        hwnd = win32gui.FindWindow(None, 'BloonsTD6') or win32gui.FindWindow(None, 'BloonsTD6-Epic')
        # game process found, focus its window
        if hwnd:
            waiting_for_game = False
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

    # Make sure we haven't exited by using the stop key.
    while bot.running:
        bot.check_for_collection_crates()
        # Choose map
        log.info("Selecting map")
        bot.select_map()   
        # main game loop
        log.info("Game start")
        bot.loop()

if __name__ == "__main__":
    
    # Start the bot on a seperate thread
    bot_thread = Thread(target=main,daemon=True)
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
    