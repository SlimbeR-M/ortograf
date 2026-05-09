import difflib


def calcular_cambios(original: str, corregido: str) -> list:
    palabras_orig = original.split()
    palabras_corr = corregido.split()

    matcher = difflib.SequenceMatcher(None, palabras_orig, palabras_corr)
    cambios = []

    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "replace":
            original_frag = " ".join(palabras_orig[i1:i2])
            corregido_frag = " ".join(palabras_corr[j1:j2])
            cambios.append({
                "tipo": "reemplazo",
                "original": original_frag,
                "corregido": corregido_frag,
                "razon": _explicar_cambio(original_frag, corregido_frag)
            })
        elif opcode == "insert":
            corregido_frag = " ".join(palabras_corr[j1:j2])
            cambios.append({
                "tipo": "insercion",
                "original": "",
                "corregido": corregido_frag,
                "razon": "Se agregó texto faltante"
            })
        elif opcode == "delete":
            original_frag = " ".join(palabras_orig[i1:i2])
            cambios.append({
                "tipo": "eliminacion",
                "original": original_frag,
                "corregido": "",
                "razon": "Se eliminó texto incorrecto o redundante"
            })

    return cambios


def _normalizar(texto: str) -> str:
    return texto.lower()\
        .replace("á","a").replace("é","e").replace("í","i")\
        .replace("ó","o").replace("ú","u").replace("ü","u")\
        .replace("ñ","n")


def _explicar_cambio(original: str, corregido: str) -> str:
    PUNTUACION = set(".,;:¿?¡!\"'")
    orig_sin_punt = ''.join(c for c in original if c not in PUNTUACION)
    corr_sin_punt = ''.join(c for c in corregido if c not in PUNTUACION)

    solo_puntuacion = (orig_sin_punt.lower() == corr_sin_punt.lower() and
                       orig_sin_punt == corr_sin_punt)

    if solo_puntuacion and original != corregido:
        return f"Puntuación: '{original}' → '{corregido}'"

    orig_l = original.lower().strip(".,;:¿?¡!")
    corr_l = corregido.lower().strip(".,;:¿?¡!")
    orig_sin = _normalizar(original).strip(".,;:¿?¡!")
    corr_sin = _normalizar(corregido).strip(".,;:¿?¡!")

    if orig_l == corr_l and original != corregido:
        return f"Mayúscula: '{original}' debe escribirse '{corregido}'"

    if orig_sin == corr_sin and orig_l != corr_l:
        return f"Tilde: '{original}' debe escribirse '{corregido}'"

    if orig_sin == corr_sin and original != corregido:
        return f"Tilde y mayúscula: '{original}' debe escribirse '{corregido}'"

    return f"Ortografía: '{original}' se escribe '{corregido}'"