def get():
    gameplan = {}
    with open("./gameplan.txt") as txt:
        for line in txt:
            (round, instruction) = line.split(' ', 1)
            if int(round) in gameplan:
                gameplan[int(round)].append(instruction[:-1])
            else:
                gameplan[int(round)] = [instruction[:-1]]
    return gameplan