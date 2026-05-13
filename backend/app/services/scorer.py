import language_tool_python

tool = language_tool_python.LanguageTool("es")

CATEGORIAS_ORTOGRAFIA = {"TYPOS", "MISSPELLING", "MORFOLOGIK_RULE"}
CATEGORIAS_GRAMATICA = {"GRAMMAR", "AGREEMENT", "PUNCTUATION", "STYLE", "REDUNDANCY"}

# Tildes diacríticas — no contar como errores porque las manejamos nosotros
TILDES_DIACRITICAS = {
    ("el", "él"), ("mas", "más"), ("esta", "está"), ("tu", "tú"),
    ("se", "sé"), ("si", "sí"), ("de", "dé"), ("te", "té"), ("aun", "aún"),
}


def _filtrar_errores(errores, texto):
    """Filtra errores que nuestro pipeline ya maneja."""
    filtrados = []
    for m in errores:
        fragmento = texto[m.offset:m.offset + m.error_length].lower()
        if m.replacements:
            par = (fragmento, m.replacements[0].lower())
            if par in TILDES_DIACRITICAS:
                continue
        filtrados.append(m)
    return filtrados


def calcular_score(texto_original: str, texto_corregido: str) -> dict:
    palabras = len(texto_original.split())

    if palabras == 0:
        return {
            "porcentaje": 100,
            "nivel": "Perfecto",
            "errores_detectados": 0,
            "ortografia": {"porcentaje": 100, "nivel": "Perfecto"},
            "gramatica": {"porcentaje": 100, "nivel": "Perfecto"},
        }

    # Errores en original — filtrados
    errores_original = _filtrar_errores(tool.check(texto_original), texto_original)

    # Errores que quedaron en el texto corregido
    errores_corregido = _filtrar_errores(tool.check(texto_corregido), texto_corregido)

    # Solo penalizar errores que quedaron sin corregir
    errores_efectivos = errores_corregido

    pen_orto = 0
    pen_gram = 0

    for error in errores_efectivos:
        categoria = error.category
        if categoria in CATEGORIAS_ORTOGRAFIA:
            pen_orto += 5
        elif categoria in CATEGORIAS_GRAMATICA:
            pen_gram += 7
        else:
            pen_orto += 2
            pen_gram += 2

    # Penalización adicional por cantidad de errores originales
    # (refleja qué tan mal escribió el usuario)
    proporcion_errores = len(errores_original) / palabras
    pen_orto += round(proporcion_errores * 10)
    pen_gram += round(proporcion_errores * 5)

    def calcular(penalizacion):
        score = max(0, 100 - (penalizacion / palabras * 20))
        return round(min(100, score))

    def nivel(score):
        if score >= 90: return "Excelente"
        if score >= 75: return "Bueno"
        if score >= 55: return "Regular"
        if score >= 35: return "Necesita mejorar"
        return "Requiere atención"

    score_orto = calcular(pen_orto)
    score_gram = calcular(pen_gram)
    score_total = round((score_orto + score_gram) / 2)

    return {
        "porcentaje": score_total,
        "nivel": nivel(score_total),
        "errores_detectados": len(errores_original),
        "ortografia": {
            "porcentaje": score_orto,
            "nivel": nivel(score_orto)
        },
        "gramatica": {
            "porcentaje": score_gram,
            "nivel": nivel(score_gram)
        }
    }