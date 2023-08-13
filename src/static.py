# Wrappers around static data
class Heros:
    pass

class Towers:
    pass

class Difficulty:
    pass

class Gamemode:
    pass
class Map (Difficulty, Gamemode):
    pass

button_positions = { # Creates a dictionary of all relative positions needed for monkeys
    "HOME_MENU_START"           : [ 0.438671875 , 0.8666666666666667 ],
    "EXPERT_SELECTION"          : [ 0.69453125 , 0.9055555555555556 ],
    "BEGINNER_SELECTION"        : [ 0.30390625 , 0.9055555555555556 ],
    "HARD_MODE"                 : [ 0.675390625 , 0.3902777777777778 ],
    "CHIMPS_MODE"               : [ 0.835546875 , 0.6805555555555556 ],
    "STANDARD_GAME_MODE"        : [ 0.330859375 , 0.5416666666666666 ],
    "OVERWRITE_SAVE"            : [ 0.59375 , 0.6763888888888889 ],
    "VICTORY_CONTINUE"          : [ 0.501171875 , 0.84375 ],
    "VICTORY_HOME"              : [ 0.366796875 , 0.7805555555555556 ],
    "DEFEAT_HOME_NO_CONTINUE"   : [ 0.36328125 , 0.7520833333333333 ],
    "EVENT_COLLECTION"         : [ 0.499609375 , 0.6326388888888889 ],
    "F_LEFT_INSTA"              : [ 0.3390625 , 0.5013888888888889 ],
    "F_RIGHT_INSTA"             : [ 0.65625 , 0.5013888888888889 ],
    "LEFT_INSTA"                : [ 0.41953125 , 0.5034722222222222 ],
    "RIGHT_INSTA"               : [ 0.577734375 , 0.5027777777777778 ],
    "MID_INSTA"                 : [ 0.4984375 , 0.5048611111111111 ],
    "EVENT_CONTINUE"           : [ 0.5 , 0.9236111111111112 ],
    "EVENT_EXIT"               : [ 0.0390625 , 0.06458333333333334 ],
    "HERO_SELECT"               : [ 0.312109375 , 0.8833333333333333 ],
    "CONFIRM_HERO"              : [ 0.587890625 , 0.5722222222222222 ],
    "TARGET_BUTTON_MORTAR"      : [ 0.745703125 , 0.34097222222222223 ],
    "SETTINGS"                  : [ 0.037500 , 0.191667],
    "LANGUAGE"                  : [ 0.555208 , 0.659259],
    "ENGLISH"                   : [ 0.224479 , 0.192593],
    "STARTUP"                   : [ 0.5, 0.925]
}

hero_positions = {
    "OBYN"              : [ 0.04140625 , 0.36944444444444446 ]
}

hero_cooldowns = {
    "OBYN"              : [35, 90]       
}

tower_keybinds = {
    "DART" : "q",
    "BOOMERANG" : "w",
    "BOMB" : "e",
    "TACK" : "r",
    "ICE" : "t",
    "GLUE" : "y",
    "SNIPER" : "z",
    "SUBMARINE" : "x",
    "BUCCANEER" : "c",
    "ACE" : "v",
    "HELI" : "b",
    "MORTAR" : "n",
    "DARTLING" : "m",
    "WIZARD" : "a",
    "SUPER" : "s",
    "NINJA" : "d",
    "ALCHEMIST" : "f",
    "DRUID" : "g",
    "BANANA" : "h",
    "ENGINEER" : "l",
    "BEAST" : "i",
    "SPIKE" : "j",
    "VILLAGE" : "k",
    "HERO" : "u"
}

upgrade_keybinds = {
    "top" : ",",
    "middle" : ".",
    "bottom" : "/"
}

# Index, regular targets, spike factory targets
target_order_regular = [ "FIRST", "LAST", "CLOSE", "STRONG" ]
target_order_spike   = [ "NORMAL", "CLOSE", "FAR", "SMART" ]
