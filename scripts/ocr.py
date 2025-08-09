import cv2
import numpy as np
import pytesseract


def ocr_colored_digits(img, lower=(0, 100, 100), upper=(80, 255, 255)):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array(lower)  # e.g. H=15°, S=150, V=150
    upper = np.array(upper)  # H=40°, max S/V
    mask = cv2.inRange(hsv, lower, upper)
    canvas = np.full(mask.shape, 255, dtype=np.uint8)
    canvas[mask == 0] = 0
    # cv2.imwrite("test_im.png", canvas)

    custom_config = r'--oem 3 --psm 7 outputbase digits'
    text = pytesseract.image_to_string(canvas, config=custom_config)
    return text.strip()


if __name__ == "__main__":
    result = ocr_colored_digits(cv2.imread("/Users/qiaoxuan/Desktop/testim.png"))
    print("Detected number:", result)
