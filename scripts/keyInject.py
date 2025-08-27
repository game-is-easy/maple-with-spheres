import json, shutil, subprocess, time
import random

PRLCTL = shutil.which("prlctl") or "/usr/local/bin/prlctl"
VM = "Windows 11"

# Parallels key codes (US layout). Full table: docs link in README.
PRL = {
    # letters
    **{c: v for c, v in zip("QWERTYUIOP", [24,25,26,27,28,29,30,31,32,33])},
    **{c: v for c, v in zip("ASDFGHJKL", [38,39,40,41,42,43,44,45,46])},
    **{c: v for c, v in zip("ZXCVBNM",   [52,53,54,55,56,57,58])},
    # digits row
    **{c: v for c, v in zip("1234567890", [10,11,12,13,14,15,16,17,18,19])},
    " ": 65, "ENTER": 36, "TAB": 23, "BACKSPACE": 22, "ESCAPE": 9,
    "-": 20, "=": 21, "[": 34, "]": 35, "\\": 51, ";": 47, "'": 48, "`": 49,
    ",": 59, ".": 60, "/": 61,
    "LEFT_SHIFT": 50, "RIGHT_SHIFT": 62,
    "LEFT_CTRL": 37, "LEFT_ALT": 64, "LEFT_WIN": 115, "SPACE": 65,
    "UP": 98, "LEFT": 100, "RIGHT": 102, "DOWN": 104,
    "F6": 72
}

WASD_TO_ARROW = {'w': PRL["UP"], 's': PRL["DOWN"], 'a': PRL["LEFT"], 'd': PRL["RIGHT"]}

SHIFT = PRL["LEFT_SHIFT"]

def _run_json(vm, events):
    proc = subprocess.run(
        [PRLCTL, "send-key-event", vm, "-j"],
        input=(json.dumps(events) + "\n").encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return proc.stdout.decode()


# very basic US-ASCII typer (expand as needed)
_SYMBOLS = {
    "!": ("1", True), "@": ("2", True), "#": ("3", True), "$": ("4", True),
    "%": ("5", True), "^": ("6", True), "&": ("7", True), "*": ("8", True),
    "(": ("9", True), ")": ("0", True),
    "_": ("-", True), "+": ("=", True), "{": ("[", True), "}": ("]", True),
    "|": ("\\", True), ":": (";", True), "\"": ("'", True),
    "<": (",", True), ">": (".", True), "?": ("/", True), "~": ("`", True),
}

def type_text(vm, text, inter_key_delay_ms=20):
    events = []
    for ch in text:
        use_shift = False
        base = ch

        if ch == "\n":
            events += [{"key": PRL["ENTER"], "event": "press"},
                       {"key": PRL["ENTER"], "event": "release", "delay": inter_key_delay_ms}]
            continue

        if ch in _SYMBOLS:
            base, use_shift = _SYMBOLS[ch]
        elif "A" <= ch <= "Z":
            base, use_shift = ch, True
        elif "a" <= ch <= "z":
            base = ch.upper()
        elif ch in PRL:
            base = ch

        code = PRL.get(base.upper() if base.isalpha() else base)
        if code is None:
            # skip unsupported char
            continue

        inter_key_delay_ms += int(inter_key_delay_ms * random.random() / 3)
        if use_shift:
            events.append({"key": SHIFT, "event": "press"})
        events.append({"key": code, "event": "press"})
        events.append({"key": code, "event": "release", "delay": inter_key_delay_ms})
        if use_shift:
            events.append({"key": SHIFT, "event": "release", "delay": inter_key_delay_ms})

    return _run_json(vm, events)


def add_event_to_json(j, key_code, event_type, delay):
    # press all, release in reverse
    j.append({"key": key_code, "event": event_type, "delay": int(delay * 1000)})
    return j


def keydown(vm, key_code):
    return _run_json(vm, [{"key": key_code, "event": "press"}])


def keyup(vm, key_code):
    return _run_json(vm, [{"key": key_code, "event": "release"}])


def keypress(vm, key_code, duration=0.05, delay_after=0.0):
    # For games: make the key logically down, wait, then up.
    return _run_json(vm, [
        {"key": key_code, "event": "press", "delay": int(duration * 1000)},
        {"key": key_code, "event": "release", "delay": int(delay_after * 1000)}
    ])


def key_seq(vm, seq_json):
    return _run_json(vm, seq_json)


def keyDown(key_code):
    keydown(VM, key_code)


def keyUp(key_code):
    keyup(VM, key_code)


def keyPress(key_code, duration=0.05, delay_after=0.0):
    keypress(VM, key_code, duration, delay_after)


def keySequence(seq_json):
    key_seq(VM, seq_json)


if __name__ == "__main__":
    # Example usage:
    WSAD = {'w': PRL["UP"], 's': PRL["DOWN"], 'a': PRL["LEFT"], 'd': PRL["RIGHT"]}
    wsad = "adww"
    j = []
    delays = [random.random()*0.06+0.07 for _ in range(8)]
    t0 = time.perf_counter()
    for i, c in enumerate(wsad):
        add_event_to_json(j, WSAD[c], "press", delays[i*2])
        add_event_to_json(j, WSAD[c], "release", delays[i*2+1])
    keySequence(j)
    print(time.perf_counter() - t0)
    time.sleep(1)
    t1 = time.perf_counter()
    for i, c in enumerate(wsad):
        keyPress(WSAD[c], delays[i*2], delay_after=delays[i*2+1])
    print(time.perf_counter() - t1)
    # keypress(VM, PRL["RIGHT"], 549)
    # type_text(vm, "Hello, World!\n")
    # combo(vm, [PRL["LEFT_WIN"], PRL["PRINT"]])  # Win+PrtScr
