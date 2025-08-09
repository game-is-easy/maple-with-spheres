import time
import json
from pynput import keyboard
from pathlib import Path

duration = 30  # seconds
output_file = Path("../data/recorded_sequence.json")

events = []
start_time = None  # we initialize this on first event

def normalize_key(key):
    try:
        return key.char if key.char else str(key)
    except AttributeError:
        return str(key)

def record_event(event_type, key):
    global start_time
    now = time.time()

    if start_time is None:
        start_time = now
        rel_time = 0.0
    else:
        rel_time = now - start_time

    if events:
        delay = rel_time - events[-1]["timestamp"]
    else:
        delay = 0.0

    events.append({
        "event": event_type,
        "key": normalize_key(key),
        "timestamp": rel_time,
        "delay": delay
    })

def on_press(key):
    record_event("keydown", key)

def on_release(key):
    record_event("keyup", key)
    if time.time() - start_time > duration:
        return False

print(f"Recording for {duration} seconds...")
with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
    listener.join()

with open(output_file, "w") as f:
    json.dump(events, f, indent=2)

print(f"\nSaved {len(events)} events to {output_file.absolute()}")
