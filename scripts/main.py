import time

from gameUI import *
from comboKeys import *
from discord_bot import start_bot, send_dm_and_wait_for_response


minimap_region = extract_minimap_region()
STARTING_POSITION_SPRING1 = Position(84, 86)
RESET_POSITION_SPRING1 = Position(84, 62)
STARTING_POSITION_SPRING4 = Position(302, 128)
SPEED = 32
BLINK_HORIZONTAL_DISTANCE = 36
BLINK_VERTICAL_DISTANCE = 48
DISTANCE_BETWEEN_BLINKS = 14
TIME_BETWEEN_BLINKS = 0.66

KEY_TS = KEY_4
KEY_ERDA = KEY_E
KEY_SPHERE = KEY_R
KEY_BUFF = KEY_6
KEY_BUFF2 = KEY_7
KEY_ATT = KEY_X
KEY_ATT2 = KEY_Z
KEY_ATT3 = KEY_SPACE
KEY_INTERACT = KEY_B
KEY_GUILD_BOSS = key_codes['8']
KEY_GUILD_DMG = key_codes['9']
KEY_GUILD_CRITDMG = key_codes['0']

INFINITY_REGION = get_skill_region("infinity")
INFINITY2_REGION = get_skill_region("infinity2")
GUILD_CRITDMG_REGION = get_skill_region("guild_critdmg")

DC_USER_ID = 304671527784284160


def move_horizontal_by(arrow_key_code, distance):
    blinks = (distance + DISTANCE_BETWEEN_BLINKS) // (BLINK_HORIZONTAL_DISTANCE + DISTANCE_BETWEEN_BLINKS)
    if blinks == 0:
        if distance <= 2:
            std = distance / SPEED * 0.2
            min = 0.01
        else:
            std = 0.1
            min = 0.02
        keyPress(arrow_key_code, random_norm(distance / SPEED, std, min))
    else:
        keyDown(arrow_key_code)
        short_delay()
        keyDown(KEY_BLINK)
        short_delay()
        time.sleep(TIME_BETWEEN_BLINKS * blinks)
        keyUp(KEY_BLINK)
        short_delay()
        keyUp(arrow_key_code)


def go_to(position, need_jump_down=False, need_jump_combo=False, tolerance_x=2, tolerance_y=2):
    t0 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    while not is_overlap_x(current_position, position, max(2, tolerance_x)) and time.perf_counter() - t0 < 20:
        arrow_key_code = KEY_LEFT_ARROW if current_position.x > position.x else KEY_RIGHT_ARROW
        distance = abs(current_position.x - position.x)
        move_horizontal_by(arrow_key_code, distance)
        short_delay(6)
        current_position = get_current_position_of("player", minimap_region)
    t1 = time.perf_counter()
    while not is_overlap_y(current_position, position, tolerance_y) and time.perf_counter() - t1 < 10:
        if current_position.y < position.y:
            if need_jump_down:
                down_jump()
            else:
                random_action(down_jump, down_blink)()
        elif need_jump_combo:
            jump_up_combo(KEY_BLINK)
        else:
            blink(KEY_UP_ARROW)
        short_delay(6)
        current_position = get_current_position_of("player", minimap_region)
    t2 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    while not is_overlap_x(current_position, position, tolerance_x) and time.perf_counter() - t2 < 3:
        arrow_key_code = KEY_LEFT_ARROW if current_position.x > position.x else KEY_RIGHT_ARROW
        distance = abs(current_position.x - position.x)
        move_horizontal_by(arrow_key_code, distance)
        short_delay(6)
        current_position = get_current_position_of("player", minimap_region)
    return is_overlap(get_current_position_of("player", minimap_region), position, tolerance_x, tolerance_y)


# def place_spheres(arrow_key_code):


def back_to_start_position_spring1():
    if not current_at_position(STARTING_POSITION_SPRING1, minimap_region, 100, 100):
        if current_at_position(Position(292, 108), minimap_region, tolerance_x=1):
            short_press(KEY_UP_ARROW)
            short_delay(10)
        else:
            while not is_overlap_y(get_current_position_of("player", minimap_region), Position(292, 108)):
                random_action(down_blink, down_jump)()
                short_delay(10)
            down_jump()
            short_delay(10)
        down_jump()
        short_delay()
        short_press(KEY_RIGHT_ARROW)
        short_delay(9)
    go_to(STARTING_POSITION_SPRING1, need_jump_down=True, need_jump_combo=True)


def setup_placement_spring1():
    t0 = time.perf_counter()
    minor_setup_spring1(prepare_for_full_setup=True)
    short_delay(3)
    blink_with_key(KEY_ATT2, KEY_RIGHT_ARROW)
    short_delay(5)
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to(Position(250, 86), tolerance_x=10)
    short_delay()
    if np.random.random() < 0.5:
        blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    else:
        short_press(KEY_SPHERE)
        move_horizontal_by(KEY_RIGHT_ARROW, 30)
    go_to(Position(300, 108), tolerance_x=10)
    short_press(KEY_SPHERE)
    short_delay(5)
    short_press(KEY_ATT)
    short_delay(10)
    return time.perf_counter() - t0


def loot_spring1():
    blink_with_key(KEY_ATT, KEY_RIGHT_ARROW)
    short_delay(10)
    blink_with_key(KEY_ATT, KEY_RIGHT_ARROW)
    short_delay(20)
    action_with_prob(blink_with_key, 0.6)(KEY_ATT, KEY_RIGHT_ARROW)
    go_to(Position(240, 86), tolerance_x=30, tolerance_y=30)
    # move_horizontal_by(KEY_RIGHT_ARROW, random_unif(40, 25))
    short_delay()
    short_press(KEY_ATT)
    short_delay(20)
    action_with_prob(short_press, 0.8)(KEY_1)
    short_delay(5)
    # teleport_position = Position(292, 108)
    go_to(Position(292, 108), tolerance_x=30)
    short_delay(10)
    back_to_start_position_spring1()


def minor_setup_spring1(prepare_for_full_setup=False):
    t0 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION_SPRING1):
        if not go_to(STARTING_POSITION_SPRING1, need_jump_down=True, need_jump_combo=True):
            return False
    blink_with_key(KEY_TS, KEY_RIGHT_ARROW)
    short_delay(8)
    short_press(KEY_RIGHT_ARROW)
    short_delay()
    if prepare_for_full_setup:
        blink_with_key(KEY_ERDA, KEY_RIGHT_ARROW)
    else:
        short_press(KEY_ERDA)
    short_delay(5)
    return time.perf_counter() - t0


def back_to_start_position_spring4():
    go_to(STARTING_POSITION_SPRING4)


def setup_placement_spring4():
    t0 = time.perf_counter()
    minor_setup_spring4()
    go_to(Position(326, 68), tolerance_x=1)
    short_press(KEY_UP_ARROW)
    short_delay(3)
    go_to(Position(78, 102), tolerance_x=4)
    short_delay()
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    blink_with_key(KEY_ATT2, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to(Position(164, 100), tolerance_x=4)
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to(Position(230, 68), tolerance_x=4)
    short_delay()
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to(STARTING_POSITION_SPRING4)
    short_delay()
    short_press(KEY_LEFT_ARROW)
    return time.perf_counter() - t0


def minor_setup_spring4():
    t0 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION_SPRING4):
        if not go_to(STARTING_POSITION_SPRING4):
            return False
    blink_with_key(KEY_TS, KEY_UP_ARROW)
    short_delay(10)
    blink(KEY_UP_ARROW)
    short_delay(5)
    short_press(KEY_RIGHT_ARROW)
    short_delay()
    short_press(KEY_RIGHT_ARROW)
    short_delay()
    short_press(KEY_ERDA)
    short_delay(5)
    return time.perf_counter() - t0


def loot_spring4():
    t0 = time.perf_counter()
    keyDown(KEY_LEFT_ARROW)
    short_delay(5)
    # keyPress(KEY_BLINK)
    hold_press(KEY_ATT, KEY_BLINK)
    short_delay()
    keyUp(KEY_LEFT_ARROW)
    short_delay(10)
    keyDown(KEY_LEFT_ARROW)
    short_delay(5)
    # keyPress(KEY_BLINK)
    hold_press(KEY_ATT, KEY_BLINK)
    short_delay()
    keyUp(KEY_LEFT_ARROW)
    short_delay(20)
    go_to(Position(128, 100))
    short_delay(20)
    blink_with_key(KEY_ATT, KEY_LEFT_ARROW)
    short_delay(10)
    go_to(Position(62, 80), tolerance_x=1)
    short_delay()
    short_press(KEY_UP_ARROW)
    short_delay(5)
    # random_action(down_jump, down_blink)()
    # short_delay(5)
    # random_action(down_jump, down_blink)()
    # short_delay(5)
    go_to(STARTING_POSITION_SPRING4)
    short_press(KEY_LEFT_ARROW)
    return time.perf_counter() - t0


def unlock_rune(attempts=2):
    if attempts == 0:
        return False
    rune_unlocked = False
    rune_position = get_current_position_of("rune", minimap_region)
    if rune_position:
        subprocess.run(['say', 'Rune spawned.'])
        short_press(KEY_ATT)
        short_delay(5)
        if is_overlap(rune_position, RESET_POSITION_SPRING1, 100, 100):
            down_jump()
            short_delay(10)
        go_to(rune_position, need_jump_down=True, need_jump_combo=True,
              tolerance_x=8, tolerance_y=6)
        short_press(KEY_ATT)
        delay(0.8, 0.08, 0.6, 1.0)
        file_name = datetime.now().strftime('%m%d%H%M')
        # screenshot(os.path.join(DIR, f"training/{file_name}_base.png"), region=(750, 400, 1060, 300))
        press_duration = random_norm(0.05, 0.01, 0.02, 0.08)
        for _ in range(3):
            screencapture(region=(100, 100, 2, 2))
        n_image = 1
        t0 = time.perf_counter()
        keyPress(KEY_INTERACT, press_duration)
        time.sleep(0.1 - press_duration)
        while time.perf_counter() - t0 < 0.4:
            screencapture(os.path.join(DIR, f"training/{file_name}_{n_image}.png"), region=(800, 500, 960, 300))
            n_image += 1
        time.sleep(0.1)
        image_path = os.path.join(DIR, f"training/{file_name}_{n_image}.png")
        screencapture(image_path, region=(800, 500, 960, 300))
        # if wait_key('z', 'x'):
        #     rune_unlocked = True
        result = send_dm_and_wait_for_response(user_id=DC_USER_ID, image_path=image_path, wait_keys='zx', timeout=10.0)
        if result['success']:
            if result['trigger'] == 'key':
                return True
            elif result['discord_reply'].strip().lower() == 'b':
                return unlock_rune(attempts)
            elif len(result['discord_reply'].strip()) == 4:
                print(result['discord_reply'].strip())
                for direction_char in result['discord_reply'].strip().lower():
                    arrow_key = WSAD_TO_ARROW.get(direction_char)
                    if arrow_key:
                        random_delay_rep = 1 if np.random.random() < 0.7 else 3
                        short_press(arrow_key)
                        short_delay(random_delay_rep)
                    else:
                        return unlock_rune(attempts - 1)
                    random_action(attack1, attack2)()
                return True
        random_action(attack1, attack2, attack3)()
        subprocess.run(['say', 'Rune is still there!'])
    return False


def periodically_attack(duration, recast_after=0, max_gap=10):
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    random_action(attack1, attack3)()
    while time.perf_counter() - t0 < duration:
        if 0 < recast_after < time.perf_counter() - t0:
            recast_after = buff_infinity()
        if np.random.random() < ((time.perf_counter() - t1) / max_gap) ** 2:
            t1 = time.perf_counter()
            random_action(attack1, attack2, attack3)()
            def special_attack():
                short_press(KEY_A)
                short_delay()
                short_press(KEY_A)
            def special_attack_2():
                short_press(KEY_S)
                short_delay()
            action_with_prob(special_attack, 0.01)()
            action_with_prob(special_attack_2, 0.01)()
        else:
            short_delay(10)
    short_delay(5)
    return time.perf_counter() - t0


def buff_infinity():
    inf_cd = check_time_to_up("infinity", INFINITY_REGION, 180)
    inf2_cd = check_time_to_up("infinity", INFINITY2_REGION, 340)
    if inf_cd == 0 and inf2_cd == 0:
        short_press(KEY_BUFF2)
    else:
        short_press(KEY_BUFF)
    short_delay(3)
    return np.max([np.min([10, inf_cd, inf2_cd]), 0])


def buff_guild():
    buffed = False
    keyDown(KEY_LEFT_ALT)
    short_delay()
    guild_cd = check_time_to_up("guild_boss", GUILD_CRITDMG_REGION, 300)
    if guild_cd == 0:
        short_press(KEY_GUILD_CRITDMG)
        short_delay()
        short_press(KEY_GUILD_DMG)
        short_delay()
        short_press(KEY_GUILD_BOSS)
        short_delay(3)
        buffed = True
    keyUp(KEY_LEFT_ALT)
    short_delay(3)
    short_press(key_codes['f6'])
    return buffed


def attack1():
    short_press(KEY_ATT)
    short_delay(3)


def attack2():
    short_press(KEY_ATT2)
    short_delay(3)


def attack3():
    short_press(KEY_ATT3)
    short_delay(7)


def loop(minor_setup_fn, setup_fn, loot_fn, back_fn, minutes=18):
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    recast_ref = time.perf_counter()
    guild_buff_ref = time.perf_counter()
    buff_guild()
    while time.perf_counter() - t0 < 60 * minutes:
        log("setting up...")
        t1 = time.perf_counter()
        setup_fn()
        log("setup down...")
        short_delay()
        log("buffing...")
        recast_after = buff_infinity()
        if recast_after > 0:
            log(f"recasting infinity after {recast_after} seconds...")
            recast_ref = time.perf_counter()
        time_left = 60 * minutes - time.perf_counter() + t0
        log(f"{time_left:.2f} seconds left.")
        if time_left < 60:
            subprocess.run(['say', 'less than one minutes left!'])
        if unlock_rune():
            t0 = time.perf_counter()
        if 0 < recast_after < time.perf_counter() - recast_ref:
            recast_after = buff_infinity()
        back_fn()
        if 0 < recast_after < time.perf_counter() - recast_ref:
            recast_after = buff_infinity()
        if np.random.random() < ((time.perf_counter() - guild_buff_ref) / 1500) ** 2:
            buff_guild()
            guild_buff_ref = time.perf_counter()
        periodically_attack(58 + random_norm(1.5, 0.5, 0.2, 2.8) - time.perf_counter() + t1, recast_after)
        t1 = time.perf_counter()
        minor_setup_fn()
        short_delay(3)
        periodically_attack(35 + random_norm(1.5, 0.5, 0.2, 2.8) - time.perf_counter() + t1)
        short_delay(3)
        log("starting loot...")
        loot_fn()
        short_delay(5)
        log("loot done. staying until setup...")
        periodically_attack(58 + random_norm(1.5, 0.5, 0.2, 2.8) - time.perf_counter() + t1)


if __name__ == '__main__':
    start_bot()
    if not os.path.exists(os.path.join(DIR, "training")):
        os.mkdir(os.path.join(DIR, "training"))
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    time.sleep(0.3)

    minor_setup = minor_setup_spring1
    setup = setup_placement_spring1
    loot = loot_spring1
    back = back_to_start_position_spring1
    loop(minor_setup, setup, loot, back)
    # loop(minor_setup_spring4, setup_placement_spring4, loot_spring4, back_to_start_position_spring4, alt_buff=KEY_BUFF2)
    #
