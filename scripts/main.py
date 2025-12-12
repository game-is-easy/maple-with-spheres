from gameUI import *
from comboKeys import *
from jobs.ExpMages import IL
from maps.top_deck_6 import back_to_start_position, minor_setup, setup_placement, loot
from discord_bot import start_bot, send_text_message, send_dm_and_wait_for_response
from scripts.arrow_detection.process_arrow_image import *

INFINITY_REGION = get_skill_region("infinity")
INFINITY2_REGION = get_skill_region("infinity2")
GUILD_BOSS_REGION = get_skill_region("guild_boss")
GUILD_CRITDMG_REGION = get_skill_region("guild_critdmg")

DC_USER_ID = 304671527784284160
WINDOW_REGION = get_window_region()
ARROW_REGION = (600 + WINDOW_REGION[0], 400 + WINDOW_REGION[1] - 68, 1360, 400)


def unlock_rune(go_to_fn, rune_position=None, character=None, attempts=2):
    """
    Return Ture if rune unlocked; False if failed.
    """
    if attempts == 0:
        return False
    first_attempt = (attempts == 2)
    if rune_position is None:
        rune_position = get_current_position_of("rune", character.map.minimap_region if character else None)
    if rune_position:
        send_text_message(f"[{datetime.now().strftime('%H:%M:%S')}] Rune spwaned. Be ready.")
        subprocess.run(['say', 'Rune spawned.'])
        if first_attempt:
            short_press(KEY_ATT, delay_after_rep=5)
            rune_platform_edges = character.map.get_edges_at(rune_position)
            tolerance_left = int(np.min([rune_position.x - rune_platform_edges[0], 4]))
            tolerance_right = int(np.min([rune_platform_edges[1] - rune_position.x, 4]))
            go_to_fn(rune_position, need_jump_combo=True, tolerance_x=4, tolerance_y=4, tolerance_left=tolerance_left, tolerance_right=tolerance_right, teleport_to_position=True)
        short_press(KEY_ATT)
        delay(0.6, 0.06, 0.45, 0.75)
        file_name = datetime.now().strftime('%m%d%H%M')
        # screenshot(os.path.join(DIR, f"training/{file_name}_base.png"), region=(750, 400, 1060, 300))
        press_duration = random_norm(0.05, 0.01, 0.02, 0.08)
        for _ in range(3):
            screencapture(region=(100, 100, 2, 2))
        n_image = 1
        active_app = get_active_application()
        time.sleep(0.1)
        activate_window()
        time.sleep(0.1)
        activate_window("Discord")
        t0 = time.perf_counter()
        keyPress(KEY_INTERACT, press_duration)
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
                return unlock_rune(go_to_fn, rune_position, character, attempts)
            elif len(result['discord_reply'].strip().replace(' ', '')) >= 4:
                labels = result['discord_reply'].strip().replace(' ', '')[-4:].lower()
                print(labels)
                seq = []
                for direction_char in labels:
                    arrow_key = WASD_TO_ARROW.get(direction_char)
                    if arrow_key:
                        random_delay_rep = 1 if np.random.random() < 0.7 else 3
                        seq.extend(short_press(arrow_key, random_delay_rep, execute=False))
                    else:
                        return unlock_rune(go_to_fn, rune_position, character, attempts - 1)
                seq.extend(random_action(attack1, attack2)(execute=False))
                exec_key_sequence(seq)
            if active_app is not None:
                subprocess.run(["osascript", "-e", 'tell application "System Events" to set visible of process "Discord" to False'])
                activate_window(active_app)
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


def periodically_attack(duration, recast_after=0, max_gap=10, cast_fz_after=None):
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    short_press(PRL['D'], 3)
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
    guild_cd = check_time_to_up("guild_boss", GUILD_BOSS_REGION, 300)
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


def loop(minor_setup_fn, setup_fn, loot_fn, back_fn, go_to_fn, rune_cd, character):
    log("start!")
    minimap_region = character.map.minimap_region
    max_duration = rune_cd + 240
    t0 = time.perf_counter()
    t1 = time.perf_counter()
    rune_ref = time.perf_counter() - rune_cd
    recast_ref = time.perf_counter()
    short_press(PRL['8'], 5)
    fz_ref = time.perf_counter()
    guild_buff_ref = time.process_time() - 1800
    # if buff_guild():
    #     guild_buff_ref = time.perf_counter()
    # else:
    #     guild_buff_ref = time.perf_counter() - 300
    while time.perf_counter() - t0 < max_duration:
        rune_position = get_current_position_of("rune", minimap_region)
        log("setting up...")
        t1 = time.perf_counter()
        setup_fn(go_to_fn)
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
            if unlock_rune(go_to_fn, rune_position, character):
                rune_ref = t0 = time.perf_counter()
        if 0 < recast_after < time.perf_counter() - recast_ref:
            inf_cd_remain = buff_infinity()
            recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
        back_fn(go_to_fn)
        if 0 < recast_after < time.perf_counter() - recast_ref:
            inf_cd_remain = buff_infinity()
            recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
        if np.random.random() < ((time.perf_counter() - guild_buff_ref) / 1500) ** 2:
            if buff_guild():
                guild_buff_ref = time.perf_counter()
        seq = short_press(PRL['H'], 10, execute=False)
        seq.extend(multi_press(PRL['Y'], 3, execute=False))
        exec_key_sequence(seq)
        if np.random.random() < ((time.perf_counter() - fz_ref) / 300) ** 2:
            short_press(PRL['8'], 5)
            fz_ref = time.perf_counter()
        short_delay(3)
        blink_with_key(KEY_ATT, KEY_DOWN_ARROW, delay_after_rep=3)
        periodically_attack(59 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1, recast_after)
        t1 = time.perf_counter()
        minor_setup_fn(go_to_fn)
        short_delay(3)
        periodically_attack(32 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1)
        short_delay(3)
        log("starting loot...")
        loot_fn(go_to_fn)
        short_delay(5)
        short_press(PRL['8'], 5)
        log("loot done. staying until setup...")
        periodically_attack(59 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1)


if __name__ == '__main__':
    start_bot()
    if not os.path.exists(os.path.join(DIR, "training")):
        os.mkdir(os.path.join(DIR, "training"))
    activate_window()
    # time.sleep(0.3)

    # attempt_jump_blink = True
    character = IL("Top Deck Passage 6")

    def go_to_fn(position, need_jump_combo=False, attempt_jump_blink=True, tolerance_x=2, tolerance_y=2, tolerance_left=None, tolerance_right=None, teleport_to_position=False):
        return character.go_to(position, need_jump_combo, attempt_jump_blink, tolerance_x, tolerance_y, tolerance_left, tolerance_right, teleport_to_position=teleport_to_position)

    minor_setup_fn = minor_setup
    setup_fn = setup_placement
    loot_fn = loot
    back_fn = back_to_start_position

    rune_cd = 900
    loop(minor_setup_fn, setup_fn, loot_fn, back_fn, go_to_fn, rune_cd, character)
    # loop(minor_setup_spring4, setup_placement_spring4, loot_spring4, back_to_start_position_spring4, alt_buff=KEY_BUFF2)
    #o

