# Ortograf IA

Corrector ortográfico y gramatical inteligente para español. Analiza texto en tiempo real mediante un pipeline de 10 etapas, devuelve el texto corregido con indicadores visuales de cambios, evalúa la calidad de escritura con un score porcentual, y detecta ambigüedades lingüísticas reales con opciones de interpretación intercambiables.
<img width="1889" height="1066" alt="image" src="https://github.com/user-attachments/assets/8677abb0-cc47-49d1-8761-9f3adccefb53" />
<img width="1896" height="1060" alt="image" src="https://github.com/user-attachments/assets/3757ed26-c47e-4cc3-b738-d45c2a4ffa67" />
<img width="1886" height="1071" alt="image" src="https://github.com/user-attachments/assets/a6167e28-93ef-4af3-9752-bb58a338d8da" />



---

## Características

- Interfaz tipo chat, intuitiva y con diseño oscuro responsive (móvil y desktop)
- Pipeline de corrección multicapa con 10 etapas de procesamiento
- Corrección ortográfica con LanguageTool filtrado y pyspellchecker
- Corrección gramatical con reglas RAE sobre tildes N-gram, homófonos y puntuación
- Tildes diacríticas con análisis de contexto N-gram (él/el, más/mas, sé/se, sí/si, dé/de…)
- Detección y corrección de homófonos contextuales (has/haz/as, sino/si no, de/dé)
- Protección de términos técnicos y anglicismos (tech guard) durante la corrección
- Reconocimiento de nombres propios ambiguos por estructura gramatical (NER con spaCy)
- Sustitución de jerga coloquial con diccionario configurable
- Mapa semántico configurable para reemplazar frases coloquiales por términos precisos
- Correcciones forzadas para patrones que escapan al pipeline automático
- Pulido final con Groq/Llama-3.3-70b como capa de IA externa (paso 10, opcional)
- Detección de ambigüedad lingüística real con tarjetas A/B intercambiables en la UI
- Score de escritura con porcentaje global, desglose ortografía/gramática y penalización por correcciones de IA
- Correcciones agrupadas por categoría (tildes, mayúsculas, puntuación, semántica, ortografía)
- Autenticación de usuarios con registro, login y recuperación de contraseña
- Historial de conversaciones persistente por usuario (SQLite)
- Botón de perfil con inicial del usuario o texto "Iniciar sesión" según el estado de sesión

---

## Tecnologías

**Frontend**
- Vite
- JavaScript Vanilla (sin frameworks), con módulos ES separados por responsabilidad
- HTML5 semántico con metodología BEM
- CSS modular con variables y diseño responsive

**Backend**
- Python 3.14
- FastAPI + Uvicorn
- LanguageTool (detección gramatical y ortográfica)
- spaCy `es_core_news_md` (NER y análisis de dependencias)
- Groq API / Llama-3.3-70b-versatile (pulido semántico e detección de ambigüedad)
- Pipeline NLP propio con reglas contextuales RAE

---

## Arquitectura del backend

```
backend/
└── app/
    ├── main.py
    ├── data/
    │   ├── correcciones_forzadas.json   # Patrones de corrección manual
    │   ├── homofonos_lexico.json        # Léxico para desambiguación de homófonos
    │   ├── ner_datos.json               # Datos para reconocimiento de entidades
    │   ├── semantic_map.json            # Mapa semántico: frases → términos precisos
    │   ├── slang_dict.json              # Diccionario de jerga coloquial
    │   ├── tech_whitelist.json          # Términos técnicos protegidos
    │   ├── grammar/
    │   │   ├── adjetivos_comunes.json
    │   │   ├── adjetivos_grado.json
    │   │   ├── mas_bloqueadores.json
    │   │   ├── sustantivos_cantidad.json
    │   │   ├── verbos_2da.json
    │   │   ├── verbos_3ra.json
    │   │   ├── verbos_futuro.json
    │   │   ├── verbos_pasado.json
    │   │   └── verbos_tiempo.json
    │   ├── geo/
    │   │   ├── geonombres.json
    │   │   └── toponimos_compuestos.json
    │   └── spelling/
    │       ├── futuros_protegidos.json
    │       ├── palabras_cortas.json
    │       ├── palabras_regionales.json
    │       └── raices_tecnicas.json
    ├── db/
    │   ├── database.py                  # Conexión SQLite
    │   └── models.py                    # Modelos Usuario, Chat, Mensaje
    ├── routes/
    │   ├── auth.py                      # Endpoints de autenticación
    │   └── chats.py                     # Endpoints de historial
    └── services/
        ├── pipeline.py                  # Orquestador principal (10 pasos)
        ├── normalize.py                 # Limpieza de espacios y saltos de línea
        ├── slang.py                     # Sustitución de jerga
        ├── correcciones.py              # Correcciones forzadas por patrón
        ├── semantic.py                  # Mapa semántico configurable
        ├── spelling.py                  # Corrección ortográfica (LanguageTool)
        ├── grammar.py                   # Reglas gramaticales RAE con JSONs de datos
        ├── tech_guard.py                # Protección de anglicismos
        ├── homofonos.py                 # Desambiguación de homófonos
        ├── ner.py                       # Reconocimiento de entidades (spaCy)
        ├── postprocess.py               # Capitalización y puntuación final
        ├── scorer.py                    # Evaluación de escritura con score parcial por IA
        ├── diff.py                      # Detección de cambios original → corregido
        └── ai_polish.py                 # Pulido con Groq/Llama y detección de ambigüedad
```

---

## Arquitectura del frontend

```
frontend/
└── src/
    ├── main.js                  # Punto de entrada: orquesta módulos y eventos de sesión
    ├── api/
    │   └── spelling.js          # Llamadas al backend (correct_text, historial)
    ├── ui/
    │   ├── auth.js              # Autenticación: login, registro, recuperación, perfil
    │   ├── chat.js              # Renderizado de burbujas y lógica del chat
    │   ├── corrections.js       # HTML de correcciones por categoría y tarjetas de ambigüedad
    │   ├── editor.js            # Área de escritura, subrayado de errores y envío
    │   └── history.js           # Carga y gestión del historial de conversaciones
    ├── utils/
    │   └── diff.js              # Diferencia palabra a palabra para recalcular correcciones
    ├── assets/
    │   ├── enviar.png
    │   └── cancelar.png
    └── styles/
        ├── main.css
        ├── base.css
        ├── layout.css
        └── components/
            ├── auth.css
            ├── chat.css
            ├── editor.css
            └── sidebar.css
```

---

## Pipeline de corrección

```
texto original
│
▼  1. replace_slang          xq → porque, tmb → también
   aplicar_correcciones      patrones de corrección manual
   apply_semantic_map        frases coloquiales → términos precisos
▼  2. normalize              limpieza de espacios y saltos de línea
▼  3. proteger_tecnicos      deploy → TECH_0  (blinda anglicismos)
▼  4. correct_spelling       LanguageTool filtrado + pyspellchecker
▼  5. correct_grammar        tildes N-gram, puntuación, verbos RAE
▼  6. restaurar_tecnicos     TECH_0 → deploy
▼  7. resolver_homofonos     has/haz/as, de/dé, sino/si no
▼  8. capitalizar_entidades  rosa (sujeto propio) → Rosa  (spaCy NER)
▼  9. finalize_text          mayúsculas de párrafo y punto final
▼ 10. pulir_texto (Groq)     revisión semántica con Llama-3.3-70b  [opcional]
│
▼
texto corregido + score + cambios + alternativa (si hay ambigüedad)
```

El paso 10 es opcional: se activa cuando la variable de entorno `GROQ_API_KEY` está presente. Si no existe la clave, el pipeline devuelve el resultado del paso 9 sin modificación. Las correcciones introducidas por Groq aplican una penalización adicional al score de ortografía y gramática.

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
| pyspellchecker | 0.9.0 | Corrección ortográfica complementaria |
| groq | 1.2.0 | Cliente de la API de Groq (Llama-3.3-70b) |
| sqlalchemy | 2.0.49 | ORM para base de datos SQLite |
| bcrypt | 5.0.0 | Encriptación de contraseñas |
| python-jose | 3.5.0 | Tokens JWT para autenticación |
| jellyfish | 1.2.1 | Similitud fonética para corrección ortográfica |

---

## Versiones estables

| Versión | Descripción |
|---------|-------------|
| v1.0.0 | Refactor completo: datos estáticos de grammar.py extraídos a JSONs en subcarpetas; frontend separado en módulos ES (ui/, utils/, api/); gemini.py renombrado a ai_polish.py; botón de perfil con estado de sesión; pipeline procesado párrafo por párrafo |

---

## Autor

**Jonathan Hernández**  
Proyecto de portafolio personal.
