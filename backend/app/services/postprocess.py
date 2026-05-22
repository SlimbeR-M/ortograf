import re
import json
import os

_DATOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
try:
    with open(os.path.join(_DATOS, 'toponimos_compuestos.json'), encoding='utf-8') as _f:
        _TOPONIMOS = sorted(json.load(_f)['paises_compuestos'], key=len, reverse=True)
except (OSError, KeyError, json.JSONDecodeError):
    _TOPONIMOS = []


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
    _HOLD = r'__TOP\d+__'
    _GENT = (
        r'(?:Latina|Latino|Central|Oriental|Occidental'
        r'|Septentrional|Meridional|Austral|Boreal)'
    )
    # Artículo + 1-2 palabras de cualquier caso (3+ chars cada una).
    # Cubre: "el Caribe" (art+Cap), "la salud" (art+lower), "el océano Índico"
    # (art+lower+Cap), "el medio ambiente" (art+lower+lower).
    _ART_WORD = r'[a-záéíóúüñA-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]{2,}'
    # RAE: preposiciones y contracciones forman sintagma indivisible con su complemento
    # y nunca son el último componente de un elemento de enumeración.
    _PREPS = (
        r'(?:del|de|en|con|por|para|sin|sobre|entre|ante|bajo|tras'
        r'|hacia|hasta|desde|según|durante|mediante|contra|al)'
    )
    _ART_WORD2 = r'(?!' + _PREPS + r'\b)' + _ART_WORD
    _ART_ELEM = r'(?:el|la|los|las) ' + _ART_WORD + r'(?: ' + _ART_WORD2 + r')?'
    ELEM = r'(?:' + _HOLD + r'|' + _ART_ELEM + r'|' + _WORD + r')'

    patron = re.compile(
        r'(' + ELEM + r') (?!' + _GENT + r'\b)(' + ELEM + r')'
        r'(?=(?:(?:, | )' + ELEM + r')* (?:y|o|ni) ' + ELEM + r')'
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
    # GN: 1-2 palabras de contenido; la primera no puede ser palabra funcional
    _GN = r'(?:' + _WORD_CONTENT + r'(?:\s+' + _WORD + r')?)'

    patron = re.compile(
        r'(' + _GN + r') (' + _GN + r')'
        r'(?=(?:(?:, | )' + _GN + r')* (?:y|o|ni) ' + _GN + r')'
    )

    def _sub(m):
        for w in (m.group(1) + ' ' + m.group(2)).split():
            if w.lower() in _FUNC:
                return m.group(0)
        return m.group(1) + ', ' + m.group(2)

    return patron.sub(_sub, text)


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

    text = _coma_en_enumeracion_nombres_propios(text)

    # RAE: en "Nombre Apellido y Nombre Apellido" no se inserta coma entre
    # nombre y apellido. Si la función anterior añadió coma dentro de un par
    # compuesto (Cap, Cap y Cap Cap), se revierte; distinguible porque tras
    # el conector "y/o/ni" vienen DOS palabras capitalizadas (apellidos incluidos).
    # Con los placeholders aún activos, los topónimos compuestos no se ven afectados.
    text = _REVERTIR_COMA_NOMBRES.sub(r'\1 \2 \3 \4 \5', text)

    # Restaurar topónimos a sus formas canónicas
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
