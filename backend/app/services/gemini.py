import os
from groq import Groq


def pulir_con_gemini(texto_original: str, texto_corregido: str) -> str:
    """
    Pule el texto usando Groq como capa final de corrección semántica.
    Si no hay API key o falla, devuelve texto_corregido sin cambios.
    Mantiene el nombre pulir_con_gemini para no modificar pipeline.py.
    """
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
                        "déjalo como está."
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
