import json
import os
import re

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "correcciones_forzadas.json")

with open(DATA_PATH, "r", encoding="utf-8") as f:
    CORRECCIONES = json.load(f)


def aplicar_correcciones_forzadas(text: str) -> str:
    def _normalizar(palabra: str) -> str:
        return palabra.lower()\
            .replace("á","a").replace("é","e").replace("í","i")\
            .replace("ó","o").replace("ú","u").replace("ü","u")

    parrafos = text.split('\n')
    resultado = []
    for parrafo in parrafos:
        tokens = parrafo.split()
        tokens_corregidos = []
        for token in tokens:
            limpio = re.sub(r'^[¿¡\(\[\"\']+|[\)\]\"\'\.,:;!?]+$', '', token)
            limpio_norm = _normalizar(limpio)
            if limpio_norm in CORRECCIONES:
                corregido = CORRECCIONES[limpio_norm]
                if limpio[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                prefijo = re.match(r'^([¿¡\(\[\"\']*)', token).group(1)
                sufijo = re.search(r'([\)\]\"\'\.,:;!?]*)$', token).group(1)
                tokens_corregidos.append(prefijo + corregido + sufijo)
            else:
                tokens_corregidos.append(token)
        resultado.append(' '.join(tokens_corregidos))
    return '\n'.join(resultado)