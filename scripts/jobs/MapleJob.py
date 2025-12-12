import time

from scripts.comboKeys import *
from scripts.gameUI import *
from scripts.maps.Map import Map
from scripts.arrow_detection.process_arrow_image import process_image

WINDOW_REGION = get_window_region()
ARROW_REGION = (600 + WINDOW_REGION[0], 400 + WINDOW_REGION[1] - 68, 1360, 400)


class MapleJob:
    def __init__(self, map_name):
        # self.minimap_region = extract_minimap_region()
        self.speed = 32
        self.start_speed = 8
        self.jump_height = 12
        self.map = Map(map_name)
        self.current_position = None
        self.guild_boss_region = get_skill_region("guild_boss")
        self.guild_critdmg_region = get_skill_region("guild_critdmg")
        self.attacks = []
        self.special_attacks = []
        self.mercedes_cdr = 0.05
        self.cor = False  # chains of resentment
        self.erda_cast_timestamp = 0
        self.next_task_start_at = 0

    def attack1(self, execute=True):
        return short_press(KEY_ATT, 5, execute=execute)

    def buff_guild(self):
        buffed = False
        keyDown(KEY_COMBO)
        short_delay(3)
        guild_cd = check_time_to_up("guild_boss", self.guild_boss_region, 300)
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

    def enter_door(self, door_position, target_position, max_timeout=6, **kwargs):
        kwargs.update({
            "tolerance_x": 4,
            "tolerance_y": 4
        })
        self.go_to(door_position, **kwargs)
        t0 = time.perf_counter()
        current_position = get_current_position_of("player", minimap_region=self.map.minimap_region)

        while not is_overlap(current_position, target_position) and time.perf_counter() - t0 < max_timeout:
            if time.perf_counter() - t0 > max_timeout or not is_overlap_y(current_position, door_position, tolerance=4):
                return self.go_to(target_position, need_jump_down=True, need_jump_combo=True, attempt_jump_blink=True)
            if current_position.x == door_position.x:
                seq = short_press(KEY_UP_ARROW, delay_after_rep=10, execute=False)
            else:
                if abs(current_position.x - door_position.x) >= 4:
                    direction_hold_duration = random_norm(0.35, 0.015, 0.3, 0.4)
                    delay_before_enter = random_norm(0.12, 0.015, 0.1, 0.14)
                else:  # distances are different by 2
                    direction_hold_duration = random_norm(0.25, 0.015, 0.22, 0.3)
                    delay_before_enter = random_norm(0.05, 0.01, 0.03, 0.08)
                direction_key_code = KEY_LEFT_ARROW if current_position.x > door_position.x else KEY_RIGHT_ARROW
                total_delay_during_hold = delay_before_enter
                seq = get_keyDown_seq(direction_key_code, delay_before_enter)
                for _ in range(3):
                    duration = random_norm(0.05, 0.01, 0.03, 0.065)
                    delay_after = random_norm(0.04, 0.008, 0.025, 0.06)
                    if duration + total_delay_during_hold < direction_hold_duration - smallest_delay():
                        if duration + delay_after + total_delay_during_hold < direction_hold_duration - smallest_delay():
                            total_delay_during_hold += duration + delay_after
                            seq.extend(get_keyPress_seq(KEY_UP_ARROW, duration, delay_after))
                        else:
                            total_delay_during_hold += duration
                            seq.extend(get_keyPress_seq(KEY_UP_ARROW, duration, direction_hold_duration - total_delay_during_hold))
                            break
                    else:
                        break
                seq.extend(get_keyUp_seq(direction_key_code, delay=get_short_delay(8)))
            exec_key_sequence(seq)
            current_position = get_current_position_of("player", minimap_region=self.map.minimap_region)

    def go_to(self, position, **kwargs):
        return False

    def back_to_start_position(self):
        return self.go_to(self.map.start_position, teleport_to_position=True)

    def go_to_standby_position(self):
        return self.go_to(self.map.standby_position, tolerance_x=4, tolerance_y=4, teleport_to_position=True)

    def minor_setup(self):
        self.back_to_start_position()
        short_press(KEY_TS, 8)
        self.go_to(self.map.erda_position, tolerance_x=4, tolerance_y=4)
        short_press(KEY_ERDA, 8)
        self.erda_cast_timestamp = time.perf_counter()

    def setup_placement(self):
        self.minor_setup()
        for position in self.map.sphere_positions:
            self.go_to(position)
            short_press(KEY_SPHERE, 5)
        action_with_prob(short_press, 0.8)(KEY_S, 10)

    def loot(self):
        for loot_event in self.map.loot_series:
            if "position" in loot_event:
                self.go_to(loot_event["position"], **loot_event.get("params"))
            elif "action" in loot_event:
                if loot_event["action"] == "attack":
                    key_code = KEY_ATT
                elif loot_event["action"] == "attack2":
                    key_code = KEY_ATT2
                elif loot_event["action"] == "attack3":
                    key_code = KEY_ATT3
                elif loot_event["action"] == "snow_of_spirit":
                    key_code = KEY_1
                else:
                    key_code = KEY_ATT
                short_press(key_code, **loot_event.get("params"))
        if self.cor:
            short_press(KEY_COR, 5)
        self.go_to_standby_position()
        # self.back_to_start_position()

    def unlock_rune(self, rune_position=None, dcbot=None, attempts=2):
        if attempts == 0:
            return False
        first_attempt = (attempts == 2)
        if rune_position is None:
            rune_position = get_current_position_of("rune", self.map.minimap_region)
        if rune_position:
            dcbot.send_message(f"[{datetime.now().strftime('%H:%M:%S')}] Rune spwaned. Be ready.")
            subprocess.run(['say', 'Rune spawned.'])
            if first_attempt:
                self.attack1()
                rune_platform_edges = self.map.get_edges_at(rune_position)
                tolerance_left = int(np.min([rune_position.x - rune_platform_edges[0], 4])) if rune_platform_edges else 4
                tolerance_right = int(np.min([rune_platform_edges[1] - rune_position.x, 4])) if rune_platform_edges else 4
                self.go_to(rune_position, tolerance_y=4, tolerance_left=tolerance_left, tolerance_right=tolerance_right, teleport_to_position=True)
            self.attack1()
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
            image_path = os.path.join(DIR,
                                      f"training/{file_name}_{n_image}.png")
            images.append(screencapture(image_path, region=ARROW_REGION))
            result = dcbot.send_dm_and_wait_for_response(user_id=0, image_path=image_path, timeout=10.0)
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
                    return self.unlock_rune(rune_position, dcbot, attempts)
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
                            return self.unlock_rune(rune_position, dcbot, attempts - 1)
                    # seq.extend(random_action(self.attack1, self.attack2)(execute=False))
                    seq.extend(self.attack1(execute=False))
                    exec_key_sequence(seq)
                if active_app is not None:
                    subprocess.run(["osascript", "-e",
                                    'tell application "System Events" to set visible of process "Discord" to False'])
                    activate_window(active_app)
                if os.path.exists(os.path.join(DIR, f"training/labels.json")):
                    with open(os.path.join(DIR, f"training/labels.json"),
                              'r') as f:
                        data = json.load(f)
                else:
                    data = []
                data.append({"image_prefix": file_name, "labels": labels})
                with open(os.path.join(DIR, f"training/labels.json"),
                          'w') as f:
                    json.dump(data, f)
                return True
            # random_action(attack1, attack2, attack3)()
            subprocess.run(['say', 'Rune is still there!'])
