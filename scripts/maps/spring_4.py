from ..gameUI import *
from ..comboKeys import *


minimap_region = extract_minimap_region()
STARTING_POSITION = Position(302, 128)


def back_to_start_position(go_to_fn):
    go_to_fn(STARTING_POSITION)


def setup_placement(go_to_fn):
    t0 = time.perf_counter()
    minor_setup()
    go_to_fn(Position(326, 68), tolerance_x=1)
    short_press(KEY_UP_ARROW)
    short_delay(3)
    go_to_fn(Position(78, 102), tolerance_x=4)
    short_delay()
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    blink_with_key(KEY_ATT2, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to_fn(Position(164, 100), tolerance_x=4)
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to_fn(Position(230, 68), tolerance_x=4)
    short_delay()
    blink_with_key(KEY_SPHERE, KEY_RIGHT_ARROW)
    short_delay(3)
    go_to_fn(STARTING_POSITION)
    short_delay()
    short_press(KEY_LEFT_ARROW)
    return time.perf_counter() - t0


def minor_setup(go_to_fn):
    t0 = time.perf_counter()
    current_position = get_current_position_of("player", minimap_region)
    if not is_overlap(current_position, STARTING_POSITION):
        if not go_to_fn(STARTING_POSITION):
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


def loot(go_to_fn):
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
    go_to_fn(Position(128, 100))
    short_delay(20)
    blink_with_key(KEY_ATT, KEY_LEFT_ARROW)
    short_delay(10)
    go_to_fn(Position(62, 80), tolerance_x=1)
    short_delay()
    short_press(KEY_UP_ARROW)
    short_delay(5)
    # random_action(down_jump, down_blink)()
    # short_delay(5)
    # random_action(down_jump, down_blink)()
    # short_delay(5)
    go_to_fn(STARTING_POSITION)
    short_press(KEY_LEFT_ARROW)
    return time.perf_counter() - t0