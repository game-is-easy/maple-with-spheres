import cv2
import numpy as np
import pytesseract


def ocr_colored_digits(img, lower=(20, 100, 100), upper=(70, 255, 255)):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    lower = np.array(lower)  # e.g. H=15°, S=150, V=150
    upper = np.array(upper)  # H=40°, max S/V
    mask = cv2.inRange(hsv, lower, upper)
    canvas = np.full(mask.shape, 0, dtype=np.uint8)
    canvas[mask == 0] = 255
    # scale = 4
    # up = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite("test_im.png", canvas)

    custom_config = r'--oem 3 --psm 7 outputbase digits'
    text = pytesseract.image_to_string(canvas, config=custom_config)
    return text.strip()


def ocr_inv_bg_fg(img):
    scale_factor = 2
    line_height = scale_factor * 50
    if len(img.shape) > 2:
        img = cv2.resize(img, None, fx=scale_factor, fy=scale_factor,interpolation=cv2.INTER_CUBIC)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    img = cv2.bitwise_not(img)
    threshold, mask = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # mask = np.zeros_like(img)
    # mask[np.where(img > threshold)] = 0
    # mask[np.where(img <= threshold)] = 255
    # cv2.imshow("test", mask)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    lines = ['', '', '']
    for i in range(3):
        lines[i] = pytesseract.image_to_string(
            mask[i*line_height:(i+1)*line_height,:],
            config=r'--oem 3 --psm 6 -c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+-%:. "'
        ).strip()
        # lines[i] = pytesseract.image_to_data(mask[i*line_height:(i+1)*line_height,:], output_type=pytesseract.Output.DICT)
    return lines

if __name__ == "__main__":
    result = ocr_colored_digits(cv2.imread("/Users/qiaoxuan/PycharmProjects/maple-with-spheres/scripts/cd_inf_167.png"))
    print("Detected number:", result)
