from scripts.gameUI import *
from scripts.comboKeys import *
from scripts.maps.Map import Map

TOP_LEVEL = 50
STARTING_POSITION = Position(276, 36)
ERDA_POSITION = Position(204, 72)
SPHERE_POSITION_1 = Position(204, 132)
SPHERE_POSITION_2 = Position(278, 124)
SPHERE_POSITION_3 = Position(68, 136)
TP_POSITION_1 = Position(240, 36)
TP_POSITION_2 = Position(240, 132)
TP_POSITION_3 = Position(68, 136)
TP_POSITION_A = Position(48, 150)
TP_POSITION_B = Position(90, 72)
TP_POSITION_C = Position(168, 132)
TP_POSITION_D = Position(334, 150)
TP_POSITION_E = Position(346, 80)
TP_POSITIONS = [TP_POSITION_1, TP_POSITION_2, TP_POSITION_3, TP_POSITION_A, TP_POSITION_B, TP_POSITION_C, TP_POSITION_D, TP_POSITION_E]
TP_COUNT_TO_POS1 = [0, 2, 1, 5, 4, 3, 2, 1]
RESET_POSITION = None
minimap_region = extract_minimap_region()


def back_to_start_position(go_to_fn):
    # if not current_at_position(STARTING_POSITION, minimap_region, 130, 60):
    #     if current_at_position(TP_POSITION_3, minimap_region, 90, 30):
    #         go_to_fn(TP_POSITION_3, need_jump_combo=True, tolerance_x=1, tolerance_y=2)
    #         seq = short_press(KEY_UP_ARROW, 10, execute=False)
    #     elif current_at_position(TP_POSITION_2, minimap_region, 80, 30):
    #         go_to_fn(TP_POSITION_2, need_jump_combo=True, tolerance_x=1, tolerance_y=2)
    #         seq = short_press(KEY_UP_ARROW, 10, execute=False)
    #         seq.extend(short_press(KEY_UP_ARROW, 10, execute=False))
    #     elif current_at_position(TP_POSITION_B, minimap_region, 1, 2):
    #         seq = short_press(KEY_UP_ARROW, 10, execute=False)
    #         for _ in range(3):
    #             seq.extend(short_press(KEY_UP_ARROW, 10, execute=False))
    #     elif current_at_position(TP_POSITION_D, minimap_region, 1, 2):
    #         seq = short_press(KEY_UP_ARROW, 10, execute=False)
    #         seq.extend(short_press(KEY_UP_ARROW, 10, execute=False))
    #     elif current_at_position(TP_POSITION_E, minimap_region, 1, 2):
    #         seq = short_press(KEY_UP_ARROW, 10, execute=False)
    #     else:
    #         seq = []
    #     if seq:
    #         exec_key_sequence(seq)
    return is_overlap(go_to_fn(STARTING_POSITION, teleport_to_position=True), STARTING_POSITION)


def setup_placement(go_to_fn):
    t0 = time.perf_counter()
    seq = minor_setup(go_to_fn, prepare_for_full_setup=True)
    seq.extend(blink_with_key(KEY_ATT2, KEY_DOWN_ARROW, delay_after_rep=6, execute=False))
    exec_key_sequence(seq)
    go_to_fn(SPHERE_POSITION_1, need_jump_combo=True)
    seq = blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW, delay_after_rep=3, execute=False)
    seq.extend(blink_with_key(KEY_ATT, KEY_RIGHT_ARROW, delay_after_rep=1, execute=False))
    exec_key_sequence(seq)
    go_to_fn(SPHERE_POSITION_2, need_jump_combo=True, attempt_jump_blink=False, tolerance_x=4)
    blink_with_key(KEY_SPHERE, KEY_LEFT_ARROW, delay_after_rep=1)
    go_to_fn(SPHERE_POSITION_3, teleport_to_position=True)
    # go_to_fn(TP_POSITION_2, need_jump_combo=True, tolerance_x=1, tolerance_y=2)
    # short_press(KEY_UP_ARROW, 10)
    # go_to_fn(SPHERE_POSITION_3, need_jump_combo=True)
    seq = short_press(KEY_SPHERE, 5, execute=False)
    seq.extend(short_press(KEY_ATT, delay_after_rep=6, execute=False))
    seq.extend(action_with_prob(short_press, 0.8)(KEY_S, 10, execute=False))
    exec_key_sequence(seq)
    return time.perf_counter() - t0


def loot(go_to_fn):
    action_with_prob(blink_with_key, 0.6)(KEY_ATT, KEY_RIGHT_ARROW)
    go_to_fn(Position(280, 84), tolerance_x=25, tolerance_y=30)
    go_to_fn(Position(280, 124), need_jump_combo=True, tolerance_x=25, tolerance_y=20)
    short_delay(15)
    # seq = random_action(down_blink, down_jump)(delay_after=get_short_delay(30), execute=False)
    # seq.extend(short_press(KEY_ATT, delay_after_rep=20, execute=False)
    seq = short_press(KEY_ATT3, delay_after_rep=15, execute=False)
    if np.random.random() < 0.5:
        seq.extend(action_with_prob(blink, 0.5)(KEY_LEFT_ARROW, get_short_delay(10), execute=False))
    exec_key_sequence(seq)
    go_to_fn(Position(200, 132), tolerance_x=20, tolerance_y=20)
    short_press(PRL['D'], 15)
    # short_delay(15)
    go_to_fn(Position(120, 150), tolerance_x=10, tolerance_y=4)
    action_with_prob(short_press, 0.8)(KEY_1, 5)
    # seq = action_with_prob(short_press, 0.8)(KEY_1, 5, execute=False)
    # seq.extend(jump_direction_combo(jump_direction_combo(KEY_LEFT_ARROW, KEY_BLINK, delay_after_rep=15, execute=False)))
    # exec_key_sequence(seq)
    # go_to_fn(Position(68, 136), need_jump_combo=True, attempt_jump_blink=True, tolerance_x=1, tolerance_y=2)
    back_to_start_position(go_to_fn)


def minor_setup(go_to_fn, prepare_for_full_setup=False):
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION):
        if not back_to_start_position(go_to_fn):
            return False
    if np.random.random() < 0.05:
        seq = blink_with_key(KEY_TS, KEY_LEFT_ARROW, delay_after_rep=12, execute=False)
        seq.extend(blink_with_key(KEY_ATT, KEY_LEFT_ARROW, delay_after_rep=8, execute=False))
        seq.extend(down_jump(delay_after=get_short_delay(), execute=False))
        seq.extend(short_press(KEY_LEFT_ARROW, 14, execute=False))
    else:
        seq = short_press(KEY_TS, 8, execute=False)
        seq.extend(blink(KEY_DOWN_ARROW, delay_after=get_short_delay(5), execute=False))
        seq.extend(blink_with_key(KEY_ATT, KEY_LEFT_ARROW, delay_after_rep=8, execute=False))
        seq.extend(jump_direction_combo(KEY_LEFT_ARROW, KEY_BLINK, delay_after_rep=3, execute=False))
    exec_key_sequence(seq)
    go_to_fn(ERDA_POSITION, need_jump_combo=True, tolerance_x=6, tolerance_y=4)
    seq = multi_press(KEY_LEFT_ARROW, delay_after_rep=0, execute=False)
    seq.extend(short_press(KEY_ERDA, delay_after_rep=8, execute=False))
    seq.extend(blink(KEY_DOWN_ARROW, delay_after=get_short_delay(5), execute=False))
    if prepare_for_full_setup:
        return seq
    else:
        exec_key_sequence(seq)


class TopDeck6(Map):
    def __init__(self):
        super().__init__("arteria")
        self.set_starting_position(STARTING_POSITION)
        self.set_erda_position(ERDA_POSITION)
        self.set_sphere_positions([SPHERE_POSITION_1, SPHERE_POSITION_2, SPHERE_POSITION_3])
        self.set_tp_positions([TP_POSITION_1, TP_POSITION_2, TP_POSITION_3], loop=True)
        self.set_tp_positions([TP_POSITION_A, TP_POSITION_B, TP_POSITION_C, TP_POSITION_D, TP_POSITION_E, TP_POSITION_1])


