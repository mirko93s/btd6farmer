# width, height, top, left

import format
import cv2
import pytesseract

def getTextFromImage(image):
    """ returns text from image """
    imageCandidate = format.formatImageOCR(image)
    # Write result to disk:
    if DEBUG:
        cv2.imwrite("./DEBUG/round.png", imageCandidate, [cv2.IMWRITE_PNG_COMPRESSION, 0])

    # NOTE: This part seems to be buggy
    # Get current round from screenshot with tesseract
    return pytesseract.image_to_string(imageCandidate,  config='--psm 7').replace("\n", "")

