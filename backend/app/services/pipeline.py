import re
import difflib

from app.services.normalize import normalize
from app.services.slang import replace_slang
from app.services.spelling import correct_spelling, tool
from app.services.grammar import correct_grammar
from app.services.postprocess import finalize_text
from app.services.scorer import calcular_score
from app.services.diff import calcular_cambios
from app.services.tech_guard import proteger_tecnicos, restaurar_tecnicos
from app.services.ner import capitalizar_entidades
from app.services.homofonos import resolver_homofonos
from app.services.correcciones import aplicar_correcciones_forzadas
from app.services.semantic import apply_semantic_map
from app.services.gemini import pulir_con_gemini, detectar_ambiguedad


def _cambios_gemini(texto_corregido: str, texto_gemini: str) -> list:
    palabras_corr = texto_corregido.split()
    palabras_gem = texto_gemini.split()
    matcher = difflib.SequenceMatcher(None, palabras_corr, palabras_gem)
    cambios = []
    for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
        if opcode == "replace":
            orig = " ".join(palabras_corr[i1:i2])
            corr = " ".join(palabras_gem[j1:j2])
            cambios.append({
                "tipo": "reemplazo",
                "original": orig,
                "corregido": corr,
                "razon": f"Corrección semántica/gramatical: '{orig}' → '{corr}'"
            })
    return cambios


def _pipeline_parrafo(parrafo: str) -> str:
    """Pasos 1-8 del pipeline aplicados a un párrafo individual."""
    text = parrafo

    # 1. Slang + correcciones forzadas + semántico
    text = replace_slang(text)
    text = aplicar_correcciones_forzadas(text)
    try:
        text = apply_semantic_map(text)
    except Exception:
        pass

    # 2. Normalización
    text = normalize(text)

    # 3-6. Ortografía con protección de técnicos
    text, mapa_tech = proteger_tecnicos(text)
    text = correct_spelling(text)
    text = correct_grammar(text)
    text = restaurar_tecnicos(text, mapa_tech)

    # 7. Homófonos
    text = resolver_homofonos(text)

    # 8. NER
    text = capitalizar_entidades(text)

    return text


def correct_text(text: str):
    texto_original = text

    # Reducir saltos excesivos y dividir en párrafos por línea en blanco
    text_prep = re.sub(r'\n{3,}', '\n\n', text)
    parrafos = text_prep.split('\n\n')

    # Pasos 1-8: cada párrafo se procesa de forma independiente
    # Esto evita que correct_spelling colapse los \n\n al unir tokens
    parrafos_corr = [
        _pipeline_parrafo(p) if p.strip() else ''
        for p in parrafos
    ]

    # 9. Postproceso sobre el texto completo reunido
    # finalize_text ya procesa párrafo por párrafo internamente
    text = finalize_text('\n\n'.join(parrafos_corr))

    texto_corregido = text

    # 10. Pulido semántico con Groq/Gemini (opcional)
    texto_gemini = pulir_con_gemini(texto_original, texto_corregido)

    # Cambios del pipeline (original → pipeline)
    cambios = calcular_cambios(texto_original, texto_corregido)

    # Cambios adicionales de Gemini (pipeline → Gemini)
    extras = _cambios_gemini(texto_corregido, texto_gemini)
    cambios.extend(extras)

    score = calcular_score(texto_original, texto_gemini, n_cambios_gemini=len(extras))

    alternativa = None
    try:
        alternativa = detectar_ambiguedad(texto_original, texto_gemini)
    except Exception:
        pass

    return {
        "texto_corregido": texto_gemini,
        "cambios": cambios,
        "score": score,
        "alternativa": alternativa
    }


def review_text(text: str):
    errores = tool.check(text)
    return {"errores": errores}