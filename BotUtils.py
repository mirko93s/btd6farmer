import sys
import time
import keyboard
import mouse
import static
import tkinter
from pathlib import Path

import numpy as np
import cv2
import pytesseract

if sys.platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

import re
import mss

import ctypes
from collections import defaultdict

class BotUtils:
    def __init__(self):

        try:
            if sys.platform == "win32":
                ctypes.windll.shcore.SetProcessDpiAwareness(2) # DPI indipendent
            tk = tkinter.Tk()
            self.width, self.height = tk.winfo_screenwidth(), tk.winfo_screenheight()
        except Exception as e:
            raise Exception("Could not retrieve monitor resolution")

        self.support_dir = self.get_resource_dir("assets")

        # Defing a lamda function that can be used to get a path to a specific image
        # self._image_path = lambda image, root_dir=self.support_dir, height=self.height : root_dir/f"{height}_{image}.png"
        self._image_path = lambda image, root_dir=self.support_dir : root_dir/f"{image}.png"


        # Resolutions for for padding
        self.reso_16 = [
            { "width": 1280, "height": 720  },
            { "width": 1920, "height": 1080 },
            { "width": 2560, "height": 1440 },
            { "width": 3840, "height": 2160 }
        ]
        self.round_area = None

    def get_resource_dir(self, path):
        return Path(__file__).resolve().parent/path

    def getRound(self):
        # Change to https://stackoverflow.com/questions/66334737/pytesseract-is-very-slow-for-real-time-ocr-any-way-to-optimise-my-code 
        # or https://www.reddit.com/r/learnpython/comments/kt5zzw/how_to_speed_up_pytesseract_ocr_processing/

        # The screen part to capture

        # If round area is not located yet
        if self.round_area is None:
    
            self.round_area = defaultdict()
            self.round_area["width"] = 200
            self.round_area["height"] = 42

            area = self.locate_round_area() # Search for round text, returns (1484,13) on 1080p
            
            # If it cant find anything
            if area == None:
                if self.DEBUG:
                    self.log("Could not find round area, setting default values")
                scaled_values = self._scaling([0.7083333333333333, 0.0277777777777778]) # Use default values, (1360,30) on 1080p

                # left = x
                # top = y
                self.round_area["left"] = scaled_values[0]
                self.round_area["top"] = scaled_values[1]
            else:
                if self.DEBUG:
                    self.log("Found round area")
                # set round area to the found area + offset
                x, y, roundwidth, roundheight = area
                
                xOffset, yOffset = ((roundwidth + 55), int(roundheight * 2) - 5)
                self.round_area["top"] = y + yOffset
                self.round_area["left"] = x - xOffset
        
        # Setting up screen capture area
        monitor = {'top': self.round_area["top"], 'left': self.round_area["left"], 'width': self.round_area["width"], 'height': self.round_area["height"]}
        # print("region", monitor)

        # Take Screenshot
        with mss.mss() as sct:
            sct_image = sct.grab(monitor)
            screenshot = np.array(sct_image, dtype=np.uint8)
            # Get local maximum:
            kernelSize = 5
            maxKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernelSize, kernelSize))
            localMax = cv2.morphologyEx(screenshot, cv2.MORPH_CLOSE, maxKernel, None, None, 1, cv2.BORDER_REFLECT101)
            # Perform gain division
            gainDivision = np.where(localMax == 0, 0, (screenshot/localMax))
            # Clip the values to [0,255]
            gainDivision = np.clip((255 * gainDivision), 0, 255)
            # Convert the mat type from float to uint8:
            gainDivision = gainDivision.astype("uint8")
            # Convert RGB to grayscale:
            grayscaleImage = cv2.cvtColor(gainDivision, cv2.COLOR_BGR2GRAY)
            # Resize image to improve the quality
            grayscaleImage = cv2.resize(grayscaleImage,(0,0), fx=3.0, fy=3.0)
            # Get binary image via Otsu:
            _, final_image = cv2.threshold(grayscaleImage, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # Set kernel (structuring element) size:
            kernelSize = 3
            # Set morph operation iterations:
            opIterations = 1
            # Get the structuring element:
            morphKernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernelSize, kernelSize))
            # Perform closing:
            final_image = cv2.morphologyEx( final_image, cv2.MORPH_CLOSE, morphKernel, None, None, opIterations, cv2.BORDER_REFLECT101 )
            # Flood fill (white + black):
            cv2.floodFill(final_image, mask=None, seedPoint=(int(0), int(0)), newVal=(255))
            # Invert image so target blobs are colored in white:
            final_image = 255 - final_image
            # Find the blobs on the binary image:
            contours, hierarchy = cv2.findContours(final_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            # Process the contours:
            for i, c in enumerate(contours):
                # Get contour hierarchy:
                currentHierarchy = hierarchy[0][i][3]
                # Look only for children contours (the holes):
                if currentHierarchy != -1:
                    # Get the contour bounding rectangle:
                    boundRect = cv2.boundingRect(c)
                    # Get the dimensions of the bounding rect:
                    rectX = boundRect[0]
                    rectY = boundRect[1]
                    rectWidth = boundRect[2]
                    rectHeight = boundRect[3]
                    # Get the center of the contour the will act as
                    # seed point to the Flood-Filling:
                    fx = rectX + 0.5 * rectWidth
                    fy = rectY + 0.5 * rectHeight
                    # Fill the hole:
                    cv2.floodFill(final_image, mask=None, seedPoint=(int(fx), int(fy)), newVal=(0))
            # Write result to disk:
            if self.DEBUG:
                cv2.imwrite("./DEBUG/round.png", final_image, [cv2.IMWRITE_PNG_COMPRESSION, 0])

            # Get current round from screenshot with tesseract
            found_text = pytesseract.image_to_string(final_image,  config='--psm 7').replace("\n", "")

            # Get only the first number/group so we don't need to replace anything in the string
            if re.search(r"(\d+/\d+)", found_text):
                found_text = re.search(r"(\d+)", found_text)
                return int(found_text.group(0))

            else:
                if self.DEBUG:
                    self.log("Found text '{}' does not match regex requirements".format(found_text))
                    self.save_file(data=mss.tools.to_png(sct_image.rgb, sct_image.size), _file_name="get_current_round_failed.png")
                    self.log("Saved screenshot of what was found")

                return None
    
    def save_file(self, data=format(0, 'b'), _file_name="noname", folder="DEBUG", ):
        directory = Path(__file__).resolve().parent/folder
        
        if not directory.exists():
            Path.mkdir(directory)

        with open(directory/_file_name, "wb") as output_file:
            output_file.write(data)

    def _move_mouse(self, location, move_timeout=0.1):
        mouse.move(x=location[0], y=location[1])
        time.sleep(move_timeout)

    def click(self, location: tuple | tuple, amount=1, timeout=0.5, move_timeout=0.1, press_time=0.075):        
        """
            Method to click on a specific location on the screen
            @param location: The location to click on
            @param amount: amount of clicks to be performed
            @param timeout: time to wait between clicks
            @param move_timeout: time to wait between move and click
            @param press_time: time to wait between press and release
        """

        # If location is a string then assume that its a static button
        if isinstance(location, str):
            location = static.button_positions[location]
        
        # Move mouse to location
        self._move_mouse(self._scaling(location), move_timeout)

        for _ in range(amount):
            mouse.press(button='left')
            time.sleep(press_time) # https://www.reddit.com/r/AskTechnology/comments/4ne2tv/how_long_does_a_mouse_click_last/ TLDR; dont click too fast otherwise shit will break
            mouse.release(button='left')
            
            """
                We don't need to apply cooldown and slow down the bot on single clicks
                So we only apply the .1 delay if the bot has to click on the same spot multiple times
                This is currently used for level selection and levelup screen
            """
            if amount > 1:
                time.sleep(timeout)
        
        time.sleep(timeout)

    def press_key(self, key, timeout=0.1, amount=1):
        for _ in range(amount):
            keyboard.send(key)
            time.sleep(timeout)

    # Different methods for different checks all wraps over _find()
    def menu_check(self):
        return self._find( self._image_path("menu") )

    def insta_monkey_check(self):
        return self._find( self._image_path("instamonkey") )

    def monkey_knowledge_check(self):
        return self._find( self._image_path("monkey_knowledge") )

    def victory_check(self):
        return self._find( self._image_path("victory") )

    def defeat_check(self):
        return self._find( self._image_path("defeat") )

    def levelup_check(self):
        return self._find( self._image_path("levelup") )

    def hero_check(self, heroString):
        if self._find( self._image_path(heroString) ):
            return True
        elif self._image_path(heroString + "_2") is not None:
            if self._find( self._image_path(heroString + "_2") ):
                return True
        elif self._image_path(heroString + "_3") is not None:
            if self._find( self._image_path(heroString + "_3") ):
                return True
        else:
            return False

    def loading_screen_check(self):
        return self._find( self._image_path("loading_screen") )

    def confirm_mode_check(self):
        return self._find( self._image_path("confirm_chimps") ) or \
            self._find( self._image_path("confirm_apopalypse") )

    def home_menu_check(self):
        return self._find( self._image_path("play") )

    def language_check(self):
        return self._find( self._image_path("english") )

    def collection_event_check(self):
        return self._find(self._image_path("diamond_case") )

    def locate_static_target_button(self):
        return self._find(self._image_path("set_target_button"), return_cords=True)
    
    def locate_round_area(self):
        return self._find(self._image_path("round_area"), return_cords=True, center_on_found=False)

    # Generic function to see if something is present on the screen
    def _find(self, path, confidence=0.9, return_cords=False, center_on_found=True):
        if self.DEBUG:
            self.log("Finding image: "+re.sub(r"(.+\\)",'',str(path)))
        try:
            if return_cords:
                cords = self._locate(path, confidence=confidence)
                if self.DEBUG:
                    self.log(cords)
                if cords is not None:
                    left, top, width, height = cords
                    if center_on_found:
                        return (left + width // 2, top + height // 2) # Return middle of found image   
                    else:
                        return (left, top, width, height)
                else:
                    return None
            if self._locate(path, confidence=confidence) is not None:
                self.log("Found image: "+re.sub(r"(.+\\)",'',str(path)))
                return True
            else:
                self.log("Not found image: "+re.sub(r"(.+\\)",'',str(path)))
                return False


        except Exception as e:
            raise Exception(e)

    # Scaling functions for different resolutions support
    def _scaling(self, pos_list):
        """
            This function will dynamically calculate the coordinates for the current resolution given the normalized ones in static.py
            it will also add any padding needed to positions to account for 21:9 

            do_padding -- this is used during start 
        """

        reso_21 = False
        for x in self.reso_16: 
            if self.height == x['height']:
                if self.width != x['width']:
                    reso_21 = True
                    x = pos_list[0]
                    break

        if reso_21 != True:
            x = pos_list[0] * self.width
        
        y = pos_list[1] * self.height
        x = x + self._padding() # Add's the pad to to the curent x position variable

        if self.DEBUG:
            self.log("Scaling: {} -> {}".format(pos_list, (int(x), int(y))))

        return (int(x), int(y))
        # return (x,y)


    def _padding(self):
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
        for x in self.reso_16: 
            if self.height == x['height']:
                padding = (self.width - x['width'])/2

        return padding

    def _load_img(self, img):
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


    def _locate_all(self, template_path, confidence=0.9, limit=100, region=None):
        """
            Template matching a method to match a template to a screenshot taken with mss.
            
            @template_path - Path to the template image
            @confidence - A threshold value between {> 0.0f & < 1.0f} (Defaults to 0.9f)

            credit: https://github.com/asweigart/pyscreeze/blob/b693ca9b2c964988a7e924a52f73e15db38511a8/pyscreeze/__init__.py#L184

            Returns a list of cordinates to where openCV found matches of the template on the screenshot taken
        """

        monitor = {'top': 0, 'left': 0, 'width': self.width, 'height': self.height} if region is None else region

        if  0.0 > confidence <= 1.0:
            raise ValueError("Confidence must be a value between 0.0 and 1.0")

        with mss.mss() as sct:

            # Load the taken screenshot into a opencv img object
            img = np.array(sct.grab(monitor))
            screenshot = self._load_img(img) 

            if region:
                screenshot = screenshot[region[1]:region[1]+region[3],
                                        region[0]:region[0]+region[2]
                                        ]
            else:
                region = (0, 0)
            # Load the template image
            template = self._load_img(template_path)

            confidence = float(confidence)

            # width & height of the template
            templateHeight, templateWidth = template.shape[:2]

            # scale template
            if self.width != 1920 or self.height != 1080:
                template = cv2.resize(template, dsize=(int(templateWidth/(1920/self.width)), int(templateHeight/(1080/self.height))), interpolation=cv2.INTER_CUBIC)

            # Find all the matches
            # https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image/9253805#9253805
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)    # heatmap of the template and the screenshot"
            match_indices = np.arange(result.size)[(result > confidence).flatten()]
            matches = np.unravel_index(match_indices[:limit], result.shape)
            
            # Defining the coordinates of the matched region
            matchesX = matches[1] * 1 + region[0]
            matchesY = matches[0] * 1 + region[1]

            if len(matches[0]) == 0:
                return None
            else:
                return [ (x, y, templateWidth, templateHeight) for x, y in zip(matchesX, matchesY) ]

    def _locate(self, template_path, confidence=0.9, tries=1):
        """
            Locates a template on the screen.

            Note: @tries does not do anything at the moment
        """
        result = self._locate_all(template_path, confidence)
        return result[0] if result is not None else None


if __name__ == "__main__":
    import time

    inst = BotUtils()
    inst.log = print
    inst.DEBUG = True
    time.sleep(2)


    print(inst.getRound())

    # res = inst._locate(inst._image_path("obyn"), confidence=0.9)
    # print(res)
