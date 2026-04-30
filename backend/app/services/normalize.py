import re

def normalize(text: str) -> str:
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\s+([?.!,¿¡])', r'\1', text)
    return text