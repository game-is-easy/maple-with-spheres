import numpy as np
import cv2
import collections
import subprocess
import Quartz
from Quartz import CGMainDisplayID, CGDisplayCreateImageForRect, CGRectMake
from scripts.src.appscreenshot import get_screenshot_provider
import os
import datetime

Box = collections.namedtuple('Box', 'left top width height')
RGB = collections.namedtuple('RGB', 'red green blue')
Position = collections.namedtuple('Position', 'x y')
# Point = collections.namedtuple('Point', 'x y')
# screenshot_provider = get_screenshot_provider()


def screenshot(image_name=None, region=None):
    if image_name is None:
        tmp_filename = f"screenshot{(datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))}.png"
    else:
        tmp_filename = image_name
    if region is None:
        subprocess.run(['screencapture', '-x', tmp_filename])
        im = cv2.imread(tmp_filename)
    else:
        subprocess.run(['screencapture', '-x', "-R", f"{region[0]//2},{region[1]//2},{region[2]//2+1},{region[3]//2+1}", tmp_filename])
        im = cv2.imread(tmp_filename)
        im = im[region[1] % 2:region[1] % 2 + region[3], region[0] % 2:region[0] % 2 + region[2], :]

    if image_name is None:
        os.unlink(tmp_filename)
    elif region is not None:
        cv2.imwrite(image_name, im)
    return im


def screencapture(image_name=None, region=None, retina_region=True, png_compression=1):
    if image_name is None:
        tmp_filename = f"screenshot{(datetime.datetime.now().strftime('%Y-%m%d_%H-%M-%S-%f'))}.png"
    else:
        tmp_filename = image_name
    if region is None:
        x, y, w, h = (0, 0, 3456, 2234)
        # im = CGDisplayCreateImageForRect(CGMainDisplayID())
    else:
        x, y, w, h = region
    if retina_region:
        x //= 2
        y //= 2
        w //= 2
        h //= 2
    im = CGDisplayCreateImageForRect(CGMainDisplayID(), CGRectMake(x, y, w, h))
    w = Quartz.CGImageGetWidth(im)
    h = Quartz.CGImageGetHeight(im)
    rowbytes = Quartz.CGImageGetBytesPerRow(im)
    data = Quartz.CGDataProviderCopyData(Quartz.CGImageGetDataProvider(im))
    buf = np.frombuffer(data, dtype=np.uint8)
    expected = h * rowbytes
    if buf.size < expected:
        raise ValueError(f"Provider too small: {buf.size} < {expected}")
    if buf.size > expected:
        buf = buf[:expected]
    bgra = buf.reshape((h, rowbytes))[:, :w * 4].reshape((h, w, 4))
    bgr = cv2.cvtColor(bgra, cv2.COLOR_BGRA2BGR)
    cv2.imwrite(tmp_filename, bgr, [cv2.IMWRITE_PNG_COMPRESSION, png_compression])

    if image_name is None:
        os.unlink(tmp_filename)
    return bgr


def screengrab(image_name=None, region=None, png_compression=1):
    bgr = screenshot_provider.grab(region)
    if image_name is not None:
        cv2.imwrite(image_name, bgr, [cv2.IMWRITE_PNG_COMPRESSION, png_compression])
    return bgr


def locate_all(needle_image, haystack_image, limit=10000, confidence=0.999, show=False):
    if type(needle_image) == str:
        needle_image = cv2.imread(needle_image)
        if needle_image is None:
            raise FileNotFoundError("can't open/read file: check file path/integrity")
    if type(haystack_image) == str:
        haystack_image = cv2.imread(haystack_image)
        if haystack_image is None:
            raise FileNotFoundError("can't open/read file: check file path/integrity")

    needle_height, needle_width = needle_image.shape[:2]
    if show:
        from PIL import Image
        Image._show(Image.fromarray(needle_image[:,:,-1]))
        Image._show(Image.fromarray(haystack_image[:,:,-1]))

    print(haystack_image.shape)
    print(needle_image.shape)
    if (haystack_image.shape[0] < needle_image.shape[0] or haystack_image.shape[1] < needle_image.shape[1]):
        # avoid semi-cryptic OpenCV error below if bad size
        raise ValueError('needle dimension(s) exceed the haystack image or region dimensions')

    # get all matches at once, credit: https://stackoverflow.com/questions/7670112/finding-a-subimage-inside-a-numpy-image/9253805#9253805
    result = cv2.matchTemplate(haystack_image, needle_image, cv2.TM_CCOEFF_NORMED)
    match_indices = np.arange(result.size)[(result > confidence).flatten()]
    matches = np.unravel_index(match_indices[:limit], result.shape)

    if len(matches[0]) == 0:
        return

    # use a generator for API consistency:
    matchx = matches[1]  # vectorized
    matchy = matches[0]
    # return matchx, matchy, needle_width, needle_height
    for x, y in zip(matchx, matchy):
        yield Box(x, y, needle_width, needle_height)


def locate(needle_image, haystack_image, limit=10000, confidence=0.999):
    results = tuple(locate_all(needle_image, haystack_image, limit, confidence))
    if len(results) > 0:
        return results[0]


def locate_all_on_screen(im_name, region=None, confidence=0.999, target_color=None, color_tolerance=0):
    needle_image = cv2.imread(im_name)
    haystack_image = screencapture(region=region)
    if target_color is not None:
        needle_image = filter_color(needle_image, target_color, color_tolerance)
        haystack_image = filter_color(haystack_image, target_color, color_tolerance)
        # lb = np.clip(np.array(target_color) - color_tolerance, 0, 255)
        # ub = np.clip(np.array(target_color) + color_tolerance, 0, 255)
        # needle_mask = cv2.inRange(needle_image, lb, ub)
        # haystack_mask = cv2.inRange(haystack_image, lb, ub)
        # needle_image = cv2.bitwise_and(needle_image, needle_image, mask=needle_mask)
        # haystack_image = cv2.bitwise_and(haystack_image, haystack_image, mask=haystack_mask)
    relative_results = tuple(locate_all(needle_image, haystack_image, confidence=confidence))
    absolute_results = []
    if region is None:
        region = (0, 0, 0, 0)
    for result in relative_results:
        absolute_results.append(Box(int(result[0]) + region[0], int(result[1]) + region[1], result[2], result[3]))
    return absolute_results


def locate_on_screen(im_name, region=None, confidence=0.999, target_color=None, color_tolerance=0):
    results = locate_all_on_screen(im_name, region, confidence, target_color, color_tolerance)
    return results[0] if len(results) > 0 else None


def locate_center_on_screen(im_name, region=None, confidence=0.999, target_color=None):
    result = locate_on_screen(im_name, region, confidence, target_color)
    return Position(result.left + int(result.width / 2), result.top + int(result.height / 2))


def get_rgb_at(x, y, im_name=None):
    if im_name:
        return cv2.imread(im_name)[y, x, ::-1]
    return screenshot(region=(x, y, 1, 1))[0, 0, ::-1]


def gen_mask(im, color, tolerance):
    lb = np.clip(np.array(color) - tolerance, 0, 255)
    ub = np.clip(np.array(color) + tolerance, 0, 255)
    return cv2.inRange(im, lb, ub)


def filter_color(im, color, tolerance):
    mask = gen_mask(im, color, tolerance)
    return cv2.bitwise_and(im, im, mask=mask)


def pixel_match_color(x, y, expected_RGB_color, tolerance=0):
    pix = get_rgb_at(x, y)
    assert len(expected_RGB_color) == 3
    expected = np.array(expected_RGB_color)
    return (np.abs(pix - expected) < tolerance).all()


if __name__ == '__main__':
    # import time
    # n_image = 1
    # for _ in range(3):
    #     screencapture(region=(100,100,2,2))
    # # time.sleep(1)
    # t0 = time.perf_counter()
    # while time.perf_counter() - t0 < 0.2:
    #     print("start", time.perf_counter() - t0)
    #     screencapture(region=(100, 100, 500, 300))
    #     print("end", time.perf_counter() - t0)
    #     n_image += 1
    # screencapture("test002.png", (100, 100, 500, 300))
    screenshot("screenshot_test.png")
    screencapture("screencapture_test.png")
    screengrab("screengrab_text.png")