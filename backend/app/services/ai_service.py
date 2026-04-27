import language_tool_python
from transformers import pipeline
from difflib import SequenceMatcher


tool = language_tool_python.LanguageTool('es')
fill_mask = pipeline('fill-mask', model='dccuchile/bert-base-spanish-wwm-cased')

def elegir_mejor_sugerencia(texto, error):
    inicio = error.offset
    fin = error.offset + error.error_length
    palabra_original = texto[inicio:fin]
    texto_con_mask = texto[:inicio] + '[MASK]' + texto[fin:]
    resultados = fill_mask(texto_con_mask)
    for sugerencia in error.replacements:
        for resultado in resultados:
            if sugerencia == resultado['token_str']:
                similitud = SequenceMatcher(None, palabra_original.lower(), sugerencia.lower()).ratio()
                if similitud > 0.5:
                    return sugerencia
    if error.replacements:
        return error.replacements[0]
    return None


def corregir_texto(texto):
    errores = tool.check(texto)
    for error in reversed(errores):
        mejor_sugerencia = elegir_mejor_sugerencia(texto, error)
        if mejor_sugerencia != None:
            inicio = error.offset
            fin = error.offset + error.error_length
            texto = texto[:inicio] + mejor_sugerencia + texto[fin:]
    return errores, texto

def revisar_texto(texto):
    errores = tool.check(texto)
    return{"errores": errores}