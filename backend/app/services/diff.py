import difflib


def calcular_cambios(original: str, corregido: str) -> list:
    """
    Compara el texto original con el corregido y retorna
    una lista de cambios con explicación de cada uno.
    """
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


def _explicar_cambio(original: str, corregido: str) -> str:
    """Genera una explicación legible del cambio realizado."""
    orig_l = original.lower()
    corr_l = corregido.lower()

    # Tildes
    if orig_l == corr_l.replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u").replace("ü","u"):
        return f"Tilde: '{original}' debe escribirse '{corregido}'"

    # Mayúscula
    if orig_l == corr_l:
        return f"Mayúscula: '{original}' debe ser '{corregido}'"

    # Puntuación
    if orig_l.replace(",","").replace(".","").replace("¿","").replace("?","") == corr_l.replace(",","").replace(".","").replace("¿","").replace("?",""):
        return f"Puntuación corregida: '{original}' → '{corregido}'"

    # Ortografía general
    return f"Ortografía: '{original}' se escribe '{corregido}'"