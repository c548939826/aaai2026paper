import json
import os

def ensure_dir_exists(dir_path):
    os.makedirs(dir_path, exist_ok=True)

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_json(data, filepath, indent=2):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)

def get_last_index(data_list, default=0):
    if data_list and isinstance(data_list, list):
        return len(data_list)
    return default