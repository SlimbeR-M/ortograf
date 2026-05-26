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
                        "Eres un corrector ortográfico y gramatical experto "
                        "en español mexicano. Tu tarea es revisar el texto "
                        "que se te proporciona y corregir ÚNICAMENTE errores "
                        "reales según las reglas de la RAE: homófonos "
                        "incorrectos (haber/a ver, vaya/valla, asta/hasta), "
                        "palabras con significado incorrecto en contexto, "
                        "errores de concordancia gramatical, palabras mal "
                        "escritas que el corrector previo no detectó. "
                        "REGLAS IMPORTANTES: "
                        "1. Si el texto ya está correctamente escrito, "
                        "devuelve EXACTAMENTE el mismo texto sin ningún cambio. "
                        "2. NO cambies el estilo ni vocabulario del autor. "
                        "3. NO agregues ni elimines palabras innecesariamente. "
                        "4. NO cambies nombres propios, siglas ni términos técnicos. "
                        "5. Devuelve ÚNICAMENTE el texto corregido, sin "
                        "explicaciones, sin comillas, sin marcadores adicionales."
                    )
                },
                {
                    "role": "user",
                    "content": f"Revisa y corrige si es necesario:\n\n{texto_corregido}"
                }
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        resultado = response.choices[0].message.content.strip()
        print(f"[GROQ] Texto cambió: {texto_corregido != resultado}")
        return resultado if resultado else texto_corregido
    except Exception as e:
        print(f"[GROQ] ERROR: {type(e).__name__}: {e}")
        return texto_corregido
