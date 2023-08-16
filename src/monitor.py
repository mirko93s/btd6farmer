import ctypes

print("Getting resolution")
ctypes.windll.shcore.SetProcessDpiAwareness(2)
width = ctypes.windll.user32.GetSystemMetrics(0)
height = ctypes.windll.user32.GetSystemMetrics(1)
ratio = round((width/height),2)

def scaling(coords):
    """Scales coordinates for different screen resolutions"""

    _x, _y = coords

    if ratio == 1.6: # 16:10
        # below are formulas used only for in game tower palcement coords, from gameplan
        # they aren't quite perfect, but 99% of the times the coords are good or off by 1 pixel at most...
        # this can be improved if we calculate exactly how the gameplay area changes from 16:9 to 16:10 in size, position, zoom and origin of zoom
        x = (_x - (0.018229166666666668 * (0.6942708333333333 - _x)) / 0.6942708333333333) * width
        y = (_y - (0.013888888888888888 * (0.5 - _y)) / 0.5) * height

    elif ratio == 1.78: # 16:9
        x = _x * width
        y = _y * height

    elif ratio > 1.78: # 21:9, 32:9 (any aspect ratio bigger than 1.77 should be the same, just side bars getting bigger)
        x = _x * height * 1.7777777777777777 + (width - height * 1.7777777777777777) / 2
        y = _y * height

    elif ratio == 1.33: # 4:3
        # to be implemented
        # tower selection ui on the bottom
        # no bars
        pass

    elif ratio == 1.25: # 5:4
        # to be implemented
        # tower selection ui on the bottom
        # bars above and below like in 16:10
        pass

    else:
        # resolution should not be supported, try anyway ???
        pass

    # this are just truncated using int, they may not be always precise to the pixel, round should be better
    return (int(x), int(y))