import re


def finalize_text(text: str) -> str:
    text = text.strip()

    # Proteger puntos suspensivos
    text = re.sub(r'\.{3,}', '__ELLIPSIS__', text)

    # Limpiar puntuación duplicada
    text = re.sub(r'(?<=[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])\.{2}(?=[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])', '.', text)
    text = re.sub(r'\?{2,}', '?', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'([.?!])\s*([.?!])', r'\1', text)
    text = re.sub(r'([.?!])(["\'])(\s|$)', r'\1\3', text)

    # Restaurar puntos suspensivos
    text = text.replace('__ELLIPSIS__', '...')

    # CRÍTICO: eliminar coma SOLO cuando está pegada entre letras sin espacio
    # "Estimado,s" → "Estimados"  |  "Estimados, compañeros" → sin cambio
    text = re.sub(
        r'([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]),([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])',
        r'\1\2',
        text
    )

    # Capitalizar primera letra saltando signos de apertura
    if text:
        i = 0
        while i < len(text) and text[i] in ('¡', '¿', ' '):
            i += 1
        if i < len(text) and text[i].islower():
            text = text[:i] + text[i].upper() + text[i+1:]

    # Capitalizar después de punto final
    text = re.sub(
        r'(\. )([a-záéíóúüñ])',
        lambda m: m.group(1) + m.group(2).upper(),
        text
    )

    # Capitalizar después de ¡ o ¿
    text = re.sub(
        r'([¡¿]\s*)([a-záéíóúüñ])',
        lambda m: m.group(1) + m.group(2).upper(),
        text
    )

    if not text.endswith(("?", ".", "!", "...", "¿", "¡")):
        text += "."

    return text