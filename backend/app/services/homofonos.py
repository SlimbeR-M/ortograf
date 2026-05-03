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


def resolver_homofonos(text: str) -> str:
    nlp = get_nlp()
    doc = nlp(text)
    tokens = list(doc)
    resultado = list(text)
    offset_acum = 0

    for i, token in enumerate(tokens):
        tok_lower = token.text.lower()

        # ── se (pronombre) nunca lleva tilde si va seguido de verbo/clítico ─
        if token.text == "sé" or token.text == "Sé":
            siguiente = tokens[i + 1] if i + 1 < len(tokens) else None
            if siguiente:
                # Si sigue verbo o clítico → revertir tilde
                clíticos = {"me", "te", "le", "lo", "la", "les", "los",
                            "las", "nos", "os", "se", "de", "fue",
                            "cayó", "dio", "puso", "hizo"}
                if (siguiente.pos_ in ["VERB", "AUX"] or
                        siguiente.text.lower() in clíticos):
                    inicio = token.idx
                    fin = inicio + len(token.text)
                    sin_tilde = "se" if token.text[0].islower() else "Se"
                    resultado[inicio:fin] = list(sin_tilde)

        # ── has / as / haz ────────────────────────────────────────────────
        if tok_lower in ["as", "has", "haz"]:
            siguiente = tokens[i + 1] if i + 1 < len(tokens) else None
            dos_sig = tokens[i + 2] if i + 2 < len(tokens) else None

            correcto = None

            if siguiente:
                sig_lower = siguiente.text.lower()
                # Has: seguido de participio (-ado, -ido, -to, -so, -cho)
                if re.search(r'(ado|ido|to|so|cho)$', sig_lower):
                    correcto = "has"
                # Has: seguido de "de" + infinitivo
                elif sig_lower == "de" and dos_sig and re.search(r'(ar|er|ir)$', dos_sig.text.lower()):
                    correcto = "has"
                # Haz: verbo hacer en imperativo
                elif siguiente.pos_ in ["NOUN", "PROPN", "DET"]:
                    correcto = "haz"
                # As: sustantivo (carta, experto)
                elif siguiente.pos_ in ["ADP", "VERB"] and tok_lower == "as":
                    correcto = "as"

            if correcto and correcto != tok_lower:
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = correcto if token.text[0].islower() else correcto.capitalize()
                resultado[inicio:fin] = list(nuevo)

        # ── hazar / asar ─────────────────────────────────────────────────
        if tok_lower in ["hazar", "azar"] and tok_lower != "azar":
            # Verificar contexto de cocina en ventana de 5 tokens
            ventana = [t.text.lower() for t in tokens[max(0, i-3):i+4]]
            if any(w in LEXICO_COCINA for w in ventana):
                inicio = token.idx
                fin = inicio + len(token.text)
                nuevo = "asar" if token.text[0].islower() else "Asar"
                resultado[inicio:fin] = list(nuevo)

        # ── mas / más ─────────────────────────────────────────────────────
        if tok_lower == "mas":
            # Si puede sustituirse por "pero" → conjunción adversativa → sin tilde
            # Detectar: si el token anterior es verbo/adj/adv y el siguiente también
            anterior = tokens[i - 1] if i > 0 else None
            siguiente = tokens[i + 1] if i + 1 < len(tokens) else None

            es_adversativo = (
                anterior and anterior.pos_ in ["VERB", "ADJ", "ADV", "NOUN"] and
                siguiente and siguiente.pos_ in ["VERB", "ADJ", "ADV", "NOUN", "PRON"]
            )

            if not es_adversativo:
                # Es adverbio comparativo → necesita tilde
                inicio = token.idx
                fin = inicio + len(token.text)
                resultado[inicio:fin] = list("más")
        
        # ── de / dé ───────────────────────────────────────────────────────
        if tok_lower == "de":
            anterior = tokens[i - 1] if i > 0 else None
            siguiente = tokens[i + 1] if i + 1 < len(tokens) else None

            CLÍTICOS = {"que", "me", "le", "les", "nos", "te", "se", "no"}

            es_imperativo = (
                anterior and anterior.text.lower() in CLÍTICOS and
                siguiente and siguiente.pos_ in ["NOUN", "DET", "PRON", "ADJ"]
            )

            # Casos extra: "se dé cuenta", "no me dé"
            dos_antes = tokens[i - 2] if i > 1 else None
            es_reflexivo = (
                anterior and anterior.text.lower() in {"se", "me", "te", "nos"} and
                dos_antes and dos_antes.text.lower() in {"que", "no", "nunca", "jamás"}
            )

            if es_imperativo or es_reflexivo:
                inicio = token.idx
                fin = inicio + len(token.text)
                resultado[inicio:fin] = list("dé")

    return "".join(resultado)