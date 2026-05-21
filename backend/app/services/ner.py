import spacy
import re

# Para normalizar texto antes de pasarlo a spaCy: el modelo reconoce mejor
# "monica" que "mónica" (entrenado con formas sin acentos en muchos casos).
# Usamos strip de tildes solo para NER; los índices de carácter se conservan
# porque ó→o, á→a, etc. mantienen la longitud de cadena invariante en Python.
# Solo tildes vocálicas — ñ se conserva para que spaCy reconozca verbos
# correctamente ("señalo" no debe convertirse en "senalo").
_ACCENT_STRIP = str.maketrans('áéíóúüÁÉÍÓÚÜ', 'aeiouuAEIOUU')

_nlp = None

NOMBRES_AMBIGUOS = {
    "rosa", "victoria", "dulce", "marcos", "leon",
    "paz", "fe", "mercedes", "luz", "aurora", "gloria",
    "esperanza", "angel", "lupe", "consuelo", "rocio"
}

# Títulos que van en minúscula ante nombre propio según la RAE
TITULOS_MINUSCULA = {
    "doctor", "doctora", "ingeniero", "ingeniera",
    "licenciado", "licenciada", "secretario", "secretaria",
    "arquitecto", "arquitecta", "maestro", "maestra",
    "director", "directora", "gerente", "coordinador", "coordinadora",
    "subsecretario", "subsecretaria",
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
    # Correr NER sobre texto en minúsculas SIN tildes: el modelo es más robusto
    # con formas no acentuadas ("monica" > "mónica") porque muchos corpus de
    # entrenamiento no tienen acento. Los índices de carácter se conservan
    # porque cada ó→o, á→a, etc. mantiene la longitud de cadena.
    doc = nlp(text.lower().translate(_ACCENT_STRIP))
    resultado = list(text)

    for i, token in enumerate(doc):
        tok_lower = token.text  # ya es minúscula porque doc es de text.lower()
        debe_capitalizar = False

        anterior = doc[i - 1] if i > 0 else None
        tiene_art_generico = (
            anterior and anterior.text in ARTICULOS_GENERICOS
        )

        # Estrategia 1: NER reconoció la entidad
        # Los títulos (doctor, ingeniero…) van en minúscula según RAE salvo inicio
        if token.ent_type_ in ["PER", "LOC", "ORG"]:
            if tok_lower in TITULOS_MINUSCULA and i > 0:
                pass  # título en mitad de texto → no capitalizar
            elif token.ent_type_ == "ORG" and token.pos_ != "PROPN":
                pass  # RAE: sustantivos/adj/preposiciones comunes en mid-sentence → minúscula
            elif token.ent_type_ == "ORG" and token.idx < len(resultado) and resultado[token.idx].islower():
                pass  # LT no capitalizó este token → sustantivo común, no nombre propio
            elif token.pos_ in {"ADP", "CCONJ", "SCONJ", "DET"} and i > 0:
                pass  # RAE: preposiciones, conjunciones y artículos nunca llevan mayúscula salvo inicio
            elif token.pos_ == "VERB" and i > 0:
                # En entidades PER un VERB puede ser un apellido mal etiquetado (ej: "vega" en "luis vega").
                # Solo capitalizar si la forma original NO termina en pretérito (ó/é); esas sí son verbos.
                if token.ent_type_ == "PER":
                    _end = token.idx + len(token.text)
                    _orig = ''.join(resultado[token.idx:_end]) if _end <= len(resultado) else ''
                    if not any(_orig.endswith(t) for t in ('ó', 'é', 'ó.', 'é.')):
                        debe_capitalizar = True
            else:
                debe_capitalizar = True

        # Estrategia 2: nombre ambiguo con heurística
        elif tok_lower in NOMBRES_AMBIGUOS:
            if not tiene_art_generico:
                es_inicio = token.i == 0
                es_sujeto = token.dep_ == "nsubj"
                # Si spaCy ya etiqueta el token como PROPN, es nombre propio en ese contexto
                # (ej: "habla Rosa vega" donde "rosa" tiene dep_=obj pero pos_=PROPN)
                es_propn = token.pos_ == "PROPN"
                tras_conjuncion = (
                    anterior and anterior.text in CONJUNCIONES
                )
                tiene_det = any(
                    t.pos_ == "DET" and t.i == token.i - 1
                    for t in doc
                )
                if (es_inicio or es_sujeto or es_propn or tras_conjuncion) and not tiene_det:
                    debe_capitalizar = True

        # Solo capitalizar si el carácter en el texto ORIGINAL está en minúscula
        if debe_capitalizar:
            idx = token.idx
            if idx < len(resultado) and resultado[idx].islower():
                resultado[idx] = resultado[idx].upper()

    # Estrategia 4: extender entidades PER al token inmediatamente posterior
    # cuando spaCy no incluyó el apellido en la entidad por contexto largo.
    # Regla RAE: cualquier parte de un nombre de persona lleva mayúscula.
    # Solo se extiende para PER; ORG/LOC ya tienen su propia lógica.
    _POS_APELLIDO = {"PROPN", "NOUN", "ADJ"}
    _POS_NO_APELLIDO = {"AUX", "ADP", "DET", "CCONJ", "SCONJ", "PUNCT", "NUM", "ADV"}
    _TERMINACIONES_VERBALES = ('ó', 'é', 'ó.', 'é.')  # pretérito con tilde
    # Dependencias que indican que el token es parte del nombre compuesto, no verbo real
    _DEP_APELLIDO_VERBAL = {"flat", "amod"}
    # Dependencias/POS del token siguiente que indican verbo real (tiene argumento)
    _POS_ARG_VERBAL = {"DET", "ADP", "SCONJ", "CCONJ", "PUNCT"}
    for i, token in enumerate(doc):
        if (token.ent_type_ == "PER" and
                i + 1 < len(doc) and
                doc[i + 1].ent_type_ == ""):
            sig = doc[i + 1]
            idx = sig.idx
            end_idx = idx + len(sig.text)
            orig_word = ''.join(resultado[idx:end_idx]) if end_idx <= len(resultado) else ''

            # Excluir formas verbales con tilde de pretérito (indicó, llegó…)
            if any(orig_word.endswith(t) for t in _TERMINACIONES_VERBALES):
                continue

            es_candidato = False
            if (sig.pos_ in _POS_APELLIDO and sig.pos_ not in _POS_NO_APELLIDO and
                    sig.dep_ not in {"aux", "auxpass", "cop"} and not sig.is_stop):
                # Caso clásico: PROPN/NOUN/ADJ sin tilde verbal
                # dep_=aux/auxpass/cop excluidos: spaCy a veces asigna pos_=PROPN
                # a auxiliares como "habían" cuando siguen a un nombre compuesto
                es_candidato = True
            elif sig.pos_ == "VERB" and sig.dep_ in _DEP_APELLIDO_VERBAL and not sig.is_stop:
                # spaCy etiqueta el apellido como VERB (dep=flat o dep=amod)
                # Solo si el token siguiente NO introduce argumento verbal
                sig_next = doc[i + 2] if i + 2 < len(doc) else None
                if sig_next is None or sig_next.pos_ not in _POS_ARG_VERBAL:
                    es_candidato = True
            elif sig.pos_ == "VERB" and sig.dep_ == "ROOT" and not sig.is_stop:
                # spaCy asigna dep_=ROOT al apellido cuando el verbo real (corregido
                # por grammar con tilde ó/é) aparece inmediatamente después.
                # Si el token siguiente en resultado termina en ó/é, ese es el verbo
                # real → sig es apellido, no predicado principal.
                sig_next = doc[i + 2] if i + 2 < len(doc) else None
                if sig_next is not None:
                    n_idx = sig_next.idx
                    n_end = n_idx + len(sig_next.text)
                    n_word = ''.join(resultado[n_idx:n_end]) if n_end <= len(resultado) else ''
                    if any(n_word.endswith(t) for t in _TERMINACIONES_VERBALES):
                        es_candidato = True

            if es_candidato and idx < len(resultado) and resultado[idx].islower():
                resultado[idx] = resultado[idx].upper()

    # Estrategia 5: token ya capitalizado por LT (pos_=ADJ dep_=amod) cuyo head es
    # NOUN en función de sujeto → par nombre-apellido que spaCy no reconoce como PER.
    # (ej: spaCy ve "Monica" como ADJ→amod de "torres" NOUN→nsubj)
    # Condición: el ADJ debe venir ANTES de su head en el texto (Nombre + Apellido),
    # no DESPUÉS (como "África Subsahariana" donde "Subsahariana" es post-modificador).
    for i, token in enumerate(doc):
        if (token.ent_type_ == "" and
                token.pos_ == "ADJ" and
                token.dep_ == "amod" and
                token.idx < len(resultado) and
                resultado[token.idx].isupper()):  # LT ya lo marcó como nombre propio
            head = token.head
            if (token.idx < head.idx and  # ADJ precede a su head → patrón Nombre Apellido
                    head.pos_ in {"NOUN", "PROPN"} and
                    head.dep_ in {"nsubj", "ROOT", "flat"} and
                    not head.is_stop and
                    head.ent_type_ == ""):
                idx = head.idx
                if idx < len(resultado) and resultado[idx].islower():
                    resultado[idx] = resultado[idx].upper()

    # Estrategia 5b: apellido POST-posicionado de nombre ambiguo capitalizado.
    # Cubre el patrón inverso de E5: spaCy da apellido=ADJ-amod DESPUÉS del head
    # nombre=PROPN (ej: "Rosa Vega" donde "vega"=ADJ amod de "rosa"=PROPN).
    # Guarda: head debe estar en NOMBRES_AMBIGUOS para evitar falsos positivos
    # con adjetivos comunes que siguen a nombres propios ("Rosa bella").
    for i, token in enumerate(doc):
        if (token.ent_type_ == "" and
                token.pos_ == "ADJ" and
                token.dep_ == "amod" and
                not token.is_stop):
            head = token.head
            head_lower = head.text
            if (head.idx < token.idx and
                    head.pos_ == "PROPN" and
                    head_lower in NOMBRES_AMBIGUOS and
                    head.ent_type_ == "" and
                    head.idx < len(resultado) and
                    resultado[head.idx].isupper() and
                    not head.is_stop):
                idx = token.idx
                end_idx = idx + len(token.text)
                orig_word = ''.join(resultado[idx:end_idx]) if end_idx <= len(resultado) else ''
                if not any(orig_word.endswith(t) for t in _TERMINACIONES_VERBALES):
                    if idx < len(resultado) and resultado[idx].islower():
                        resultado[idx] = resultado[idx].upper()

    # Estrategia 6: nombre propio precedido de título (TITULOS_MINUSCULA).
    # Cubre "la doctora ana vega" cuando spaCy no detecta entidad PER porque
    # el primer token del nombre tiene pos_=ADJ (ej: "ana") y no PROPN.
    # Paso 0: precargar _titulo_con_nombre desde appos PER ya detectadas por spaCy.
    #   Previene que Paso 1 capitalice tokens POSTERIORES al nombre cuando spaCy
    #   detectó el nombre en PER pero siguió asignando appos adicionales al título
    #   (ej: "ana campo" → PER, pero spaCy pone "desarrollo", "metodologia" también
    #   como appos de "doctora" → sin esta guarda los capitalizaría incorrectamente).
    # Paso 1: capitalizar el nombre que aparece como dep=appos del título.
    # Paso 2: capitalizar el apellido que sigue como dep=amod del mismo título.
    # Guarda: no toca tokens con entidad (ya manejados por E1), no capitaliza
    # formas verbales con tilde de pretérito (ó/é), y el apellido debe aparecer
    # DESPUÉS del nombre en el texto (para no capitalizar adjetivos pre-posicionados).
    _titulo_con_nombre: dict[int, int] = {}  # título.idx → último nombre.idx
    for token in doc:
        if (token.dep_ == "appos" and
                token.head.text in TITULOS_MINUSCULA and
                token.head.ent_type_ == "" and
                token.ent_type_ == "PER"):
            prev = _titulo_con_nombre.get(token.head.idx, -1)
            if token.idx > prev:
                _titulo_con_nombre[token.head.idx] = token.idx
    for token in doc:
        if (token.ent_type_ == "" and
                not token.is_stop and
                token.dep_ == "appos" and
                token.head.text in TITULOS_MINUSCULA and
                token.head.ent_type_ == ""):
            # Si ya hay un appos PER del mismo título ANTES de este token,
            # spaCy detectó el nombre → este token no es parte del nombre.
            per_nombre_idx = _titulo_con_nombre.get(token.head.idx, -1)
            if per_nombre_idx >= 0 and per_nombre_idx < token.idx:
                continue
            _end = token.idx + len(token.text)
            _orig = ''.join(resultado[token.idx:_end]) if _end <= len(resultado) else ''
            if not any(_orig.endswith(t) for t in ('ó', 'é', 'ó.', 'é.')):
                if token.idx < len(resultado) and resultado[token.idx].islower():
                    resultado[token.idx] = resultado[token.idx].upper()
                _titulo_con_nombre[token.head.idx] = token.idx
    for token in doc:
        if (token.ent_type_ == "" and
                not token.is_stop and
                token.dep_ == "amod" and
                token.head.ent_type_ == "" and
                token.head.idx in _titulo_con_nombre and
                token.idx > _titulo_con_nombre[token.head.idx]):
            _end = token.idx + len(token.text)
            _orig = ''.join(resultado[token.idx:_end]) if _end <= len(resultado) else ''
            if not any(_orig.endswith(t) for t in ('ó', 'é', 'ó.', 'é.')):
                if token.idx < len(resultado) and resultado[token.idx].islower():
                    resultado[token.idx] = resultado[token.idx].upper()

    # Estrategia 3: secuencia de 2+ PROPNs sin entidad → nombre propio
    # Cubre "ana patricia torres" cuando el contexto largo rompe el NER de spaCy.
    # Condiciones de arranque: el PROPN no debe estar anclado a una entidad existente
    # (dep_=flat a un LOC/PER/ORG confunde a spaCy y hace que palabras comunes como
    # "requería" aparezcan como PROPN).
    # Condición de continuación: solo PROPN, no NOUN (los post-modificadores de sustantivos
    # comunes como "anuncio" o "atención" son NOUN y no deben incluirse en la cadena).
    k = 0
    while k < len(doc):
        token = doc[k]
        if (token.pos_ == "PROPN" and
                token.ent_type_ == "" and
                token.text not in TITULOS_MINUSCULA and
                token.head.ent_type_ == "" and  # no está anclado a una entidad
                token.idx < len(resultado) and resultado[token.idx].isupper()):  # LT ya lo capitalizó
            chain = [k]
            j = k + 1
            while (j < len(doc) and
                   (doc[j].pos_ == "PROPN" or
                    (doc[j].pos_ == "NOUN" and doc[j].dep_ == "appos" and not doc[j].is_stop)) and
                   doc[j].ent_type_ == "" and
                   doc[j].text not in TITULOS_MINUSCULA):
                chain.append(j)
                j += 1
            if len(chain) >= 2:
                for ci in chain:
                    t = doc[ci]
                    char_idx = t.idx
                    if char_idx < len(resultado) and resultado[char_idx].islower():
                        resultado[char_idx] = resultado[char_idx].upper()
            k = j
        else:
            k += 1

    return "".join(resultado)