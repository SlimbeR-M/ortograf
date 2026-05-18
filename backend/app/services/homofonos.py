import spacy
import re

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("es_core_news_md")
    return _nlp

LEXICO_COCINA = {
    "carne", "pollo", "pescado", "cebolla", "ajo", "aceite",
    "horno", "sartén", "parrilla", "fuego", "cocina", "cocer",
    "hervir", "freír", "saltear", "marinar", "sazonar", "sal",
    "pimienta", "salsa", "guiso", "estofado", "asado"
}

LEXICO_VIOLENCIA = {
    "golpeó", "golpeo", "tiró", "tiro", "lanzó", "lanzo", "empujó",
    "empujo", "atacó", "ataco", "agredió", "agredio", "pegó", "pego",
    "disparó", "disparo", "amenazó", "huyó", "huyo", "persiguió",
    "piedra", "objeto", "botella", "palo", "golpe", "puñetazo",
    "patada", "balazo", "cuchillo", "arma", "proyectil", "roca"
}

LEXICO_NATURALEZA = {
    "río", "rio", "agua", "orilla", "corriente", "arroyo", "riachuelo",
    "lago", "laguna", "manantial", "cauce", "afluente", "caudal"
}

LEXICO_DESTRUCCION = {
    "rota", "roto", "dañada", "dañado", "destruida", "destruido",
    "valla", "puerta", "ventana", "pared", "techo", "muro", "cerca",
    "deteriorada", "deteriorado", "vieja", "viejo", "caída", "caido"
}

LEXICO_ELIMINACION = {
    "basura", "residuos", "desperdicios", "tira", "bota", "elimina",
    "descarta", "rechaza", "ignora", "desestima", "abandona"
}


def resolver_homofonos(text: str) -> str:
    nlp = get_nlp()
    doc = nlp(text)
    tokens = list(doc)
    resultado = list(text)

    for i, token in enumerate(tokens):
        tok_lower = token.text.lower()
        siguiente = tokens[i + 1] if i + 1 < len(tokens) else None
        anterior = tokens[i - 1] if i > 0 else None
        dos_sig = tokens[i + 2] if i + 2 < len(tokens) else None
        dos_antes = tokens[i - 2] if i > 1 else None

        sig_lower = siguiente.text.lower() if siguiente else ""
        sig_pos = siguiente.pos_ if siguiente else ""

        # ── se → revertir tilde si va seguido de verbo/clítico ──────────
        if token.text in ("sé", "Sé"):
            if siguiente:
                clíticos = {"me", "te", "le", "lo", "la", "les", "los",
                            "las", "nos", "os", "se", "de", "fue",
                            "cayó", "dio", "puso", "hizo"}
                if sig_pos in ["VERB", "AUX"] or sig_lower in clíticos:
                    inicio = token.idx
                    fin = inicio + len(token.text)
                    sin_tilde = "se" if token.text[0].islower() else "Se"
                    resultado[inicio:fin] = list(sin_tilde)

        # ── has / as / haz ───────────────────────────────────────────────
        elif tok_lower in ["as", "has", "haz"]:
            correcto = None
            if siguiente:
                if re.search(r'(ado|ido|to|so|cho)$', sig_lower):
                    correcto = "has"
                elif sig_lower == "de" and dos_sig and re.search(r'(ar|er|ir)$', dos_sig.text.lower()):
                    correcto = "has"
                elif sig_pos in ["NOUN", "PROPN", "DET"]:
                    correcto = "haz"
                elif sig_pos in ["ADP", "VERB"] and tok_lower == "as":
                    correcto = "as"
            if correcto and correcto != tok_lower:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = correcto if token.text[0].islower() else correcto.capitalize()
                resultado[inicio:fin] = list(nuevo)

        # ── aun / aún ────────────────────────────────────────────────────
        elif tok_lower == "aun":
            # "aún" = todavía → sigue verbo, adverbio o negación
            # "aun" = incluso → no tildar (aun cuando, aun si, aun así)
            BLOQUEADORES_AUN = {"cuando", "si", "siendo", "habiendo", "a", "con"}
            if sig_lower in BLOQUEADORES_AUN:
                pass  # es "incluso" → no tildar
            elif sig_pos in ["VERB", "AUX", "ADV"] or sig_lower in {"no", "ni", "más", "mas"}:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "aún" if token.text[0].islower() else "Aún"
                resultado[inicio:fin] = list(nuevo)

        # ── mas / más ────────────────────────────────────────────────────
        elif tok_lower == "mas":
            BLOQUEADORES_MAS = {
                "no", "ni", "nunca", "jamás", "tampoco", "pudo", "quiso",
                "quiere", "quería", "sabía", "sabe", "puede", "podía",
                "fue", "era", "es", "son", "hay", "tiene", "tenía",
                "pero", "sino", "aunque", "sin", "embargo", "que", "si",
                "se", "me", "te", "le", "lo", "la", "nos", "vale",
                "dijo", "llegó",
            }
            if sig_lower in BLOQUEADORES_MAS:
                pass  # conjunción → no tildar
            elif sig_pos in ["ADJ", "ADV", "NUM"]:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "más" if token.text[0].islower() else "Más"
                resultado[inicio:fin] = list(nuevo)

        # ── de / dé ──────────────────────────────────────────────────────
        elif tok_lower == "de":
            CLÍTICOS = {"que", "me", "le", "les", "nos", "te", "se", "no"}
            es_imperativo = (
                anterior and anterior.text.lower() in CLÍTICOS and
                siguiente and sig_pos in ["NOUN", "DET", "PRON", "ADJ"]
            )
            es_reflexivo = (
                anterior and anterior.text.lower() in {"se", "me", "te", "nos"} and
                dos_antes and dos_antes.text.lower() in {"que", "no", "nunca", "jamás"}
            )
            if es_imperativo or es_reflexivo:
                inicio = token.idx
                fin = inicio + len(token.text)
                resultado[inicio:fin] = list("dé")
        
        # ── arroyo / arrojó ──────────────────────────────────────────────
        elif tok_lower == "arroyo":
            ventana = [t.text.lower() for t in tokens[max(0, i-5):i+6]]
            tiene_violencia = any(w in LEXICO_VIOLENCIA for w in ventana)
            tiene_naturaleza = any(w in LEXICO_NATURALEZA for w in ventana)
            if tiene_violencia and not tiene_naturaleza:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "arrojó" if token.text[0].islower() else "Arrojó"
                resultado[inicio:fin] = list(nuevo)

        # ── hacho / hecho ────────────────────────────────────────────────
        elif tok_lower == "hacho":
            anterior_lower = anterior.text.lower() if anterior else ""
            if anterior_lower in {"se", "lo", "ha", "había", "haber", "fue"}:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "hecho" if token.text[0].islower() else "Hecho"
                resultado[inicio:fin] = list(nuevo)
        
        # ── allá / haya ──────────────────────────────────────────────────
        elif tok_lower == "allá" or tok_lower == "alla":
            if siguiente and re.search(r'(ado|ido|to|so|cho)$', sig_lower):
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "haya" if token.text[0].islower() else "Haya"
                resultado[inicio:fin] = list(nuevo)
        
        elif tok_lower == "hacia":
            # VERB/AUX → imperfecto de "hacer" → "hacía"
            # ADP → preposición direccional → sin tilde
            if token.pos_ in ["VERB", "AUX"]:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "hacía" if token.text[0].islower() else "Hacía"
                resultado[inicio:fin] = list(nuevo)

    return "".join(resultado)