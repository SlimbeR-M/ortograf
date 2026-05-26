import re
import json
import os
from difflib import SequenceMatcher
import language_tool_python

tool = language_tool_python.LanguageTool("es")
PLACEHOLDER_PATTERN = re.compile(r'__TECH_\d+__')
_GEO_PH_PAT = re.compile(r'__GEO\d+__')

# ---------------------------------------------------------------------------
# Topónimos compuestos — protección ante LanguageTool
# Se cargan al inicio del módulo (mismo JSON que postprocess.py).
# Antes de pasarle el texto a LT, cada topónimo compuesto se reemplaza por
# un placeholder __GEO{n}__ para que LT no lo toque ni lo corrompa.
# Después de aplicar las correcciones de LT, los placeholders se restauran
# a sus formas canónicas del JSON.
# ---------------------------------------------------------------------------
_DATOS_SPELL = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
try:
    with open(os.path.join(_DATOS_SPELL, 'toponimos_compuestos.json'), encoding='utf-8') as _fsp:
        _TOPONIMOS_SPELL = sorted(json.load(_fsp)['paises_compuestos'], key=len, reverse=True)
except (OSError, KeyError, json.JSONDecodeError):
    _TOPONIMOS_SPELL = []

# Tabla de normalización de tildes para hacer match de entradas sin acentar
_ACCENT_MAP = str.maketrans('áéíóúüñÁÉÍÓÚÜÑ', 'aeiouunAEIOUUN')

# Pre-compilar patrones: para cada topónimo, patrón exacto (con IGNORECASE)
# más patrón sin tildes (solo cuando difieren), para capturar input sin acentar.
_TOP_PATTERNS: list[tuple[str, list[re.Pattern]]] = []
for _top in _TOPONIMOS_SPELL:
    _pats = [re.compile(r'\b' + re.escape(_top) + r'\b', re.IGNORECASE)]
    _stripped = _top.translate(_ACCENT_MAP)
    if _stripped != _top:
        _pats.append(re.compile(r'\b' + re.escape(_stripped) + r'\b', re.IGNORECASE))
    _TOP_PATTERNS.append((_top, _pats))


RAICES_TECNICAS = {
    "deploy", "build", "debug", "fix", "push", "pull", "fetch",
    "merge", "clone", "commit", "release", "update", "install",
    "config", "setup", "import", "export", "render", "load",
    "cache", "crash", "login", "logout", "upload", "download",
    "fitear", "fitea", "deployar", "buildear", "dev", "ops",
    "sysadmin", "devops", "repo", "fullstack"
}

PALABRAS_CORTAS_PROTEGIDAS = {
    "dev", "devs", "ops", "api", "css", "xml", "log", "bug",
    "fix", "git", "sql", "cdn", "ram", "cpu", "gpu", "url",
    "ia", "ml", "nlp"
}

CLITICOS_PROTEGIDOS = {
    "nos", "les", "me", "te", "lo", "la", "le",
    "los", "las", "os", "se"
}

TILDES_DIACRITICAS = {
    ("el", "él"), ("mas", "más"), ("esta", "está"), ("tu", "tú"),
    ("se", "sé"), ("si", "sí"), ("de", "dé"), ("te", "té"), ("aun", "aún"),
}

# Verbos que grammar.py acentúa correctamente según contexto.
# Bloqueamos que LanguageTool les añada la tilde equivocada.
VERBOS_TILDE_PROTEGIDOS = {
    "publico",   # publicó (verbo) vs público (adj) — grammar.py decide
}

# Importación diferida para evitar referencias en tiempo de módulo;
# grammar.py no importa spelling.py → sin circular.
def _get_verbos_pasado():
    from app.services.grammar import VERBOS_PASADO_1RA
    return VERBOS_PASADO_1RA


def _get_geonombres():
    from app.services.postprocess import _GEONOMBRES
    return _GEONOMBRES

FUTUROS_PROTEGIDOS = {
    "dara", "hara", "tendra", "podra", "querra", "vendra",
    "saldra", "pondra", "valdra", "cabra", "habra", "sabra",
    "volvera", "llegara", "comprara", "buscara", "encontrara",
    "trabajara", "estudiara", "vivira", "comera", "bebera",
    "correra", "dormira", "traera", "llevara", "pagara",
    "jugara", "llamara", "esperara", "usara", "necesitara",
    "ayudara", "cambiara", "pensara", "sentira", "conocera",
    "recordara", "olvidara", "pedira", "seguira", "entendera",
    "perdera", "ganara", "recibira", "decidira", "cumplira",
    "sufrira", "reducira", "producira", "construira", "destruira",
    "contribuira", "distribuira", "huira", "funcionara", "mejorara",
    "crecera", "avanzara", "desarrollara", "afectara", "generara",
    "terminara", "empezara", "comenzara", "acabara", "finalizara",
    "iniciara", "existira", "aumentara", "disminuira",
}

PALABRAS_REGIONALES = {
    "tlayuda", "tlayudas", "mezcal", "mole", "pozole", "tamal", "tamales",
    "atole", "tepache", "pulque", "chapulines", "molcajete", "comal",
    "metate", "tlacoyo", "memela", "tetela", "huarache", "sope",
    "tostada", "enchilada", "quesadilla",
}


def _tiene_raiz_tecnica(palabra: str) -> bool:
    p = palabra.lower()
    return any(p.startswith(raiz) for raiz in RAICES_TECNICAS)


def _es_verbo_tecnico(palabra: str) -> bool:
    p = palabra.lower()
    # Solo sufijos largos y específicos de anglicismos verbales (-ear/-eando/-eado/-ean).
    # Se excluye "eo"/"ea"/"eas": son terminaciones de centenares de palabras españolas
    # legítimas (contemporáneo, europeo, idea, marea…) que LT sí necesita corregir.
    # Las formas en -eo/-ea/-eas de anglicismos técnicos (deployeo, buildea…) ya quedan
    # protegidas por _tiene_raiz_tecnica() porque su raíz está en RAICES_TECNICAS.
    sufijos = ('ear', 'eando', 'eado', 'ean')
    if any(p.endswith(s) for s in sufijos):
        return True
    if _tiene_raiz_tecnica(p):
        return True
    return False


def correct_spelling(text: str) -> str:
    # -----------------------------------------------------------------------
    # Fase 1: proteger topónimos compuestos antes de LanguageTool
    # -----------------------------------------------------------------------
    geo_slots: dict[str, str] = {}
    protected = text
    for i, (canonical, pats) in enumerate(_TOP_PATTERNS):
        key: str | None = None
        for pat in pats:
            if pat.search(protected):
                if key is None:
                    key = f'__GEO{i}__'
                    geo_slots[key] = canonical
                protected = pat.sub(key, protected)

    # -----------------------------------------------------------------------
    # Fase 2: corrección ortográfica con LanguageTool
    # -----------------------------------------------------------------------
    matches = tool.check(protected)
    matches_seguros = []

    for m in matches:
        fragmento = protected[m.offset:m.offset + m.error_length]
        frag_lower = fragmento.lower()

        # Ignorar placeholders (tech y geo)
        if PLACEHOLDER_PATTERN.search(fragmento) or _GEO_PH_PAT.search(fragmento):
            continue

        # Bloquear tildes diacríticas
        if m.replacements:
            par = (frag_lower, m.replacements[0].lower())
            if par in TILDES_DIACRITICAS:
                continue

        # Proteger verbos que grammar.py acentúa según contexto
        if any(p in VERBOS_TILDE_PROTEGIDOS for p in frag_lower.split()):
            continue

        # Regla RAE: si la palabra es un verbo en pasado que grammar.py tildará
        # contextualmente (ej: "indico" → "indicó"), bloquear cualquier tilde
        # en posición errónea que LT proponga (ej: "índico" esdrújula).
        if m.replacements and frag_lower in _get_verbos_pasado():
            expected_verb = _get_verbos_pasado()[frag_lower]
            if m.replacements[0].lower() != expected_verb:
                continue

        # Bloquear la regla SE_CREO2 de LT cuando añade tilde a vocal final de
        # una palabra no reconocida como verbo pretérito. SE_CREO2 se confunde
        # con nombres propios llanos terminados en vocal (ej: "pablo" → "pabló").
        # RAE: palabras llanas terminadas en vocal no llevan tilde; SE_CREO2
        # solo debe operar sobre verbos pretéritos confirmados en VERBOS_PASADO_1RA.
        # (SE_CREO sin sufijo sí es correcto: "celebro"→"celebró", "noto"→"notó")
        if (m.rule_id == "SE_CREO2" and
                frag_lower not in _get_verbos_pasado() and
                m.replacements):
            repl_lower = m.replacements[0].lower()
            if (len(frag_lower) == len(repl_lower) and
                    frag_lower[-1] in 'aeiou' and
                    repl_lower[-1] in 'áéíóú' and
                    frag_lower[:-1] == repl_lower[:-1].translate(
                        str.maketrans('áéíóú', 'aeiou'))):
                continue

        # Bloquear correcciones estructurales (no solo tilde) sobre nombres
        # geográficos reconocidos por _GEONOMBRES. LT puede aplicar reglas de
        # concordancia o conjugación a estas palabras (ej: AGREEMENT_DET_ADJ:
        # "el himalaya" → "el himalayo"; SUBJUNTIVO_INCORRECTO: "andes" → "andas").
        # Se permiten cambios de solo tilde porque no alteran la estructura.
        if m.replacements:
            _geos = _get_geonombres()
            if any(w in _geos for w in frag_lower.split()):
                if frag_lower.translate(_ACCENT_MAP) != m.replacements[0].lower().translate(_ACCENT_MAP):
                    continue

        # Proteger pronombres clíticos
        if frag_lower in CLITICOS_PROTEGIDOS:
            continue

        # Bloquear si la corrección elimina un pronombre clítico
        if m.replacements:
            orig_palabras = set(frag_lower.split())
            corr_palabras = set(m.replacements[0].lower().split())
            cliticos_perdidos = orig_palabras & CLITICOS_PROTEGIDOS - corr_palabras
            if cliticos_perdidos:
                continue

        # Bloquear AGREEMENT_POSTPONED_ADJ cuando el adjetivo pospuesto sigue
        # inmediatamente a un participio pasado (-ado/-ido): LT confunde el
        # participio con el sustantivo antecedente del adjetivo y propone un
        # cambio de género incorrecto (ej: "habían adoptado nuevas técnicas"
        # → "nuevo técnicas"). RAE §33.5: el adjetivo concuerda con el
        # sustantivo al que se refiere, no con el participio precedente.
        if m.rule_id == "AGREEMENT_POSTPONED_ADJ" and m.replacements:
            _prev_ctx = protected[max(0, m.offset - 50):m.offset]
            _prev_tokens = _prev_ctx.split()
            _prev_word = re.sub(r'\W+$', '', _prev_tokens[-1]).lower() if _prev_tokens else ""
            if re.search(r'[ai]do$', _prev_word):
                continue

        # Bloquear reemplazos multi-palabra problemáticos
        if m.replacements:
            orig_words = frag_lower.split()
            repl_words = m.replacements[0].lower().split()
            if len(orig_words) == 1 and len(repl_words) > 1:
                # Palabra única → múltiples tokens: solo permitir si similitud >= 0.75
                # con alguno de los tokens del reemplazo. Si la similitud es baja,
                # la fragmentación empeora el texto y es mejor dejarla para Groq.
                _max_sim = max(
                    SequenceMatcher(None, frag_lower, w).ratio()
                    for w in repl_words
                )
                if _max_sim < 0.75:
                    continue
            elif len(orig_words) > 1 and len(repl_words) > 1:
                if len(orig_words) == len(repl_words):
                    n_same = sum(1 for o, r in zip(orig_words, repl_words) if o == r)
                    if n_same == 0:
                        # Permitir si TODAS las diferencias son solo tildes (RAE: nombres propios)
                        all_accent_only = all(
                            o.translate(_ACCENT_MAP) == r.translate(_ACCENT_MAP)
                            for o, r in zip(orig_words, repl_words)
                        )
                        if not all_accent_only:
                            # Primer reemplazo cambia formas de palabra (ej: "comisiona probara").
                            # Buscar entre las alternativas una con cambios de solo tilde.
                            _mejor = None
                            for _alt in m.replacements[1:]:
                                _aw = _alt.lower().split()
                                if len(_aw) == len(orig_words):
                                    _ac = [(o, r) for o, r in zip(orig_words, _aw) if o != r]
                                    if _ac and all(
                                        o.translate(_ACCENT_MAP) == r.translate(_ACCENT_MAP)
                                        for o, r in _ac
                                    ):
                                        _mejor = _alt
                                        break
                            if _mejor is None:
                                continue
                            m.replacements.insert(0, _mejor)
                    else:
                        # Bloquear si los cambios son SOLO de número (singular/plural) —
                        # estas "correcciones" de concordancia adj-sustantivo tratan
                        # incorrectamente nombres propios como pares comunes.
                        changed = [(o, r) for o, r in zip(orig_words, repl_words) if o != r]
                        if changed and all(
                            o.rstrip('s') == r.rstrip('s') and
                            (o.endswith('s') or r.endswith('s'))
                            for o, r in changed
                        ):
                            continue
                        # Bloquear si alguna palabra cambiada tiene raíz diferente
                        # (no solo tilde): ej "maria García"→"Marta García" donde
                        # "maria"→"marta" cambia la raíz. Correcciones de solo tilde
                        # ("maria"→"maría") se permiten porque la raíz es igual.
                        if changed and not all(
                            o.translate(_ACCENT_MAP) == r.translate(_ACCENT_MAP)
                            for o, r in changed
                        ):
                            continue
                else:
                    sim = SequenceMatcher(None, frag_lower, m.replacements[0].lower()).ratio()
                    if sim < 0.7:
                        continue

        if m.replacements and "buen" in frag_lower and "bien" in m.replacements[0].lower():
            continue

        # Bloquear "quien" → "quién" cuando es pronombre relativo
        if (frag_lower == "quien" and m.replacements and
                m.replacements[0].lower() == "quién"):
            _VERBOS_INTERROG = {
                "sé", "se", "sabes", "sabe", "sabía", "saber",
                "dime", "dinos", "pregunta", "pregunto", "preguntó", "pregunté",
                "explica", "explicó", "conoces", "conoce", "conocía",
                "averigua", "averiguó", "ignora", "ignoraba", "importa",
            }
            texto_previo = text[:m.offset].lower()
            palabras_previas = set(re.findall(r'\b\w+\b', texto_previo[-60:]))
            es_interrogativo = (
                "?" in text or "¿" in text or
                bool(palabras_previas & _VERBOS_INTERROG)
            )
            if not es_interrogativo:
                continue

        # Bloquear "a el" → "al" cuando "el" es pronombre
        if m.replacements and frag_lower == "a el" and m.replacements[0].lower() == "al":
            continue

        # Bloquear "el" → "en"
        if m.replacements and "el" in frag_lower and m.replacements[0].lower() == "en":
            continue

        # Bloquear verbos en futuro — los maneja grammar.py
        if frag_lower in FUTUROS_PROTEGIDOS:
            continue

        fragmento_palabras = frag_lower.split()
        if any(p in FUTUROS_PROTEGIDOS for p in fragmento_palabras):
            continue

        if frag_lower in PALABRAS_CORTAS_PROTEGIDAS:
            continue

        if frag_lower in PALABRAS_REGIONALES:
            continue

        if len(fragmento) < 4 and _tiene_raiz_tecnica(fragmento):
            continue

        if _es_verbo_tecnico(fragmento):
            continue

        if _tiene_raiz_tecnica(fragmento) and m.replacements:
            sim = SequenceMatcher(None, frag_lower, m.replacements[0].lower()).ratio()
            if sim < 0.80:
                continue

        if m.replacements:
            if (frag_lower.endswith('e') and
                m.replacements[0].lower().endswith('a') and
                SequenceMatcher(None, frag_lower[:-1], m.replacements[0].lower()[:-1]).ratio() > 0.85):
                continue

        # Bloquear MORFOLOGIK sobre palabras que empiezan con mayúscula en el input.
        # RAE: los nombres propios extranjeros se escriben en su idioma original.
        # Una palabra con primera letra mayúscula es un nombre propio que MORFOLOGIK
        # trata erróneamente como error ortográfico español (ej: "Curry"→"Curri",
        # "LeBron"→"Lebrón", "Warriors"→"Barrios").
        # Las tildes de nombres propios españoles se corrigen en Fase 2b (pase
        # secundario que solo aplica cambios acento-a-acento sin alterar la palabra).
        if m.rule_id.startswith("MORFOLOGIK") and fragmento[0].isupper():
            continue

        # Bloquear MORFOLOGIK cuando el reemplazo tiene raíz diferente a la palabra
        # original. MORFOLOGIK no conoce términos médicos/técnicos en minúscula
        # (ej: "zika"→"Mika", "discalculia"→"descálcela") y propone la palabra más
        # cercana de su diccionario. Se permite si solo cambian tildes (misma raíz sin
        # acento). Para sugerencias en minúscula con raíz diferente, solo se bloquea
        # cuando la similitud es baja (<0.85): así se permiten correcciones legítimas
        # de errores ortográficos con raíz casi idéntica (ej: "exepcion"→"excepción",
        # ratio≈0.94), pero se bloquean sustituciones de términos desconocidos
        # (ej: "discalculia"→"descálcela", ratio≈0.76).
        if (m.rule_id.startswith("MORFOLOGIK") and
                m.replacements and
                not fragmento[0].isupper()):
            _repl_base = m.replacements[0].lower().translate(_ACCENT_MAP)
            _frag_base = frag_lower.translate(_ACCENT_MAP)
            if _repl_base != _frag_base:
                if m.replacements[0][0].isupper():
                    continue  # Sugerencia capitalizada → nombre propio extraño sustituido
                _sim = SequenceMatcher(None, _frag_base, _repl_base).ratio()
                if _sim < 0.85:
                    continue  # Raíz diferente + baja similitud → término especializado

        matches_seguros.append(m)

    result = language_tool_python.utils.correct(protected, matches_seguros)

    # -----------------------------------------------------------------------
    # Fase 2b: pase secundario — tildes en palabras capitalizadas que LT omite
    # porque las trata como nombres propios válidos (ej. "Jose" → "José").
    # RAE: los nombres propios siguen las mismas reglas de acentuación.
    # -----------------------------------------------------------------------
    _cap_lower: dict[str, str] = {}
    _cap_tokens = result.split()
    for _i, _tok in enumerate(_cap_tokens):
        _core = re.sub(r'[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', '', _tok)
        if _core and _core[0].isupper() and not re.search(r'[áéíóúü]', _core):
            # Saltar palabras con mayúscula interna (CamelCase): son nombres propios
            # extranjeros (LeBron, McDonald, iPhone) que no deben acentuarse como
            # palabras españolas.
            if any(c.isupper() for c in _core[1:]):
                continue
            # Saltar palabras precedidas por un token capitalizado corto (≤3 chars):
            # estos tokens son artículos o preposiciones de nombres propios compuestos
            # (Los, Las, El, La, New, San, Von, De…) que indican que la palabra
            # siguiente es parte de un nombre compuesto extranjero o geográfico,
            # no una palabra española que requiera tilde. Ej: "Los Angeles" →
            # "Angeles" no debe convertirse en "Ángeles"; "El Paso" → "Paso" intacto.
            # Esto NO afecta nombres como "Jose Maria" porque "Jose" tiene 4 chars.
            if _i > 0:
                _prev_core = re.sub(r'[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', '', _cap_tokens[_i - 1])
                if _prev_core and _prev_core[0].isupper() and len(_prev_core) <= 3:
                    continue
            _lw = _core.lower()
            if _lw not in _cap_lower:
                _cap_lower[_lw] = _core
    if _cap_lower:
        _batch = '\n'.join(_cap_lower)
        _accent_fixes: dict[str, str] = {}
        for _m in tool.check(_batch):
            if not _m.replacements:
                continue
            _frag = _batch[_m.offset:_m.offset + _m.error_length]
            if '\n' in _frag or ' ' in _frag or _frag not in _cap_lower:
                continue
            _repl = _m.replacements[0].lower()
            if (_frag, _repl) in TILDES_DIACRITICAS:
                continue
            if _frag.translate(_ACCENT_MAP) == _repl.translate(_ACCENT_MAP) and _frag != _repl:
                _accent_fixes[_frag] = _repl
        if _accent_fixes:
            def _fix_cap(tok, _af=_accent_fixes):
                _c = re.sub(r'[^a-zA-ZáéíóúüñÁÉÍÓÚÜÑ]', '', tok)
                if not _c or not _c[0].isupper():
                    return tok
                _lw = _c.lower()
                if _lw in _af:
                    _acc = _af[_lw][0].upper() + _af[_lw][1:]
                    return tok.replace(_c, _acc, 1)
                return tok
            result = ' '.join(_fix_cap(t) for t in result.split())

    # -----------------------------------------------------------------------
    # Fase 3: restaurar topónimos a sus formas canónicas del JSON
    # -----------------------------------------------------------------------
    for key, canonical in geo_slots.items():
        result = result.replace(key, canonical)

    return result
