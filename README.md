# BTD 6 farmer | A Macro creator for Bloons td 6
<span style="font-size:16px;">Inspired from [RavingSmurfGB/Py_AutoBloons](https://github.com/RavingSmurfGB/Py_AutoBloons)</span>

[![Python application](https://github.com/linus-jansson/btd6farmer/actions/workflows/check_bot.yml/badge.svg?branch=main)](https://github.com/linus-jansson/btd6farmer/actions/workflows/check_bot.yml) 

Join the [Discord](https://discord.gg/qyKT6bzqZQ) for support, updates and sharing gameplans.

Feel free to make a pull request if you have any improvements or create a issue if something isn't working correctly!

## Table Of Contents (TODO)
- [Dependencies](#dependenices) 
- [Installation](#installation)
- [Running the bot](#running)
- [Having issues?](#issues)
- [Roadmap](#roadmap)
- [Creating your own gameplan](#contributing)
    - [Setup file](#setup_file)
    - [Gameplan file](#gameplan_file)
    - [Stats](#stats)
    - [Keyword cheatsheet](#keywords)
        - [Gamemodes](#gamemodes)
        - [Difficulties](#difficulties)
        - [Maps](#maps)
        - [Heros](#heros)
        - [Monkeys](#monkeys)

<a name="dependenices"/>

## Requirements & Dependencies
- Python 3.10+

```
keyboard==0.13.5
mouse==0.7.1
mss==9.0.1
numpy==1.25.1
opencv_python==4.8.0.74
Pymem==1.12.0
pywin32==306
```
<a name="installation"/>

## Installation of dependencies:
The python library requirments can be installed using `python -m pip install -r requirements.txt` or by running `Install_Requirements.bat`

<a name="running"/>

## Running the bot
1. Open up BTD 6
2. Run main.py in the command line with `py <location of script>/main.py --path <directory to gameplan>` or start `run.bat` to run with the default settings and gameplan. Some gamplans are included in the `gameplans` folder.
3. Navigate to the homescreen of BTD 6.

### Bot Launch options
```
>> py main.py --help
options:
  -h, --help            show this help message and exit
  -p PATH, --path PATH, --gameplan_path PATH
                        Path to the gameplan directory
  -d, --debug           Enable debug mode
  -r, --restart         automatically restarts the game when finished, instead of going to home screen
  -s, --sandbox         Try put gameplan in sandbox mode without waiting for specific rounds
```

<a name="issues"/>

## Having issues with the bot?
If you have any issues with the bot, find any bugs or have any suggestions for improvements, please create an issue or create a pull request!

<a name="roadmap"/>

### Roadmap
The projects roadmap can be found [here](https://github.com/users/linus-jansson/projects/1/views/5)

<a name="contributing"/>

## Creating your own gameplans
You are really welcome to create your own gameplans using your own stratergies and submiting them to the repo with a pull request. I will add it to the repository after testing!

## Contributing to the project
If you find any issues with the bot or have any suggestions for improvements, please create an issue. If you have any changes you would like to contribute with you can also create a pull request to the development branch!

__*NOTE: AS THIS IS STILL A WORK IN PROGRESS I MAY CHANGE THE GUIDE AND LAYOUT OF THE GAMEPLAN IN THE FUTURE FOR EASE OF USE. ALSO SOME FREATURES SPECIFIED IN THE DOCS ARE NOT YET IMPLEMENTED BUT ARE PLANNED TO*__


<a name="setup_file"/>

### setup.json
The setup file is used for the bot to know which hero, map, difficulty and gamemode it should use.
It should be named `setup.json` and be placed in the same directory as the gameplan.

```json
{
    "VERSION": "1",
    "HERO": "OBYN",
    "MAP": "DARK_CASTLE",
    "DIFFICULTY": "HARD_MODE",
    "GAMEMODE": "STANDARD_GAME_MODE",
}
```
> `Hero` - Which hero to use *[list of avaliable heros](#heros)*  \
> `MAP` - Which map to use *[list of avaliable maps](#maps)* \
> `DIFFICULTY` - Which Difficulty to use *[list of avaliable difficultues](#difficulties)* \
> `GAMEMODE` - Which Gamemode to use *[list of avaliable Gamemodes](#gamemodes)* \

<a name="gameplan_file"/>

### instructions.json
#### Creating the gameplan and example
The gameplan is a json file that contains the round as a key and the value as an array with instructions. 
All coordinates are normalized to you'r screen resolution, to work with a wider range of computers. (a value between 0 and 1)

The following example instruction places a tower on the absolute center of the map and starts the game in fast forward mode, on round 3. See [instruction types](#instruction_types) for more information about the different types of instructions. 

```json
{
    "3": [
        {
            "INSTRUCTION_TYPE": "PLACE_TOWER",
            "ARGUMENTS": {
                "TOWER": "TOWER_TYPE",
                "POSITION": [ 0.5, 0.5 ]
            }
        },
        {
            "INSTRUCTION_TYPE": "START",
            "ARGUMENTS": {
                "FAST_FORWARD": true,
            }
        }
    ]
}

```

<a name="instruction_types"/>

##### instruction types
- `START` - Indicates the game
    - `FAST_FORWARD` - (true / false) Defaults to True. Should the bot play in fast forward mode?
- `PLACE_TOWER` - Place a tower on the map
    - `MONKEY` - Type of monkey to place 
    - `LOCATION` - [x, y] position of tower to be placed 
- `UPGRADE_TOWER` - Upgrade a tower on the map
    - `LOCATION` - [x, y]  position of tower to be upgraded
    - `UPGRADE_PATH` - [top, middle, bottom] array of upgrades eg [1, 0, 1]
- `CHANGE_TARGET` - changes target of a tower
    - `LOCATION` - [x, y] location of the tower
    - `TARGET` - target or targets eg [ "FIRST", "LAST", "STRONG" ]. Can be a string or a array of targets
    - `TYPE` - (SPIKE or REGULAR) [*Heli & gunner not yet supported*]
    - `DELAY` - *(optional)* Defaults to 3 delay between each target change. Can also be an array of delays. Can be one delay eg `2` for 2 seconds or multiple `[1, 3, 4]` to sleep for 1 second, 3 seconds and 4 seconds respectively for each target change.
- `REMOVE_TOWER` - Removes a tower
    - `LOCATION` - [x, y] location of the tower
- `SET_STATIC_TARGET`
    - `LOCATION` - [x, y] location of tower
    - `TARGET_LOCATION` - [x, y] location of target
- `END` - (OPTIONAL) Finished instructions


An instruction array in a round can have multiple objects that will be executed after each other. for example:
```json
    //...
    "33": [
        {
            "INSTRUCTION_TYPE": "PLACE_TOWER",
            "ARGUMENTS": {
                "MONKEY": "DRUID",
                "LOCATION": [ 0.399609375, 0.35347222222222224 ]
            }
        },
        {
            "INSTRUCTION_TYPE": "PLACE_TOWER",
            "ARGUMENTS": {
                "MONKEY": "DRUID",
                "LOCATION": [ 0.43984375, 0.35555555555555557 ]
            }
        },
        {
            "INSTRUCTION_TYPE": "PLACE_TOWER",
            "ARGUMENTS": {
                "MONKEY": "DRUID",
                "LOCATION": [ 0.479296875, 0.35833333333333334 ]
            }
        }
    ]
    //...
```
### Getting the position of a tower or the target position.
An easy way to get the position of the tower or the target you want, is to use the following code:
```py
import mouse, time
import tkinter
import static
import keyboard
import os
tk = tkinter.Tk()
width, height = tk.winfo_screenwidth(), tk.winfo_screenheight()
tk.destroy()
step = """
{{
    "INSTRUCTION_TYPE": "PLACE_TOWER",
    "ARGUMENTS": {{
        "MONKEY": "{0}",
        "LOCATION": [
            {1},
            {2}
        ]
    }}
}}
        """
def find_tower(letter):
    for tower in static.tower_keybinds:
        if static.tower_keybinds[tower] == letter:
            return tower
    return None

while True:
    for tower in static.tower_keybinds:
        print(static.tower_keybinds[tower].upper() + ". " +tower )

    print("Press the key of the tower you want the coords for or press O to quit")
    while True:
        if keyboard.read_key().lower() in static.tower_keybinds.values():
            letter = keyboard.read_key().lower()
            break
        elif keyboard.read_key().lower() == 'o':
            exit()
    tower = find_tower(letter)
    if tower:
        print("Press P to get the coords")
        while True:
            if keyboard.is_pressed('p'):
                os.system('cls')
                x, y = mouse.get_position()
                w_norm, h_norm = x / width, y / height
                print("Step:")
                print(step.format(tower, w_norm, h_norm))
                print("Press O to quit or press any other key to continue")
                while True:
                    if keyboard.read_key().lower() == 'o':
                        exit()
                    else:
                        os.system('cls')
                        break
                break
        
    else:
        print("Invalid tower")
```
Run it in a terminal and copy the decired position into the gameplan.


### Stats
[Experience points per level](https://bloons.fandom.com/wiki/Experience_Point_Farming)
|Rounds|Beginner|Intermediate|Advanced|Expert|
|--|--|--|--|--|
|1-40 (Easy)|21 400|23 540|25 680|27 820|
|31-60 (Deflation)|45 950|50 545|55 140|59 735|
|1-60 (Medium)|56 950|62 645|68 340|74 035|
|3-80 (Hard)|126 150|138 765|151 380|163 995|
|6-100 (Impoppable/CHIMPS)|231 150|254 265|277 380|300 495|

<a name="keywords"/>

#### Keyword cheatsheet for the setup file and the gameplan

<a name="gamemodes"/>
<details>
<summary>Gamemodes</summary>

|Gamemode|Keyword in file|
|--|--|
|Chimps|CHIMPS_MODE|
|Chimps|CHIMPS|
|Deflation|DEFLATION|
|Apopalypse|APOPALYPSE|
|Reverse|REVERSE|
|Military Only|MILITARY_ONLY|
|Magic monkeys only|MAGIC_MONKEYS_ONLY|
|Double HP MOABS|DOUBLE_HP_MOABS|
|Half cash|HALF_CASH|
|Alternate Bloons Rounds|ALTERNATE_BLOONS_ROUNDS|
|Impoppable|IMPOPPABLE|
|Standard|STANDARD_GAME_MODE|

</details>

<a name="difficulties"/>
<details>
<summary>Difficulties</summary>

|Difficulty|Keyword in file|
|--|--|
|Easy|EASY_MODE|
|Medium|MEDIUM_MODE|
|Hard|HARD_MODE|

</details>

<a name="maps"/>
<details>
<summary>Maps</summary>

|Monkey|Keyword in file|
|--|--|
|Monkey Meadow|MONKEY_MEADOW|
|Tree Stump|TREE_STUMP|
|Town Center|TOWN_CENTER|
|Scrapyard|SCRAPYARD|
|The Cabin|THE_CABIN|
|Resort|RESORT|
|Skates|SKATES|
|Lotus Island|LOTUS_ISLAND|
|Candy Falls|CANDY_FALLS|
|Winter Park|WINTER_PARK|
|Carved|CARVED|
|Park Path|PARK_PATH|
|Alpine Run|ALPINE_RUN|
|Frozen Over|FROZEN_OVER|
|In The Loop|IN_THE_LOOP|
|Cubism|CUBISM|
|Four Circles|FOUR_CIRCLES|
|Hedge|HEDGE|
|End Of The Road|END_OF_THE_ROAD|
|Logs|LOGS|
|Covered Garden|COVERED_GARDEN|
|Quarry|QUARRY|
|Quiet Street|QUIET_STREET|
|Bloonarius Prime|BLOONARIUS_PRIME|
|Balance|BALANCE|
|Encrypted|ENCRYPTED|
|Bazaar|BAZAAR|
|Adora's Temple|ADORAS_TEMPLE|
|Spring Spring|SPRING_SPRING|
|KartsNDarts|KARTSNDARTS|
|Moon Landing|MOON_LANDING|
|Haunted|HAUNTED|
|Downstream|DOWNSTREAM|
|Firing Range|FIRING_RANGE|
|Cracked|CRACKED|
|Streambed|STREAMBED|
|Chutes|CHUTES|
|Rake|RAKE|
|Spice Islands|SPICE_ISLANDS|
|Midnight Mansion|MIDNIGHT_MANSION|
|Sunken Columns|SUNKEN_COLUMNS|
|X Factor|XFACTOR|
|Mesa|MESA|
|Geared|GEARED|
|Spillway|SPILLWAY|
|Cargo|CARGO|
|Pat's Pond|PATS_POND|
|Peninsula|PENINSULA|
|High Finance|HIGH_FINANCE|
|Another Brick|ANOTHER_BRICK|
|Off The Coast|OFF_THE_COAST|
|Cornfield|CORNFIELD|
|Underground|UNDERGROUND|
|Sanctuary|SANCTUARY|
|Ravine|RAVINE|
|Flooded Valley|FLOODED_VALLEY|
|Infernal|INFERNAL|
|Bloody Puddles|BLOODY_PUDDLES|
|Workshop|WORKSHOP|
|Quad|QUAD|
|Dark Castle|DARK_CASTLE|
|Muddy Puddles|MUDDY_PUDDLES|
|#Ouch|OUCH|

</details>

<a name="heros"/>
<details>
<summary>Heros</summary>

|Monkey|Keyword in setupfile|
|--|--|
|Quincy|QUINCY|
|Gwendolin|GWENDOLIN|
|Striker Jones|STRIKER_JONES|
|Obyn Greenfoot|OBYN|
|Captain Churchill|MONKEY|
|Benjamin|BENJAMIN|
|Ezili|EZILI|
|Pat Fusty|PAT_FUSTY|
|Adora|ADORA|
|Admiral Brickell|ADMIRAL_BRICKELL|
|Etienne|ETIENNE|
|Sauda|SAUDA|
|Psi|PSI|
|Geraldo|GERALDO|

</details>

<a name="monkeys"/>
<details>
<summary>Monkeys</summary>

|Monkey|Keyword in instruction|
|--|--|
|Hero|HERO|
|Dart Monkey|DART|
|Boomerang Monkey|BOOMERANG|
|Bomb Shooter|BOMB|
|Tack Shooter|TACK|
|Ice Monkey|ICE|
|Glue Gunner|GLUE|
|Sniper Monkey|SNIPER|
|Monkey Sub|SUBMARINE|
|Monkey Buccaneer|BUCCANEER|
|Monkey Ace|ACE|
|Heli Pilot|HELI|
|Mortar Monkey|MORTAR|
|Dartling Gunner|DARTLING|
|Wizard Monkey|WIZARD|
|Super Monkey|SUPER|
|Ninja Monkey|NINJA|
|Alchemist|ALCHEMIST|
|Druid|DRUID|
|Banana Farm|BANANA|
|Spike factory|SPIKE|
|Monkey Village|VILLAGE|
|Engineer Monkey|ENGINEER|

</details>


