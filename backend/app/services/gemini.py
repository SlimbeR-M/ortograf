import os
import json
import re
from difflib import SequenceMatcher
from groq import Groq


def pulir_con_gemini(texto_original: str, texto_corregido: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    print(f"[GROQ] API key presente: {bool(api_key)}")
    if not api_key:
        return texto_corregido

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un corrector ortográfico y gramatical de español "
                        "mexicano. Tu ÚNICA función es corregir errores evidentes. "
                        "REGLAS ESTRICTAS QUE DEBES SEGUIR SIN EXCEPCIÓN: "
                        "1. Devuelve el texto corregido y NADA MÁS — sin "
                        "explicaciones, sin comentarios, sin alternativas. "
                        "2. Si el texto no tiene errores ortográficos ni gramaticales "
                        "evidentes, devuelve EXACTAMENTE el mismo texto sin "
                        "cambiar ni una sola palabra. "
                        "3. NUNCA reescribas, parafrasees, ni cambies el significado "
                        "del texto original. "
                        "4. NUNCA agregues palabras, frases, oraciones ni explicaciones "
                        "que no estaban en el texto original. "
                        "5. NUNCA cambies el vocabulario elegido por el autor salvo "
                        "que sea un error ortográfico claro. "
                        "6. Solo corrige: palabras mal escritas, homófonos incorrectos "
                        "(haber/a ver, vaya/valla, asta/hasta), tildes faltantes "
                        "que el corrector previo no detectó. "
                        "7. Si tienes duda sobre si algo es error o estilo del autor, "
                        "déjalo como está. "
                        "8. NUNCA modifiques los saltos de línea ni la estructura de párrafos. "
                        "Preserva exactamente la separación entre párrafos tal como aparece en el texto."
                    )
                },
                {
                    "role": "user",
                    "content": f"Revisa y corrige si es necesario:\n\n{texto_corregido}"
                }
            ],
            temperature=0.0,
            max_tokens=4096,
        )
        resultado = response.choices[0].message.content.strip()
        print(f"[GROQ] Texto cambió: {texto_corregido != resultado}")
        return resultado if resultado else texto_corregido
    except Exception as e:
        print(f"[GROQ] ERROR: {type(e).__name__}: {e}")
        return texto_corregido


def detectar_ambiguedad(texto_original: str, texto_corregido: str) -> dict | None:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Eres un lingüista experto en español. Detecta ambigüedad lingüística REAL "
                        "y GENUINA. La ambigüedad solo existe cuando el texto puede tener dos "
                        "interpretaciones igualmente válidas y el contexto NO permite resolver cuál "
                        "es correcta.\n\n"
                        "CASOS VÁLIDOS de ambigüedad (muy raros):\n"
                        "1. Verbo sin tilde con sujeto ausente o ambiguo donde presente e imperfecto "
                        "son igualmente posibles.\n"
                        "   Ejemplo válido: 'Hablo con tu hermano' — sin contexto no se sabe si es "
                        "presente (yo hablo ahora) o pretérito reportado de otra persona.\n"
                        "   Ejemplo NO válido: 'El presidente anuncio los resultados' — sujeto "
                        "explícito 3ª persona, solo puede ser 'anunció'.\n"
                        "   Ejemplo NO válido: 'El gobierno convoco a directores' — sujeto explícito "
                        "3ª persona, solo puede ser 'convocó'.\n"
                        "2. Homófonos que cambien completamente el significado Y donde ambas lecturas "
                        "sean plausibles en el contexto.\n"
                        "   Ejemplo válido: 'Se cayo el sistema' — puede ser caer o callar si el "
                        "contexto lo permite.\n"
                        "   Ejemplo NO válido: 'Valla que hasta donde llegamos' — 'vaya' es "
                        "claramente la forma correcta, no hay ambigüedad.\n\n"
                        "REGLAS ESTRICTAS:\n"
                        "- Si el sujeto está explícito y es 3ª persona singular o plural, NO hay "
                        "ambigüedad en verbos sin tilde.\n"
                        "- Si la corrección es evidente por contexto, NO hay ambigüedad.\n"
                        "- En caso de duda, responde tiene_ambiguedad: false.\n"
                        "- Es preferible NO reportar ambigüedad a reportar una falsa.\n"
                        "- Cada opción debe ser el texto COMPLETO, preservando exactamente la "
                        "puntuación, mayúsculas y estructura del texto corregido. Solo cambia "
                        "la palabra ambigua, nada más.\n\n"
                        "Responde ÚNICAMENTE en JSON con este formato exacto:\n"
                        '{"tiene_ambiguedad": false}\n'
                        "O si hay ambigüedad genuina:\n"
                        '{"tiene_ambiguedad": true, "opcion_a": {"texto": "texto completo opción A", '
                        '"etiqueta": "etiqueta corta", "descripcion": "máximo 8 palabras"}, '
                        '"opcion_b": {"texto": "texto completo opción B", '
                        '"etiqueta": "etiqueta corta", "descripcion": "máximo 8 palabras"}}\n'
                        "Sin explicaciones fuera del JSON."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Texto original: {texto_original}\n"
                        f"Texto corregido: {texto_corregido}\n"
                        "¿Existe ambigüedad lingüística real?"
                    )
                }
            ],
            temperature=0.0,
            max_tokens=512,
        )
        contenido = response.choices[0].message.content.strip()
        match = re.search(r'\{.*\}', contenido, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group())
        if not data.get("tiene_ambiguedad"):
            return None
        if "opcion_a" not in data or "opcion_b" not in data:
            return None

        # Comparar contra texto_corregido para que opcion_a siempre
        # coincida con el texto ya mostrado al usuario.
        sim_a = SequenceMatcher(None, texto_corregido.lower(), data['opcion_a']['texto'].lower()).ratio()
        sim_b = SequenceMatcher(None, texto_corregido.lower(), data['opcion_b']['texto'].lower()).ratio()
        if sim_b > sim_a:
            data['opcion_a'], data['opcion_b'] = data['opcion_b'], data['opcion_a']

        return data
    except Exception:
        return None