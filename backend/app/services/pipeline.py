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
from app.services.gemini import pulir_con_gemini


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


def correct_text(text: str):
    texto_original = text

    # 1. Slang primero — antes de cualquier análisis
    text = replace_slang(text)
    text = aplicar_correcciones_forzadas(text)

    # 2. Normalización
    text = normalize(text)

    # 3. Proteger términos técnicos
    text, mapa_tech = proteger_tecnicos(text)

    # 4. Corrección ortográfica
    text = correct_spelling(text)

    # 5. Corrección gramatical
    text = correct_grammar(text)

    # 6. Restaurar técnicos
    text = restaurar_tecnicos(text, mapa_tech)

    # 7. Homófonos
    text = resolver_homofonos(text)

    # 8. NER
    text = capitalizar_entidades(text)

    # 9. Postproceso
    text = finalize_text(text)

    texto_corregido = text

    # 10. Pulido semántico con Gemini (opcional — se omite si GEMINI_API_KEY no está configurada)
    texto_gemini = pulir_con_gemini(texto_original, texto_corregido)

    # Cambios del pipeline (original → pipeline)
    cambios = calcular_cambios(texto_original, texto_corregido)

    # Cambios adicionales de Gemini (pipeline → Gemini)
    extras = _cambios_gemini(texto_corregido, texto_gemini)
    cambios.extend(extras)

    score = calcular_score(texto_original, texto_gemini, n_cambios_gemini=len(extras))

    return {
        "texto_corregido": texto_gemini,
        "cambios": cambios,
        "score": score
    }


def review_text(text: str):
    errores = tool.check(text)
    return {"errores": errores}