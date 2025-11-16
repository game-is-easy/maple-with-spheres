from pynput import keyboard
import numpy as np


mode = "prl"

if mode == "prl":
    from keyInject import *

    KEY_BLINK = PRL['V']
    KEY_JUMP = PRL['C']
    KEY_TS = PRL['4']
    KEY_ERDA = PRL['E']
    KEY_SPHERE = PRL['R']
    KEY_1 = PRL['1']
    KEY_BUFF = PRL['6']
    KEY_BUFF2 = PRL['7']
    KEY_ATT = PRL['X']
    KEY_ATT2 = PRL['Z']
    KEY_ATT3 = PRL['SPACE']
    KEY_INTERACT = PRL['B']
    KEY_COMBO = PRL["LEFT_ALT"]
    KEY_GUILD_BOSS = PRL['8']
    KEY_GUILD_DMG = PRL['9']
    KEY_GUILD_CRITDMG = PRL['0']
    KEY_A = PRL['A']
    KEY_S = PRL['S']
    KEY_UP_ARROW = PRL["UP"]
    KEY_LEFT_ARROW = PRL["LEFT"]
    KEY_RIGHT_ARROW = PRL["RIGHT"]
    KEY_DOWN_ARROW = PRL["DOWN"]
    KEY_ECHO = PRL["F6"]
    KEY_ESC = PRL["ESCAPE"]

    def exec_key_sequence(seq):
        keySequence(seq)

else:
    from quartzKeys import keyDown, keyUp, keyPress
    from keyCodes import *

    KEY_BLINK = KEY_V
    KEY_JUMP = KEY_C
    KEY_TS = KEY_4
    KEY_ERDA = KEY_E
    KEY_SPHERE = KEY_R
    KEY_BUFF = KEY_6
    KEY_BUFF2 = KEY_7
    KEY_ATT = KEY_X
    KEY_ATT2 = KEY_Z
    KEY_ATT3 = KEY_SPACE
    KEY_INTERACT = KEY_B
    KEY_COMBO = KEY_LEFT_ALT
    KEY_GUILD_BOSS = key_codes['8']
    KEY_GUILD_DMG = key_codes['9']
    KEY_GUILD_CRITDMG = key_codes['0']
    KEY_ECHO = key_codes['f6']

    def exec_key_sequence(seq):
        for e in seq:
            if e["event"] == "press":
                keyDown(e["key"])
            else:
                keyUp(e["key"])
            if e.get("delay"):
                time.sleep(e["delay"] / 1000)


def add_event_to_json(j, key_code, event_type, delay):
    # press all, release in reverse
    j.append({"key": key_code, "event": event_type, "delay": int(delay * 1000)})
    return j


def get_keyDown_seq(key_code, delay=None):
    if delay:
        delay = float(np.max([delay, smallest_delay()]))
        return [{"key": key_code, "event": "press", "delay": int(delay * 1000)}]
    else:
        return [{"key": key_code, "event": "press"}]


def get_keyUp_seq(key_code, delay=None):
    if delay:
        delay = float(np.max([delay, smallest_delay()]))
        return [{"key": key_code, "event": "release", "delay": int(delay * 1000)}]
    else:
        return [{"key": key_code, "event": "release"}]


def get_keyPress_seq(key_code, duration=0.05, delay_after=0.0):
    duration = float(np.max([duration, smallest_delay()]))
    delay_after = float(np.max([delay_after, smallest_delay()]))
    return [
        {"key": key_code, "event": "press", "delay": int(duration * 1000)},
        {"key": key_code, "event": "release", "delay": int(delay_after * 1000)}
    ]


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
    seq = []
    for char in wsad.strip().lower():
        try:
            seq += short_press(WASD_TO_ARROW[char], 2, False)
        except:
            print(f"unable to convert {char}")
            return False
    exec_key_sequence(seq)


def random_norm(mu, sigma, min=0.001, max=None):
    x = np.random.default_rng().normal(loc=mu, scale=sigma, size=1)[0]
    # if min is not None:
    x = np.max([min, x])
    if max is not None:
        x = np.min([max, x])
    return float(x)


def random_unif(max, min=0):
    return np.random.random() * (max - min) + min


def smallest_delay():
    return 0.03 + random_unif(0.01)


def blink_with_key(key_code, arrow_key_code, delay_after_rep=0, execute=True):
    time_key_up = random_norm(0.1024, 0.0186, smallest_delay(), 0.15 - smallest_delay())
    time_blink_down = random_norm(0.1894, 0.0351, smallest_delay(), 0.3 - smallest_delay())
    time_blink_press = random_norm(0.0997, 0.0137, smallest_delay(), 0.15 - smallest_delay())
    time_blink_up = time_blink_down + time_blink_press
    time_arrow_down = random_norm(0.1069, 0.0417, smallest_delay(), time_blink_down - smallest_delay())
    time_arrow_up = random_norm(0.55, 0.0756, 0.45 + smallest_delay(), 0.66 - smallest_delay())
    if time_key_up < time_arrow_down:
        seq = get_keyDown_seq(key_code, time_key_up)
        seq.extend(get_keyUp_seq(key_code, time_arrow_down - time_key_up))
        seq.extend(get_keyDown_seq(arrow_key_code, time_blink_down - time_arrow_down))
        seq.extend(get_keyPress_seq(KEY_BLINK, time_blink_press, time_arrow_up - time_blink_up))
        if delay_after_rep > 0:
            seq.extend(get_keyUp_seq(arrow_key_code, get_short_delay(delay_after_rep)))
        else:
            seq.extend(get_keyUp_seq(arrow_key_code))
    else:
        seq = get_keyDown_seq(key_code, time_arrow_down)
        if time_key_up < time_blink_down:
            seq.extend(get_keyDown_seq(arrow_key_code, time_key_up - time_arrow_down))
            seq.extend(get_keyUp_seq(key_code, time_blink_down - time_key_up))
            seq.extend(get_keyPress_seq(KEY_BLINK, time_blink_press, time_arrow_up - time_blink_up))
        else:
            seq.extend(get_keyDown_seq(arrow_key_code, time_blink_down - time_arrow_down))
            keyDown(KEY_BLINK)
            if time_key_up < time_blink_up:
                seq.extend(get_keyDown_seq(KEY_BLINK, time_key_up - time_blink_down))
                seq.extend(get_keyUp_seq(key_code, time_blink_up - time_key_up))
                seq.extend(get_keyUp_seq(KEY_BLINK, time_arrow_up - time_blink_up))
            else:
                seq.extend(get_keyPress_seq(KEY_BLINK, time_blink_press, time_key_up - time_blink_up))
                seq.extend(get_keyUp_seq(key_code, time_arrow_up - time_key_up))
        seq.extend(get_keyUp_seq(arrow_key_code, get_short_delay(delay_after_rep)))
    seq.extend(get_keyUp_seq(arrow_key_code, smallest_delay()))  # test
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def hold_press(hold_key_code, press_key_code, hold_duration=0.2, delay_after=0.0, execute=True):
    # hold_duration = random_norm(hold_duration, hold_duration * 0.2)
    press_key_duration = get_short_delay()
    delay_before_press = get_short_delay()
    hold_duration += delay_before_press
    delay_after = get_precise_delay(delay_after) if delay_after > 0 else delay_after
    seq = get_keyDown_seq(hold_key_code, delay_before_press)
    if press_key_duration + delay_before_press < hold_duration:
        delay_after_press = float(np.max([hold_duration - press_key_duration - delay_before_press, smallest_delay()]))
        seq.extend(get_keyPress_seq(press_key_code, press_key_duration, delay_after_press))
        seq.extend(get_keyUp_seq(hold_key_code, smallest_delay()))
    else:
        seq.extend(get_keyDown_seq(press_key_code, float(np.max([hold_duration - delay_before_press, smallest_delay()]))))
        seq.extend(get_keyUp_seq(hold_key_code, float(np.max([press_key_duration + delay_before_press - hold_duration, smallest_delay()]))))
        seq.extend(get_keyUp_seq(press_key_code, smallest_delay()))
    seq.extend(get_keyUp_seq(hold_key_code, delay_after))
    # if delay_after > 0:
    #     seq.append({"delay": int(get_precise_delay(delay_after) * 1000)})
        # precise_delay(delay_after)
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def blink(arrow_key_code, delay_after=0.0, execute=True):
    arrow_key_duration = random_norm(0.4, 0.04, 0.3)
    return hold_press(arrow_key_code, KEY_BLINK, arrow_key_duration, delay_after, execute=execute)


def down_jump(delay_after=0.0, execute=True):
    arrow_key_duration = random_norm(0.4, 0.03, 0.3, 0.5)
    return hold_press(KEY_DOWN_ARROW, KEY_JUMP, arrow_key_duration, delay_after, execute=execute)


def down_blink(delay_after=0.0, execute=True):
    return blink(KEY_DOWN_ARROW, delay_after, execute=execute)


def jump_seq_combo(combo_seq, hold_key_code=None, delay_after_rep=0, execute=True):
    duration_jump_press = random_norm(0.1, 0.02, 0.04, 0.16)
    delay_after_jump = float(np.max([random_norm(0.2, 0.02, duration_jump_press, 0.25) - duration_jump_press, smallest_delay()]))
    delay_before_combo = random_norm(0.36, 0.02, 0.3, 0.42) - delay_after_jump - duration_jump_press
    if hold_key_code is not None:
        seq = get_keyPress_seq(KEY_JUMP, duration_jump_press, delay_after_jump)
        seq.extend(get_keyDown_seq(hold_key_code, delay_before_combo))
        seq.extend(combo_seq)
        seq.extend(get_keyUp_seq(hold_key_code, get_short_delay(delay_after_rep)))
    else:
        seq = get_keyPress_seq(KEY_JUMP, duration_jump_press, delay_after_jump + delay_before_combo)
        seq.extend(combo_seq)
    if hold_key_code is not None:
        seq.extend(get_keyUp_seq(hold_key_code))
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def jump_direction_combo(direction_key_code, combo_key_code, delay_after_rep=0, execute=True):
    # duration_jump_press = random_norm(0.1, 0.02, 0.04, 0.16)
    # delay_after_jump = float(np.max([random_norm(0.2, 0.02, duration_jump_press, 0.25) - duration_jump_press, smallest_delay()]))
    # delay_before_key = random_norm(0.36, 0.02, 0.3, 0.42) - delay_after_jump - duration_jump_press
    # seq = get_keyPress_seq(KEY_JUMP, duration_jump_press, delay_after_jump)
    # seq.extend(get_keyDown_seq(direction_key_code, delay_before_key))
    # seq.extend(short_press(combo_key_code, 1, execute=False))
    # seq.extend(get_keyUp_seq(direction_key_code, get_short_delay(delay_after_rep)))
    combo_seq = short_press(combo_key_code, 1, execute=False)
    return jump_seq_combo(combo_seq, hold_key_code=direction_key_code, delay_after_rep=delay_after_rep, execute=execute)
    # if execute:
    #     exec_key_sequence(seq)
    # else:
    #     return seq


def jump_up_combo(combo_key_code, execute=True):
    return jump_direction_combo(KEY_UP_ARROW, combo_key_code, execute)


def jump_up_seq_combo(combo_seq, delay_after_rep=5, execute=True):
    return jump_seq_combo(combo_seq, hold_key_code=KEY_UP_ARROW, delay_after_rep=delay_after_rep, execute=execute)


def up_jump(delay_after_rep=8, execute=True):
    return jump_up_seq_combo([], delay_after_rep=delay_after_rep, execute=execute)


def up_jump_blink(delay_after_rep=5, execute=True):
    delay_after_up_jump = random_norm(0.4, 0.02, 0.35, 0.45)
    seq = get_keyPress_seq(KEY_JUMP, get_short_delay(), delay_after_up_jump)
    seq.extend(short_press(KEY_BLINK, delay_after_rep=1, execute=False))
    return jump_seq_combo(seq, hold_key_code=KEY_UP_ARROW, delay_after_rep=delay_after_rep, execute=execute)


def random_action(*actions):
    actions = list(actions)
    n = int(np.random.random() * len(actions))
    return actions[n]


def action_with_prob(action, prob):
    if np.random.random() < prob:
        return action
    else:
        def f(*args, execute=True):
            return None if execute else []
        return f


def get_short_delay(rep=1):
    delay = 0.0
    for _ in range(rep):
        delay += random_norm(0.1, 0.015, 0.06, 0.14)
    return delay


def short_delay(rep=1):
    time.sleep(get_short_delay(rep))


def get_random_delay(duration, stddev=0.02, lb=0.01, ub=None):
    if ub is None or ub < duration:
        ub = np.inf
    return random_norm(duration, stddev, lb, ub)


def delay(duration, stddev=0.02, lb=0.01, ub=None):
    time.sleep(get_random_delay(duration, stddev, lb, ub))


def get_precise_delay(duration, stddev=0.01, frac_tolerance=0.2):
    return get_random_delay(duration, stddev, duration * (1 - frac_tolerance), duration * (1 + frac_tolerance))


def precise_delay(duration, stddev=0.01, frac_tolerance=0.2):
    time.sleep(get_precise_delay(duration, stddev, frac_tolerance))


def short_press(key_code, delay_after_rep=0, execute=True):
    if delay_after_rep > 0:
        delay_after = get_short_delay(delay_after_rep)
        seq = get_keyPress_seq(key_code, random_norm(0.1, 0.02, 0.06, 0.15), delay_after)
    else:
        seq = get_keyPress_seq(key_code, random_norm(0.1, 0.02, 0.06, 0.15))
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def multi_press(key_code, n_press=2, delay_after_rep=0, execute=True):
    if delay_after_rep > 0:
        delay_after = get_short_delay(delay_after_rep)
    else:
        delay_after = 0
    seq = []
    for _ in range(n_press - 1):
        press_duration = random_norm(0.055, 0.012, smallest_delay())
        delay_between = random_norm(0.1, 0.005)
        seq.extend(get_keyPress_seq(key_code, press_duration, delay_between))
    press_duration = random_norm(0.055, 0.012, smallest_delay())
    seq.extend(get_keyPress_seq(key_code, press_duration, delay_after))
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


if __name__ == '__main__':
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    time.sleep(0.3)
    # while 1:
    #     delay_rep = int(np.random.random() * 3) + 1
    #     short_press(PRL['SPACE'], delay_after_rep=delay_rep)
    # print(blink_with_key(KEY_X, KEY_RIGHT_ARROW))
    # print(hold_press(KEY_DOWN_ARROW, KEY_C))
    # print(jump_up_combo(KEY_BLINK))
    # t0 = time.time()
    # print(wait_key('z'))
    # print('dd')
    # print(timyye.time() - t0)
    # short_press(KEY_JUMP)
    # blink_with_key(KEY_ATT, KEY_RIGHT_ARROW)
    # wsad = "wasd"
    # enter_rune_arrows(wsad)

    # 0.125 - 0.175: move by 2
    # 0.175 - 0.2: move by 4
    # 0.2 - 0.24: move by 6
    # 0.24 - 0.28: move by 8
    # keyPress(KEY_RIGHT_ARROW, 0.28)

    from jobs.ExpMages import IL
    from gameUI import get_current_position_of
    time.sleep(0.3)

    character = IL("Top Deck Passage 6")
    rune_position = get_current_position_of("rune", character.map.minimap_region)
    character.go_to(rune_position, need_jump_combo=True, tolerance_x=4, tolerance_y=4, teleport_to_position=True)
    # tp_from = character.map.tp_positions[2]
    # character.enter_door(tp_from, tp_from.next())
