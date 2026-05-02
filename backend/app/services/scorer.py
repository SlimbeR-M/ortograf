import language_tool_python

tool = language_tool_python.LanguageTool("es")


def calcular_score(texto_original: str, texto_corregido: str) -> dict:
    errores_originales = tool.check(texto_original)
    palabras = len(texto_original.split())

    if palabras == 0:
        return {"porcentaje": 100, "nivel": "Perfecto", "errores": 0}

    penalizacion = 0
    for error in errores_originales:
        categoria = error.category
        if categoria in ["TYPOS", "MISSPELLING"]:
            penalizacion += 5
        elif categoria in ["GRAMMAR", "AGREEMENT"]:
            penalizacion += 7
        elif categoria in ["PUNCTUATION"]:
            penalizacion += 3
        else:
            penalizacion += 4

    # Más agresivo: divide entre palabras sin multiplicar suave
    score = max(0, 100 - (penalizacion / palabras * 20))
    score = round(min(100, score))

    if score >= 90:
        nivel = "Excelente"
    elif score >= 75:
        nivel = "Bueno"
    elif score >= 55:
        nivel = "Regular"
    elif score >= 35:
        nivel = "Necesita mejorar"
    else:
        nivel = "Requiere atención"

    return {
        "porcentaje": score,
        "nivel": nivel,
        "errores_detectados": len(errores_originales)
    }