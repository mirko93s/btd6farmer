import time
import sys
from Bot import Bot
from threading import Thread
import mouse
import simulatedinput
import monitor
import os
import win32gui
import subprocess

def main():
    
    bot = Bot()
    os.system('cls' if os.name == 'nt' else 'clear')
    print("Setting up Bot...")

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

    while waiting_for_home is False:
        time.sleep(0.2) # add a short timeout to avoid spamming the cpu
        waiting_for_startup, waiting_for_home = bot.checkFor(["startup","home_menu"], return_raw=True)
        if waiting_for_startup:
            simulatedinput.click("STARTUP")
    
    print("Starting bot..\nIf you want to stop the bot, move your mouse to the upper left corner of your screen or press ctrl+c in the terminal")
    
    simulatedinput.send_key("alt")
    
    if bot.checkFor("english") is False:
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
        bot.select_map()   
        # main game loop
        bot.loop()

if __name__ == "__main__":
    
    # Start the bot on a seperate thread
    bot_thread = Thread(target=main,daemon=True)
    bot_thread.start()

    # Failsafe option, move mouse to upper left corner (0,0) to instantly kill the bot
    while mouse.get_position() != (0,0) and bot_thread.is_alive():
        time.sleep(0.1)
    
    if mouse.get_position() == (0, 0):
        sys.exit(1)