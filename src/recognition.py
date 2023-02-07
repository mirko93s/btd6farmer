from pathlib import Path
import numpy as np
import cv2
import mss
import monitor
from logger import logger as log

#Generic function to see if something is present on the screen
def find(path, confidence=0.9, return_cords=False, center_on_found=True):

    try:
        if return_cords:
            cords = locate(path, confidence=confidence)
            
            log.debug("Found cords: " + str(cords))

            if cords is not None:
                left, top, width, height = cords
                if center_on_found:
                    return (left + width // 2, top + height // 2) # Return middle of found image   
                else:
                    return (left, top, width, height)
            else:
                return None
        return True if locate(path, confidence=confidence) is not None else False

    except Exception as e:
        raise Exception(e)


def load_image(img):
    """
    TODO
    """
    # load images if given Path, or convert as needed to opencv
    # Alpha layer just causes failures at this point, so flatten to RGB.
    # RGBA: load with -1 * cv2.CV_LOAD_IMAGE_COLOR to preserve alpha
    # to matchTemplate, need template and image to be the same wrt having alpha
    
    if isinstance(img, Path):
        # The function imread loads an image from the specified file and
        # returns it. If the image cannot be read (because of missing
        # file, improper permissions, unsupported or invalid format),
        # the function returns an empty matrix
        # http://docs.opencv.org/3.0-beta/modules/imgcodecs/doc/reading_and_writing_images.html
        img_cv = cv2.imread(str(img), cv2.IMREAD_GRAYSCALE)
        if img_cv is None:
            raise IOError(f"Failed to read {img} because file is missing, has improper permissions, or is an unsupported or invalid format")
    elif isinstance(img, np.ndarray):
        img_cv = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # don't try to convert an already-gray image to gray
        # if grayscale and len(img.shape) == 3:  # and img.shape[2] == 3:
        # else:
        #     img_cv = img
    elif hasattr(img, 'convert'):
        # assume its a PIL.Image, convert to cv format
        img_array = np.array(img.convert('RGB'))
        img_cv = img_array[:, :, ::-1].copy()  # -1 does RGB -> BGR
        img_cv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    else:
        raise TypeError('expected an image filename, OpenCV numpy array, or PIL image')
    
    return img_cv


def locate_all(template_path, confidence=0.9, limit=100, region=None):
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

        # Scale template to screenshot resolution
        if monitor.width != 2560 or monitor.height != 1440:
            # print("Template scaling to monitor resolution")
            template = cv2.resize(
                template, 
                dsize=(int(templateWidth/(2560/monitor.width)), int(templateHeight/(1440/monitor.height))), 
                interpolation=cv2.INTER_AREA 
            )
        
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
            return [ (x, y, templateWidth, templateHeight) for x, y in zip(matchesX, matchesY) ]

def locate(template_path, confidence=0.9, tries=1):
    """
        Locates a template on the screen.

        Note: @tries does not do anything at the moment
    """
    result = locate_all(template_path, confidence)
    return result[0] if result is not None else None