from quartzKeys import keyDown, keyUp, keyPress
from keyCodes import *
from pynput import keyboard
import numpy as np
import time


KEY_BLINK = KEY_V
KEY_JUMP = KEY_C


def wait_key(*keys, max_timeout=10):
    t0 = time.time()
    if len(keys) == 1:
        keys = keys[0]

    def on_press(key):
        try:
            k = key.char.lower()  # normalize to lowercase
        except AttributeError:
            return  # special keys (ctrl, shift, etc.)—ignore
        if k in keys:
            return False

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join(max_timeout)
    if time.time() - t0 > max_timeout:
        return False
    return True


def enter_rune_arrows(wsad):
    for char in wsad.strip().lower():
        try:
            short_press(WSAD_TO_ARROW[char])
            short_delay()
        except:
            print(f"unable to convert {char}")
            break


def random_norm(mu, sigma, min=0.001, max=None):
    x = np.random.default_rng().normal(loc=mu, scale=sigma, size=1)[0]
    if min is not None:
        x = np.max([min, x])
    if max is not None:
        x = np.min([max, x])
    return float(x)


def random_unif(max, min=0):
    return np.random.random() * (max - min) + min


def smallest_delay():
    return 0.01 + random_unif(0.01)


def blink_with_key(key_code, arrow_key_code):
    t0 = time.time()
    keyDown(key_code)
    time_key_up = random_norm(0.1024, 0.0186, smallest_delay(), 0.15 - smallest_delay())
    time_blink_down = random_norm(0.1894, 0.0351, smallest_delay(), 0.3 - smallest_delay())
    time_blink_press = random_norm(0.0997, 0.0137, smallest_delay(), 0.15 - smallest_delay())
    time_blink_up = time_blink_down + time_blink_press
    time_arrow_down = random_norm(0.1069, 0.0417, smallest_delay(), time_blink_down - smallest_delay())
    time_arrow_up = random_norm(0.55, 0.0756, 0.44 + smallest_delay(), 0.66 - smallest_delay())
    if time_key_up < time_arrow_down:
        time.sleep(time_key_up)
        keyUp(key_code)
        time.sleep(time_arrow_down - time_key_up)
        keyDown(arrow_key_code)
        time.sleep(time_blink_down - time_arrow_down)
        keyPress(KEY_BLINK, time_blink_press)
        time.sleep(time_arrow_up - time_blink_up)
        keyUp(arrow_key_code)
    else:
        time.sleep(time_arrow_down)
        keyDown(arrow_key_code)
        if time_key_up < time_blink_down:
            time.sleep(time_key_up - time_arrow_down)
            keyUp(key_code)
            time.sleep(time_blink_down - time_key_up)
            keyDown(KEY_BLINK)
            time.sleep(time_blink_press)
            keyUp(KEY_BLINK)
            time.sleep(time_arrow_up - time_blink_up)
        else:
            time.sleep(time_blink_down - time_arrow_down)
            keyDown(KEY_BLINK)
            if time_key_up < time_blink_up:
                time.sleep(time_key_up - time_blink_down)
                keyUp(key_code)
                time.sleep(time_blink_up - time_key_up)
                keyUp(KEY_BLINK)
                time.sleep(time_arrow_up - time_blink_up)
            else:
                time.sleep(time_blink_press)
                keyUp(KEY_BLINK)
                time.sleep(time_key_up - time_blink_up)
                keyUp(key_code)
                time.sleep(time_arrow_up - time_key_up)
        keyUp(arrow_key_code)
    return time.time() - t0


def hold_press(hold_key_code, press_key_code, hold_duration=0.2, delay_after=0.0):
    t0 = time.time()
    time_hold_key_up = random_norm(hold_duration, hold_duration * 0.2)
    time_press_key_duration = random_norm(0.1, 0.02)
    keyDown(hold_key_code)
    short_delay()
    keyDown(press_key_code)
    t1 = time.time() - t0
    time_press_key_up = t1 + time_press_key_duration
    if time_press_key_up < time_hold_key_up:
        time.sleep(time_press_key_duration)
        keyUp(press_key_code)
        time.sleep(time_hold_key_up - time_press_key_up)
        keyUp(hold_key_code)
    else:
        time.sleep(np.max([time_hold_key_up - t1, smallest_delay()]))
        keyUp(hold_key_code)
        time.sleep(time_press_key_up - time_hold_key_up)
        keyUp(press_key_code)
    if delay_after > 0:
        precise_delay(delay_after)
    return time.time() - t0


def blink(arrow_key_code):
    arrow_key_duration = random_norm(0.3, 0.02, 0.24)
    return hold_press(arrow_key_code, KEY_BLINK, arrow_key_duration)


def down_jump():
    arrow_key_duration = random_norm(0.3, 0.02, 0.24, 0.36)
    return hold_press(KEY_DOWN_ARROW, KEY_JUMP, arrow_key_duration)


def down_blink():
    return blink(KEY_DOWN_ARROW)


def jump_up_combo(combo_key_code):
    t0 = time.time()
    short_press(KEY_JUMP)
    time.sleep(random_norm(0.2, 0.02, time.time() - t0 + 0.01, 0.25) - time.time() + t0)
    keyDown(KEY_UP_ARROW)
    time.sleep(random_norm(0.36, 0.02, 0.3, 0.42) - time.time() + t0)
    keyPress(combo_key_code)
    short_delay()
    keyUp(KEY_UP_ARROW)
    return time.time() - t0


def random_action(*actions):
    actions = list(actions)
    n = int(np.random.random() * len(actions))
    return actions[n]


def action_with_prob(action, prob):
    if np.random.random() < prob:
        return action
    else:
        def f(*args):
            pass
        return f


def short_delay(rep=1):
    for _ in range(rep):
        time.sleep(random_norm(0.1, 0.02, 0.04, 0.16))


def delay(duration, stddev=0.02, lb=0.01, ub=None):
    if ub is None or ub < duration:
        ub = np.inf
    time.sleep(random_norm(duration, stddev, lb, ub))


def precise_delay(duration, stddev=0.01, frac_tolerance=0.2):
    delay(duration, stddev, duration * (1 - frac_tolerance), duration * (1 + frac_tolerance))


def short_press(key_code, exec=True):
    keyPress(key_code, random_norm(0.1, 0.02, 0.02, 0.18))


def exec_key_sequence(seq):
    for e in seq:
        if e["event"] == "press":
            keyDown(e["key"])
        else:
            keyUp(e["key"])
        if e.get("delay"):
            time.sleep(e["delay"])


if __name__ == '__main__':
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    time.sleep(0.3)
    # print(blink_with_key(KEY_X, KEY_RIGHT_ARROW))
    # print(hold_press(KEY_DOWN_ARROW, KEY_C))
    # print(jump_up_combo(KEY_BLINK))
    # t0 = time.time()
    # print(wait_key('z'))
    # print('dd')
    # print(timyye.time() - t0)
    wsad = "wasd"
    enter_rune_arrows(wsad)

