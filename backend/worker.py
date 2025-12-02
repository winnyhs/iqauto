import time, json

state = {
    "start_time": None,
    "duration_min": 30,
    "done": False
}

def start():
    state["start_time"] = time.time()
    state["done"] = False

def progress():
    if state["start_time"] is None:
        return 0, False

    elapsed = (time.time() - state["start_time"]) / 60.0
    total = state["duration_min"]

    if elapsed >= total:
        state["done"] = True
        return 100, True

    pct = int((elapsed / total) * 100)
    return pct, False


