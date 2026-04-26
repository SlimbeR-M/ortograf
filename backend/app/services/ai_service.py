import language_tool_python

tool = language_tool_python.LanguageTool('es')

def corregir_texto(texto):
    errores = tool.check(texto)
    texto_corregido = language_tool_python.utils.correct(texto, errores)
    return errores, texto_corregido
