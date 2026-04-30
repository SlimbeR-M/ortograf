import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "slang_dict.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SLANG = json.load(f)

def replace_slang(text: str) -> str:
    words = text.split()
    return " ".join([SLANG.get(w.lower(), w) for w in words])