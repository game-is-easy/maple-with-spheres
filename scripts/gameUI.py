import json
import time

from scripts.locate_im import *
from scripts.ocr import ocr_colored_digits
from datetime import datetime
import subprocess
import os.path

DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
RESOURCES_DIR = os.path.join(DIR, "resources")

MINIMAP_POSITION_DEFAULT = (30, 342)


def find_minimap_ui(map_name, img=None):
    if img is None:
        x, y, _, _ = locate_on_screen(os.path.join(DIR, f"resources/{map_name}.png"), region=get_window_region(), confidence=0.8)
    else:
        x, y, _, _ = locate(os.path.join(DIR, f"resources/{map_name}.png"), img, confidence=0.9)
    return x - 20, y + 66


def extract_minimap_region(map_name="arteria", img=None, search_frac=1, blur_kernel=(7, 7),
                           canny_params=(30, 100), im_show=False):
    if img is None:
        minimap_ui_x, minimap_ui_y = find_minimap_ui(map_name)
        img = screencapture(region=(minimap_ui_x, minimap_ui_y, 1000, 800))
    else:
        minimap_ui_x, minimap_ui_y = find_minimap_ui(map_name, img)
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
            if 1.0 < ar < 3.0 and area > 20000:
                if area > best_area:
                    best_area = area
                    best = (x, y, wc, hc)

    if best:
        x, y, wc, hc = best
        if im_show:
            cv2.rectangle(img, (x, y), (x + wc, y + hc), (0, 0, 255), 3)
            cv2.namedWindow('minimap detected', cv2.WINDOW_AUTOSIZE)
            cv2.imshow('minimap detected', img)
        return Box(x + minimap_ui_x, y + minimap_ui_y, wc, hc)


def extract_symbol_on_minimap(symbol_name, symbol_radius=5, color=None,
                              location=None, im_name=None, tolerance=10):
    # if im_name is None:
    #     im = screenshot()
    # else:
    #     im = cv2.imread(im_name)
    im = screencapture()
    minimap_region = extract_minimap_region()
    if minimap_region:
        x, y, w, h = minimap_region
        im = im[y:y + h, x:x + w]
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
        xc -= x
        yc -= y
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


def get_current_position_of(symbol, minimap_region=None, map_name=None, confidence=0.8, attempts=3):
    if attempts <= 0:
        return None
    if minimap_region is None:
        minimap_region = extract_minimap_region(map_name)
    with open(os.path.join(RESOURCES_DIR, "symbol_colors.json"), 'r') as f:
        symbol_colors = json.load(f)
    color = symbol_colors.get(symbol)
    im_name = os.path.join(RESOURCES_DIR, f"{symbol}.png")
    symbol_box = locate_on_screen(im_name, minimap_region, confidence, color, 5)
    # while symbol_box is None and confidence > 0.5:
    #     symbol_box = locate_on_screen(im_name, minimap_region, confidence - 0.1, color)
    if symbol_box is not None:
        x = int(symbol_box.left - minimap_region.left + int(symbol_box.width / 2))
        y = int(symbol_box.top - minimap_region.top + int(symbol_box.height / 2))
        if symbol == "rune":
            y += 1
        # return Position(int(symbol_box.left - minimap_region.left + int(symbol_box.width / 2)),
        #                 int(symbol_box.top - minimap_region.top + int(symbol_box.height / 2)))
        return Position(x, y)
    time.sleep(1)
    return get_current_position_of(symbol, minimap_region, confidence=confidence * 0.9, attempts=attempts - 1)


def is_overlap_x(current_position, target_position, tolerance=2, tolerance_left=None, tolerance_right=None):
    tolerance_left = tolerance_left or tolerance
    tolerance_right = tolerance_right or tolerance
    # if tolerance_left is not None and tolerance_right is not None:
    #     return target_position.x - tolerance_left <= current_position.x <= target_position.x + tolerance_right
    return target_position.x - tolerance_left <= current_position.x <= target_position.x + tolerance_right
    # return abs(current_position.x - target_position.x) <= tolerance


def is_overlap_y(position1, position2, tolerance=2):
    return abs(position1.y - position2.y) <= tolerance


def is_overlap(position1, position2, tolerance_x=2, tolerance_y=2, tolerance_x_left=None, tolerance_x_right=None):
    return is_overlap_x(position1, position2, tolerance_x, tolerance_x_left, tolerance_x_right) and is_overlap_y(position1, position2, tolerance_y)


def current_at_position(position, minimap_region=None, tolerance_x=2, tolerance_y=2, tolerance_x_left=None, tolerance_x_right=None):
    return is_overlap(get_current_position_of("player", minimap_region), position, tolerance_x, tolerance_y, tolerance_x_left, tolerance_x_right)


def check_skill_use_popup():
    dialog_check_im_path = os.path.join(RESOURCES_DIR, "cancel.png")
    return locate_on_screen(dialog_check_im_path, region=(1300, 940, 160, 50), confidence=0.9)


def detect_skill_region(skill_name, save=False, unreliable_memory_copy=False):
    if os.path.exists(os.path.join(DIR, f"resources/{skill_name}.png")):
        regions = locate_all_on_screen(os.path.join(DIR, f"resources/{skill_name}.png"), region=(1400, 1300, 1160, 280), confidence=0.9)
        if not regions:
            return None
        if unreliable_memory_copy and len(regions) == 2:
            skill_name = f"{skill_name}2"
            region = tuple(regions[1])
        else:
            region = tuple(regions[0])
        if save:
            if os.path.exists(os.path.join(DIR, "resources/skill_icon_region.json")):
                with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'r') as f:
                    data = json.load(f)
            else:
                data = {}
            data.update({skill_name: region})
            with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'w') as f:
                json.dump(data, f)
        return region


def get_skill_region(skill_name):
    with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'r') as f:
        data = json.load(f)
    return data.get(skill_name)


def check_frac_cd_to_up(skill_name, skill_im):
    brightness = float(cv2.cvtColor(skill_im, cv2.COLOR_BGR2GRAY).mean())
    skill_off_cd_im = cv2.imread(os.path.join(DIR, f"resources/{skill_name}.png"))
    max_brightness = float(cv2.cvtColor(skill_off_cd_im, cv2.COLOR_BGR2GRAY).mean())
    skill_on_cd_im = cv2.imread(os.path.join(DIR, f"resources/{skill_name}_on_cd.png"))
    min_brightness = float(cv2.cvtColor(skill_on_cd_im, cv2.COLOR_BGR2GRAY).mean())
    return (max_brightness - brightness) / (max_brightness - min_brightness) * 0.95


def check_time_to_up(skill_name, skill_region, skill_cd):
    """
    :param skill_name: e.g.: 'infinity'
    :param skill_region: (x, y, w, h)
    :param skill_cd: int
    :return: 0 if up; 1 if ≤5 seconds; 6-60 accurate; 60+ estimate.
    """
    x, y, w, h = skill_region
    window_pos_x, window_pos_y = get_window_pos()
    window_pos_y -= 144
    abs_skill_region = (x + window_pos_x, y + window_pos_y, w, h)
    skill_im = screencapture(region=abs_skill_region)
    est_frac_cd = check_frac_cd_to_up(skill_name, skill_im)
    # print(f"DEBUG: cd is {est_frac_cd:.4f}")
    if est_frac_cd > 0.2:
        result = ocr_colored_digits(skill_im[14:45, 14:45])
        if result and result.isdigit():
            return int(result) + 1
        return int(est_frac_cd * skill_cd)
    elif est_frac_cd < 0.025:
        # print(f"DEBUG: cd is {est_frac_cd} of total.")
        return 0
    return 1


def get_window_pos():
    pos = subprocess.run(["osascript", "-e",
                          'tell application "System Events" to tell process "Parallels Desktop" to get position of window 1'],
                         stdout=subprocess.PIPE)
    x0, y0 = [int(n) for n in pos.stdout.decode("utf-8").strip().split(", ")]
    return x0 * 2, y0 * 2 + 76


def get_window_size():
    pos = subprocess.run(["osascript", "-e",
                          'tell application "System Events" to tell process "Parallels Desktop" to get size of window 1'],
                         stdout=subprocess.PIPE)
    w, h = [int(n) for n in pos.stdout.decode("utf-8").strip().split(", ")]
    return w * 2, h * 2


def get_window_region():
    return *get_window_pos(), *get_window_size()


def get_active_application():
    script = '''tell application "System Events"
    set frontmostProcessName to name of the first process whose frontmost is true
    set processBid to get the bundle identifier of process frontmostProcessName
    set applicationName to file of (application processes where bundle identifier is processBid)
end tell
return applicationName as string'''

    try:
        result_bytes = subprocess.check_output(["osascript", "-e", script])
        result_string = result_bytes.decode('utf-8').strip()
        app_name = result_string[result_string.find("Applications:") + len("Applications:"):result_string.find(".app")]
        if "Launcher" in app_name:
            app_name = app_name.replace("Launcher", '').strip()
        return app_name
    except subprocess.CalledProcessError as e:
        log(f"Error executing AppleScript: {e}")
        return None


def activate_window(window_name="Parallels Desktop"):
    subprocess.run(["osascript", "-e", f'tell application "{window_name}" to activate'])


def preview_image(im, delay):
    cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
    cv2.imshow('image', im)
    cv2.waitKey(delay)
    cv2.destroyAllWindows()


def log(contents):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {contents}")


if __name__ == '__main__':
    # subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    time.sleep(0.5)
    # skill_name = "infinity2"
    # print(check_frac_cd_to_up(skill_name, screencapture(region=get_skill_region(skill_name))))
    # x0, y0 = get_window_pos()
    # w, h = get_window_size()
    # x1 = x0 + w
    # y1 = y0 + h
    # screenshot("testinf.png", region=get_skill_region("infinity"))
    # screencapture("new_ui.png")

    minimap_region = extract_minimap_region("Carcion")
    # minimap_region = extract_minimap_region("carcion")
    print(minimap_region)
    # extract_symbol_on_minimap("player", symbol_radius=3, location=(3192, 1904))

    # import time
    #
    # while 1:
    #     print(get_current_position_of("player", minimap_region))
    #     # print(is_overlap_y(get_current_position_of("player", minimap_region), Position(106, 178)))
    #     time.sleep(1)

    # print(get_window_region())
    # x1 = x0 + w
    # y1 = y0 + h
    # screencapture("test.png")

    # skill_name = "guild_critdmg"
    # res = locate_on_screen(os.path.join(DIR, f"resources/{skill_name}.png"), region=(1400, 1280, 1160, 300), confidence=0.9)
    # with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'r') as f:
    #     data = json.load(f)
    # data.update({skill_name: res})
    # with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'w') as f:
    #     json.dump(data, f)

    res = locate_all_on_screen(os.path.join(DIR, "resources/infinity.png"), confidence=0.9)
    regions = []
    for r in res:
        regions.append([])
        for n in r:
             regions[-1].append(int(n))
    print(regions)
    # d = {"infinity": regions[0],
    #      "infinity2": regions[1]}
    # with open(os.path.join(DIR, "resources/skill_icon_region.json"), 'wr') as f:
    #     originals = json.load(f)
    #     d.update(originals)
    #     json.dump(d, f)
    # import subprocess
    # subprocess.run(["osascript", "-e",
    #                 'tell application "Parallels Desktop" to activate'])
    # time.sleep(2)
    # screenshot("cd03.png")
    # skill_name = "infinity"
    # x,y,w,h = get_skill_region("infinity2")
    # window_pos_x, window_pos_y = get_window_pos()
    # window_pos_y -= 144
    # abs_skill_region = (x + window_pos_x, y + window_pos_y, w, h)
    # print(abs_skill_region)
    # time.sleep(2)
    # t0 = time.perf_counter()
    # for t in range(1, 185):
    #     # skill_im = screenshot(f"cd_inf_{t}.png", region=skill_region)
    #     skill_im = screenshot(region=skill_region)
    #     print(181 - int(time.perf_counter() - t0), end=': ')
    #     print(check_time_to_up(skill_name, skill_region, 180))
    #     time.sleep(t - time.perf_counter() + t0)
