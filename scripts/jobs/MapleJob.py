import time

from scripts.comboKeys import *
from scripts.gameUI import *
from scripts.maps.Map import Map
from scripts.arrow_detection.process_arrow_image import process_image

WINDOW_REGION = get_window_region()
# ARROW_REGION = (600 + WINDOW_REGION[0], 400 + WINDOW_REGION[1] - 68, 1360, 400)
ARROW_REGION = (600, 400 - 68, 1360, 400)


class MapleJob:
    def __init__(self, map_name):
        # self.minimap_region = extract_minimap_region()
        self.speed = 32
        self.start_speed = 0
        self.accelerate_time = 0.15
        self.jump_height = 12
        self.map = Map(map_name)
        self.current_position = None
        self.guild_boss_region = get_skill_region("guild_boss")
        self.guild_critdmg_region = get_skill_region("guild_critdmg")
        self.attacks = []
        self.special_attacks = []
        self.max_sphere = True
        self.mercedes_cdr = 0.05
        self.cor = False  # chains of resentment
        self.using_booster = False
        self.always_using_booster = False
        self.silence_mode = False
        self.auto_active_dc_window = False
        self.booster_use_timestamp = 0
        self.erda_cast_timestamp = 0
        self.rune_unlock_timestamp = 0
        self.next_task_start_at = 0

    def inv_x_t(self, x):
        acceleration = (self.speed - self.start_speed) / self.accelerate_time
        accelerated_distance = self.accelerate_time * (self.speed + self.start_speed) / 2
        if x < accelerated_distance:
            mean_t = (2 * x / acceleration) ** 0.5
        else:
            mean_t = (x - accelerated_distance) / self.speed + self.accelerate_time
        std = float(np.min([mean_t * 0.05, 0.1]))
        min = mean_t - 2 * std
        max = mean_t + 2 * std
        return random_norm(mean_t, std, min, max)


    def attack1(self, execute=True):
        return short_press(KEY_ATT, 5, execute=execute)

    def buff_guild(self):
        # buffed = False
        # keyDown(KEY_COMBO)
        # short_delay(5)
        # guild_cd = check_time_to_up("guild_boss", self.guild_boss_region, 300)
        # seq = []
        # if guild_cd == 0:
        #     seq.extend(short_press(KEY_GUILD_CRITDMG, 3, execute=False))
        #     seq.extend(short_press(KEY_GUILD_DMG, 3, execute=False))
        #     seq.extend(short_press(KEY_GUILD_BOSS, 3, execute=False))
        #     seq.extend(get_keyUp_seq(KEY_COMBO, get_short_delay(3)))
        #     seq.extend(short_press(KEY_ECHO, 1, execute=False))
        #     buffed = True
        # else:
        #     seq.extend(get_keyUp_seq(KEY_COMBO, get_short_delay(1)))
        # exec_key_sequence(seq)
        # # dialog_check_im_path = os.path.join(RESOURCES_DIR, "cancel.png")
        # # if locate_on_screen(dialog_check_im_path, region=(1300, 940, 160, 50), confidence=0.9):
        # while check_skill_use_popup():
        #     short_press(KEY_ESC, 3)
        #     buffed = False
        short_press(KEY_ECHO, 6)
        region = check_buff_use_popup()
        buffed = region is None
        while region:
            short_press(PRL["ENTER"], 5)
            region = check_skill_use_popup()
        seq = short_press(KEY_LEFT_ARROW, 3, False)
        seq.extend(short_press(KEY_RIGHT_ARROW, 1, False))
        exec_key_sequence(seq)
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

    def go_to_transit_position(self):
        if self.map.transit_position is not None:
            return self.go_to(self.map.transit_position, tolerance_x=4, tolerance_y=4, teleport_to_position=True)

    def go_to_standby_position(self):
        self.go_to_transit_position()
        return self.go_to(self.map.standby_position, tolerance_x=4, tolerance_y=4, teleport_to_position=True)

    def minor_setup(self):
        self.back_to_start_position()
        short_press(KEY_TS, 8)
        self.go_to(self.map.erda_position, tolerance_x=4, tolerance_y=4)
        if self.map.erda_direction is not None:
            arrow_key_code = KEY_LEFT_ARROW if self.map.erda_direction == "left" else KEY_RIGHT_ARROW
            multi_press(arrow_key_code, 2)
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
                elif loot_event["action"] == "press":
                    print(loot_event)
                    # key_code = PRL[str(loot_event["key_code"])]
                    key_code = KEY_TS
                else:
                    key_code = KEY_ATT
                short_press(key_code, **loot_event.get("params"))
        if self.cor:
            short_press(KEY_COR, 5)
        # self.go_to_standby_position()
        # self.back_to_start_position()

    # def unlock_rune(self, rune_position=None, dcbot=None, attempts=2):
    def unlock_rune(self, dcbot=None, attempts=2, active_app=None):
        if attempts == 0:
            return False
        first_attempt = (attempts == 2)
        if self.map.rune_position is None:
            # rune_position = get_current_position_of("rune", self.map.minimap_region)
            self.map.find_rune_on_map()
        if self.map.rune_position is not None:
            dcbot.send_message(f"[{datetime.now().strftime('%H:%M:%S')}] Rune spwaned. Be ready.")
            if first_attempt:
                if not self.silence_mode:
                    subprocess.run(['say', 'Rune spawned.'])
                self.attack1()
                rune_platform_edges = self.map.get_edges_at(self.map.rune_position)
                tolerance_left = int(np.min([self.map.rune_position.x - rune_platform_edges[0], 4])) if rune_platform_edges else 4
                tolerance_right = int(np.min([rune_platform_edges[1] - self.map.rune_position.x, 4])) if rune_platform_edges else 4
                self.go_to(self.map.rune_position, tolerance_y=4, tolerance_left=tolerance_left, tolerance_right=tolerance_right, teleport_to_position=True)
            self.attack1()
            delay(0.6, 0.06, 0.45, 0.75)
            file_name = datetime.now().strftime('%m%d%H%M')
            # screenshot(os.path.join(DIR, f"training/{file_name}_base.png"), region=(750, 400, 1060, 300))
            press_duration = random_norm(0.05, 0.01, 0.02, 0.08)
            # for _ in range(3):
            #     screencapture(region=(100, 100, 2, 2))
            if not self.silence_mode:
                if active_app is None:
                    active_app = get_active_application()
                time.sleep(0.1)
                activate_window()
                time.sleep(0.1)
                activate_window("Discord")
            elif self.auto_active_dc_window:
                activate_window("Discord")

            n_image = 1
            t0 = time.perf_counter()
            keyPress(KEY_INTERACT, press_duration)
            time.sleep(float(np.max([0.2 - time.perf_counter() + t0, 0])))
            images = []
            while time.perf_counter() - t0 < 0.8:
                # images.append(screencapture(os.path.join(DIR, f"training/{file_name}_{n_image}.png"), region=ARROW_REGION))
                images.append(screengrab(os.path.join(DIR, f"training/{file_name}_{n_image}.png"), region=ARROW_REGION))
                n_image += 1
            time.sleep(0.3)
            image_path = os.path.join(DIR, f"training/{file_name}_{n_image}.png")
            # images.append(screencapture(image_path, region=ARROW_REGION))
            images.append(screengrab(image_path, region=ARROW_REGION))
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
                    return self.unlock_rune(dcbot, attempts, active_app=active_app)
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
                            return self.unlock_rune(dcbot, attempts - 1, active_app=active_app)
                    seq.extend(self.attack1(execute=False))
                    exec_key_sequence(seq)
                    # TODO: check if rune unlock is successful
                    self.rune_unlock_timestamp = time.perf_counter()
                if active_app is not None and not self.silence_mode:
                    subprocess.run(["osascript", "-e", 'tell application "System Events" to set visible of process "Discord" to False'])
                    activate_window(active_app)
                elif self.auto_active_dc_window:
                    subprocess.run(["osascript", "-e", 'tell application "System Events" to set visible of process "Discord" to False'])
                if os.path.exists(os.path.join(DIR, f"training/labels.json")):
                    with open(os.path.join(DIR, f"training/labels.json"), 'r') as f:
                        data = json.load(f)
                else:
                    data = []
                data.append({"image_prefix": file_name, "labels": labels})
                with open(os.path.join(DIR, f"training/labels.json"),
                          'w') as f:
                    json.dump(data, f)
                self.map.rune_position = None
                return True
            # random_action(attack1, attack2, attack3)()
            subprocess.run(['say', 'Rune is still there!'])

    def check_stop_event_and_simultaneous_events(self, stop_event):
        if stop_event is not None and stop_event.is_set():
            return True
        if self.using_booster:
            # booster_use_until = np.inf if self.always_using_booster else self.rune_unlock_timestamp + 250
            booster_use_until = self.rune_unlock_timestamp + 250
            if self.booster_use_timestamp + 108 < time.perf_counter() < booster_use_until:
                log("Using booster...")
                self.use_booster()
        if self.cor:
            short_delay(3)
            short_press(KEY_COR, 6)
        return False

    def use_booster(self, booster_key_code=PRL['H']):
        short_delay(3)
        seq = multi_press(booster_key_code, 4, 10, execute=False)
        seq.extend(multi_press(PRL['Y'], 3, execute=False))
        exec_key_sequence(seq)
        self.booster_use_timestamp = time.perf_counter()

