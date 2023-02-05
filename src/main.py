import time
import sys
import argparse
from pathlib import Path
from Bot import Bot
from threading import Thread
from Failsafe import FailSafe
import mouse
import simulatedinput
from logger import logger as log

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
            verbose_mode=(args['verbose']), 
            restart_mode=(args['restart'])
        )
        
    print("Setting up Bot...")
    print("Using gameplan located in: " + str(gameplan_path))
    
    bot.initilize() # Initialize the bot (presses alt, etc)

    print("Waiting for Home screen. Please switch to Bloons TD 6 window.")

    # Wait for btd6 home screen
    waiting_for_home = False

    log.info("Waiting for home screen..")
    while waiting_for_home is False:

        time.sleep(0.2) # add a short timeout to avoid spamming the cpu
        waiting_for_home = bot.home_menu_check()
    log.info("Home screen detected")

    if bot.language_check() is False:
        log.info("Setting game to english")
        simulatedinput.click("SETTINGS")
        simulatedinput.click("LANGUAGE")
        simulatedinput.click("ENGLISH")
        bot.press_key("esc", timeout=0.5, amount=2)

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
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose mode (not done)')
    parser.add_argument('-r', '--restart', action='store_true', help='automatically restarts the game when finished, instead of going to home screen')
    parser.add_argument('-s', '--sandbox', action='store_true', help='Try put gameplan in sandbox mode without waiting for specific rounds (not done)')
    
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
    