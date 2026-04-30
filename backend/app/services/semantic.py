import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "semantic_map.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SEMANTIC_MAP = json.load(f)


def apply_semantic_map(text: str, guards=None) -> str:
    """
    Reemplazo semántico SOLO si la frase completa coincide o es segura.
    """

    if guards is None:
        guards = set()

    lower_text = text.lower()

    for k, v in SEMANTIC_MAP.items():
        if k in lower_text:

            # 🚫 NO tocar si está protegido por contexto
            if k in guards:
                continue

            # reemplazo seguro
            text = text.replace(k, v)

    return text