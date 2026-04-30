def finalize_text(text: str) -> str:
    text = text.strip()

    if text:
        text = text[0].upper() + text[1:]

    if not text.endswith(("?", ".", "!")):
        text += "."

    return text