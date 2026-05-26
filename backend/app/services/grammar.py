import re
import json
import os
from app.services.postprocess import _GEONOMBRES as _GEONOMBRES_GEOGRAFICOS

# ─── Carga de datos estáticos desde JSON ─────────────────────────────────────

_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'grammar')

def _load_set(name: str) -> set:
    with open(os.path.join(_DATA, name), encoding='utf-8') as _f:
        return set(json.load(_f))

def _load_dict(name: str) -> dict:
    with open(os.path.join(_DATA, name), encoding='utf-8') as _f:
        return json.load(_f)

MAS_BLOQUEADORES: set         = _load_set('mas_bloqueadores.json')
MAS_SUSTANTIVOS_CANTIDAD: set = _load_set('sustantivos_cantidad.json')
MAS_ADJETIVOS_GRADO: set      = _load_set('adjetivos_grado.json')
VERBOS_3RA: set               = _load_set('verbos_3ra.json')
VERBOS_2DA: set               = _load_set('verbos_2da.json')
VERBOS_TIEMPO: set            = _load_set('verbos_tiempo.json')
VERBOS_PASADO_1RA: dict       = _load_dict('verbos_pasado.json')
VERBOS_FUTURO: dict           = _load_dict('verbos_futuro.json')
ADJETIVOS_COMUNES: set        = _load_set('adjetivos_comunes.json')

# ─── Contextos bloqueadores ───────────────────────────────────────────────────

ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas",
             "este", "esta", "ese", "esa", "aquel", "aquella"}

PREPOSICIONES_LUGAR = {
    "en", "sobre", "bajo", "dentro", "fuera", "encima",
    "debajo", "junto", "cerca", "lejos", "delante", "detrás",
    "entre", "contra", "hacia", "desde"
}

CLITICOS = {"lo", "la", "le", "se", "me", "te", "nos", "les"}

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
    r'\bah\b(?= ido| estado| sido| tenido| podido| querido| dicho| hecho)': 'ha',
}


VERBOS_DESEO_PASADO = {
    "esperaba", "queria", "quería", "pedia", "pedía", "necesitaba",
    "requeria", "requería", "deseaba", "preferia", "prefería",
    "rogaba", "suplicaba", "ordenaba", "mandaba", "exigia", "exigía",
    "pidio", "pidió", "ordeno", "ordenó", "rogo", "rogó",
    "quiso", "deseo", "deseó",
}

# Verbos de anuncio: introducen futuro reportado ("dijo que haría") → no subjuntivo
VERBOS_ANUNCIO = {
    "anunció", "anuncio", "dijo", "informó", "informo", "confirmó",
    "confirmo", "declaró", "declaro", "comunicó", "comunico",
    "adelantó", "adelanto", "reveló", "revelo", "señaló", "señalo",
    "indicó", "indico", "aseguró", "aseguro", "sostuvo", "afirmó", "afirmo",
}

_SUBJUNTIVO_ANTE_QUE = {"de", "para", "sin", "antes", "a", "con"}
_CORTE_CLAUSULA = {
    "y", "o", "pero", "sino", "porque", "ya", "así", "entonces",
    "pues", "además", "mientras", "aunque",
}


def _es_subjuntivo_clausula(palabras: list, j: int) -> bool:
    """True si la palabra en posición j está en cláusula subjuntiva.

    Busca hacia atrás hasta 9 posiciones un 'que' precedido por
    preposición subordinante o verbo de deseo/expectativa.
    Devuelve False si el 'que' es introducido por verbo de anuncio
    (en ese caso el verbo siguiente es futuro reportado, no subjuntivo).
    """
    for k in range(j - 1, max(j - 10, -1), -1):
        w = re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabras[k]).lower()
        if w in _CORTE_CLAUSULA:
            break
        if w == "que":
            # RAE: "que" al inicio absoluto de oración es siempre conjunción
            # subordinante (no puede ser relativo sin antecedente previo).
            if k == 0:
                return True
            ante_que = re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabras[k - 1]).lower()
            # Verbo de anuncio → futuro reportado → no bloquear tilde
            if ante_que in VERBOS_ANUNCIO:
                return False
            if ante_que in _SUBJUNTIVO_ANTE_QUE or ante_que in VERBOS_DESEO_PASADO:
                return True
            break
    return False


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
    parrafos = text.split('\n')
    return '\n'.join(_procesar_parrafo_ngram(p) for p in parrafos)


def _procesar_parrafo_ngram(text: str) -> str:
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

        if nucleo == "mas":
            if sig in MAS_BLOQUEADORES or palabra.endswith(","):
                continue
            # Si anterior es infinitivo → "esforzarme más", "trabajar más"
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior_nucleo = _limpiar_nucleo(anterior_raw)
            es_infinitivo_anterior = bool(re.search(r'\w+(?:ar|er|ir|rme|rte|rse|rnos)$', anterior_nucleo))
            if es_infinitivo_anterior:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            # Si anterior es verbo conjugado → "me guste más", "lo que más"
            es_verbo_anterior = bool(re.search(r'\w+(?:e|a|o|en|an|on)$', anterior_nucleo)) and len(anterior_nucleo) > 3
            if es_verbo_anterior and anterior_nucleo not in MAS_BLOQUEADORES:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            if sig == "de" and (dos_sig.isdigit() or dos_sig in MAS_SUSTANTIVOS_CANTIDAD):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            if sig not in MAS_ADJETIVOS_GRADO and \
               sig not in MAS_SUSTANTIVOS_CANTIDAD and \
               not sig.isdigit():
                continue
            cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))

        elif nucleo == "el":
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior_nucleo = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            if sig in CLITICOS and (
                dos_sig in VERBOS_3RA or dos_sig in VERBOS_2DA or
                tres_sig in VERBOS_3RA or tres_sig in VERBOS_2DA
            ):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig == "se" and dos_sig in VERBOS_3RA | VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in {"no", "ni", "nunca", "jamás"} and dos_sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            ADVERBIOS_PRONOMBRE = {"también", "tampoco", "siempre", "nunca",
                                   "ya", "todavía", "aún", "solo", "sólo"}
            if sig in ADVERBIOS_PRONOMBRE:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if anterior_nucleo == "a" and (not sig or sufijo or sig[0].isupper()):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if anterior_nucleo == "a" and sig in {"quien", "quién", "que", "cual"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in {"quien", "quién"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            # "el señaló/analizó/..." — verbo pasado ya tildado por paso 5.5
            if sig in set(VERBOS_PASADO_1RA.values()):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            # "según él la IA / según él explicó" — preposición personal
            _PREP_PRONOMBRE = {"según", "segun"}
            if anterior_nucleo in _PREP_PRONOMBRE and (
                sig in VERBOS_3RA or
                sig in set(VERBOS_PASADO_1RA.values()) or
                sig in {"la", "los", "las", "un", "una"}
            ):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            continue

        elif nucleo in ("esta", "este"):
            sin_t = nucleo
            con_t = "está" if nucleo == "esta" else "esté"
            es_gerundio = bool(re.search(r'\w+(?:ando|iendo)$', sig))
            if sig in PREPOSICIONES_LUGAR or \
               sig in ADJETIVOS_COMUNES or \
               sig in INTENSIFICADORES or \
               sig in VERBOS_3RA | VERBOS_2DA or \
               es_gerundio:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))

        elif nucleo == "tu":
            # "tú que", "tú quien" → siempre pronombre
            if sig in {"que", "quien", "quién", "cual", "cuál"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))
                continue
            if "?" in text or "¿" in text:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))
                continue
            if sig in VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))

        elif nucleo == "si":
            if i == 0 or palabra[0].isupper():
                continue

            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            CONJUNCIONES = {"pero", "aunque", "y", "o", "ni", "sino",
               "porque", "como", "mas", "se", "sé", "que",
               "pregunte", "pregunté", "pregunto", "preguntó"}
            if anterior in CONJUNCIONES:
                # Excepción: "respondió que sí", "dijo que sí"
                VERBOS_RESPUESTA = {"respondio", "respondió", "dijo", "contesto",
                                   "contestó", "afirmo", "afirmó", "confirmo", "confirmó"}
                anterior_a_anterior = _limpiar_nucleo(palabras[i-2]) if i > 1 else ""
                if anterior == "que" and anterior_a_anterior in VERBOS_RESPUESTA:
                    cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                    continue
                continue

            # "por sí mismo", "en sí misma" → pronombre reflexivo enfático
            if anterior in {"para", "por", "en", "de", "a"} and sig in CLITICOS | {"mismo", "misma"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

            AFIRMACION_DIRECTA = {"yo", "claro", "pues", "bueno", "obvio"}
            if anterior in AFIRMACION_DIRECTA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

            # RAE: "si" seguido de verbo conjugado o clítico+verbo en posición
            # mid-sentence es conjunción condicional, no adverbio afirmativo.
            # Solo se añade tilde cuando hay evidencia positiva de afirmación:
            # la palabra anterior termina en coma (", sí lo haré").
            AFIRMACION_CONTEXTO = VERBOS_3RA | VERBOS_2DA | {"vaya", "viene", "claro"}
            if anterior_raw.endswith(',') and (sig in AFIRMACION_CONTEXTO or sig in CLITICOS):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

        elif nucleo == "se":
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            if anterior in {"no", "nunca", "jamás", "si", "sí", "yo", "lo"} and sig in {"si", "sí", "que", ""}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            if bool(re.search(r'\w+(?:ar|er|ir)$', sig)):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            # "solo sé", "yo sé" → verbo saber
            if anterior in {"solo", "sólo", "yo", "tampoco", "también"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            if anterior in {"ahora", "solo", "sólo", "tampoco", "también",
                            "no", "nunca", "jamás", "si", "sí", "yo", "lo"} and \
                sig in {"que", "si", "sí", ""}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

        elif nucleo == "cual":
            tiene_interrogacion = "?" in text or "¿" in text
            tokens_lista = [re.sub(r'[^a-záéíóúüñ]', '', p.lower()) for p in palabras]
            ventana = tokens_lista[max(0, i-5):i]
            tiene_verbo_pregunta = any(v in VERBOS_PREGUNTA for v in ventana)
            if tiene_interrogacion or tiene_verbo_pregunta:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "cual", "cuál") + sufijo))

        elif nucleo == "aun":
            if (sig in VERBOS_3RA or sig in VERBOS_2DA or
                    sig in VERBOS_TIEMPO or sig in {"no", "ni", "nunca"}):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "aun", "aún") + sufijo))
        
        elif nucleo == "como":
            # "cómo" interrogativo indirecto — precedido de verbo de pregunta
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())
            VERBOS_PREGUNTA_INDIRECTA = {
                "pregunto", "preguntó", "pregunta", "pregunté",
                "dime", "dinos", "explica", "explicó", "saber",
                "sabes", "sabe", "sabía", "ignora", "ignoraba",
                "cuenta", "contó", "describe", "describió",
                "averigua", "averiguó", "me", "te", "le", "nos"
            }
            if anterior in VERBOS_PREGUNTA_INDIRECTA or "?" in text or "¿" in text:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "como", "cómo") + sufijo))

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
    # RAE: no se inserta coma cuando ya hay signo de puntuación fuerte antes
    # (punto y coma, punto, interrogación, exclamación) — evita ";, pero".
    text = re.sub(
        r'(?<![,;.!?]) \b(pero|aunque|sino)\b',
        lambda m: ', ' + m.group(1),
        text
    )

    # 5.1 Coma ante "quien" en cláusulas explicativas (relativo no restrictivo)
    # El grupo capturado excluye signos de puntuación para evitar "programar;, quien".
    _BLOQ_QUIEN = {"a", "para", "con", "de", "por", "sin", "ante", "sobre",
                   "tras", "se", "sé", "sabe", "sabes", "no", "es", "era",
                   "que", "lo", "al", "del", "ni", "hay"}
    def _fix_quien_comma(m):
        return m.group(0) if m.group(1).lower() in _BLOQ_QUIEN else m.group(1) + ', ' + m.group(2)
    text = re.sub(r'([^\s,;.!?]+) (quien)\b', _fix_quien_comma, text, flags=re.IGNORECASE)

    # 5.2 Comas alrededor de "por ejemplo" en el interior de una oración
    text = re.sub(
        r'(?<=[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]) (por ejemplo) ',
        ', por ejemplo, ',
        text, flags=re.IGNORECASE
    )

    # 5.5 Verbos en pasado sin tilde
    # RAE: "de" introduce sintagma preposicional donde el verbo no puede ser
    # pretérito de 1ª persona ("de doble filo" → adjetivo, no "doblé").
    BLOQUEADORES_SUBJ = {"para", "si", "aunque",
                         "ojalá", "el", "un", "la", "una", "mi", "tu", "su", "antes", "de"}

    AMBIGUOS = {"trabajo", "estudio", "caso", "trato", "cambio",
            "inicio", "termino", "aumento", "bajo",
            "peso", "cobro", "monto", "noto", "camino", "regreso",
            "viaje", "avance", "seria", "proceso",
            "desarrollo", "ingreso", "progreso", "registro", "acceso",
            "apoyo", "empleo", "ensayo", "relevo", "relato", "cargo",
            "mando", "manejo", "arreglo", "ajuste", "rechazo", "retraso",
            "reemplazo", "rescate", "repaso", "reflejo", "remedio",
            "recurso", "riesgo", "resumen", "turno", "paso",
            "anuncio", "acuerdo", "intento", "aumento", "decreto",
            "impacto", "resultado", "efecto",
            "negocio",  # negociar (pasado) vs sustantivo "negocio"
            "indico",  # indicar (pasado) vs adjetivo geográfico "índico"
            "critico",  # criticar (pasado) vs adjetivo/sustantivo "crítico"
            "diagnostico",  # diagnosticar (pasado) vs sustantivo "diagnóstico"
            "diseño",  # diseñar (pasado) vs sustantivo "diseño"
            "publico",  # publicar (pasado) vs adjetivo "público"
            }

    # Formas esdrújulas correctas para palabras en AMBIGUOS cuando son sustantivos/adjetivos
    _FORMAS_ESDRUJULO = {
        "diagnostico": "diagnóstico",
        "critico": "crítico",
        "termino": "término",
        "publico": "público",
    }

    VERBOS_PRESENTE_1RA = {"espero", "busco", "necesito", "quiero",
                       "deseo", "uso", "tomo", "como",
                       "bebo", "creo", "pienso", "siento", "digo",
                       "hago", "voy", "vengo", "tengo", "puedo",
                       "sé", "veo", "oigo", "pido", "sigo"}

    FORZADORES_PASADO = {"él", "ella", "usted", "ellos", "ellas", "ustedes"}

    DETERMINANTES_RELATIVOS = {"lo", "el", "la", "los", "las", "todo", 
                           "algo", "nada", "hasta", "para", "cuando"}

    def _es_futuro(palabra: str) -> bool:
        # Solo verdaderos futuros verbales: terminan en r + vocal acentuada (hablará, vendrá…)
        return bool(re.search(r'r[áéíóú][sn]?$', palabra.lower()))

    palabras = text.split()
    resultado = []
    for j, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)
        anterior = _limpiar_nucleo(palabras[j-1]) if j > 0 else ""
        anterior_orig = palabras[j-1] if j > 0 else ""
        anterior_a_que = _limpiar_nucleo(palabras[j-2]) if j > 1 else ""
        tres_antes = _limpiar_nucleo(palabras[j-3]) if j > 2 else ""
        siguiente = _limpiar_nucleo(palabras[j+1]) if j + 1 < len(palabras) else ""
        anterior_es_futuro = _es_futuro(anterior_orig) if anterior_orig else False

        # Cuando la palabra termina en puntuación de fin de oración (.?!), el siguiente
        # token pertenece a otra oración y no debe usarse como contexto gramatical
        # (RAE: el sustantivo "estudio" en "regiones de estudio. El foro" no es verbo).
        siguiente_adj = "" if re.search(r'[.?!]+$', palabra) else siguiente

        # Cláusula subjuntiva detectada por lookback → nunca tildar
        if _es_subjuntivo_clausula(palabras, j):
            resultado.append(palabra)
            continue

        # Verificar si "que" anterior es pronombre relativo
        # ej: "todo lo que pasó", "algo que ocurrió"
        que_es_relativo = (anterior == "que" and anterior_a_que in DETERMINANTES_RELATIVOS)

        # Bloqueadores efectivos — si "que" es relativo, no bloquea
        bloqueadores_efectivos = BLOQUEADORES_SUBJ - {"que"} if que_es_relativo else BLOQUEADORES_SUBJ

        # Verbos presente primera persona — lógica especial
        if nucleo in VERBOS_PRESENTE_1RA:
            # Sigue "que" → presente → no tildar
            if siguiente in {"que", "poder", "hacer", "ir", "venir", "ser", "estar"}:
                resultado.append(palabra)
                continue
            # Inicio de oración o precedido de "yo" → presente → no tildar
            if anterior in {"yo", ""} or j == 0:
                resultado.append(palabra)
                continue
            # Precedido de pronombre sujeto o sustantivo → pasado → tildar
            if anterior_orig in FORZADORES_PASADO or (
                anterior not in {"y", "o", "pero", "aunque", "sino", "que",
                                  "si", "porque", "como", "cuando", "donde"}
                and len(anterior) > 2
            ):
                if nucleo in VERBOS_PASADO_1RA:
                    corregido = VERBOS_PASADO_1RA[nucleo]
                    if palabra[0].isupper():
                        corregido = corregido[0].upper() + corregido[1:]
                    resultado.append(corregido)
                    continue
            resultado.append(palabra)
            continue

        # RAE: "se + verbo-e" es reflexivo/impersonal o subjuntivo, nunca pretérito
        # de 1ª persona ("se doble", "se revise", "se aplique").
        _es_se_subj = anterior == "se" and nucleo.endswith("e")

        if nucleo in VERBOS_PASADO_1RA and (
            anterior not in bloqueadores_efectivos or
            anterior_orig in FORZADORES_PASADO or
            (anterior == "el" and nucleo not in AMBIGUOS)
        ) and not anterior_es_futuro and not _es_se_subj:
            _AMBIGUOS_BLOQ = {"el", "al", "un", "la", "una",
                              "mi", "tu", "su", "del", "este",
                              "ese", "aquel", "nuestro", "cada", "de",
                              "a", "por", "para", "con", "sin",
                              "costo", "costó", "habia", "había",
                              "costado", "escolar", "nuevo",
                              "duro", "mucho", "poco",
                              "incluye", "incluyen", "incluía"}
            # Adjetivos que aparecen entre determinante y sustantivo en "DET ADJ SUST":
            # solo ellos habilitan la búsqueda dos posiciones atrás (anterior_a_que).
            # Sujetos-sustantivo como "médico", "juez", "rector" no están aquí → no
            # alcanzan hasta el "el" que los precede para confundir verbo con sustantivo.
            _MODS_PREVIOS = {"buen", "gran", "mal", "bien", "mejor", "peor",
                             "primer", "último", "cierto", "cierta",
                             "propio", "propia", "mismo", "misma"}
            _SUFIJOS_ADJ = ("al", "oso", "osa", "ico", "ica", "ivo", "iva",
                            "ble", "ante", "iente", "ado", "ada", "ido", "ida")
            _ARTS_DIRECTOS = {"el", "la", "los", "las", "un", "una", "al", "del"}
            if nucleo in AMBIGUOS and siguiente == "que" and anterior not in _ARTS_DIRECTOS:
                # "SUJETO verbo que [cláusula]" → verbo pasado introduce cláusula sustantiva
                corregido = VERBOS_PASADO_1RA[nucleo]
                if palabra[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                resultado.append(corregido)
            elif (nucleo in AMBIGUOS and nucleo in _GEONOMBRES_GEOGRAFICOS
                  and siguiente != "que"
                  and anterior_orig not in FORZADORES_PASADO):
                # RAE: adjetivo geográfico (ej: "océano índico") → preservar sin tilde verbal;
                # postprocess lo capitalizará como nombre propio geográfico.
                resultado.append(palabra)
            elif nucleo in AMBIGUOS and siguiente_adj not in {
                "la", "el", "los", "las", "un", "una", "unas", "unos"
            } and (siguiente_adj != "" or anterior in _AMBIGUOS_BLOQ) and (
                anterior in _AMBIGUOS_BLOQ or
                (anterior_a_que in {"el", "al", "un", "la", "una", "mi", "tu",
                                    "su", "del", "este", "ese", "aquel",
                                    "nuestro", "cada", "de", "por", "para", "con"}
                 and (anterior in _AMBIGUOS_BLOQ or anterior in _MODS_PREVIOS)) or
                (len(siguiente_adj) >= 4 and
                 any(siguiente_adj.endswith(s) for s in _SUFIJOS_ADJ)) or
                # RAE: dos verbos finitos no pueden ser consecutivos sin conjunción.
                # Si el siguiente también parece verbo pretérito y el contexto anterior
                # es un sintagma nominal (DET+SUST), la palabra AMBIGUA es adjetivo.
                (siguiente_adj in VERBOS_PASADO_1RA and
                 anterior_a_que in {"el", "al", "un", "la", "una", "mi", "tu",
                                    "su", "del", "este", "ese", "aquel",
                                    "nuestro", "cada", "de", "por", "para", "con"} and
                 len(anterior) > 2)
            ):
                # Sustantivo/adjetivo: aplicar forma esdrújula si corresponde
                if nucleo in _FORMAS_ESDRUJULO:
                    _m_suf_e = re.search(r'(["\'\?!,\.;:\)\]]+)$', palabra)
                    _suf_e = _m_suf_e.group(1) if _m_suf_e else ""
                    esdruj_form = _FORMAS_ESDRUJULO[nucleo]
                    if palabra[0].isupper():
                        esdruj_form = esdruj_form[0].upper() + esdruj_form[1:]
                    resultado.append(esdruj_form + _suf_e)
                else:
                    resultado.append(palabra)
            elif (nucleo in AMBIGUOS and
                  siguiente == "" and
                  anterior in {"y", "o", "ni", "e"} and
                  anterior_a_que not in VERBOS_PASADO_1RA):
                # Último elemento de enumeración nominal tras conjunción coordinante:
                # "investigación, innovación y desarrollo" → sustantivo, no verbo.
                resultado.append(palabra)
            elif (nucleo in AMBIGUOS and
                  siguiente in _ARTS_DIRECTOS and
                  j + 2 < len(palabras) and
                  _limpiar_nucleo(palabras[j + 2]) == anterior):
                # Patrón "N adj DET N": siguiente DET introduce construcción paralela
                # con el mismo núcleo nominal (ej: "sector público el sector privado").
                # RAE: adj modificador, no verbo transitivo.
                if nucleo in _FORMAS_ESDRUJULO:
                    _m_suf_p = re.search(r'(["\'\?!,\.;:\)\]]+)$', palabra)
                    _suf_p = _m_suf_p.group(1) if _m_suf_p else ""
                    esdruj_form = _FORMAS_ESDRUJULO[nucleo]
                    if palabra[0].isupper():
                        esdruj_form = esdruj_form[0].upper() + esdruj_form[1:]
                    resultado.append(esdruj_form + _suf_p)
                else:
                    resultado.append(palabra)
            else:
                # Preservar puntuación final (ej: "estudió." cuando es verbo ante punto)
                _m_suf_verbo = re.search(r'["\'\?!,\.;:\)\]]+$', palabra)
                _suf_verbo = _m_suf_verbo.group(0) if _m_suf_verbo else ""
                corregido = VERBOS_PASADO_1RA[nucleo]
                if palabra[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                resultado.append(corregido + _suf_verbo)
        else:
            resultado.append(palabra)
    text = " ".join(resultado)

    # 5.6 Verbos en futuro sin tilde
    palabras = text.split()
    resultado = []
    for k, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)
        # Cláusula subjuntiva → no tildar como futuro
        if _es_subjuntivo_clausula(palabras, k):
            resultado.append(palabra)
            continue
        if nucleo in VERBOS_FUTURO:
            corregido = VERBOS_FUTURO[nucleo]
            if palabra[0].isupper():
                corregido = corregido[0].upper() + corregido[1:]
            resultado.append(corregido)
        else:
            resultado.append(palabra)
    text = " ".join(resultado)

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