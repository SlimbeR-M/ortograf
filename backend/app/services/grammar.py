def correct_grammar(text: str) -> str:
    # reglas simples iniciales (puedes expandir)
    text = text.replace(" yo tiene ", " yo tengo ")
    text = text.replace(" tu no ", " tú no ")
    return text