import sys
import time

if sys.platform == "win32":
    import winsound
else:
    import subprocess


events = {
    "rune_spawned": {
        "win32": [
            {"frequency": 1000, "duration": 0.5},
            {"frequency": 700, "duration": 0.5},
        ],
        "darwin": "Rune spawned.",
        "linux": "Rune spawned.",
    },
    "rune_solve_failed": {
        "win32": [
            {"frequency": 1000, "duration": 0.3},
            {"frequency": 1000, "duration": 0.3},
            {"frequency": 1000, "duration": 0.3}
        ],
        "darwin": "Rune is still there!",
        "linux": "Rune is still there!",
    },
    "time_out_soon":{
        "win32": [
            {"frequency": 600, "duration": 0.2},
            {"frequency": 500, "duration": 0.2},
            {"frequency": 400, "duration": 0.2},
            {"frequency": 300, "duration": 0.2}
        ],
        "darwin": "Less than one minute left!",
        "linux": "Less than one minute left!",
    },
}


def alert(event):
    """
    :param event: 'rune_spawned', 'rune_solve_failed', 'time_out_soon'
    :return: None

    Make corresponding alert.
    """
    if sys.platform == "darwin":
        subprocess.run(["say", events[event]["darwin"]])
    elif sys.platform.startswith("linux"):
        subprocess.run(["spd-say", events[event]["linux"]])
    else:
        for sound in events[event]["win32"]:
            winsound.Beep(sound["frequency"], sound["duration"])
            time.sleep(0.1)