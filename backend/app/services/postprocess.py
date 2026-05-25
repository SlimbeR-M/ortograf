import re
import json
import os
import unicodedata
from functools import lru_cache
from .spelling import tool as _lt

_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
try:
    with open(os.path.join(_DATOS, 'toponimos_compuestos.json'), encoding='utf-8') as _f:
        _TOPONIMOS = sorted(json.load(_f)['paises_compuestos'], key=len, reverse=True)
except (OSError, KeyError, json.JSONDecodeError):
    _TOPONIMOS = []


@lru_cache(maxsize=256)
def _is_foreign_word(word: str) -> bool:
    """True if LT's MORFOLOGIK doesn't recognize this as a known Spanish proper noun.

    Known Spanish proper nouns (Europa, África, Berlín) have their
    capitalized/accented form as a top MORFOLOGIK suggestion, so
    strip_accents(suggestion) == strip_accents(word) → False (known).
    Foreign words (warriors, golden, state) get phonetically similar but
    semantically different Spanish words → True (foreign).
    """
    wl = word.lower()
    for m in _lt.check(wl):
        if not m.rule_id.startswith('MORFOLOGIK'):
            continue
        for sug in m.replacements[:3]:
            sug_base = ''.join(
                c for c in unicodedata.normalize('NFD', sug.lower())
                if unicodedata.category(c) != 'Mn'
            )
            word_base = ''.join(
                c for c in unicodedata.normalize('NFD', wl)
                if unicodedata.category(c) != 'Mn'
            )
            if sug_base == word_base:
                return False
        return True
    return False


def finalize_text(text: str) -> str:
    parrafos = text.split('\n')
    resultado = []
    for parrafo in parrafos:
        if not parrafo.strip():
            resultado.append('')
            continue
        parrafo = _finalizar_parrafo(parrafo)
        resultado.append(parrafo)
    return '\n'.join(resultado)


_TITULOS_RAE_RE = re.compile(
    r'(?<=\w )'
    r'(Doctor|Doctora|Ingeniero|Ingeniera|Licenciado|Licenciada'
    r'|Secretario|Secretaria|Arquitecto|Arquitecta|Maestro|Maestra'
    r'|Director|Directora|Gerente|Coordinador|Coordinadora'
    r'|Subsecretario|Subsecretaria)\b'
)


def _coma_en_enumeracion_nombres_propios(text: str) -> str:
    """
    RAE: en enumeraciones de 3+ elementos, todos los intermedios llevan coma.
    Inserta comas entre elementos con el patrón ELEM.
    ELEM cubre:
      - Placeholder de topónimo compuesto: __TOPn__
      - Artículo + 1-2 palabras (cualquier caso, 3+ chars): "el Caribe",
        "la salud", "el océano Índico", "el medio ambiente"
      - Palabra capitalizada (4+ chars): "Europa", "Asia"
    La coma se inserta ANTES del artículo del siguiente elemento.
    Los topónimos compuestos deben estar protegidos con __TOPn__ placeholders
    antes de llamar; la protección y restauración las gestiona el llamador.
    """
    _WORD = r'[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{3,}'
    _HOLD = r'(?:__TOP\d+__|__CPN\d+__)'
    _GENT = (
        r'(?:Latina|Latino|Central|Oriental|Occidental'
        r'|Septentrional|Meridional|Austral|Boreal)'
    )
    # Artículo + 1-2 palabras de cualquier caso (3+ chars cada una).
    # Cubre: "el Caribe" (art+Cap), "la salud" (art+lower), "el océano Índico"
    # (art+lower+Cap), "el medio ambiente" (art+lower+lower),
    # "el TDAH" / "la UNESCO" (art+sigla todo-mayúsculas).
    _ART_WORD = r'[a-záéíóúüñA-ZÁÉÍÓÚÜÑ][a-záéíóúüñA-ZÁÉÍÓÚÜÑ]{2,}'
    # RAE: preposiciones y contracciones forman sintagma indivisible con su complemento
    # y nunca son el último componente de un elemento de enumeración.
    _PREPS = (
        r'(?:del|de|en|con|por|para|sin|sobre|entre|ante|bajo|tras'
        r'|hacia|hasta|desde|según|durante|mediante|contra|al)'
    )
    _ART_WORD2 = r'(?!' + _PREPS + r'\b)' + _ART_WORD
    # \b evita capturar "los" embebido en palabras (ej: "Pueblos" contiene "los")
    _ART_ELEM = r'\b(?:el|la|los|las) ' + _ART_WORD + r'(?: ' + _ART_WORD2 + r')?'
    # Cubre "el Golfo de México", "el Mar del Norte": art + palabra + de/del + palabra
    _ART_PREP_ELEM = r'\b(?:el|la|los|las) ' + _ART_WORD + r' de(?:l)? ' + _ART_WORD
    ELEM = r'(?:' + _HOLD + r'|' + _ART_PREP_ELEM + r'|' + _ART_ELEM + r'|' + _WORD + r')'

    patron = re.compile(
        r'(' + ELEM + r') (?!' + _GENT + r'\b)(' + ELEM + r')'
        r'(?=(?:(?:, | )' + ELEM + r')* (?:y|e|u|o|ni) ' + ELEM + r')'
    )

    anterior = None
    while anterior != text:
        anterior = text
        text = patron.sub(lambda m: m.group(1) + ', ' + m.group(2), text)

    return text


def _coma_en_enumeracion_sustantivos(text: str) -> str:
    """
    RAE §91.2.1: en una enumeración de 3+ grupos nominales comunes sin coma,
    todos los intermedios llevan coma. Complementa _coma_en_enumeracion_nombres_propios,
    que cubre nombres propios y elementos precedidos de artículo.
    Solo actúa sobre palabras de contenido en minúscula (los nombres propios
    capitalizados están cubiertos por la función anterior).
    Conservadora: requiere ≥3 elementos; excluye formas verbales comunes.
    """
    _FUNC = frozenset({
        'sobre', 'entre', 'desde', 'hasta', 'según', 'hacia',
        'durante', 'mediante', 'contra', 'porque', 'aunque',
        'cuando', 'donde', 'mientras', 'también', 'tampoco',
        'estos', 'estas', 'esos', 'esas', 'aquellos', 'aquellas',
    })
    # Palabra de contenido: 5+ chars minúscula, no termina en tilde pretérito
    # (ó/é/á/í), no termina en sufijo de 3ª plural pretérito (-aron/-eron/-ieron),
    # no termina en -uye (conjugación presente de verbos -uir: incluye, construye…;
    # ningún sustantivo español termina en -uye).
    _WORD = (
        r'[a-záéíóúüñ]{5,}'
        r'(?<![óéáí])'
        r'(?<!aron)(?<!eron)(?<!ieron)'
        r'(?<!uye)'
    )
    # RAE: preposiciones y conjunciones no inician elementos de enumeración.
    # Las palabras funcionales de ≥5 letras que coinciden con _WORD se excluyen
    # del inicio de GN: si el motor las consume, avanza la posición y nunca
    # prueba la palabra de contenido siguiente como primer elemento real.
    _FUNC_START = (
        r'(?:sobre|entre|desde|hasta|según|hacia|durante|mediante|contra'
        r'|porque|aunque|cuando|donde|mientras|también|tampoco'
        r'|estos|estas|aquellos|aquellas)'
    )
    _WORD_CONTENT = r'(?!' + _FUNC_START + r'\b)' + _WORD
    # GN: 1-2 palabras de contenido; ninguna puede ser palabra funcional.
    # La segunda palabra también usa _WORD_CONTENT: si usara _WORD (sin
    # restricción), "temas sobre" formaría un GN válido, _sub lo bloquearía,
    # pero el engine ya habría consumido "temas" y no volvería a probar
    # "privacidad" como GN1 → la coma no se insertaría.
    _GN = r'(?:' + _WORD_CONTENT + r'(?:\s+' + _WORD_CONTENT + r')?)'

    patron = re.compile(
        r'(' + _GN + r') (' + _GN + r')(?!,)'
        r'(?=(?:(?:, | )' + _GN + r')* (?:y|o|ni) ' + _GN + r')'
    )

    # RAE: en "N adj1 y adj2", los adjetivos modifican al sustantivo y no forman
    # una enumeración independiente → no se inserta coma antes del primer adjetivo.
    # Discriminación: si GN2 termina en sufijo adjetival y GN1 no → patrón N+adj.
    _ADJ_SUFIJOS = (
        'al', 'ales', 'ar', 'ares',
        'ico', 'ica', 'icos', 'icas',
        'oso', 'osa', 'osos', 'osas',
        'ivo', 'iva', 'ivos', 'ivas',
        'ble', 'bles',
    )

    def _sub(m):
        for w in (m.group(1) + ' ' + m.group(2)).split():
            if w.lower() in _FUNC:
                return m.group(0)
        # Detectar patrón sustantivo + adjetivos modificadores ("salud física y mental")
        gn2_ult = m.group(2).split()[-1].lower()
        gn1_ult = m.group(1).split()[-1].lower()
        if (any(gn2_ult.endswith(s) for s in _ADJ_SUFIJOS) and
                not any(gn1_ult.endswith(s) for s in _ADJ_SUFIJOS)):
            return m.group(0)
        return m.group(1) + ', ' + m.group(2)

    anterior = None
    while anterior != text:
        anterior = text
        text = patron.sub(_sub, text)
    return text


_GEONOMBRES = {
    "caribe": "Caribe",
    "mediterráneo": "Mediterráneo",
    "mediterraneo": "Mediterráneo",
    "atlántico": "Atlántico",
    "atlantico": "Atlántico",
    "pacífico": "Pacífico",
    "pacifico": "Pacífico",
    "índico": "Índico",
    "indico": "Índico",
    "ártico": "Ártico",
    "artico": "Ártico",
    "antártico": "Antártico",
    "antartico": "Antártico",
    "andes": "Andes",
    "amazonas": "Amazonas",
    "sáhara": "Sáhara",
    "sahara": "Sáhara",
    "himalaya": "Himalaya",
    "nilo": "Nilo",
    "danubio": "Danubio",
    "pirineos": "Pirineos",
    "alpes": "Alpes",
    "orinoco": "Orinoco",
    "everest": "Everest",
    "titicaca": "Titicaca",
    "kilimanjaro": "Kilimanjaro",
    "urales": "Urales",
    "volga": "Volga",
    "congo": "Congo",
    "ganges": "Ganges",
    "mekong": "Mekong",
    "zambeze": "Zambeze",
    "rin": "Rin",
    "sena": "Sena",
    "támesis": "Támesis",
    "tamesis": "Támesis",
    "éufrates": "Éufrates",
    "eufrates": "Éufrates",
    "tigris": "Tigris",
    "balcanes": "Balcanes",
    "cáucaso": "Cáucaso",
    "caucaso": "Cáucaso",
    "níger": "Níger",
    "niger": "Níger",
    # Estados mexicanos que LT no capitaliza por ser palabras comunes en español
    "guerrero": "Guerrero",
    "campeche": "Campeche",
}


def _capitalizar_geonombres_en_contexto(text: str) -> str:
    """
    RAE: nombres propios geográficos llevan mayúscula en cualquier posición,
    incluso cuando no siguen directamente a un artículo
    (ej: 'océano índico' → 'océano Índico').
    Se aplica como pase complementario al de artículo+geonombre.
    Las formas sin tilde que son también verbos (ej: 'indico') no se
    capitalizan en inicio de oración, donde son ambiguas con el presente.
    """
    _TILDES_VOCALES = set('áéíóúü')
    _INICIO_ORACION = re.compile(r'(?:^|[.!?]\s+)\Z')

    def _fix(m):
        key_lower = m.group(0).lower()
        canonical = _GEONOMBRES.get(key_lower)
        if canonical is None:
            return m.group(0)
        # Formas sin tilde: verificar que no estén en posición de verbo (inicio de oración)
        if not any(c in key_lower for c in _TILDES_VOCALES):
            prefijo = text[:m.start()]
            if not prefijo.strip() or _INICIO_ORACION.search(prefijo):
                return m.group(0)
        return canonical

    all_keys = sorted(_GEONOMBRES.keys(), key=len, reverse=True)
    pat = re.compile(
        r'\b(?:' + '|'.join(re.escape(k) for k in all_keys) + r')\b',
        re.IGNORECASE
    )
    return pat.sub(_fix, text)


def _capitalizar_nombres_geograficos_con_articulo(text: str) -> str:
    """
    RAE: nombres propios geográficos llevan mayúscula aunque vayan
    precedidos de artículo ('el caribe' → 'el Caribe').
    Solo actúa cuando el nombre geográfico está en minúscula.
    """
    def _fix(m):
        art = m.group(1)
        correcto = _GEONOMBRES.get(m.group(2).lower())
        if correcto:
            return art + correcto
        return m.group(0)

    return re.sub(
        r'(\b(?:[Ee]l|[Ll]a|[Ll]os|[Ll]as)\s+)([a-záéíóúüñ][a-záéíóúüñ]*)',
        _fix,
        text
    )


def _capitalizar_toponimos_compuestos(text: str) -> str:
    """
    RAE: en nombres geográficos compuestos, cada elemento que integra el nombre
    propio lleva mayúscula inicial. No capitaliza artículos ni preposiciones
    internas ('del', 'de', 'la'…) ni palabras no gentilicias/direccionales.
    """
    GENTILICIOS_TOPONIMO = {
        "latina", "latino", "central", "norte", "sur",
        "oriental", "occidental", "septentrional",
        "meridional", "austral", "boreal", "subsahariana",
    }

    def _fix(m):
        primera = m.group(1)
        segunda = m.group(2)
        if segunda.lower() in GENTILICIOS_TOPONIMO:
            return primera + ' ' + segunda.capitalize()
        return m.group(0)

    text = re.sub(
        r'\b([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{3,}) ([a-záéíóúüñ]+)\b',
        _fix,
        text
    )

    # Topónimos con preposición intermedia: "América del Sur", "Corea del Norte"
    # RAE: los cardinales forman parte del nombre propio → mayúscula inicial
    CARDINALES_PREP = {
        "norte", "sur", "este", "oeste", "oriente", "occidente",
        "latina", "latino", "central", "oriental", "occidental",
        "septentrional", "meridional", "austral", "boreal",
    }

    def _fix_prep(m):
        if m.group(3).lower() in CARDINALES_PREP:
            return m.group(1) + ' ' + m.group(2).lower() + ' ' + m.group(3).capitalize()
        return m.group(0)

    return re.sub(
        r'\b([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{3,}) ([Dd]el|[Dd]e) ([A-ZÁÉÍÓÚÜÑa-záéíóúüñ][a-záéíóúüñ]*)\b',
        _fix_prep,
        text
    )


_WORD_CAP = r'[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{2,}'
_REVERTIR_COMA_NOMBRES = re.compile(
    r'(' + _WORD_CAP + r'), (' + _WORD_CAP + r') (y|o|ni) (' + _WORD_CAP + r') (' + _WORD_CAP + r')'
)


def _finalizar_parrafo(text: str) -> str:
    text = text.strip()

    # Proteger topónimos compuestos con placeholders ANTES de insertar comas y
    # de aplicar _REVERTIR_COMA_NOMBRES. Mientras los placeholders (__TOPn__)
    # estén activos, _REVERTIR no puede confundir "Japón, Australia y __TOP__"
    # con un par nombre+apellido, porque __TOPn__ no coincide con _WORD_CAP.
    # La restauración ocurre justo después del revert.
    slots: dict[str, str] = {}
    for i, top in enumerate(_TOPONIMOS):
        pat = re.compile(r'\b' + re.escape(top) + r'\b', re.IGNORECASE)
        if pat.search(text):
            key = f'__TOP{i}__'
            slots[key] = top
            text = pat.sub(key, text)

    # Proteger secuencias de 3+ palabras capitalizadas consecutivas (sin coma entre
    # ellas) como nombres propios compuestos que no deben fragmentarse.
    # RAE: los nombres propios compuestos son unidades indivisibles.
    # Ej: "Golden State Warriors", "Los Angeles Lakers".
    # Las topónimos ya protegidos con __TOP__ no interfieren (no coinciden con _WORD_CAPS).
    # Solo 3+ palabras: con 2 palabras la ambigüedad es mayor (podría ser lista de
    # dos nombres propios como "Europa Asia") y los casos de 2 palabras están cubiertos
    # mayoritariamente por los placeholders de topónimos del JSON.
    # {2,}: palabras de 3+ chars (Foo, Red, Hot) también quedan visibles para CPN.
    # La guarda _is_foreign_word evita que pares españoles (Europa Asia) se protejan.
    _WORD_CAPS_DEF = r'[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{2,}'
    _cpn_re = re.compile(_WORD_CAPS_DEF + r'(?:\s+' + _WORD_CAPS_DEF + r'){2,}')
    cpn_slots: dict[str, str] = {}
    _cpn_n = [0]

    def _cpn_sub(m):
        run_words = m.group(0).split()
        # Solo proteger si al menos una palabra es extranjera (no es un nombre
        # propio español reconocido por LT). Las listas de topónimos españoles
        # (Europa Asia África) no contienen palabras extranjeras → no se protegen.
        if not any(_is_foreign_word(w) for w in run_words):
            return m.group(0)
        key = f'__CPN{_cpn_n[0]}__'
        cpn_slots[key] = m.group(0)
        _cpn_n[0] += 1
        return key

    text = _cpn_re.sub(_cpn_sub, text)

    # Proteger pares de 2 palabras capitalizadas donde al menos una es extranjera
    # (ej: "Miami Heat", "Chicago Bulls"). Los pares completamente españoles
    # (Europa Asia, Carlos Torres) no contienen palabras extranjeras → no se protegen.
    _cpn_re_2 = re.compile(_WORD_CAPS_DEF + r'\s+' + _WORD_CAPS_DEF)

    def _cpn_sub_2(m):
        run_words = m.group(0).split()
        if not any(_is_foreign_word(w) for w in run_words):
            return m.group(0)
        key = f'__CPN{_cpn_n[0]}__'
        cpn_slots[key] = m.group(0)
        _cpn_n[0] += 1
        return key

    text = _cpn_re_2.sub(_cpn_sub_2, text)

    # Pre-capitalizar geonombres antes de insertar comas: asegura que nombres
    # geográficos en minúscula (ej: "pacífico") sean ELEM válidos (_WORD requiere
    # mayúscula inicial). Se vuelven a aplicar al final (son idempotentes).
    text = _capitalizar_geonombres_en_contexto(text)
    text = _capitalizar_nombres_geograficos_con_articulo(text)

    text = _coma_en_enumeracion_nombres_propios(text)

    # RAE: en "Nombre Apellido y Nombre Apellido" no se inserta coma entre
    # nombre y apellido. Si la función anterior añadió coma dentro de un par
    # compuesto (Cap, Cap y Cap Cap), se revierte; distinguible porque tras
    # el conector "y/o/ni" vienen DOS palabras capitalizadas (apellidos incluidos).
    # Con los placeholders aún activos, los topónimos compuestos no se ven afectados.
    text = _REVERTIR_COMA_NOMBRES.sub(r'\1 \2 \3 \4 \5', text)

    # Restaurar nombres propios compuestos (CPN) ANTES que los topónimos.
    # El segundo REVERTIR corre aquí con los __TOP__ aún activos: así los compuestos
    # topónimos (Nueva Zelanda, América Latina) siguen siendo placeholders opacos y
    # no disparan el revert. Solo los CPN restaurados (Chicago Bulls, Miami Heat)
    # pueden coincidir con el patrón y revertirse correctamente.
    for key, compound in cpn_slots.items():
        text = text.replace(key, compound)

    # Segunda pasada de REVERTIR: "Boston, Celtics y Chicago Bulls" → "Boston Celtics y Chicago Bulls".
    # "Japón, Australia y __TOP49__" no se toca: __TOP49__ no coincide con _WORD_CAP.
    text = _REVERTIR_COMA_NOMBRES.sub(r'\1 \2 \3 \4 \5', text)

    # Restaurar topónimos a sus formas canónicas (después del segundo REVERTIR)
    for key, canonical in slots.items():
        text = text.replace(key, canonical)

    # RAE §91.2.1: comas en enumeraciones de sustantivos comunes sin artículo
    # (ej: "cambio climático energía renovable y desarrollo tecnológico").
    # Corre DESPUÉS de restaurar topónimos para no afectar placeholders.
    text = _coma_en_enumeracion_sustantivos(text)

    # Títulos ante nombre propio → minúscula según RAE (no al inicio de oración)
    text = _TITULOS_RAE_RE.sub(lambda m: m.group(1).lower(), text)

    # Proteger puntos suspensivos
    text = re.sub(r'\.{3,}', '__ELLIPSIS__', text)

    # Limpiar puntuación duplicada
    text = re.sub(r'(?<=[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])\.{2}(?=[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])', '.', text)
    text = re.sub(r'\?{2,}', '?', text)
    text = re.sub(r'!{2,}', '!', text)
    text = re.sub(r'([.?!])\s*([.?!])', r'\1', text)
    text = re.sub(r'([.?!])(["\'])(\s|$)', r'\1\3', text)

    # Restaurar puntos suspensivos
    text = text.replace('__ELLIPSIS__', '...')

    # Eliminar coma pegada entre letras
    text = re.sub(
        r'([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]),([a-zA-ZáéíóúüñÁÉÍÓÚÜÑ])',
        r'\1\2',
        text
    )

    # Capitalizar primera letra
    if text:
        i = 0
        while i < len(text) and text[i] in ('¡', '¿', ' '):
            i += 1
        if i < len(text) and text[i].islower():
            text = text[:i] + text[i].upper() + text[i+1:]

    # Capitalizar después de punto final
    text = re.sub(
        r'(\. )([a-záéíóúüñ])',
        lambda m: m.group(1) + m.group(2).upper(),
        text
    )

    # Capitalizar después de ¡ o ¿
    text = re.sub(
        r'([¡¿]\s*)([a-záéíóúüñ])',
        lambda m: m.group(1) + m.group(2).upper(),
        text
    )

    # Restaurar siglas conocidas a mayúsculas completas
    _SIGLAS = {r'\bIa\b': 'IA', r'\bia\b': 'IA',
               r'\bMl\b': 'ML', r'\bNlp\b': 'NLP'}
    for patron, sigla in _SIGLAS.items():
        text = re.sub(patron, sigla, text)

    text = _capitalizar_toponimos_compuestos(text)
    text = _capitalizar_nombres_geograficos_con_articulo(text)
    text = _capitalizar_geonombres_en_contexto(text)

    if not text.endswith(("?", ".", "!", "...", "¿", "¡")):
        text += "."

    return text
