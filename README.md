# Ortograf IA

Corrector ortográfico y gramatical inteligente con IA local. Analiza textos en tiempo real, detecta errores ortográficos y gramaticales, evalúa la calidad de escritura con un score porcentual, y devuelve el texto corregido con indicadores visuales de los cambios realizados.

---

## Vista previa

> 🚧 Proyecto en desarrollo activo — `v0.6.1`

---

## Características

- Interfaz tipo chat para una experiencia natural e intuitiva
- Corrección ortográfica y gramatical en tiempo real con subrayado de errores
- Pipeline de corrección multicapa con 9 etapas de procesamiento
- Protección de términos técnicos y anglicismos (tech guard)
- Detección de homófonos contextuales (has/haz/as, sino/si no, de/dé)
- Reconocimiento de nombres propios ambiguos por estructura gramatical (NER)
- Score de escritura con porcentaje y nivel de calidad
- Indicadores visuales de qué cambió y por qué
- Diseño oscuro y moderno, responsive para móvil y desktop

---

## Tecnologías

**Frontend**
- Vite
- JavaScript Vanilla (sin frameworks)
- HTML5 semántico con metodología BEM
- CSS modular con variables y diseño responsive

**Backend**
- Python 3.14
- FastAPI + Uvicorn
- LanguageTool (detección gramatical)
- spaCy `es_core_news_md` (NER y análisis de dependencias)
- Pipeline NLP propio con reglas contextuales

---

## Arquitectura del backend

```
backend/
└── app/
    ├── main.py
    ├── data/
    │   ├── slang_dict.json          # Diccionario de jerga
    │   ├── semantic_map.json        # Mapa semántico
    │   └── tech_whitelist.json      # Términos técnicos protegidos
    └── services/
        ├── pipeline.py              # Orquestador principal
        ├── normalize.py             # Limpieza de texto
        ├── slang.py                 # Sustitución de jerga
        ├── spelling.py              # Corrección ortográfica
        ├── grammar.py               # Reglas gramaticales
        ├── tech_guard.py            # Protección de anglicismos
        ├── homofonos.py             # Desambiguación de homófonos
        ├── ner.py                   # Reconocimiento de entidades
        ├── postprocess.py           # Capitalización y puntuación
        ├── scorer.py                # Evaluación de escritura
        └── diff.py                  # Detección de cambios
```

---

## Pipeline de corrección
texto original
│
▼

replace_slang       → xq → porque
normalize           → limpieza de espacios y saltos de línea
proteger_tecnicos   → deploy → TECH_0
correct_spelling    → LanguageTool filtrado
correct_grammar     → tildes, homófonos, puntuación
restaurar_tecnicos  → TECH_0 → deploy
resolver_homofonos  → has/haz/as, de/dé, sino/si no
capitalizar_NER     → rosa (sujeto) → Rosa
finalize_text       → mayúsculas y punto final


---

## Dependencias

**Frontend**
| Librería | Versión | Uso |
|----------|---------|-----|
| vite | latest | Bundler y servidor de desarrollo |

**Backend**
| Librería | Versión | Uso |
|----------|---------|-----|
| fastapi | 0.136.1 | Framework web y endpoints REST |
| uvicorn | 0.46.0 | Servidor ASGI |
| pydantic | 2.13.3 | Validación de datos de entrada |
| language-tool-python | 3.3.0 | Detección de errores ortográficos y gramaticales |
| spacy | 3.8.13 | NER y análisis de dependencias gramaticales |
| es-core-news-md | 3.8.0 | Modelo de español para spaCy |
| transformers | 5.6.2 | Tokenizador y modelos de lenguaje |
| torch | 2.11.0 | Backend de cómputo para transformers |
| sentencepiece | 0.2.1 | Tokenización de mT5 |

---

## Versiones

| Versión | Descripción |
|---------|-------------|
| v0.1.0 | Frontend completo, IA simulada |
| v0.2.0 | Backend conectado, corrección básica |
| v0.3.0 | Corrector en tiempo real con subrayado |
| v0.4.0 | Pipeline multicapa con normalización y slang |
| v0.5.0 | Score de escritura e indicadores de cambios |
| v0.6.0 | Errores marcados en burbuja del usuario |
| v0.6.1 | NER, tech guard, homófonos y correcciones avanzadas |

---

## Autor

**Jonathan Hernández**  
Proyecto académico y de portafolio personal.