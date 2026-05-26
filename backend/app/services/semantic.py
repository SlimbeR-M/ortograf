import re
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "semantic_map.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    SEMANTIC_MAP = json.load(f)

# Pre-compilar patrones con word boundaries para cada clave del mapa.
# El orden del JSON se preserva: claves más largas (más específicas) van primero.
_SEMANTIC_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    (k, v, re.compile(r'\b' + re.escape(k) + r'\b', re.IGNORECASE))
    for k, v in SEMANTIC_MAP.items()
]


def apply_semantic_map(text: str, guards=None) -> str:
    """
    Reemplaza frases coloquiales por términos técnicos usando el mapa semántico.
    Búsqueda case-insensitive con word boundaries; preserva capitalización de inicio.
    """
    if guards is None:
        guards = set()

    for k, v, pat in _SEMANTIC_PATTERNS:
        if k in guards:
            continue
        if not pat.search(text):
            continue

        def _repl(m, _v=v):
            matched = m.group(0)
            if matched[0].isupper():
                return _v[0].upper() + _v[1:]
            return _v

        text = pat.sub(_repl, text)

    return text
