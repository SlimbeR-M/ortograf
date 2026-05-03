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

        # Regla 1: ignorar placeholders
        if PLACEHOLDER_PATTERN.search(fragmento):
            continue

        # Regla 2: palabras cortas protegidas explícitamente
        if frag_lower in PALABRAS_CORTAS_PROTEGIDAS:
            continue

        # Regla 3: palabras cortas (menos de 4 letras) con raíz técnica
        if len(fragmento) < 4 and _tiene_raiz_tecnica(fragmento):
            continue

        # Regla 4: verbos técnicos por morfología
        if _es_verbo_tecnico(fragmento):
            continue

        # Regla 5: raíz técnica con cambio drástico
        if _tiene_raiz_tecnica(fragmento) and m.replacements:
            sim = SequenceMatcher(
                None,
                frag_lower,
                m.replacements[0].lower()
            ).ratio()
            if sim < 0.80:
                continue

        matches_seguros.append(m)

    return language_tool_python.utils.correct(text, matches_seguros)