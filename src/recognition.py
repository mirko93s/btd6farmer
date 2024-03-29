from pathlib import Path
import numpy as np
import cv2
import mss
import monitor

#Generic function to see if something is present on the screen
def find(path, confidence=0.9, return_cords=False, center_on_found=True):

    if return_cords:
        cords = locate(path, confidence=confidence)

        if cords is not None:
            left, top, width, height = cords
            if center_on_found:
                return ((left + width // 2), (top + height // 2)) # Return middle of found image   
            else:
                return (left, top, width, height)
        else:
            return None
    return True if locate(path, confidence=confidence) is not None else False


def load_image(img):

    if isinstance(img, Path):
        # this is used to load images and convert them to grayscale
        img_cv = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE)

    elif isinstance(img, np.ndarray):
        # this is used for screenshots, it converts them to grayscale
        img_cv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    return img_cv

def locate(template_path, confidence=0.9, limit=100, region=None, locate_all=False):
    """
        Template matching a method to match a template to a screenshot taken with mss.
        
        @template_path - Path to the template image
        @confidence - A threshold value between {> 0.0f & < 1.0f} (Defaults to 0.9f)

        credit: https://github.com/asweigart/pyscreeze/blob/b693ca9b2c964988a7e924a52f73e15db38511a8/pyscreeze/__init__.py#L184

        Returns a list of cordinates to where openCV found matches of the template on the screenshot taken
    """

    screenshotArea = {
        'top': 0, 
        'left': 0, 
        'width': monitor.width, 
        'height': monitor.height
    } if region is None else region

    if 0.0 > confidence <= 1.0:
        raise ValueError("Confidence must be a value between 0.0 and 1.0")

    with mss.mss() as screenshotter:

        # Load the taken screenshot into a opencv img object
        img = np.array(screenshotter.grab(screenshotArea))
        screenshot = load_image(img) 
        # cv2.imwrite(f"./DEBUG/LOCATE_ALL{str(time.time())}.png", screenshot, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        if region:
            screenshot = screenshot[region[1]:region[1]+region[3],
                                    region[0]:region[0]+region[2]
                                    ]
        else:
            region = (0, 0)
        # Load the template image
        template = load_image(template_path)

        confidence = float(confidence)

        # width & height of the template
        templateHeight, templateWidth = template.shape[:2]

        # Scale template to monitor resolution
        # The game ui gets bigger only if the height gets bigger, we shouldn't care about monitor width != 1920
        # TODO: 4:3 and 5:4 ???
        # update all the assets to 4k, it's better to downscale than to upscale
        if monitor.height != 1080:
            scale_factor = (int(templateWidth/(1080/monitor.height)), int(templateHeight/(1080/monitor.height)))
            template = cv2.resize(template, scale_factor, interpolation=cv2.INTER_AREA)
        
        # Find all the matches
        # https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image/9253805#9253805
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)    # heatmap of the template and the screenshot"
        # cv2.imwrite(f"./DEBUG/LOCATE_ALL_RESULT{str(time.time())}.png", result, [cv2.IMWRITE_PNG_COMPRESSION, 0])

        match_indices = np.arange(result.size)[(result > confidence).flatten()]
        matches = np.unravel_index(match_indices[:limit], result.shape)
        # print("matches:" matches)
        
        # Defining the coordinates of the matched region
        matchesX = matches[1] * 1 + region[0]
        matchesY = matches[0] * 1 + region[1]

        if len(matches[0]) == 0:
            return None
        else:
            result = [ (x, y, templateWidth, templateHeight) for x, y in zip(matchesX, matchesY) ]

    return result if locate_all else result[0]