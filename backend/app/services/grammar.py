import re

# ─── Tildes diacríticas ───────────────────────────────────────────────────────

TILDES_DIACRITICAS = [
    # sé antes de cualquier infinitivo (-ar, -er, -ir)
    (r'\bse\b (\w+(?:ar|er|ir)\b)',
     lambda m: 'sé ' + m.group(1)),
    # sé antes de palabras clave de conocimiento
    (r'\bse\b (que|cómo|como|si|lo|la|las|los|poco|mucho|nada)',
     lambda m: 'sé ' + m.group(1)),
    # tú antes de verbo
    (r'\btu\b (eres|tienes|puedes|debes|sabes|quieres|vas|vendrás|harás|dices|fuiste|serás|estás|estabas)',
     lambda m: 'tú ' + m.group(1)),
    # él pronombre antes de verbo
    (r'\bel\b (es|fue|era|será|tiene|dijo|viene|sabe|puede|estaba|llegó|salió)',
     lambda m: 'él ' + m.group(1)),
    # más adverbio
    (r'\bmas\b (no|nunca|tampoco|sin|bien|mal|tarde|temprano)',
     lambda m: 'más ' + m.group(1)),
    # sí afirmación
    (r'\bsi\b(,| señor| señora| claro| por supuesto| quiero| acepto)',
     lambda m: 'sí' + m.group(1)),
]

# ─── Homófonos ────────────────────────────────────────────────────────────────

# tubo → tuvo SOLO si va seguido de verbo o complemento verbal
# NO cambia si va precedido de artículo + contexto de objeto físico
HOMOFONOS_VERBALES = [
    # tubo → tuvo solo si hay sujeto antes (pronombre o nombre propio)
    (r'\b(él|ella|usted|Juan|María|Pedro|Ana|Carlos|Luis|yo|tú)\b([\w\s,]+)\btubo\b',
     lambda m: m.group(1) + m.group(2) + 'tuvo'),
    # halla → haya cuando es auxiliar (antes de participio -ado/-ido o sustantivo)
    (r'\bhalla\b (mucha|mucho|más|bastante|suficiente|poca|poco|\w+ado\b|\w+ido\b)',
     lambda m: 'haya ' + m.group(1)),
    # halla → haya después de "que" (subjuntivo)
    (r'\bque halla\b',
     'que haya'),
    # valla → vaya con movimiento
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

# ─── Dequeísmo ────────────────────────────────────────────────────────────────

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

# ─── Concordancia básica ──────────────────────────────────────────────────────

CONCORDANCIA = [
    (" yo tiene ", " yo tengo "),
    (" tu no ", " tú no "),
    (" en base a ", " con base en "),
    (" de acuerdo a ", " de acuerdo con "),
]

# ─── Saludos que requieren coma ───────────────────────────────────────────────

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

    for patron in SALUDOS_COMA:
        text = re.sub(patron, lambda m: m.group(1) + ',', text)

    text = re.sub(
        r'(?<![,]) \b(pero|aunque|sino)\b',
        lambda m: ', ' + m.group(1),
        text
    )

    for patron, reemplazo in TILDES_DIACRITICAS:
        text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    for patron, reemplazo in HOMOFONOS_VERBALES:
        if callable(reemplazo):
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)
        else:
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    for patron, correcto in HOMOFONOS_SIMPLES.items():
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 6. Dequeísmo
    for patron in DEQUEISMO:
        correcto = patron.replace(' de que', ' que')
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 7. Concordancia
    for incorrecto, correcto in CONCORDANCIA:
        text = text.replace(incorrecto, correcto)

    return text