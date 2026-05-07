import re

def normalize(text: str) -> str:
    # Preservar saltos de línea — procesar cada párrafo por separado
    parrafos = text.split('\n')
    resultado = []
    for parrafo in parrafos:
        parrafo = parrafo.strip()
        parrafo = re.sub(r'\s+', ' ', parrafo)
        parrafo = re.sub(r'\s+([?.!,¿¡])', r'\1', parrafo)
        resultado.append(parrafo)
    # Filtrar líneas vacías múltiples consecutivas
    texto = '\n'.join(resultado)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto