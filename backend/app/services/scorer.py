import language_tool_python

tool = language_tool_python.LanguageTool("es")

CATEGORIAS_ORTOGRAFIA = {"TYPOS", "MISSPELLING", "MORFOLOGIK_RULE"}
CATEGORIAS_GRAMATICA = {"GRAMMAR", "AGREEMENT", "PUNCTUATION", "STYLE", "REDUNDANCY"}


def calcular_score(texto_original: str, texto_corregido: str) -> dict:
    errores = tool.check(texto_original)
    palabras = len(texto_original.split())

    if palabras == 0:
        return {
            "porcentaje": 100,
            "nivel": "Perfecto",
            "errores": 0,
            "ortografia": {"porcentaje": 100, "nivel": "Perfecto"},
            "gramatica": {"porcentaje": 100, "nivel": "Perfecto"},
        }

    pen_orto = 0
    pen_gram = 0

    for error in errores:
        categoria = error.category
        if categoria in CATEGORIAS_ORTOGRAFIA:
            pen_orto += 5
        elif categoria in CATEGORIAS_GRAMATICA:
            pen_gram += 7
        else:
            # Sin categoría clara — dividir entre ambos
            pen_orto += 2
            pen_gram += 2

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
        "errores_detectados": len(errores),
        "ortografia": {
            "porcentaje": score_orto,
            "nivel": nivel(score_orto)
        },
        "gramatica": {
            "porcentaje": score_gram,
            "nivel": nivel(score_gram)
        }
    }