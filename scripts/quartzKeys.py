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


def keyPress(key_code, duration=0.05):
    keyDown(key_code)
    time.sleep(duration)
    keyUp(key_code)


if __name__ == '__main__':
    from keyCodes import *
    time.sleep(0.3)
    keyPress(KEY_LEFT_ARROW)