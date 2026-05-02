def generar_variantes(texto_original: str, texto_corregido: str) -> list:
    """
    Genera variantes adicionales SOLO si el texto original
    tiene ambigüedad o múltiples formas válidas de corrección.
    Máximo 2 variantes extra (total 3 con la principal).
    Si el texto corregido es claramente el mejor, retorna lista vacía.
    """
    variantes = []

    # Sin variantes si el texto es muy corto
    if len(texto_corregido.split()) < 4:
        return []

    # Sin variantes si el original ya estaba muy bien
    if texto_original.strip() == texto_corregido.strip():
        return []

    # Variante formal: primera letra mayúscula + punto final
    variante_formal = texto_corregido
    if not variante_formal.endswith((".", "?", "!")):
        variante_formal = variante_formal + "."
    if variante_formal != texto_corregido:
        variantes.append({
            "texto": variante_formal,
            "etiqueta": "Formal"
        })

    # Variante sin puntuación final (estilo casual)
    variante_casual = texto_corregido.rstrip(".")
    if variante_casual != texto_corregido and variante_casual != variante_formal:
        variantes.append({
            "texto": variante_casual,
            "etiqueta": "Casual"
        })

    return variantes[:2]