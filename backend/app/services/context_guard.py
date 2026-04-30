import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "semantic_map.json")

try:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        SEMANTIC_MAP = json.load(f)
except FileNotFoundError:
    SEMANTIC_MAP = {}

def check_context(text: str) -> str:
    # placeholder realista
    return text