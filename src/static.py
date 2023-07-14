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
    "RIGHT_ARROW_SELECTION"     : [ 0.856640625 , 0.4041666666666667 ],
    "DARK_CASTLE"               : [ 0.5546875 , 0.24305555555555555 ],
    "MAP_INDEX_1"               : [ 0.2734375 , 0.24305555555555555 ],
    "MAP_INDEX_2"               : [ 0.5546875 , 0.24305555555555555 ],
    "MAP_INDEX_3"               : [ 0.78125 , 0.24305555555555555 ],
    "MAP_INDEX_4"               : [ 0.2734375 , 0.4861111111111111 ],
    "MAP_INDEX_5"               : [ 0.5546875 , 0.4861111111111111 ],
    "MAP_INDEX_6"               : [ 0.78125 , 0.4861111111111111 ],
    "HARD_MODE"                 : [ 0.675390625 , 0.3902777777777778 ],
    "EASY_MODE"                 : [ 0.284765625 , 0.3902777777777778 ],
    "MEDIUM_MODE"               : [ 0.480078125 , 0.3902777777777778 ],
    "CHIMPS_MODE"               : [ 0.835546875 , 0.6805555555555556 ],
    "DEFLATION"                 : [ 0.662890625 , 0.4166666666666667 ],
    "SANDBOX_EASY"              : [ 0.5015625 , 0.6770833333333334 ],
    "SANDBOX_MEDIUM"            : [ 0.667578125 , 0.6791666666666667 ],
    "SANDBOX_HARD"              : [ 0.1453125 , 0.5458333333333333 ],
    "PRIMARY_ONLY"              : [ 0.48671875 , 0.4152777777777778 ],
    "APOPALYPSE"                : [ 0.667578125 , 0.4048611111111111 ],
    "REVERSE"                   : [ 0.500390625 , 0.6798611111111111 ],
    "MILITARY_ONLY"             : [ 0.4984375 , 0.41458333333333336 ],
    "MAGIC_MONKEYS_ONLY"        : [ 0.49609375 , 0.4097222222222222 ],
    "DOUBLE_HP_MOABS"           : [ 0.65859375 , 0.40902777777777777 ],
    "HALF_CASH"                 : [ 0.83671875 , 0.40694444444444444 ],
    "ALTERNATE_BLOONS_ROUNDS"   : [ 0.501171875 , 0.6680555555555555 ],
    "IMPOPPABLE"                : [ 0.660546875 , 0.6791666666666667 ],
    "CHIMPS"                    : [ 0.835546875 , 0.6805555555555556 ],
    "STANDARD_GAME_MODE"        : [ 0.330859375 , 0.5416666666666666 ],
    "OVERWRITE_SAVE"            : [ 0.59375 , 0.6763888888888889 ],
    "VICTORY_CONTINUE"          : [ 0.501171875 , 0.84375 ],
    "VICTORY_HOME"              : [ 0.366796875 , 0.7805555555555556 ],
    "DEFEAT_HOME"               : [ 0.29453125 , 0.7520833333333333 ],
    "DEFEAT_HOME_NO_CONTINUE"   : [ 0.36328125 , 0.7520833333333333 ],
    "EASTER_COLLECTION"         : [ 0.499609375 , 0.6326388888888889 ],
    "F_LEFT_INSTA"              : [ 0.3390625 , 0.5013888888888889 ],
    "F_RIGHT_INSTA"             : [ 0.65625 , 0.5013888888888889 ],
    "LEFT_INSTA"                : [ 0.41953125 , 0.5034722222222222 ],
    "RIGHT_INSTA"               : [ 0.577734375 , 0.5027777777777778 ],
    "MID_INSTA"                 : [ 0.4984375 , 0.5048611111111111 ],
    "EASTER_CONTINUE"           : [ 0.5 , 0.9236111111111112 ],
    "EASTER_EXIT"               : [ 0.0390625 , 0.06458333333333334 ],
    "QUIT_HOME"                 : [ 0.43984375 , 0.7881944444444444 ],
    "HERO_SELECT"               : [ 0.312109375 , 0.8833333333333333 ],
    "CONFIRM_HERO"              : [ 0.587890625 , 0.5722222222222222 ],
    "TARGET_BUTTON_MORTAR"      : [ 0.745703125 , 0.34097222222222223 ],
    "ABILLITY_ONE"              : [ 0.098828125 , 0.9576388888888889 ],
    "ABILLITY_TWO"              : [ 0.144140625 , 0.95625 ],
    "FREEPLAY"                  : [ 0.629296875 , 0.7722222222222223 ],
    "OK_MIDDLE"                 : [ 0.5 , 0.6965277777777777 ],
    "RESTART_WIN"               : [ 0.551953125 , 0.7597222222222222 ],
    "RESTART_CONFIRM"           : [ 0.591796875 , 0.6694444444444444 ],
    "RESTART_DEFEAT"            : [ 0.430859375 , 0.7520833333333333 ],
    "RESTART_DEFEAT_NO_CONTINUE": [ 0.5 , 0.7597222222222222 ],
    "CONFIRM_CHIMPS"            : [ 0.500390625 , 0.6805555555555556 ],
    "SETTINGS"                  : [ 0.037500 , 0.191667],
    "LANGUAGE"                  : [ 0.555208 , 0.659259],
    "ENGLISH"                   : [ 0.224479 , 0.192593]
}

hero_positions = {
    "OBYN"              : [ 0.04140625 , 0.36944444444444446 ],
    "CAPTAIN_CHURCHILL" : [ 0.19765625 , 0.36944444444444446 ],
    "STRIKER_JONES"     : [ 0.19765625 , 0.16111111111111112 ],
    "GWENDOLIN"         : [ 0.11953125 , 0.16111111111111112 ],
    "QUINCY"            : [ 0.04140625 , 0.16111111111111112 ],
    "PAT_FUSTY"         : [ 0.19765625 , 0.5777777777777777 ],
    "EZILI"             : [ 0.11953125 , 0.5777777777777777 ],
    "BENJAMIN"          : [ 0.04140625 , 0.5777777777777777 ],
    "ETIENNE"           : [ 0.19765625 , 0.7861111111111111 ],
    "ADMIRAL_BRICKELL"  : [ 0.11953125 , 0.7861111111111111 ],
    "ADORA"             : [ 0.04140625 , 0.7861111111111111 ],
    "SAUDA"             : [ 0.04140625 , 0.925 ],
    "PSI"               : [ 0.11953125 , 0.925 ],
    "GERALDO"           : [ 0.11953125 , 0.36944444444444446 ]
}

#   "HERO"              : [1, 2, 3]         cooldown changes with level-ups..............           notes
hero_cooldowns = {
    "QUINCY"            : [60, 70],         # L15 [45,70]     L18 [45,55]
    "GWENDOLIN"         : [40, 60],         
    "STRIKER_JONES"     : [16, 80],         # L15 [11,80]
    "OBYN"              : [35, 90],         
    "CAPTAIN_CHURCHILL" : [30, 60],         # L20 [30,30]
    "BENJAMIN"          : [30, 65],         
    "EZILI"             : [60, 90, 60],     # L12 [45,90,60]  L20 [45,90,40]                        2n ability useless???
    "PAT_FUSTY"         : [45, 20],         
    "ADORA"             : [45, 10, 60],     #                                                       2n ability useless???
    "ADMIRAL_BRICKELL"  : [50, 60, 60],     # L13 [50,60,50]  L18 [50,60,40]
    "ETIENNE"           : [70, 90],         # L6 [55,90]      L13 [55,75]       L16 [50,75]
    "SAUDA"             : [30, 45],         
    "PSI"               : [40, 60],         
    "GERALDO"           : []                
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
    "SPIKE" : "j",
    "VILLAGE" : "k",
    "HERO" : "u"
}

# "NAME" : [PAGE, INDEX]
maps = {
    # BEGINNER
    "MONKEY_MEADOW"     : [1, 1],
    "TREE_STUMP"        : [1, 2],
    "TOWN_CENTER"       : [1, 3],
    "MIDDLE_OF_THE_ROAD": [1, 4],
    "ONE_TWO_THREE"     : [1, 5],
    "SCRAPYARD"         : [1, 6],
    "THE_CABIN"         : [2, 1],
    "RESORT"            : [2, 2],
    "SKATES"            : [2, 3],
    "LOTUS_ISLAND"      : [2, 4],
    "CANDY_FALLS"       : [2, 5],
    "WINTER_PARK"       : [2, 6],
    "CARVED"            : [3, 1],
    "PARK_PATH"         : [3, 2],
    "ALPINE_RUN"        : [3, 3],
    "FROZEN_OVER"       : [3, 4],
    "IN_THE_LOOP"       : [3, 5],
    "CUBISM"            : [3, 6],
    "FOUR_CIRCLES"      : [4, 1],
    "HEDGE"             : [4, 2],
    "END_OF_THE_ROAD"   : [4, 3],
    "LOGS"              : [4, 4],
    # INTERMEDIATE
    "POLYPHEMUS"        : [5, 1],
    "COVERED_GARDEN"    : [5, 2],
    "QUARRY"            : [5, 3],
    "QUIET_STREET"      : [5, 4],
    "BLOONARIUS_PRIME"  : [5, 5],
    "BALANCE"           : [5, 6],
    "ENCRYPTED"         : [6, 1],
    "BAZAAR"            : [6, 2],
    "ADORAS_TEMPLE"     : [6, 3],
    "SPRING_SPRING"     : [6, 4],
    "KARTSNDARTS"       : [6, 5],
    "MOON_LANDING"      : [6, 6],
    "HAUNTED"           : [7, 1], 
    "DOWNSTREAM"        : [7, 2],
    "FIRING_RANGE"      : [7, 3],
    "CRACKED"           : [7, 4],
    "STREAMBED"         : [7, 5],
    "CHUTES"            : [7, 6],
    "RAKE"              : [8, 1],
    "SPICE_ISLANDS"     : [8, 2],
    # ADVANCED
    "EROSION"           : [9, 1],
    "MIDNIGHT_MANSION"  : [9, 2],
    "SUNKEN_COLUMNS"    : [9, 3],
    "X_FACTOR"          : [9, 4],
    "MESA"              : [9, 5],
    "GEARED"            : [9, 6],
    "SPILLWAY"          : [10, 1],
    "CARGO"             : [10, 2],
    "PATS_POND"         : [10, 3],
    "PENINSULA"         : [10, 4], 
    "HIGH_FINANCE"      : [10, 5],
    "ANOTHER_BRICK"     : [10, 6],
    "OFF_THE_COAST"     : [11, 1],
    "CORNFIELD"         : [11, 2],
    "UNDERGROUND"       : [11, 3],
    # EXPERT
    "DARK_DUNGEONS"     : [12, 1],
    "SANCTUARY"         : [12, 2],
    "RAVINE"            : [12, 3],
    "FLOODED_VALLEY"    : [12, 4],
    "INFERNAL"          : [12, 5],
    "BLOODY_PUDDLES"    : [12, 6],
    "WORKSHOP"          : [13, 1],
    "QUAD"              : [13, 2],
    "DARK_CASTLE"       : [13, 3],
    "MUDDY_PUDDLES"     : [13, 4],
    "OUCH"              : [13, 5]
}

upgrade_keybinds = {
    "top" : ",",
    "middle" : ".",
    "bottom" : "/"
}

# Index, regular targets, spike factory targets
target_order_regular = [ "FIRST", "LAST", "CLOSE", "STRONG" ]
target_order_spike   = [ "NORMAL", "CLOSE", "FAR", "SMART" ]
