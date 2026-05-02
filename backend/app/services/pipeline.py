from app.services.normalize import normalize
from app.services.slang import replace_slang
from app.services.spelling import correct_spelling, tool
from app.services.grammar import correct_grammar
from app.services.postprocess import finalize_text
from app.services.scorer import calcular_score
from app.services.variants import generar_variantes
from app.services.diff import calcular_cambios


def correct_text(text: str):
    texto_original = text

    # Pipeline de corrección
    text = normalize(text)
    text = replace_slang(text)
    text = correct_spelling(text)
    text = correct_grammar(text)
    text = finalize_text(text)

    texto_corregido = text

    # Score del usuario
    score = calcular_score(texto_original, texto_corregido)

    # Cambios realizados
    cambios = calcular_cambios(texto_original, texto_corregido)

    # Variantes adicionales (solo si aplica)
    variantes = generar_variantes(texto_original, texto_corregido)

    return {
        "texto_corregido": texto_corregido,
        "variantes": variantes,
        "cambios": cambios,
        "score": score
    }


def review_text(text: str):
    errores = tool.check(text)
    return {"errores": errores}