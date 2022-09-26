import time
import sys
import mouse
from pathlib import Path
from Bot import Bot
from threading import Thread
 
def main():
    def no_gameplan_exception():
        raise Exception("No valid argument for directory.. 'python main.py --gameplan_path <directory to gameplan>'")

    # Retrives the gameplan from the command line and makes a Path object out of it
    gameplan_path = (Path(__file__).resolve().parent/sys.argv[sys.argv.index("--gameplan_path") + 1]) if "--gameplan_path" in sys.argv else no_gameplan_exception()

    # Verify directory exist.
    if not gameplan_path.exists():
        print("No directory found at: " + str(gameplan_path))
        no_gameplan_exception()
    # Verify that it is a directory
    if not gameplan_path.is_dir():
        print("Not a directory")
        no_gameplan_exception()
    
    bot = Bot(instruction_path=gameplan_path, debug_mode=("--debug" in sys.argv), verbose_mode=("--verbose" in sys.argv), restart_mode=("--restart" in sys.argv))
    print("Setting up Bot...")
    print("Using gameplan located in: " + str(gameplan_path))
    
    bot.initilize() # Initialize the bot (presses alt, etc)

    print("Waiting for Home screen. Please switch to Bloons TD 6 window.")

    # Wait for btd6 home screen
    waiting_for_home = False

    while waiting_for_home is False:
        if bot.DEBUG:
            print("Waiting for loading screen..")
        time.sleep(0.2) # add a short timeout to avoid spamming the cpu
        waiting_for_home = bot.home_menu_check()

    # Check for obyn
    bot.hero_select()

    if bot.RESTART:
        print("selecting map")
        bot.select_map()

    # Make sure we haven't exited by using the stop key.
    while bot.running:
        bot.check_for_collection_crates()

        if not bot.RESTART:
            print("selecting map")
            # Choose map
            bot.select_map()   

        print("Game start")

        # main game loop
        bot.ingame_loop()


if __name__ == "__main__":
    Thread(target=main, daemon=True).start()
    # Failsafe option, move mouse to upper left corner (0,0) to instantly kill the bot
    while mouse.get_position() != (0,0):
        time.sleep(0.2)
    
    sys.exit("FAILSAFE EXIT")