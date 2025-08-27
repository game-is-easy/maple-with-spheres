import time
from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap


def key_event(key_code, key_down=True):
    """
    key_code: hardware keycode (e.g. 0x00 for “A”)
    key_down: True for key-down, False for key-up
    """
    evt = CGEventCreateKeyboardEvent(None, key_code, key_down)
    CGEventPost(kCGHIDEventTap, evt)


def keyDown(key_code):
    key_event(key_code, True)


def keyUp(key_code):
    key_event(key_code, False)


def keyPress(key_code, duration=0.05, delay_after=0.0):
    keyDown(key_code)
    time.sleep(duration)
    keyUp(key_code)
    time.sleep(delay_after)


def exec_key_sequence(seq):
    for e in seq:
        if e["event"] == "press":
            keyDown(e["key"])
        else:
            keyUp(e["key"])
        if e.get("delay"):
            time.sleep(e["delay"])


if __name__ == '__main__':
    from keyCodes import *
    time.sleep(0.3)
    keyPress(KEY_LEFT_ARROW)