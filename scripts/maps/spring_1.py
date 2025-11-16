from scripts.gameUI import *
from scripts.comboKeys import *


STARTING_POSITION = Position(84, 86)
RESET_POSITION = Position(84, 62)
minimap_region = extract_minimap_region()


def back_to_start_position(go_to_fn):
    if not current_at_position(STARTING_POSITION, minimap_region, 100, 100):
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
    return go_to_fn(STARTING_POSITION, need_jump_down=True, need_jump_combo=True)


def setup_placement(go_to_fn):
    t0 = time.perf_counter()
    seq = minor_setup(go_to_fn, prepare_for_full_setup=True)
    seq.extend(blink_with_key(KEY_ATT2, KEY_RIGHT_ARROW, delay_after_rep=6, execute=False))
    seq.extend(blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW, delay_after_rep=3, execute=False))
    exec_key_sequence(seq)
    go_to_fn(Position(250, 86), tolerance_x=8)
    short_delay()
    if np.random.random() < 0.5:
        blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW, delay_after_rep=3)
    else:
        short_press(KEY_SPHERE)
    go_to_fn(Position(302, 108), tolerance_x=8, need_jump_down=True)
    seq = short_press(KEY_SPHERE, delay_after_rep=5, execute=False)
    seq.extend(short_press(KEY_ATT, delay_after_rep=10, execute=False))
    exec_key_sequence(seq)
    return time.perf_counter() - t0


def loot(go_to_fn):
    seq = blink_with_key(KEY_ATT, KEY_RIGHT_ARROW, delay_after_rep=10, execute=False)
    seq.extend(blink_with_key(KEY_ATT, KEY_RIGHT_ARROW, delay_after_rep=20, execute=False))
    seq.extend(action_with_prob(blink_with_key, 0.6)(KEY_ATT, KEY_RIGHT_ARROW, execute=False))
    exec_key_sequence(seq)
    go_to_fn(Position(240, 86), tolerance_x=30, tolerance_y=30)
    seq = short_press(KEY_ATT, delay_after_rep=20, execute=False)
    seq.extend(action_with_prob(short_press, 0.8)(KEY_1, 5, execute=False))
    exec_key_sequence(seq)
    go_to_fn(Position(292, 108), tolerance_x=30)
    short_delay(5)
    back_to_start_position(go_to_fn)


def minor_setup(go_to_fn, prepare_for_full_setup=False):
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION):
        if not go_to_fn(STARTING_POSITION, need_jump_down=True, need_jump_combo=True):
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