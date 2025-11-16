from scripts.comboKeys import *
from scripts.gameUI import *
from scripts.maps.Map import Map


class MapleJob:
    def __init__(self, map_name):
        # self.minimap_region = extract_minimap_region()
        self.speed = 32
        self.start_speed = 8
        self.jump_height = 12
        self.map = Map(map_name)
        self.current_position = None

    def enter_door(self, door_position, target_position, max_timeout=6, **kwargs):
        kwargs.update({
            "tolerance_x": 4,
            "tolerance_y": 4
        })
        self.go_to(door_position, **kwargs)
        t0 = time.perf_counter()
        current_position = get_current_position_of("player", minimap_region=self.map.minimap_region)

        # while not is_overlap_x(current_position, position, tolerance_x) and time.perf_counter() - t2 < 3:
        #     arrow_key_code = KEY_LEFT_ARROW if current_position.x > position.x else KEY_RIGHT_ARROW
        #     distance = abs(current_position.x - position.x)
        #     self.move_horizontal_by(arrow_key_code, distance)
        #     precise_delay(0.3, 0.02)
        #     current_position = get_current_position_of("player", minimap_region)

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

    def minor_setup(self):
        pass

    def setup_placement(self):
        pass

    def loot(self):
        pass

    def unlock_rune(self):
        pass
