import re


TILDES_DIACRITICAS = [
    (r'\bse\b (\w+(?:ar|er|ir))\b',
     lambda m: 'sé ' + m.group(1)),
    (r'\bse\b (que|poco|mucho|nada|bien|mal|dónde|cómo|cuándo)\b',
     lambda m: 'sé ' + m.group(1)),
    (r'\btu\b (eres|fuiste|serás|estás|estabas|tienes|tenías|puedes|podías|debes|sabes|quieres|vas|vendrás)\b',
     lambda m: 'tú ' + m.group(1)),
    (r'\bel\b (es|fue|era|será|tiene|tenía|dijo|viene|sabe|puede|llegó|salió|hizo|quiso)\b',
     lambda m: 'él ' + m.group(1)),
    (r'\bmas\b (no|nunca|tampoco|tarde|temprano|bien|mal)\b',
     lambda m: 'más ' + m.group(1)),
]

HOMOFONOS_VERBALES = [
    (r'\b(él|ella|usted|Juan|María|Pedro|Ana|Carlos|Luis|yo|tú)\b([\w\s,]+)\btubo\b',
     lambda m: m.group(1) + m.group(2) + 'tuvo'),
    (r'\bhalla\b (mucha|mucho|más|bastante|suficiente|poca|poco|\w+ado\b|\w+ido\b)',
     lambda m: 'haya ' + m.group(1)),
    (r'\bque halla\b', 'que haya'),
    (r'\bvalla\b (a ver|al|a la|a buscar|a hacer|a comprar|a comer|a dormir)',
     lambda m: 'vaya ' + m.group(1)),
]

HOMOFONOS_SIMPLES = {
    r'\bvien\b': 'bien',
    r'\baber\b': 'haber',
    r'\balla\b': 'allá',
    r'\bay\b(?! que)': 'hay',
    r'\bbaso\b(?! de )': 'vaso',
}

DEQUEISMO = [
    r'me parece de que',
    r'creo de que',
    r'pienso de que',
    r'opino de que',
    r'considero de que',
    r'siento de que',
    r'espero de que',
    r'imagino de que',
    r'supongo de que',
    r'insisto de que',
]

CONCORDANCIA = [
    (" yo tiene ", " yo tengo "),
    (" tu no ", " tú no "),
    (" en base a ", " con base en "),
    (" de acuerdo a ", " de acuerdo con "),
]

SALUDOS_COMA = [
    r'^(Hola)(?![,])',
    r'^(Buenos días)(?![,])',
    r'^(Buenas tardes)(?![,])',
    r'^(Buenas noches)(?![,])',
    r'^(Buen día)(?![,])',
    r'^(Estimado)(?![,])',
    r'^(Querido)(?![,])',
]


def correct_grammar(text: str) -> str:

    # 1. Coma después de saludo inicial
    for patron in SALUDOS_COMA:
        text = re.sub(patron, lambda m: m.group(1) + ',', text)

    # 2. Coma antes de conjunciones adversativas
    text = re.sub(
        r'(?<![,]) \b(pero|aunque|sino)\b',
        lambda m: ', ' + m.group(1),
        text
    )

    # 3. Tildes diacríticas
    for patron, reemplazo in TILDES_DIACRITICAS:
        text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    # 4. Homófonos verbales
    for patron, reemplazo in HOMOFONOS_VERBALES:
        if callable(reemplazo):
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)
        else:
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    # 5. Homófonos simples
    for patron, correcto in HOMOFONOS_SIMPLES.items():
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 6. Dequeísmo
    for patron in DEQUEISMO:
        correcto = patron.replace(' de que', ' que')
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 7. Concordancia
    for incorrecto, correcto in CONCORDANCIA:
        text = text.replace(incorrecto, correcto)

    # 8. Sino vs si no
    # Condicional negativa: "sino" → "si no" cuando sigue verbo o clítico
    text = re.sub(
        r'\bsino\b (se|me|te|le|lo|la|les|las|nos|viene|va|puede|quiere|tiene|dan|hay)',
        lambda m: 'si no ' + m.group(1),
        text
    )

    # Contradicción: "si no" → "sino" cuando sigue sustantivo o adjetivo
    # Solo después de coma y sin verbo a continuación
    text = re.sub(
        r',\s*si no\b (?!se |me |te |le |lo |la |les |las |viene |va |puede |quiere |tiene )',
        ', sino ',
        text
    )

    return text