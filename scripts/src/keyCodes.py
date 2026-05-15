key_codes = {
    # Lower-case letters
    'a': 0x00,
    's': 0x01,
    'd': 0x02,
    'f': 0x03,
    'h': 0x04,
    'g': 0x05,
    'z': 0x06,
    'x': 0x07,
    'c': 0x08,
    'v': 0x09,
    'b': 0x0B,
    'q': 0x0C,
    'w': 0x0D,
    'e': 0x0E,
    'r': 0x0F,
    'y': 0x10,
    't': 0x11,
    'u': 0x20,
    'i': 0x22,
    'o': 0x1F,
    'p': 0x23,
    'n': 0x2D,
    'm': 0x2E,
    'l': 0x25,
    'k': 0x28,
    'j': 0x26,

    # Digits
    '1': 0x12,
    '2': 0x13,
    '3': 0x14,
    '4': 0x15,
    '5': 0x17,
    '6': 0x16,
    '7': 0x1A,
    '8': 0x1C,
    '9': 0x19,
    '0': 0x1D,

    # Function keys
    'f1':  0x7A,
    'f2':  0x78,
    'f3':  0x63,
    'f4':  0x76,
    'f5':  0x60,
    'f6':  0x61,
    'f7':  0x62,
    'f8':  0x64,
    'f9':  0x65,
    'f10': 0x6D,
    'f11': 0x67,
    'f12': 0x6F,

    # Modifiers & common keys
    'left_shift':   0x38,
    'right_shift':  0x3C,
    'left_control': 0x3B,
    'right_control':0x3E,
    'left_option':  0x3A,
    'right_option': 0x3D,
    'command':      0x37,
    'caps_lock':    0x39,
    'fn':           0x3F,

    # Navigation & editing
    'return':         0x24,
    'tab':            0x30,
    'space':          0x31,
    'delete':         0x33,  # Backspace
    'forward_delete': 0x75,
    'escape':         0x35,
    'home':           0x73,
    'end':            0x77,
    'page_up':        0x74,
    'page_down':      0x79,
    'left_arrow':     0x7B,
    'right_arrow':    0x7C,
    'down_arrow':     0x7D,
    'up_arrow':       0x7E,

    # Media / system
    'volume_up':   0x48,
    'volume_down': 0x49,
    'mute':        0x4A,
}

# Letter keys
KEY_Q = 0x0C
KEY_W = 0x0D
KEY_E = 0x0E
KEY_R = 0x0F

KEY_A = 0x00
KEY_S = 0x01
KEY_D = 0x02
KEY_F = 0x03

KEY_Z = 0x06
KEY_X = 0x07
KEY_C = 0x08
KEY_V = 0x09
KEY_B = 0x0B

# Number keys
KEY_1 = 0x12
KEY_2 = 0x13
KEY_3 = 0x14
KEY_4 = 0x15
KEY_5 = 0x17
KEY_6 = 0x16
KEY_7 = 0x1A

# Space
KEY_SPACE = 0x31

# Arrow keys
KEY_LEFT_ARROW  = 0x7B
KEY_RIGHT_ARROW = 0x7C
KEY_DOWN_ARROW  = 0x7D
KEY_UP_ARROW    = 0x7E

# Modifiers
KEY_LEFT_SHIFT   = 0x38
KEY_LEFT_CONTROL = 0x3B
KEY_LEFT_ALT     = 0x3A  # Option key

# Function keys
KEY_F1 = 0x7A
KEY_F2 = 0x78
KEY_F3 = 0x63
KEY_F4 = 0x76

WASD_TO_ARROW = {'w': KEY_UP_ARROW,
                 's': KEY_DOWN_ARROW,
                 'a': KEY_LEFT_ARROW,
                 'd': KEY_RIGHT_ARROW}

