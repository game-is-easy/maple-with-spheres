import time
from .VNCClient import VNCClient


KEY_BLINK = 'v'
KEY_JUMP = 'c'
KEY_TS = '4'
KEY_ERDA = 'e'
KEY_SPHERE = 'r'
KEY_1 = '1'
KEY_2 = '2'
KEY_3 = '3'
KEY_F1 = 'f1'
KEY_F2 = 'f2'
KEY_F3 = 'f3'
KEY_F4 = 'f4'
KEY_F5 = 'f5'
KEY_F6 = 'f6'
KEY_F7 = 'f7'
KEY_F8 = 'f8'
KEY_BUFF = '6'
KEY_BUFF2 = '7'
KEY_ATT = 'x'
KEY_ATT2 = 'z'
KEY_ATT3 = 'space'
KEY_INTERACT = 'b'
KEY_COMBO = 'alt'
KEY_GUILD_BOSS = '8'
KEY_GUILD_DMG = '9'
KEY_GUILD_CRITDMG = '0'
KEY_Q = 'q'
KEY_W = 'w'
KEY_E = 'e'
KEY_R = 'r'
KEY_T = 't'
KEY_Y = 'y'
KEY_A = 'a'
KEY_S = 's'
KEY_D = 'd'
KEY_F = 'f'
KEY_G = 'g'
KEY_H = 'h'
KEY_Z = 'z'
KEY_X = 'x'
KEY_C = 'c'
KEY_V = 'v'
KEY_B = 'b'
KEY_N = 'n'
KEY_UP_ARROW = 'up'
KEY_LEFT_ARROW = 'left'
KEY_RIGHT_ARROW = 'right'
KEY_DOWN_ARROW = 'down'
KEY_ECHO = 'f6'
KEY_ESC = 'esc'
KEY_TOWN = 'j'
KEY_COR = 'd'
KEY_SPACE = 'space'
KEY_ENTER = 'enter'
KEY_SHIFT = 'shift'

PRL = {
    'LEFT': 'left',
    'RIGHT': 'right',
    'UP': 'up',
    'DOWN': 'down',
}


vnc = VNCClient()


def keyDown(key):
    vnc.keyDown(key)


def keyUp(key):
    vnc.keyUp(key)


def keyPress(key, duration=0.05, delay_after=0.0):
    keyDown(key)
    time.sleep(duration)
    keyUp(key)
    time.sleep(delay_after)


def keySequence(seq):
    for event in seq:
        if event["event"] == "press":
            keyDown(event["key"])
        else:
            keyUp(event["key"])
        if event.get("delay"):
            time.sleep(event["delay"] / 1000)