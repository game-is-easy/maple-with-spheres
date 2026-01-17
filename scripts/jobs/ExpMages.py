import time

from scripts.jobs.MapleJob import MapleJob
from scripts.comboKeys import *
from scripts.gameUI import *


class ExpMages(MapleJob):
    def __init__(self, map_name):
        super().__init__(map_name)
        self.up_jump_height = 60
        self.blink_horizontal_distance = 32
        self.blink_vertical_distance = 38
        self.distance_between_blinks = 14
        self.time_between_blinks = 0.66
        self.attack2_cd = 0
        self.attack2_cast_ref = 0
        self.infinity_region = get_skill_region("infinity")
        self.infinity2_region = get_skill_region("infinity2")

    def attack_blink(self, arrow_key_code, delay_after_rep=0, execute=True):
        if time.perf_counter() > self.attack2_cast_ref + self.attack2_cd:
            attack_key_code = KEY_ATT2
            self.attack2_cast_ref = time.perf_counter()
        else:
            attack_key_code = KEY_ATT
        return blink_with_key(attack_key_code, arrow_key_code, delay_after_rep, execute)

    def displacement_is_multiple_of_blinks(self, displacement, max_blinks, tolerance_left=2, tolerance_right=2):
        for n_blinks in range(1, max_blinks + 1):
            if displacement - tolerance_left <= self.blink_horizontal_distance * n_blinks <= displacement + tolerance_right or \
                    displacement - tolerance_left <= -self.blink_horizontal_distance * n_blinks <= displacement + tolerance_right:
                return n_blinks

    def move_horizontal_by(self, displacement, jump_blink=False, attack_blink=True, tolerance_left=2, tolerance_right=2, execute=True):
        arrow_key_code = KEY_LEFT_ARROW if displacement < 0 else KEY_RIGHT_ARROW
        distance = abs(displacement)
        # if -2 <= distance - self.blink_horizontal_distance <= 2:
        if not jump_blink and attack_blink:
            if displacement - tolerance_left <= self.blink_horizontal_distance <= displacement + tolerance_right or \
                    displacement - tolerance_left <= -self.blink_horizontal_distance <= displacement + tolerance_right:
                # return blink_with_key(KEY_ATT, arrow_key_code, execute=execute)
                return self.attack_blink(arrow_key_code, execute=execute)
            elif displacement - tolerance_left <= self.blink_horizontal_distance * 2 <= displacement + tolerance_right or \
                    displacement - tolerance_left <= -self.blink_horizontal_distance * 2 <= displacement + tolerance_right:
                # seq = blink_with_key(KEY_ATT, arrow_key_code, delay_after_rep=8, execute=False)
                # seq.extend(blink_with_key(KEY_ATT, arrow_key_code, execute=False))
                seq = self.attack_blink(arrow_key_code, delay_after_rep=8, execute=False)
                seq.extend(self.attack_blink(arrow_key_code, execute=False))
                if execute:
                    return exec_key_sequence(seq)
                else:
                    return seq
        if distance < self.blink_horizontal_distance * 0.8:
            blinks = 0
        else:
            blinks = int(round((distance + self.distance_between_blinks) / (self.blink_horizontal_distance + self.distance_between_blinks) - 0.3))
        if blinks > 0 and not jump_blink and np.random.random() < 0.3:
            blinks -= 1
        if blinks == 0:
            if distance <= 2:
                # mean = distance / SPEED * 2
                # std = distance / SPEED * 0.2
                mean = 0.14
                std = 0.01
                min = 0.12
                max = 0.16
            elif distance <= 4:
                mean = 0.19
                std = 0.01
                min = 0.17
                max = 0.21
            else:
                mean = distance / self.speed
                std = 0.1
                min = 0.02
                max = None
            seq = get_keyPress_seq(arrow_key_code, random_norm(mean, std, min, max))
            # keyPress(arrow_key_code, random_norm(mean, std, min))
        else:
            delay_before_blink = get_short_delay()
            if jump_blink:
                blinks -= 1
                distance -= self.blink_horizontal_distance
                if blinks > 0:
                    blink_duration = self.time_between_blinks * (blinks - 0.5)
                    distance_moved = blinks * self.blink_horizontal_distance + (blinks - 1) * self.distance_between_blinks
                    additional_move_duration = float(np.max([(distance - distance_moved) / self.speed - random_norm(0.36, 0.02, 0.3, 0.42) - delay_before_blink, smallest_delay()]))
                    # print(distance, blinks, distance_moved, additional_move_duration)
                    seq = get_keyDown_seq(arrow_key_code, delay_before_blink)
                    seq.extend(get_keyPress_seq(KEY_BLINK, blink_duration, additional_move_duration))
                    seq.extend(jump_direction_combo(arrow_key_code, KEY_BLINK, execute=False))
                else:
                    additional_move_duration = float(np.max([distance / self.speed - random_norm(0.36, 0.02, 0.3, 0.42) - delay_before_blink, smallest_delay()]))
                    seq = get_keyDown_seq(arrow_key_code, additional_move_duration)
                    seq.extend(jump_direction_combo(arrow_key_code, KEY_BLINK, execute=False))
            else:
                blink_duration = self.time_between_blinks * (blinks - 0.5)
                distance_moved = blinks * self.blink_horizontal_distance + (blinks - 1) * self.distance_between_blinks
                additional_move_duration = float(np.max([(distance - distance_moved) / self.speed - delay_before_blink, smallest_delay()]))
                seq = get_keyDown_seq(arrow_key_code, delay_before_blink)
                seq.extend(get_keyPress_seq(KEY_BLINK, blink_duration, additional_move_duration))
            seq.extend(get_keyUp_seq(arrow_key_code))
        if execute:
            exec_key_sequence(seq)
        else:
            return seq

    def go_to_x(self, current_position, position, attempt_jump_blink=True, tolerance=2, tolerance_left=None, tolerance_right=None, tp_count_at_position=0, max_timeout=15):
        t0 = time.perf_counter()
        if tp_count_at_position > 0 and is_overlap_x(current_position, position, 1):
            seq = short_press(KEY_UP_ARROW, 10, execute=False)
            if tp_count_at_position > 1:
                for _ in range(tp_count_at_position - 1):
                    seq.extend(short_press(KEY_UP_ARROW, 10, execute=False))
            exec_key_sequence(seq)
            return get_current_position_of("player", self.map.minimap_region)
        tolerance_left = tolerance_left or tolerance
        tolerance_right = tolerance_right or tolerance
        n_blinks = self.displacement_is_multiple_of_blinks(position.x - current_position.x, 2, tolerance_left, tolerance_right)
        if n_blinks is None and not self.map.on_same_platform(current_position, position) and \
                not is_overlap_x(current_position, position, self.blink_horizontal_distance) and \
                is_overlap(current_position, position, self.blink_horizontal_distance * 3 + tolerance, 8):
            target_platform_edges = self.map.get_edges_at(position)
            if target_platform_edges is not None:
                for n in [1, -1, 2, -2]:
                    inter_x = current_position.x + n * self.blink_horizontal_distance
                    if target_platform_edges[0] <= inter_x <= target_platform_edges[1]:
                        current_position = self.go_to_x(current_position, Position(inter_x, position.y), attempt_jump_blink, tolerance=10)
                        break
        while not is_overlap_x(current_position, position, tolerance, tolerance_left, tolerance_right) and time.perf_counter() - t0 < max_timeout:
            initial_x = current_position.x
            displacement = position.x - current_position.x
            jump_blink = attempt_jump_blink & (10 <= current_position.y - position.y <= 24)
            attack_blink = (-8 <= current_position.y - position.y <= 8)
            # if jump_blink:
            #     print(f"attempting jump blink, current y: {current_position.y}, target y: {position.y}")
            # self.move_horizontal_by(arrow_key_code, distance, jump_blink)
            self.move_horizontal_by(displacement, jump_blink, attack_blink, tolerance_left=tolerance_left or tolerance, tolerance_right=tolerance_right or tolerance)
            precise_delay(0.3, 0.02)
            current_position = get_current_position_of("player", self.map.minimap_region)
            if position.x < initial_x <= current_position.x:
                exec_key_sequence(get_keyUp_seq(KEY_RIGHT_ARROW))
            elif position.x > initial_x >= current_position.x:
                exec_key_sequence(get_keyUp_seq(KEY_LEFT_ARROW))
            # print(current_position, position, tp_count_at_position)
            if tp_count_at_position > 0 and is_overlap(current_position, position, 2, 4):
                short_press(KEY_UP_ARROW, 5)
                current_position = get_current_position_of("player", self.map.minimap_region)
                if not is_overlap(current_position, position, 4, 4):
                    if tp_count_at_position > 1:
                        short_delay(5)
                        for _ in range(tp_count_at_position - 1):
                            short_press(KEY_UP_ARROW, 10)
                        current_position = get_current_position_of("player", self.map.minimap_region)
                    break
        return current_position

    def go_to_y(self, current_position, position, need_jump_combo=False, tolerance=2, max_timeout=6):
        t0 = time.perf_counter()
        levels = self.map.get_all_levels_at(current_position.x)  # assume sorted ascending
        while not is_overlap_y(current_position, position, tolerance) and time.perf_counter() - t0 < max_timeout:
            if current_position.y < position.y:
                blink_target = current_position.y
                down_jump_target = current_position.y
                for i, level in enumerate(levels):
                    if current_position.y == level and i < len(levels) - 1:
                        down_jump_target = levels[i+1]
                    if current_position.y < level <= current_position.y + self.blink_vertical_distance:
                        blink_target = level
                if blink_target == current_position.y or blink_target > position.y + tolerance:
                    down_jump()
                elif down_jump_target < position.y - tolerance:
                    down_blink()
                else:
                    random_action(down_jump, down_blink)()
            elif current_position.y - position.y >= self.up_jump_height:
                up_jump_blink(delay_after_rep=1)
            elif current_position.y - position.y <= self.jump_height:
                short_press(KEY_JUMP, delay_after_rep=3)
            elif need_jump_combo or current_position.y - position.y >= self.jump_height + self.blink_vertical_distance:
                jump_up_combo(KEY_BLINK)
            else:
                blink(KEY_UP_ARROW)
            short_delay(6)
            current_position = get_current_position_of("player", self.map.minimap_region)
        return current_position

    def go_to(self,
              position,
              need_jump_combo=False,
              attempt_jump_blink=True,
              tolerance_x=2,
              tolerance_y=2,
              tolerance_left=None,
              tolerance_right=None,
              teleport_to_position=False,
              tp_count_at_position=0,
              delay_after_rep=0):
        current_position = get_current_position_of("player", self.map.minimap_region)
        if teleport_to_position:
            if is_overlap_x(current_position, position, 1):
                extra_punishment = 0
            elif tolerance_left is not None and tolerance_right is not None:
                extra_punishment = int(np.max([90 - (tolerance_left // 2 + tolerance_right // 2) * 10, 0]))
            else:
                extra_punishment = int(np.max([90 - tolerance_x // 2 * 20, 0]))
            inter_position, tp_count = self.map.get_tp_route_to_target(current_position, position, max_tp_count=2, extra_punishment=extra_punishment)
            if inter_position != position:
                current_position = self.go_to(inter_position, tolerance_x=1, tolerance_y=4, teleport_to_position=False, tp_count_at_position=tp_count)
        current_position = self.go_to_x(current_position, position, attempt_jump_blink, tolerance=max(2, tolerance_x), tolerance_left=tolerance_left, tolerance_right=tolerance_right)
        if not need_jump_combo:
            for tp_position in self.map.tp_positions:
                if is_overlap(current_position, tp_position.as_position(), 2, 4):
                    need_jump_combo = True
                    break
            if not need_jump_combo:
                for exit_position in self.map.exit_positions:
                    if is_overlap(current_position, exit_position, 4, 4):
                        need_jump_combo = True
                        break
        current_position = self.go_to_y(current_position, position, need_jump_combo, tolerance=tolerance_y)
        current_position = self.go_to_x(current_position, position, attempt_jump_blink, tolerance_x, tolerance_left, tolerance_right, tp_count_at_position, max_timeout=5)
        short_delay(delay_after_rep)
        return current_position

    def buff_infinity(self):
        inf_cd = check_time_to_up("infinity", self.infinity_region, 180)
        inf2_cd = check_time_to_up("infinity", self.infinity2_region, 340)
        if inf_cd == 0 and inf2_cd == 0:
            short_press(KEY_BUFF2)
        else:
            short_press(KEY_BUFF)
        short_delay(3)
        return np.max([np.min([10, inf_cd, inf2_cd]), 0])

    def attack2(self, execute=True):
        self.attack2_cast_ref = time.perf_counter()
        return short_press(KEY_ATT2, 4, execute=execute)

    def attack3(self, execute=True):
        return short_press(KEY_ATT3, 8, execute=execute)

    def periodically_attack(self, duration, recast_after=0, stop_at=None, max_gap=10, stop_event=None):
        t0 = t1 = time.perf_counter()
        # t1 = time.perf_counter()
        if stop_at is None:
            stop_at = t0 + duration
        # if recast_after > 0:
        #     recast_at = t1 + recast_after
        # else:
        #     recast_at = None
        if self.cor:
            self.attack3()
        else:
            self.attack1()
        # while time.perf_counter() < stop_at and (stop_event is None or not stop_event.is_set()):
        while time.perf_counter() < stop_at and not self.check_stop_event_and_simultaneous_events(stop_event):
            if 0 < recast_after < time.perf_counter() - t0:
            # if recast_at is not None and recast_at < time.perf_counter():
                inf_cd_remain = self.buff_infinity()
                recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
                # recast_at = time.perf_counter() if inf_cd_remain > recast_after else time.perf_counter() + inf_cd_remain
            if np.random.random() < ((time.perf_counter() - t1) / max_gap) ** 2:
                t1 = time.perf_counter()
                seq = random_action(*self.attacks)(execute=False)
                for special_attack in self.special_attacks:
                    seq.extend(action_with_prob(special_attack, 0.01)(execute=False))
                exec_key_sequence(seq)
            else:
                short_delay(10)
        if self.cor:
            short_press(KEY_COR, 5)
        else:
            short_delay(5)
        return time.perf_counter() - t0

    def loop(self, rune_cd, dcbot, stop_event=None):
        log("start!")
        # minimap_region = self.map.minimap_region
        max_duration = rune_cd + 240
        t0 = time.perf_counter()
        rune_ref = time.perf_counter() - rune_cd
        recast_ref = time.perf_counter()
        # if self.cor:
        #     short_press(KEY_COR, 5)
        guild_buff_ref = time.process_time() - 1800
        # while time.perf_counter() - t0 < max_duration and (stop_event is None or not stop_event.is_set()):
        while time.perf_counter() - t0 < max_duration and not self.check_stop_event_and_simultaneous_events(stop_event):
            if time.perf_counter() - rune_ref > rune_cd:
                self.map.find_rune_on_map()
            log("setting up...")
            t1 = time.perf_counter()

            self.setup_placement()
            log("setup down...")
            short_delay(3)

            log("buffing...")
            recast_after = self.buff_infinity()
            if recast_after > 0:
                log(f"recasting infinity after {recast_after} seconds...")
                recast_ref = time.perf_counter()
            time_left = max_duration - time.perf_counter() + t0
            log(f"{time_left:.2f} seconds left.")
            if time_left < 60:
                subprocess.run(['say', 'less than one minutes left!'])

            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            # if stop_event is not None and stop_event.is_set():
            #     break

            if time.perf_counter() - rune_ref > rune_cd:
                if self.unlock_rune(dcbot):
                    rune_ref = t0 = time.perf_counter()
            if 0 < recast_after < time.perf_counter() - recast_ref:
                inf_cd_remain = self.buff_infinity()
                recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            # if stop_event is not None and stop_event.is_set():
            #     break

            # if self.using_booster and (self.always_using_booster or time.perf_counter() - rune_ref < 250):
            #     seq = short_press(PRL['H'], 10, execute=False)
            #     seq.extend(multi_press(PRL['Y'], 3, execute=False))
            #     exec_key_sequence(seq)

            self.go_to_standby_position()
            if 0 < recast_after < time.perf_counter() - recast_ref:
                inf_cd_remain = self.buff_infinity()
                recast_after = 0 if inf_cd_remain > recast_after else inf_cd_remain
            if np.random.random() < ((time.perf_counter() - guild_buff_ref) / 1500) ** 2:
                if self.buff_guild():
                    guild_buff_ref = time.perf_counter()
                    short_delay(3)
            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            # if self.cor:
            #     short_press(KEY_COR, 6)
            # if stop_event is not None and stop_event.is_set():
            #     break

            self.back_to_start_position()
            # self.periodically_attack(58 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1, recast_after)
            self.periodically_attack(0, recast_after, stop_at=self.erda_cast_timestamp + 60 * (1 - self.mercedes_cdr), stop_event=stop_event)
            t1 = time.perf_counter()

            self.minor_setup()
            short_delay(3)
            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            # if stop_event is not None and stop_event.is_set():
            #     break

            self.periodically_attack(25 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1, stop_event=stop_event)
            short_delay(3)
            log("starting loot...")

            self.loot()
            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            self.go_to_standby_position()
            if self.check_stop_event_and_simultaneous_events(stop_event):
                break
            self.back_to_start_position()
            log("loot done. staying until setup...")
            # if stop_event is not None and stop_event.is_set():
            #     break

            # self.periodically_attack(56 + random_norm(1.5, 0.4, 0.5, 2.5) - time.perf_counter() + t1)
            self.periodically_attack(0, stop_at=self.erda_cast_timestamp + 60 * (1 - self.mercedes_cdr), stop_event=stop_event)
        log("loop is over.")
        dcbot.send_message("grinding ended.")


class IL(ExpMages):
    def __init__(self, map_name):
        super().__init__(map_name)
        self.blink_horizontal_distance = 36
        self.blink_vertical_distance = 50
        self.map.set_tp_equiv_distance(int(self.speed * self.time_between_blinks // 2) * 2 + self.blink_horizontal_distance)
        self.attacks = [self.attack1, self.attack2, self.attack3]
        self.attack2_cd = 5
        self.special_attacks = [self.special_attack_1, self.special_attack_2]

    def special_attack_1(self, execute=True):
        seq = short_press(KEY_A, 1, execute=False)
        seq.extend(short_press(KEY_A, execute=False))
        if execute:
            exec_key_sequence(seq)
        else:
            return seq

    def special_attack_2(self, execute=True):
        return short_press(KEY_S, 1, execute=execute)


class Bishop(ExpMages):
    def __init__(self, map_name):
        super().__init__(map_name)
        self.map.set_tp_equiv_distance(int(self.speed * self.time_between_blinks // 2) * 2 + self.blink_horizontal_distance)
        self.attack2_cd = 10


if __name__ == '__main__':
    import subprocess
    subprocess.run(["osascript", "-e", 'tell application "Parallels Desktop" to activate'])
    time.sleep(0.3)
    # minimap_region = extract_minimap_region()
    character = IL("Top Deck Passage 6")
    tp_from = character.map.tp_positions[0]
    character.enter_door(tp_from, tp_from.next())
