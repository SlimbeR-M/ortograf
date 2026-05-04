import re

# ─── Contextos bloqueadores ───────────────────────────────────────────────────

ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas",
             "este", "esta", "ese", "esa", "aquel", "aquella"}

MAS_BLOQUEADORES = {
    "no", "ni", "nunca", "jamás", "tampoco", "pudo", "quiso",
    "quiere", "quería", "sabía", "sabe", "puede", "podía",
    "fue", "era", "es", "son", "hay", "tiene", "tenía",
    "pero", "sino", "aunque", "sin", "embargo", "que", "si",
    "se", "me", "te", "le", "lo", "la", "nos",
    "vale", "dijo", "llegó",
}

MAS_SUSTANTIVOS_CANTIDAD = {
    "personas", "gente", "tiempo", "dinero", "agua", "comida",
    "trabajo", "espacio", "luz", "aire", "energía", "información",
    "datos", "recursos", "opciones", "razones", "problemas",
    "cosas", "días", "horas", "años", "meses", "semanas"
}

MAS_ADJETIVOS_GRADO = {
    "grande", "pequeño", "pequeña", "fácil", "difícil", "rápido",
    "lento", "bueno", "malo", "alta", "alto", "bajo", "baja",
    "largo", "corto", "fuerte", "débil", "bonito", "feo",
    "importante", "posible", "necesario", "útil", "seguro",
    "claro", "oscuro", "cerca", "lejos", "tarde", "temprano"
}

VERBOS_3RA = {
    "es", "fue", "era", "será", "tiene", "tenía", "dijo",
    "viene", "sabe", "puede", "llegó", "salió", "hizo",
    "quiso", "va", "venía", "llegaba", "salía", "está",
    "estaba", "habrá", "queda", "quedó", "sepa", "diga",
    "quiera", "venga", "tenga", "pueda", "haga", "sea",
    "compre", "compra", "lleve", "lleva", "traiga", "trae",
    "pague", "paga", "dice", "vea", "ve", "salga",
    "sale", "entre", "entra", "suba", "sube", "baje", "baja",
    "revisará", "revisara", "mirará", "mirara", "verá", "vera",
    "hará", "hara", "pondrá", "pondra", "sabrá", "sabra",
    "podrá", "podra", "querrá", "querra", "vendrá", "vendra",
    "tendrá", "tendra", "dirá", "dira", "irá", "ira",
    "traerá", "traera", "llevará", "llevara", "pagará", "pagara",
    "romperá", "rompera", "cuidará", "cuidara", "guardará", "guardara",
    "entenderá", "entendera", "queja", "quejará", "quejara",
    "rompe", "cuida", "guarda", "entiende", "necesita", "quiere",
    "come", "bebe", "lee", "escribe", "corre", "vive", "trabaja",
    "estudia", "juega", "duerme", "habla", "llama", "espera",
    "camina", "llega", "sale", "entra", "abre", "cierra",
    "pone", "toma", "da", "hace", "ve", "oye", "siente",
    "piensa", "cree", "sabe", "conoce", "recuerda", "olvida", 
    "entienda", "comprenda", "vea", "note", "observe",
    "recuerde", "olvide", "decida", "elija", "acepte",
    "rechace", "apruebe", "firme", "pague", "cobre",
}

VERBOS_2DA = {
    "eres", "fuiste", "serás", "estás", "estabas", "tienes",
    "tenías", "puedes", "podías", "debes", "sabes", "quieres",
    "vas", "vendrás", "harás", "dices", "haces", "vives"
}

VERBOS_TIEMPO = {
    "es", "era", "fue", "será", "siendo", "ha", "había",
    "hizo", "hace", "hacía", "sigue", "seguía", "continúa",
    "queda", "quedó", "resulta", "resultó"
}

PREPOSICIONES_LUGAR = {
    "en", "sobre", "bajo", "dentro", "fuera", "encima",
    "debajo", "junto", "cerca", "lejos", "delante", "detrás",
    "entre", "contra", "hacia", "desde"
}

CLITICOS = {"lo", "la", "le", "se", "me", "te", "nos", "les"}

ADJETIVOS_COMUNES = {
    "caro", "barato", "bien", "mal", "listo", "roto", "lleno",
    "vacío", "vacía", "abierto", "cerrado", "limpio", "sucio",
    "solo", "ocupado", "libre", "disponible", "lento", "rápido",
    "frío", "caliente", "bueno", "malo", "grande", "pequeño",
    "claro", "oscuro", "llena", "rota", "sucia", "abierta",
    "cerrada", "vacio", "vacia"
}

INTENSIFICADORES = {"más", "mas", "muy", "tan", "bastante", "poco", "bien", "mal"}

SALUDOS_COMA = [
    r'^(Hola)(?![,])',
    r'^(Buenos días)(?![,])',
    r'^(Buenas tardes)(?![,])',
    r'^(Buenas noches)(?![,])',
    r'^(Buen día)(?![,])',
    r'^(Estimado)(?![,])',
    r'^(Querido)(?![,])',
]

DEQUEISMO = [
    r'me parece de que', r'creo de que', r'pienso de que',
    r'opino de que', r'considero de que', r'siento de que',
    r'espero de que', r'imagino de que', r'supongo de que',
    r'insisto de que',
]

CONCORDANCIA = [
    (" yo tiene ", " yo tengo "),
    (" tu no ", " tú no "),
    (" en base a ", " con base en "),
    (" de acuerdo a ", " de acuerdo con "),
]

VERBOS_PREGUNTA = {
    "preguntó", "pregunta", "pregunté", "dime", "dinos",
    "explica", "explicó", "sabía", "sabe", "sabes",
    "ignora", "ignoraba", "desconoce", "averigua", "averiguó",
}

HOMOFONOS_VERBALES = [
    (r'\b(él|ella|usted|Juan|María|Pedro|Ana|Carlos|Luis|yo|tú)\b(\s+\w+)?\s+\btubo\b',
     lambda m: m.group(1) + (m.group(2) or '') + ' tuvo'),
    (r'\bhalla\b (mucha|mucho|más|bastante|suficiente|poca|poco|\w+ado\b|\w+ido\b)',
     lambda m: 'haya ' + m.group(1)),
    (r'\bque halla\b', 'que haya'),
    (r'\bvalla\b (a ver|al|a la|a buscar|a hacer|a comprar|a comer|a dormir|por|hacia|\w+ar\b|\w+er\b|\w+ir\b)',
     lambda m: 'vaya ' + m.group(1)),
]

HOMOFONOS_SIMPLES = {
    r'\bvien\b': 'bien',
    r'\baber\b': 'haber',
    r'\balla\b': 'allá',
    r'\bay\b(?! que)': 'hay',
    r'\bbaso\b': 'vaso',
    r'\bojala\b': 'ojalá',
}


def _limpiar_nucleo(palabra: str) -> str:
    return re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabra).lower()


def _tildar(original: str, sin_tilde: str, con_tilde: str) -> str:
    """Solo agrega tilde. NUNCA usa capitalize() ni title()."""
    if original == sin_tilde:
        return con_tilde
    if original == sin_tilde.upper():
        return con_tilde.upper()
    if original[0].isupper() and original[1:].islower():
        return con_tilde[0].upper() + con_tilde[1:]
    return original


def _aplicar_tildes_ngram(text: str) -> str:
    palabras = text.split()
    cambios = []

    for i, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)

        sig_raw = palabras[i + 1] if i + 1 < len(palabras) else ""
        sig = re.sub(r'[^a-záéíóúüñ]', '', sig_raw.lower())
        dos_sig_raw = palabras[i + 2] if i + 2 < len(palabras) else ""
        dos_sig = re.sub(r'[^a-záéíóúüñ]', '', dos_sig_raw.lower())
        tres_sig_raw = palabras[i + 3] if i + 3 < len(palabras) else ""
        tres_sig = re.sub(r'[^a-záéíóúüñ]', '', tres_sig_raw.lower())

        match_pref = re.match(r'^(["\'\¿¡\(\[]*)', palabra)
        prefijo = match_pref.group(1) if match_pref else ""
        match_suf = re.search(r'(["\'\?!,\.;:\)\]]+)$', palabra)
        sufijo = match_suf.group(1) if match_suf else ""
        nucleo_orig = palabra[
            len(prefijo): len(palabra) - len(sufijo) if sufijo else len(palabra)
        ]

        # ── mas / más ─────────────────────────────────────────────────────
        if nucleo == "mas":
            # Bloqueador → salir inmediatamente
            if sig in MAS_BLOQUEADORES or palabra.endswith(","):
                continue

            # Solo tildar si explícitamente permitido
            if sig not in MAS_ADJETIVOS_GRADO and \
               sig not in MAS_SUSTANTIVOS_CANTIDAD and \
               not sig.isdigit():
                continue

            cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))

        # ── el / él ───────────────────────────────────────────────────────
        elif nucleo == "el":
            # LOOK-AHEAD: clítico + verbo → pronombre → tildar
            # Esta regla va PRIMERO, antes del bloqueo de minúsculas
            if sig in CLITICOS and (
                dos_sig in VERBOS_3RA or
                dos_sig in VERBOS_2DA or
                tres_sig in VERBOS_3RA or
                tres_sig in VERBOS_2DA
            ):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue

            # "el se queja", "el se va" → se + verbo → pronombre
            if sig == "se" and dos_sig in VERBOS_3RA | VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue

            # Verbo de 3ra directo → pronombre
            if sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue

            # Negación + verbo → pronombre
            if sig in {"no", "ni", "nunca", "jamás"} and dos_sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue

            # Todo lo demás → artículo → no tildar
            continue

        # ── esta / está y este / esté ─────────────────────────────────────
        elif nucleo in ("esta", "este"):
            sin_t = nucleo
            con_t = "está" if nucleo == "esta" else "esté"

            if sig in PREPOSICIONES_LUGAR:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))
            elif sig in ADJETIVOS_COMUNES:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))
            elif sig in INTENSIFICADORES:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))
            elif sig in VERBOS_3RA | VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))

        # ── tu / tú ───────────────────────────────────────────────────────
        elif nucleo == "tu":
            if sig in VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))

        # ── si / sí ───────────────────────────────────────────────────────
        elif nucleo == "si":
            # "sí" afirmación cuando sigue verbo o va solo
            AFIRMACION_CONTEXTO = VERBOS_3RA | VERBOS_2DA | {"vaya", "viene", "claro"}
            if sig in AFIRMACION_CONTEXTO:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue
            # "sí" reflexivo: "él mismo", precedido de pronombre
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())
            if anterior in {"para", "por", "en", "de", "a"} and sig in CLITICOS | {"mismo", "misma"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

        # ── se / sé ───────────────────────────────────────────────────────
        elif nucleo == "se":
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            # "no sé si" → sé verbo saber
            if anterior in {"no", "nunca", "jamás"} and sig == "si":
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            # "sé" antes de infinitivo
            if bool(re.search(r'\w+(?:ar|er|ir)$', sig)):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

        # ── cual / cuál ───────────────────────────────────────────────────
        elif nucleo == "cual":
            tiene_interrogacion = "?" in text or "¿" in text
            tokens_lista = [re.sub(r'[^a-záéíóúüñ]', '', p.lower()) for p in palabras]
            ventana = tokens_lista[max(0, i-5):i]
            tiene_verbo_pregunta = any(v in VERBOS_PREGUNTA for v in ventana)
            if tiene_interrogacion or tiene_verbo_pregunta:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "cual", "cuál") + sufijo))

        # ── aun / aún ─────────────────────────────────────────────────────
        elif nucleo == "aun":
            if (sig in VERBOS_3RA or sig in VERBOS_2DA or
                    sig in VERBOS_TIEMPO or
                    sig in {"no", "ni", "nunca"}):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "aun", "aún") + sufijo))

    # Aplicar cambios — operación aislada por índice
    resultado = palabras[:]
    for idx, nueva in cambios:
        resultado[idx] = nueva

    return " ".join(resultado)


def _proteger_subjuntivo(text: str) -> str:
    subjuntivos = [
        "realice", "realices", "realicen", "haga", "hagas", "hagan",
        "sea", "seas", "sean", "esté", "estés", "estén",
        "tenga", "tengas", "tengan", "pueda", "puedas", "puedan",
        "venga", "vengas", "vengan",
    ]
    for verbo in subjuntivos:
        text = re.sub(
            rf'\bque\b ({verbo})\b',
            lambda m: f'que __SUBJ_{m.group(1)}__',
            text, flags=re.IGNORECASE
        )
    return text


def _restaurar_subjuntivo(text: str) -> str:
    return re.sub(r'__SUBJ_(\w+)__', r'\1', text)


def correct_grammar(text: str) -> str:

    # 1. Homófonos simples PRIMERO — minúscula estricta
    for patron, correcto in HOMOFONOS_SIMPLES.items():
        def _reemplazar_casing(m, correcto=correcto):
            original = m.group(0)
            if original.isupper():
                return correcto.upper()
            return correcto.lower()
        text = re.sub(patron, _reemplazar_casing, text, flags=re.IGNORECASE)

    # 2. Homófonos verbales
    for patron, reemplazo in HOMOFONOS_VERBALES:
        if callable(reemplazo):
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)
        else:
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    # 3. Proteger subjuntivos
    text = _proteger_subjuntivo(text)

    # 4. Coma después de saludo inicial
    for patron in SALUDOS_COMA:
        text = re.sub(patron, lambda m: m.group(1) + ',', text)

    # 5. Coma antes de conjunciones adversativas
    text = re.sub(
        r'(?<![,]) \b(pero|aunque|sino)\b',
        lambda m: ', ' + m.group(1),
        text
    )

    # 6. Tildes por N-grams
    text = _aplicar_tildes_ngram(text)

    # 7. Dequeísmo
    for patron in DEQUEISMO:
        correcto = patron.replace(' de que', ' que')
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 8. Concordancia
    for incorrecto, correcto in CONCORDANCIA:
        text = text.replace(incorrecto, correcto)

    # 9. Sino vs si no
    text = re.sub(
        r'\bsino\b (se|me|te|le|lo|la|les|las|nos|viene|va|puede|quiere|tiene|dan|hay)',
        lambda m: 'si no ' + m.group(1),
        text
    )
    text = re.sub(
        r',\s*si no\b (?!se |me |te |le |lo |la |les |las |viene |va |puede |quiere |tiene )',
        ', sino ',
        text
    )

    # 10. Restaurar subjuntivos
    text = _restaurar_subjuntivo(text)

    return text