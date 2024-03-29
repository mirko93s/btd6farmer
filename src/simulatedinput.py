import keyboard
import mouse
from time import sleep
import monitor
import static


# Maybe add static in here somewhere?
def send_key( keybind, timeout=0.1, amount=1):
    """"""

    # Check if keybind is a nick for a keybind in static otherwise use the keybind as is
    keybind = static.tower_keybinds.get(keybind, keybind)
    keybind = static.upgrade_keybinds.get(keybind, keybind) # cool stacking will pass the last value to next dictionary

    
    for _ in range(amount):
        keyboard.send(keybind)
        sleep(timeout)


def move_mouse(location, move_timeout=0.1):
    """
        Method to move the mouse to a specific location on the screen
        @param location: The location to move the mouse to (x, y)
    """
    mouse.move(x=location[0], y=location[1])
    sleep(move_timeout)


def click(location=(0.5, 0.5), amount=1, timeout=0.5, move_timeout=0.1, hold_time=0.075, _button='left', ui = False):
    """
    Method to click on a specific location on the screen
    @param location: The location to click on, if omitted it defaults to the middle of the screen
    @param amount: amount of clicks to be performed
    @param timeout: time to wait between clicks (after each click to be precise, so this also applies to a single click)
    @param move_timeout: time to wait between move and click
    @param hold_time: time to wait between press and release
    @param _button: which button to press, defaults to left
    @param ui: if false scales coordinates according to screen resolution, set to true for coordinates found matching templates
    """

    # TODO remove it, we don't use button anymore
    # If location is a string then assume that its a static button
    if isinstance(location, str):
        location = static.button_positions[location]
    
    # do not scale coordinates of matched templates they are already the correct coords and do not need any adjustement
    # TODO: autodetect when it needs to be scaled or not without using any annoying argument
    if not ui:
        location = monitor.scaling(location)
    # Move mouse to location
    move_mouse(location, move_timeout)

    for _ in range(amount):
        mouse.press(button=_button)
        sleep(hold_time) # https://www.reddit.com/r/AskTechnology/comments/4ne2tv/how_long_does_a_mouse_click_last/ TLDR; dont click too fast otherwise shit will break
        mouse.release(button=_button)
        
        """
            We don't need to apply cooldown and slow down the bot on single clicks
            So we only apply the .1 delay if the bot has to click on the same spot multiple times
            This is currently used for level selection and levelup screen
        """
        sleep(timeout)

    # Move mouse on the bottom right corner so we don't cover the screen with the cursor
    move_mouse((monitor.width,monitor.height))
    
