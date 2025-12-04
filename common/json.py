import json, os

def load_json(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data # list of dict

def save_json(json_data, json_path): 
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())

def atomic_save_json(json_data, tmp_path, json_path): 
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, json_path)
