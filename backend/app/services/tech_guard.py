import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "tech_whitelist.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    TECH_WORDS = set(word.lower() for word in json.load(f))

PLACEHOLDER_PATTERN = re.compile(r'__TECH_\d+__')


def _es_tecnica(palabra: str) -> bool:
    p = palabra.lower()

    # Match exacto
    if p in TECH_WORDS:
        return True

    # Plural automático: quitar s/es y verificar raíz
    if p.endswith('es') and len(p) > 3 and p[:-2] in TECH_WORDS:
        return True
    if p.endswith('s') and len(p) > 2 and p[:-1] in TECH_WORDS:
        return True

    # Compuestas con guion: re-deployar → deployar
    if '-' in p:
        partes = p.split('-')
        if any(parte in TECH_WORDS for parte in partes):
            return True

    return False


def proteger_tecnicos(text: str) -> tuple[str, dict]:
    mapa = {}
    contador = [0]

    def reemplazar(match):
        palabra = match.group(0)
        if _es_tecnica(palabra):
            placeholder = f"__TECH_{contador[0]}__"
            contador[0] += 1
            mapa[placeholder] = palabra
            return placeholder
        return palabra

    # Incluir palabras con guion en el patrón
    resultado = re.sub(r'\b[a-zA-Z][a-zA-Z0-9]*(?:-[a-zA-Z][a-zA-Z0-9]*)?\b',
                       reemplazar, text)
    return resultado, mapa


def restaurar_tecnicos(text: str, mapa: dict) -> str:
    for placeholder, original in mapa.items():
        text = text.replace(placeholder, original)
    return text