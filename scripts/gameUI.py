import json

from scripts.locate_im import *
from datetime import datetime
import subprocess
import os.path

DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RESOURCES_DIR = os.path.join(DIR, "resources")

INF1_KEY_REGION = Box(2352, 1434, 60, 60)
INF2_KEY_REGION = Box(2422, 1434, 60, 60)


def extract_minimap_region(img=None, search_frac=0.3, blur_kernel=(7, 7),
                           canny_params=(30, 100), im_show=False):
    if img is None:
        img = screenshot()
    h, w = img.shape[:2]

    # 1) only search in the upper-left quarter (or whatever)
    search = img[0:int(h * search_frac), 0:int(w * search_frac)]
    gray = cv2.cvtColor(search, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, blur_kernel, 0)
    edges = cv2.Canny(blur, canny_params[0], canny_params[1])

    # 2) find contours
    cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0

    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            x, y, wc, hc = cv2.boundingRect(approx)
            area = wc * hc
            ar = wc / float(hc)
            # 3) filter by a “minimap‑ish” aspect ratio (e.g. ~3:1)
            if 1.5 < ar < 5.0 and area > 2000:
                if area > best_area:
                    best_area = area
                    best = (x, y, wc, hc)

    if best:
        x, y, wc, hc = best
        if im_show:
            cv2.rectangle(img, (x, y), (x + wc, y + hc), (0, 0, 255), 3)
            cv2.namedWindow('minimap detected', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('minimap detected', img)
        return Box(x, y, wc, hc)


def extract_symbol_on_minimap(symbol_name, symbol_radius=5, color=None,
                              location=None, im_name=None, tolerance=10):
    # if im_name is None:
    #     im = screenshot()
    # else:
    #     im = cv2.imread(im_name)
    im = screenshot()
    minimap_region = extract_minimap_region(im, im_show=False)
    if minimap_region:
        x, y, w, h = minimap_region
        im = im[0:y + h, 0:x + w]
    else:
        log("minimap detection fails")
        return
    if color is None:
        if location is None or \
                location[0] > x + w - symbol_radius - 1 or location[
            1] > y + h - symbol_radius - 1 or \
                location[0] < symbol_radius or location[1] < symbol_radius:
            return
        xc, yc = location
        pixels = im[yc - symbol_radius:yc + symbol_radius,
                 xc - symbol_radius:xc + symbol_radius]
        pixels = pixels.reshape(-1, 3)
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)
        color = unique_colors[np.argmax(counts)].astype(int)
        if os.path.exists(os.path.join(RESOURCES_DIR, "symbol_colors.json")):
            with open(os.path.join(RESOURCES_DIR, "symbol_colors.json"), 'r') as f:
                symbol_colors = json.load(f)
            symbol_colors.update({symbol_name: color.tolist()})
        else:
            symbol_colors = {symbol_name: color.tolist()}
        with open(os.path.join(RESOURCES_DIR, "symbol_colors.json"), 'w') as f:
            json.dump(symbol_colors, f)

    mask = np.all(np.abs(im.astype(int) - np.array(color)) <= tolerance,
                  axis=2)
    # mask = gen_mask(im, color, tolerance)
    coords = np.column_stack(np.where(mask))
    if coords.size > 0:
        # yc, xc = coords.mean(axis=0)
        yc, xc = np.median(coords, axis=0)
        # x0 = int(round(xc - symbol_radius * 2))
        x0 = int(xc - symbol_radius * 2 + 1)
        # y0 = int(round(yc - symbol_radius * 2))
        y0 = int(yc - symbol_radius * 2 + 1)
        s = symbol_radius * 4
        im = im[y0:y0 + s, x0:x0 + s]
        filtered_im = filter_color(im, color, 10)
        cv2.imwrite(os.path.join(RESOURCES_DIR, f'{symbol_name}.png'),
                    filtered_im)


def get_current_position_of(symbol, minimap_region=None):
    if minimap_region is None:
        minimap_region = extract_minimap_region()
    with open(os.path.join(RESOURCES_DIR, "symbol_colors.json"), 'r') as f:
        symbol_colors = json.load(f)
    color = symbol_colors.get(symbol)
    im_name = os.path.join(RESOURCES_DIR, f"{symbol}.png")
    symbol_box = locate_on_screen(im_name, minimap_region, 0.8, color)
    if symbol_box is not None:
        return Position(int(symbol_box.left - minimap_region.left + int(symbol_box.width / 2)),
                        int(symbol_box.top - minimap_region.top + int(symbol_box.height / 2)))


def is_overlap_x(position1, position2, tolerance=2):
    return abs(position1[0] - position2[0]) <= tolerance


def is_overlap_y(position1, position2, tolerance=2):
    return abs(position1[1] - position2[1]) <= tolerance


def is_overlap(position1, position2, tolerance_x=2, tolerance_y=2):
    return is_overlap_x(position1, position2, tolerance_x) and is_overlap_y(position1, position2, tolerance_y)


def current_at_position(position, minimap_region=None, tolerance_x=2, tolerance_y=2):
    return is_overlap(get_current_position_of("player", minimap_region), position, tolerance_x, tolerance_y)


def check_cd(skill):
    pass


def get_window_pos():
    pos = subprocess.run(["osascript", "-e",
                          'tell application "System Events" to tell process "Parallels Desktop" to get position of window 1'],
                         stdout=subprocess.PIPE)
    x0, y0 = [int(n) for n in pos.stdout.decode("utf-8").strip().split(", ")]
    return x0 * 2, y0 * 2


def get_window_size():
    pos = subprocess.run(["osascript", "-e",
                          'tell application "System Events" to tell process "Parallels Desktop" to get size of window 1'],
                         stdout=subprocess.PIPE)
    w, h = [int(n) for n in pos.stdout.decode("utf-8").strip().split(", ")]
    return w * 2, h * 2


def preview_image(im, delay):
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('image', im)
    cv2.waitKey(delay)
    cv2.destroyAllWindows()


def log(contents):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {contents}")


if __name__ == '__main__':
    # minimap_region = extract_minimap_region()
    # extract_symbol_on_minimap("rune", symbol_radius=3, location=(83*2,163*2))
    import time

    # while 1:
    #     print(get_current_position_of("player", minimap_region))
    #     # print(is_overlap_y(get_current_position_of("player", minimap_region), Position(106, 178)))
    #     time.sleep(1)
    # x0, y0 = get_window_pos()
    # w, h = get_window_size()
    # x1 = x0 + w
    # y1 = y0 + h
    # screenshot("test002.png")
    res = locate_all_on_screen(os.path.join(DIR, "resources/infinity.png"), confidence=0.9)
    regions = []
    for r in res:
        regions.append([])
        for n in r:
             regions[-1].append(int(n))
    print(regions)
    d = {"infinity": regions[0],
         "infinity2": regions[1]}
    with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'w') as f:
        json.dump(d, f)

