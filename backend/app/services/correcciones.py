import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "correcciones_forzadas.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    CORRECCIONES = json.load(f)


def aplicar_correcciones_forzadas(text: str) -> str:
    palabras = text.split('\n')
    resultado = []
    for parrafo in palabras:
        tokens = parrafo.split()
        tokens_corregidos = []
        for token in tokens:
            # Limpiar puntuación para comparar
            limpio = re.sub(r'^[¿¡\(\[\"\']+|[\)\]\"\'\.,:;!?]+$', '', token).lower()
            if limpio in CORRECCIONES:
                corregido = CORRECCIONES[limpio]
                # Preservar casing
                if token[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                # Preservar puntuación
                prefijo = re.match(r'^([¿¡\(\[\"\']*)', token).group(1)
                sufijo = re.search(r'([\)\]\"\'\.,:;!?]*)$', token).group(1)
                tokens_corregidos.append(prefijo + corregido + sufijo)
            else:
                tokens_corregidos.append(token)
        resultado.append(' '.join(tokens_corregidos))
    return '\n'.join(resultado)