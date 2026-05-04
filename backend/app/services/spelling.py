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

        # Bloquear tildes diacríticas — las maneja grammar.py con contexto
        TILDES_DIACRITICAS = {
            ("el", "él"),
            ("mas", "más"),
            ("esta", "está"),
            ("tu", "tú"),
            ("se", "sé"),
            ("si", "sí"),
            ("de", "dé"),
            ("te", "té"),
            ("aun", "aún"),
        }
        if m.replacements:
            par = (frag_lower, m.replacements[0].lower())
            if par in TILDES_DIACRITICAS:
                continue

        # Ignorar palabras cortas protegidas
        if frag_lower in PALABRAS_CORTAS_PROTEGIDAS:
            continue

        if len(fragmento) < 4 and _tiene_raiz_tecnica(fragmento):
            continue

        if _es_verbo_tecnico(fragmento):
            continue

        if _tiene_raiz_tecnica(fragmento) and m.replacements:
            sim = SequenceMatcher(None, frag_lower, m.replacements[0].lower()).ratio()
            if sim < 0.80:
                continue

        matches_seguros.append(m)

    return language_tool_python.utils.correct(text, matches_seguros)