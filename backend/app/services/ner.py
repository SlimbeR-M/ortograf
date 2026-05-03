import spacy
import re

_nlp = None

NOMBRES_AMBIGUOS = {
    "rosa", "victoria", "dulce", "marcos", "leon",
    "paz", "fe", "mercedes", "luz", "aurora", "gloria",
    "esperanza", "angel", "lupe", "consuelo", "rocio"
}

ARTICULOS_GENERICOS = {"la", "el", "una", "un", "las", "los", "unas", "unos"}

# Conjunciones tras las que un nombre ambiguo es probablemente propio
CONJUNCIONES = {"y", "e", "pero", "aunque", "sino", "porque", "que"}


def get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("es_core_news_md")
    return _nlp


def capitalizar_entidades(text: str) -> str:
    nlp = get_nlp()
    doc = nlp(text)
    resultado = list(text)

    for i, token in enumerate(doc):
        tok_lower = token.text.lower()
        debe_capitalizar = False

        anterior = doc[i - 1] if i > 0 else None
        tiene_art_generico = (
            anterior and anterior.text.lower() in ARTICULOS_GENERICOS
        )

        # Estrategia 1: NER reconoció la entidad
        if token.ent_type_ in ["PER", "LOC", "ORG"]:
            debe_capitalizar = True

        # Estrategia 2: nombre ambiguo con heurística
        elif tok_lower in NOMBRES_AMBIGUOS and token.text[0].islower():
            if not tiene_art_generico:
                es_inicio = token.i == 0
                es_sujeto = token.dep_ == "nsubj"
                # Nuevo: después de conjunción sin artículo
                tras_conjuncion = (
                    anterior and anterior.text.lower() in CONJUNCIONES
                )
                tiene_det = any(
                    t.pos_ == "DET" and t.i == token.i - 1
                    for t in doc
                )
                if (es_inicio or es_sujeto or tras_conjuncion) and not tiene_det:
                    debe_capitalizar = True

        # Estrategia 3: nsubj sin artículo previo
        elif (token.dep_ == "nsubj" and
              token.pos_ == "NOUN" and
              token.text[0].islower() and
              not tiene_art_generico):
            tiene_det = any(
                t.pos_ == "DET" and t.i == token.i - 1
                for t in doc
            )
            if not tiene_det:
                debe_capitalizar = True

        if debe_capitalizar and token.text[0].islower():
            idx = token.idx
            resultado[idx] = resultado[idx].upper()

    return "".join(resultado)