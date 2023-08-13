"""
Handle for monitor related functions, such as 
    - scaling and padding for different resolutions
    - getting the current resolution
    - TODO: getting main monitor & resolution

"""
from logger import logger as log
 
import sys
import ctypes
import tkinter

# Resolutions for for padding
resolution_list = [
    { "width": 1280, "height": 720  },
    { "width": 1366, "height": 768  },
    { "width": 1600, "height": 900  },
    { "width": 1920, "height": 1080 },
    { "width": 2560, "height": 1440 },
    { "width": 3840, "height": 2160 }
]

def get_resolution() -> tuple[int, int]:
    global width, height
    print("Getting resolution")
    try:
        if sys.platform == "win32":
            ctypes.windll.shcore.SetProcessDpiAwareness(2) # DPI indipendent
        tk = tkinter.Tk()
        width, height = tk.winfo_screenwidth(), tk.winfo_screenheight()
        return width, height
    except Exception as e:
        log.critical("Could not retrieve monitor resolution: \n %d", e)
        raise Exception("Could not retrieve monitor resolution: \n %d", e)

width, height = get_resolution()

# Scaling functions for different resolutions support
def scaling(pos_list):
    global width, height, resolution_list
    """
        Function takes in width, and height normalized to 1920x1080
        it will then iterate through the reso_21 list and check if the current resolution height matches any of the entries
        if it does it will set reso_21 to True and break out of the loop


        This function will dynamically calculate the differance between current resolution and designed for 1920x1080
        it will also add any padding needed to positions to account for 21:9 

        do_padding -- this is used during start 
    """

    reso_21 = False
    # What does it even do?
    for x in resolution_list: 
        if height == x['height']:
            if width != x['width']:
                reso_21 = True
                x = pos_list[0]
                break
    # As Values are normalized they are never more than 1

    if reso_21 != True:
        x = pos_list[0] * width
    
    y = pos_list[1] * height
    x = x + padding() # Add's the pad to to the curent x position variable

    log.debug("Scaling: {} -> {}".format(pos_list, (int(x), int(y))))

    # Return the scaled position as tuple of ints
    return (int(x), int(y))


def padding():
    global width, height, resolution_list
    """
        Get's width and height of current resolution
        we iterate through reso_16 for heights, if current resolution height matches one of the entires 
        then it will calulate the difference of the width's between current resolution and 16:9 (reso_16) resolution
        divides by 2 for each side of padding

        Variables Used
        width -- used to referance current resolution width
        height -- used to referance current resolution height
        pad -- used to output how much padding we expect in different resolutions
        reso_16 -- list that  
    """

    padding = 0
    for x in resolution_list: 
        if height == x['height']:
            padding = (width - x['width'])/2

    return padding