import re


def finalize_text(text: str) -> str:
    parrafos = text.split('\n')
    resultado = []
    for parrafo in parrafos:
        if not parrafo.strip():
            resultado.append('')
            continue
        parrafo = _finalizar_parrafo(parrafo)
        resultado.append(parrafo)
    return '\n'.join(resultado)


_TITULOS_RAE_RE = re.compile(
    r'(?<=\w )'
    r'(Doctor|Doctora|Ingeniero|Ingeniera|Licenciado|Licenciada'
    r'|Secretario|Secretaria|Arquitecto|Arquitecta|Maestro|Maestra'
    r'|Director|Directora|Gerente|Coordinador|Coordinadora'
    r'|Subsecretario|Subsecretaria)\b'
)


def _finalizar_parrafo(text: str) -> str:
    text = text.strip()

    # Títulos ante nombre propio → minúscula según RAE (no al inicio de oración)
    text = _TITULOS_RAE_RE.sub(lambda m: m.group(1).lower(), text)

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

    # Eliminar coma pegada entre letras
    text = re.sub(
        r'([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]),([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])',
        r'\1\2',
        text
    )

    # Capitalizar primera letra
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

    # Restaurar siglas conocidas a mayúsculas completas
    _SIGLAS = {r'\bIa\b': 'IA', r'\bia\b': 'IA',
               r'\bMl\b': 'ML', r'\bNlp\b': 'NLP'}
    for patron, sigla in _SIGLAS.items():
        text = re.sub(patron, sigla, text)

    if not text.endswith(("?", ".", "!", "...", "¿", "¡")):
        text += "."

    return text