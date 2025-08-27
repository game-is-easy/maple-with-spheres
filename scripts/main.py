import time

from gameUI import *
from comboKeys import *
from discord_bot import start_bot, send_text_message, send_dm_and_wait_for_response
from process_arrow_image import *


minimap_region = extract_minimap_region()
STARTING_POSITION_SPRING1 = Position(84, 86)
RESET_POSITION_SPRING1 = Position(84, 62)
STARTING_POSITION_SPRING4 = Position(302, 128)
SPEED = 32
START_SPEED = 20
BLINK_HORIZONTAL_DISTANCE = 36
BLINK_VERTICAL_DISTANCE = 48
DISTANCE_BETWEEN_BLINKS = 14
TIME_BETWEEN_BLINKS = 0.66

INFINITY_REGION = get_skill_region("infinity")
INFINITY2_REGION = get_skill_region("infinity2")
GUILD_CRITDMG_REGION = get_skill_region("guild_critdmg")

DC_USER_ID = 304671527784284160
ARROW_REGION = (600, 400, 1360, 400)


def move_horizontal_by(arrow_key_code, distance, execute=True):
    if distance < BLINK_HORIZONTAL_DISTANCE * 0.8:
        blinks = 0
    else:
        blinks = int(round((distance + DISTANCE_BETWEEN_BLINKS) / (BLINK_HORIZONTAL_DISTANCE + DISTANCE_BETWEEN_BLINKS) - 0.3))
    if blinks > 0 and np.random.random() < 0.5:
        blinks -= 1
    if blinks == 0:
        if distance <= 2:
            mean = distance / SPEED * 2
            std = distance / SPEED * 0.2
            min = 0.01
        else:
            mean = distance / SPEED
            std = 0.1
            min = 0.02
        seq = get_keyPress_seq(arrow_key_code, random_norm(mean, std, min))
        # keyPress(arrow_key_code, random_norm(mean, std, min))
    else:
        delay_before_blink = get_short_delay()
        blink_duration = TIME_BETWEEN_BLINKS * (blinks - 0.5)
        move_duration = (distance - blinks * BLINK_HORIZONTAL_DISTANCE) / START_SPEED - delay_before_blink
        seq = get_keyDown_seq(arrow_key_code, delay_before_blink)
        seq.extend(get_keyPress_seq(KEY_BLINK, blink_duration, float(np.max([move_duration - blink_duration - delay_before_blink, smallest_delay()]))))
        seq.extend(get_keyUp_seq(arrow_key_code))
        # keyDown(arrow_key_code)
        # short_delay()
        # keyDown(KEY_BLINK)
        # short_delay()
        # time.sleep(TIME_BETWEEN_BLINKS * blinks)
        # keyUp(KEY_BLINK)
        # short_delay()
        # keyUp(arrow_key_code)
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def go_to(position, need_jump_down=False, need_jump_combo=False, tolerance_x=2, tolerance_y=2):
    t0 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    while not is_overlap_x(current_position, position, max(2, tolerance_x)) and time.perf_counter() - t0 < 20:
        arrow_key_code = KEY_LEFT_ARROW if current_position.x > position.x else KEY_RIGHT_ARROW
        distance = abs(current_position.x - position.x)
        move_horizontal_by(arrow_key_code, distance)
        precise_delay(0.3, 0.02)
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
        precise_delay(0.3, 0.02)
        current_position = get_current_position_of("player", minimap_region)
    return is_overlap(get_current_position_of("player", minimap_region), position, tolerance_x, tolerance_y)


# def place_spheres(arrow_key_code):


def back_to_start_position_spring1():
    if not current_at_position(STARTING_POSITION_SPRING1, minimap_region, 100, 100):
        if current_at_position(Position(292, 108), minimap_region, tolerance_x=1) or current_at_position(Position(310, 72), minimap_region, tolerance_x=1):
            seq = short_press(KEY_UP_ARROW, 10, execute=False)
        else:
            current_positon = get_current_position_of("player", minimap_region)
            # seq = []
            if current_positon.y < 80:
                seq = down_blink(delay_after=get_short_delay(3), execute=False)
                if current_positon.y < 50:
                    seq.extend(down_blink(delay_after=get_short_delay(3), execute=False))
            elif current_positon.y < 90:
                seq = random_action(down_blink, down_jump)(delay_after=get_short_delay(5), execute=False)
            else:
                seq = []
            # exec_key_sequence(seq)
            # while not is_overlap_y(get_current_position_of("player", minimap_region), Position(292, 108)):
            #     random_action(down_blink, down_jump)()
            #     short_delay(10)
            seq.extend(down_jump(delay_after=get_short_delay(10), execute=False))
            # seq = down_jump(delay_after=get_short_delay(10), execute=False)
            # down_jump()
            # short_delay(10)
        seq.extend(down_jump(delay_after=get_short_delay(), execute=False))
        seq.extend(short_press(KEY_RIGHT_ARROW, 9, execute=False))
        # down_jump()
        # short_delay()
        # short_press(KEY_RIGHT_ARROW)
        # short_delay(9)
        exec_key_sequence(seq)
    go_to(STARTING_POSITION_SPRING1, need_jump_down=True, need_jump_combo=True)


def setup_placement_spring1():
    t0 = time.perf_counter()
    seq = minor_setup_spring1(prepare_for_full_setup=True)
    seq.extend(blink_with_key(KEY_ATT2, KEY_RIGHT_ARROW, delay_after_rep=6, execute=False))
    seq.extend(blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW, delay_after_rep=3, execute=False))
    exec_key_sequence(seq)
    go_to(Position(250, 86), tolerance_x=8)
    short_delay()
    if np.random.random() < 0.5:
        blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW, delay_after_rep=3)
    else:
        short_press(KEY_SPHERE)
    go_to(Position(302, 108), tolerance_x=8, need_jump_down=True)
    seq = short_press(KEY_SPHERE, delay_after_rep=5, execute=False)
    seq.extend(short_press(KEY_ATT, delay_after_rep=10, execute=False))
    exec_key_sequence(seq)
    return time.perf_counter() - t0


def loot_spring1():
    seq = blink_with_key(KEY_ATT, KEY_RIGHT_ARROW, delay_after_rep=10, execute=False)
    seq.extend(blink_with_key(KEY_ATT, KEY_RIGHT_ARROW, delay_after_rep=20, execute=False))
    seq.extend(action_with_prob(blink_with_key, 0.6)(KEY_ATT, KEY_RIGHT_ARROW, execute=False))
    exec_key_sequence(seq)
    go_to(Position(240, 86), tolerance_x=30, tolerance_y=30)
    seq = short_press(KEY_ATT, delay_after_rep=20, execute=False)
    seq.extend(action_with_prob(short_press, 0.8)(KEY_1, 5, execute=False))
    exec_key_sequence(seq)
    go_to(Position(292, 108), tolerance_x=30)
    short_delay(5)
    back_to_start_position_spring1()


def minor_setup_spring1(prepare_for_full_setup=False):
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION_SPRING1):
        if not go_to(STARTING_POSITION_SPRING1, need_jump_down=True, need_jump_combo=True):
            return False
    seq = blink_with_key(KEY_TS, KEY_RIGHT_ARROW, delay_after_rep=8, execute=False)
    seq.extend(short_press(KEY_RIGHT_ARROW, 1, execute=False))
    if prepare_for_full_setup:
        seq.extend(blink_with_key(KEY_ERDA, KEY_RIGHT_ARROW, delay_after_rep=5, execute=False))
    else:
        seq.extend(short_press(KEY_ERDA, delay_after_rep=8, execute=False))
    if prepare_for_full_setup:
        return seq
    else:
        exec_key_sequence(seq)


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


def unlock_rune(rune_position=None, attempts=2):
    """
    Return Ture if rune unlocked; False if failed.
    """
    if attempts == 0:
        return False
    first_attempt = False
    if rune_position is None:
        first_attempt = True
        rune_position = get_current_position_of("rune", minimap_region)
    if rune_position:
        send_text_message(DC_USER_ID, f"[{datetime.now().strftime('%H:%M:%S')}] Rune spwaned. Be ready.")
        subprocess.run(['say', 'Rune spawned.'])
        # short_press(KEY_ATT)
        # short_delay(5)
        if first_attempt:
            seq = short_press(KEY_ATT, delay_after_rep=5, execute=False)
            if is_overlap(rune_position, RESET_POSITION_SPRING1, 100, 100):
                seq.extend(down_jump(get_short_delay(10), execute=False))
                # down_jump()
                # short_delay(10)
            exec_key_sequence(seq)
            go_to(rune_position, need_jump_down=True, need_jump_combo=True, tolerance_x=6, tolerance_y=4)
        short_press(KEY_ATT)
        delay(0.6, 0.06, 0.45, 0.75)
        file_name = datetime.now().strftime('%m%d%H%M')
        # screenshot(os.path.join(DIR, f"training/{file_name}_base.png"), region=(750, 400, 1060, 300))
        press_duration = random_norm(0.05, 0.01, 0.02, 0.08)
        for _ in range(3):
            screencapture(region=(100, 100, 2, 2))
        n_image = 1
        t0 = time.perf_counter()
        keyPress(KEY_INTERACT, press_duration)
        # multi_press(KEY_INTERACT)
        time.sleep(float(np.max([0.2 - time.perf_counter() + t0, 0])))
        images = []
        while time.perf_counter() - t0 < 0.8:
            images.append(screencapture(os.path.join(DIR, f"training/{file_name}_{n_image}.png"), region=ARROW_REGION))
            n_image += 1
        time.sleep(0.3)
        # base_image_path = os.path.join(DIR, f"training/{file_name}_1.png")
        # arrow_image_path = os.path.join(DIR, f"training/{file_name}_{n_image - 1}.png")
        image_path = os.path.join(DIR, f"training/{file_name}_{n_image}.png")
        images.append(screencapture(image_path, region=ARROW_REGION))
        result = send_dm_and_wait_for_response(user_id=DC_USER_ID, image_path=image_path, wait_keys='zx', timeout=10.0)
        processed_image_path = os.path.join(DIR, f"training/{file_name}_processed.png")
        processed_image_path_2 = os.path.join(DIR, f"training/{file_name}_processed_2.png")
        processed_images = process_image(images[0], images[-2], images[-1])
        cv2.imwrite(processed_image_path, processed_images[0])
        cv2.imwrite(processed_image_path_2, processed_images[1])
        if result['success']:
            if result['trigger'] == 'key':
                labels = result['arrow_data']
            elif result['discord_reply'].strip().lower() == 'b':
                log("retry interacting with rune...")
                return unlock_rune(rune_position, attempts)
            elif len(result['discord_reply'].strip().replace(' ', '')) == 4:
                labels = result['discord_reply'].strip().replace(' ', '').lower()
                print(labels)
                seq = []
                for direction_char in labels:
                    arrow_key = WASD_TO_ARROW.get(direction_char)
                    if arrow_key:
                        random_delay_rep = 1 if np.random.random() < 0.7 else 3
                        seq.extend(short_press(arrow_key, random_delay_rep, execute=False))
                    else:
                        return unlock_rune(rune_position, attempts - 1)
                seq.extend(random_action(attack1, attack2)(execute=False))
                exec_key_sequence(seq)
            if os.path.exists(os.path.join(DIR, f"training/labels.json")):
                with open(os.path.join(DIR, f"training/labels.json"), 'r') as f:
                    data = json.load(f)
            else:
                data = []
            data.append({"image_prefix": file_name, "labels": labels})
            with open(os.path.join(DIR, f"training/labels.json"), 'w') as f:
                json.dump(data, f)
            return True
        # random_action(attack1, attack2, attack3)()
        subprocess.run(['say', 'Rune is still there!'])
    return False


def periodically_attack(duration, recast_after=0, max_gap=10):
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    random_action(attack1, attack3)()
    while time.perf_counter() - t0 < duration:
        if 0 < recast_after < time.perf_counter() - t0:
            inf_cd_remain = buff_infinity()
            recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
        if np.random.random() < ((time.perf_counter() - t1) / max_gap) ** 2:
            t1 = time.perf_counter()
            seq = random_action(attack1, attack2, attack3)(execute=False)
            seq.extend(action_with_prob(special_attack, 0.01)(execute=False))
            seq.extend(action_with_prob(special_attack_2, 0.01)(execute=False))
            exec_key_sequence(seq)
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
    keyDown(KEY_COMBO)
    short_delay(3)
    guild_cd = check_time_to_up("guild_boss", GUILD_CRITDMG_REGION, 300)
    seq = []
    if guild_cd == 0:
        seq.extend(short_press(KEY_GUILD_CRITDMG, 1, execute=False))
        seq.extend(short_press(KEY_GUILD_DMG, 1, execute=False))
        seq.extend(short_press(KEY_GUILD_BOSS, 3, execute=False))
        seq.extend(get_keyUp_seq(KEY_COMBO, get_short_delay(3)))
        seq.extend(short_press(KEY_ECHO, 1, execute=False))
        buffed = True
    else:
        seq.extend(get_keyUp_seq(KEY_COMBO, get_short_delay(1)))
    exec_key_sequence(seq)
    dialog_check_im_path = os.path.join(RESOURCES_DIR, "cancel.png")
    if locate_on_screen(dialog_check_im_path, region=(1300, 940, 160, 50), confidence=0.9):
        short_press(KEY_ESC)
        buffed = False
    return buffed


def attack1(execute=True):
    return short_press(KEY_ATT, 4, execute=execute)


def attack2(execute=True):
    return short_press(KEY_ATT2, 4, execute=execute)


def attack3(execute=True):
    return short_press(KEY_ATT3, 8, execute=execute)


def special_attack(execute=True):
    seq = short_press(KEY_A, 1, execute=False)
    seq.extend(short_press(KEY_A, execute=False))
    if execute:
        exec_key_sequence(seq)
    else:
        return seq


def special_attack_2(execute=True):
    return short_press(KEY_S, 1, execute=execute)


def loop(minor_setup_fn, setup_fn, loot_fn, back_fn, rune_cd):
    max_duration = rune_cd + 240
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    rune_ref = time.perf_counter() - rune_cd
    recast_ref = time.perf_counter()
    if buff_guild():
        guild_buff_ref = time.perf_counter()
    else:
        guild_buff_ref = time.perf_counter() - 300
    while time.perf_counter() - t0 < max_duration:
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
        time_left = max_duration - time.perf_counter() + t0
        log(f"{time_left:.2f} seconds left.")
        if time_left < 60:
            subprocess.run(['say', 'less than one minutes left!'])
        if time.perf_counter() - rune_ref > rune_cd:
            if unlock_rune():
                rune_ref = t0 = time.perf_counter()
        if 0 < recast_after < time.perf_counter() - recast_ref:
            inf_cd_remain = buff_infinity()
            recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
        back_fn()
        if 0 < recast_after < time.perf_counter() - recast_ref:
            inf_cd_remain = buff_infinity()
            recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
        if np.random.random() < ((time.perf_counter() - guild_buff_ref) / 1500) ** 2:
            if buff_guild():
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
    # import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    activate_window()
    # time.sleep(0.3)

    minor_setup = minor_setup_spring1
    setup = setup_placement_spring1
    loot = loot_spring1
    back = back_to_start_position_spring1
    rune_cd = 900
    loop(minor_setup, setup, loot, back, rune_cd)
    # loop(minor_setup_spring4, setup_placement_spring4, loot_spring4, back_to_start_position_spring4, alt_buff=KEY_BUFF2)
    #

