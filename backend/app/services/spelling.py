import re
from difflib import SequenceMatcher
import language_tool_python

tool = language_tool_python.LanguageTool("es")
PLACEHOLDER_PATTERN = re.compile(r'__TECH_\d+__')

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
    "fix", "git", "sql", "cdn", "ram", "cpu", "gpu", "url"
}

CLITICOS_PROTEGIDOS = {
    "nos", "les", "me", "te", "lo", "la", "le",
    "los", "las", "os", "se"
}

TILDES_DIACRITICAS = {
    ("el", "él"), ("mas", "más"), ("esta", "está"), ("tu", "tú"),
    ("se", "sé"), ("si", "sí"), ("de", "dé"), ("te", "té"), ("aun", "aún"),
}

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
    sufijos = ('ear', 'eando', 'eado', 'ea', 'eas', 'eo', 'ean')
    if any(p.endswith(s) for s in sufijos):
        return True
    if _tiene_raiz_tecnica(p):
        return True
    return False


def correct_spelling(text: str) -> str:
    matches = tool.check(text)
    matches_seguros = []

    for m in matches:
        fragmento = text[m.offset:m.offset + m.error_length]
        frag_lower = fragmento.lower()

        # Ignorar placeholders
        if PLACEHOLDER_PATTERN.search(fragmento):
            continue

        # Bloquear tildes diacríticas
        if m.replacements:
            par = (frag_lower, m.replacements[0].lower())
            if par in TILDES_DIACRITICAS:
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

        if m.replacements and "buen" in frag_lower and "bien" in m.replacements[0].lower():
            continue

        # Bloquear "quien" → "quién" cuando es pronombre relativo (no interrogativo)
        # RAE: solo lleva tilde en interrogativas/exclamativas directas e indirectas
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

        # Bloquear verbos en futuro — los maneja grammar.py
        if frag_lower in FUTUROS_PROTEGIDOS:
            continue

        # Bloquear si el fragmento contiene un verbo en futuro
        fragmento_palabras = frag_lower.split()
        if any(p in FUTUROS_PROTEGIDOS for p in fragmento_palabras):
            continue

        # Ignorar palabras cortas protegidas
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

        matches_seguros.append(m)

    return language_tool_python.utils.correct(text, matches_seguros)