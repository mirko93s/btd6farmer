import os
import sys

def get():
    bundle_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
    gameplan_path = os.path.abspath(os.path.join(bundle_dir, 'gameplan.txt'))
    gameplan = {}
    with open(gameplan_path) as txt:
        for line in txt:
            (round, instruction) = line.split(' ', 1)
            if int(round) in gameplan:
                gameplan[int(round)].append(instruction[:-1])
            else:
                gameplan[int(round)] = [instruction[:-1]]
    return gameplan