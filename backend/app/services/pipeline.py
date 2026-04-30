from app.services.normalize import normalize
from app.services.slang import replace_slang
from app.services.spelling import correct_spelling, tool
from app.services.grammar import correct_grammar
from app.services.postprocess import finalize_text

def correct_text(text: str):
    text = normalize(text)
    text = replace_slang(text)
    text = correct_spelling(text)
    text = correct_grammar(text)
    text = finalize_text(text)

    return {"texto_corregido": text}


def review_text(text: str):
    errores = tool.check(text)
    return {"errores": errores}