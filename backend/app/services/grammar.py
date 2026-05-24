import re
from app.services.postprocess import _GEONOMBRES as _GEONOMBRES_GEOGRAFICOS

# ─── Contextos bloqueadores ───────────────────────────────────────────────────

ARTICULOS = {"el", "la", "los", "las", "un", "una", "unos", "unas",
             "este", "esta", "ese", "esa", "aquel", "aquella"}

MAS_BLOQUEADORES = {
    # ── Negación ──────────────────────────────────────────────────────────
    "no", "ni", "jamás", "tampoco", "nada", "nadie",

    # ── Verbos auxiliares y copulativos ───────────────────────────────────
    "es", "era", "fue", "será", "sea", "sido",
    "está", "estaba", "estuvo", "estará", "esté",
    "hay", "hubo", "había", "habrá", "haya",
    "tiene", "tenía", "tuvo", "tendrá", "tenga",
    "hace", "hacía", "hizo", "hará", "haga",

    # ── Verbos modales ────────────────────────────────────────────────────
    "puede", "podía", "pudo", "podrá", "pueda",
    "quiere", "quería", "quiso", "querrá", "quiera",
    "sabe", "sabía", "supo", "sabrá", "sepa",
    "debe", "debía", "debió", "deberá", "deba",

    # ── Conjunciones adversativas y subordinantes ─────────────────────────
    "pero", "sino", "aunque", "sin", "embargo",
    "que", "si", "porque", "como", "cuando",
    "donde", "mientras", "para", "por", "ante",

    # ── Pronombres clíticos ───────────────────────────────────────────────
    "se", "me", "te", "le", "lo", "la", "nos", "les", "las", "los",

    # ── Verbos de acción bloqueadores ─────────────────────────────────────
    "vale", "dijo", "llegó", "salió", "entró", "subió", "bajó",
    "vino", "fue", "estuvo", "tuvo", "hizo", "puso", "trajo",
    "quiso", "pudo", "supo", "anduvo", "cayó", "dio",

    # ── Adverbios bloqueadores ────────────────────────────────────────────
    "así", "también", "aún", "ya", "aun", "solo", "sólo",
    "siempre", "antes", "después", "luego", "entonces",
}

MAS_SUSTANTIVOS_CANTIDAD = {
    # ── Personas ──────────────────────────────────────────────────────────
    "personas", "gente", "individuos", "habitantes", "ciudadanos",
    "estudiantes", "trabajadores", "empleados", "usuarios", "clientes",
    "miembros", "participantes", "voluntarios", "visitantes", "turistas",
    "niños", "jóvenes", "adultos", "ancianos", "mujeres", "hombres",

    # ── Tiempo ────────────────────────────────────────────────────────────
    "tiempo", "días", "horas", "minutos", "segundos", "semanas",
    "meses", "años", "décadas", "siglos", "momentos", "instantes",
    "ratos", "temporadas", "periodos", "etapas", "épocas",

    # ── Dinero y economía ─────────────────────────────────────────────────
    "dinero", "pesos", "dólares", "euros", "recursos", "fondos",
    "presupuesto", "inversión", "capital", "ganancias", "pérdidas",
    "ingresos", "gastos", "costos", "precios", "deudas", "ahorros",

    # ── Espacio ───────────────────────────────────────────────────────────
    "espacio", "lugar", "área", "zona", "región", "territorio",
    "superficie", "terreno", "campo", "tierra", "metros", "kilómetros",

    # ── Información y conocimiento ────────────────────────────────────────
    "información", "datos", "conocimiento", "experiencia", "aprendizaje",
    "educación", "formación", "capacitación", "instrucción", "práctica",
    "detalles", "ejemplos", "casos", "situaciones", "problemas",

    # ── Trabajo y esfuerzo ────────────────────────────────────────────────
    "trabajo", "esfuerzo", "dedicación", "atención", "cuidado",
    "empeño", "compromiso", "responsabilidad", "tareas", "actividades",
    "proyectos", "avances", "logros", "resultados", "progresos",

    # ── Naturaleza ────────────────────────────────────────────────────────
    "agua", "luz", "aire", "energía", "calor", "frío",
    "lluvia", "viento", "sol", "sombra", "tierra", "fuego",

    # ── Alimentación ──────────────────────────────────────────────────────
    "comida", "alimentos", "bebidas", "ingredientes", "productos",
    "frutas", "verduras", "carnes", "pan", "arroz", "frijoles",

    # ── Comunicación ──────────────────────────────────────────────────────
    "opciones", "alternativas", "posibilidades", "soluciones", "propuestas",
    "razones", "motivos", "causas", "argumentos", "explicaciones",
    "preguntas", "respuestas", "comentarios", "sugerencias", "ideas",

    # ── Objetos y materiales ──────────────────────────────────────────────
    "cosas", "objetos", "materiales", "herramientas", "equipos",
    "documentos", "archivos", "papeles", "libros", "páginas",
    "fotos", "imágenes", "videos", "archivos", "registros",

    # ── Tecnología ────────────────────────────────────────────────────────
    "aplicaciones", "programas", "sistemas", "plataformas", "servicios",
    "dispositivos", "computadoras", "teléfonos", "pantallas", "redes",

    # ── Salud ─────────────────────────────────────────────────────────────
    "medicamentos", "tratamientos", "ejercicio", "descanso", "sueño",
    "síntomas", "enfermedades", "vitaminas", "nutrientes", "calorías",

    # ── Transporte ────────────────────────────────────────────────────────
    "kilómetros", "millas", "metros", "pasos", "viajes", "trayectos",
    "rutas", "caminos", "calles", "avenidas", "carreteras",

    # ── Abstractos cuantificables ─────────────────────────────────────────
    "problemas", "errores", "fallas", "obstáculos", "retos", "desafíos",
    "ventajas", "beneficios", "oportunidades", "riesgos", "peligros",
    "cambios", "mejoras", "avances", "retrocesos", "diferencias",
    "conciencia", "consciencia", "paciencia", "experiencia",
    "presencia", "ausencia", "existencia", "resistencia",
    "doscientos", "cientos", "miles", "millones", "cien",
    "veinte", "treinta", "cuarenta", "cincuenta", "sesenta",
    "setenta", "ochenta", "noventa", "mil", "docenas", "decenas",
}

MAS_ADJETIVOS_GRADO = {
    # ── Tamaño ────────────────────────────────────────────────────────────
    "grande", "grandes", "pequeño", "pequeña", "pequeños", "pequeñas",
    "largo", "larga", "largos", "largas", "corto", "corta", "cortos", "cortas",
    "alto", "alta", "altos", "altas", "bajo", "baja", "bajos", "bajas",
    "ancho", "ancha", "anchos", "anchas", "estrecho", "estrecha",
    "grueso", "gruesa", "delgado", "delgada", "profundo", "profunda",

    # ── Velocidad ─────────────────────────────────────────────────────────
    "rápido", "rápida", "rápidos", "rápidas",
    "lento", "lenta", "lentos", "lentas",

    # ── Calidad ───────────────────────────────────────────────────────────
    "bueno", "buena", "buenos", "buenas",
    "malo", "mala", "malos", "malas",
    "mejor", "peor", "óptimo", "pésimo",
    "excelente", "excelentes", "terrible", "terribles",
    "bonito", "bonita", "bonitos", "bonitas",
    "feo", "fea", "feos", "feas",
    "hermoso", "hermosa", "hermosos", "hermosas",
    "lindo", "linda", "lindos", "lindas",

    # ── Dificultad ────────────────────────────────────────────────────────
    "fácil", "fáciles", "difícil", "difíciles",
    "sencillo", "sencilla", "complicado", "complicada",
    "complejo", "compleja", "simple", "simples",

    # ── Importancia ───────────────────────────────────────────────────────
    "importante", "importantes", "relevante", "relevantes",
    "significativo", "significativa", "esencial", "esenciales",
    "fundamental", "fundamentales", "necesario", "necesaria",
    "útil", "útiles", "valioso", "valiosa",

    # ── Estado ────────────────────────────────────────────────────────────
    "fuerte", "fuertes", "débil", "débiles",
    "duro", "dura", "duros", "duras",
    "suave", "suaves", "blando", "blanda",
    "firme", "firmes", "frágil", "frágiles",

    # ── Temperatura ───────────────────────────────────────────────────────
    "frío", "fría", "frías", "fríos",
    "caliente", "calientes", "cálido", "cálida",
    "tibio", "tibia", "templado", "templada",

    # ── Luminosidad ───────────────────────────────────────────────────────
    "claro", "clara", "claros", "claras",
    "oscuro", "oscura", "oscuros", "oscuras",
    "brillante", "brillantes", "opaco", "opaca",

    # ── Distancia ─────────────────────────────────────────────────────────
    "cerca", "lejos", "cercano", "cercana", "lejano", "lejana",
    "próximo", "próxima", "distante", "distantes",

    # ── Tiempo ────────────────────────────────────────────────────────────
    "tarde", "temprano", "pronto", "rápido",
    "antiguo", "antigua", "moderno", "moderna",
    "nuevo", "nueva", "nuevos", "nuevas",
    "viejo", "vieja", "viejos", "viejas",
    "reciente", "recientes",

    # ── Seguridad ─────────────────────────────────────────────────────────
    "seguro", "segura", "seguros", "seguras",
    "peligroso", "peligrosa", "peligrosos", "peligrosas",
    "riesgoso", "riesgosa",

    # ── Cantidad relacionada ───────────────────────────────────────────────
    "posible", "posibles", "probable", "probables",
    "común", "comunes", "frecuente", "frecuentes",
    "raro", "rara", "raros", "raras",

    # ── Emocional ─────────────────────────────────────────────────────────
    "feliz", "felices", "triste", "tristes",
    "contento", "contenta", "contentos", "contentas",
    "alegre", "alegres", "tranquilo", "tranquila",
    "nervioso", "nerviosa", "calmado", "calmada",
    "interesante", "interesantes", "aburrido", "aburrida",
    "emocionante", "emocionantes", "agradable", "agradables",

    # ── Inteligencia ──────────────────────────────────────────────────────
    "inteligente", "inteligentes", "listo", "lista",
    "capaz", "capaces", "hábil", "hábiles",
    "talentoso", "talentosa", "creativo", "creativa",

    # ── Salud ─────────────────────────────────────────────────────────────
    "sano", "sana", "sanos", "sanas",
    "enfermo", "enferma", "enfermos", "enfermas",
    "saludable", "saludables", "delicado", "delicada",

    # ── Económico ─────────────────────────────────────────────────────────
    "caro", "cara", "caros", "caras",
    "barato", "barata", "baratos", "baratas",
    "costoso", "costosa", "económico", "económica",
    "accesible", "accesibles",

    # ── Social ────────────────────────────────────────────────────────────
    "popular", "populares", "conocido", "conocida",
    "famoso", "famosa", "famosos", "famosas",
    "importante", "importantes",

    # ── Adverbios de grado que funcionan como adjetivos ───────────────────
    "bien", "mal", "mejor", "peor",
}

VERBOS_3RA = {
    # ── Ser / Estar ───────────────────────────────────────────────────────
    "es", "fue", "era", "será", "sea", "sido", "siendo",
    "está", "estuvo", "estaba", "estará", "esté", "estado",

    # ── Haber ─────────────────────────────────────────────────────────────
    "ha", "había", "habrá", "haya", "habido",

    # ── Tener ─────────────────────────────────────────────────────────────
    "tiene", "tenía", "tendrá", "tenga", "tuvo",

    # ── Hacer ─────────────────────────────────────────────────────────────
    "hace", "hacía", "hará", "haga", "hizo",

    # ── Ir ────────────────────────────────────────────────────────────────
    "va", "iba", "irá", "vaya", "fue",

    # ── Venir ─────────────────────────────────────────────────────────────
    "viene", "venía", "vendrá", "venga", "vino",

    # ── Poder ─────────────────────────────────────────────────────────────
    "puede", "podía", "podrá", "pueda", "pudo",

    # ── Querer ────────────────────────────────────────────────────────────
    "quiere", "quería", "querrá", "quiera", "quiso",

    # ── Saber ─────────────────────────────────────────────────────────────
    "sabe", "sabía", "sabrá", "sepa", "supo",

    # ── Decir ─────────────────────────────────────────────────────────────
    "dice", "decía", "dirá", "diga", "dijo",

    # ── Ver ───────────────────────────────────────────────────────────────
    "ve", "veía", "verá", "vea", "vio",

    # ── Dar ───────────────────────────────────────────────────────────────
    "da", "daba", "dará", "dé", "dio",

    # ── Salir ─────────────────────────────────────────────────────────────
    "sale", "salía", "saldrá", "salga", "salió",

    # ── Llegar ────────────────────────────────────────────────────────────
    "llega", "llegaba", "llegará", "llegue", "llegó",

    # ── Llamar ────────────────────────────────────────────────────────────
    "llama", "llamaba", "llamará", "llame", "llamó",

    # ── Hablar ────────────────────────────────────────────────────────────
    "habla", "hablaba", "hablará", "hable", "habló",

    # ── Trabajar ──────────────────────────────────────────────────────────
    "trabaja", "trabajaba", "trabajará", "trabaje", "trabajó",

    # ── Vivir ─────────────────────────────────────────────────────────────
    "vive", "vivía", "vivirá", "viva", "vivió",

    # ── Comer ─────────────────────────────────────────────────────────────
    "come", "comía", "comerá", "coma", "comió",

    # ── Beber ─────────────────────────────────────────────────────────────
    "bebe", "bebía", "beberá", "beba", "bebió",

    # ── Leer ──────────────────────────────────────────────────────────────
    "lee", "leía", "leerá", "lea", "leyó",

    # ── Escribir ──────────────────────────────────────────────────────────
    "escribe", "escribía", "escribirá", "escriba", "escribió",

    # ── Correr ────────────────────────────────────────────────────────────
    "corre", "corría", "correrá", "corra", "corrió",

    # ── Dormir ────────────────────────────────────────────────────────────
    "duerme", "dormía", "dormirá", "duerma", "durmió",

    # ── Poner ─────────────────────────────────────────────────────────────
    "pone", "ponía", "pondrá", "ponga", "puso",

    # ── Traer ─────────────────────────────────────────────────────────────
    "trae", "traía", "traerá", "traiga", "trajo",

    # ── Llevar ────────────────────────────────────────────────────────────
    "lleva", "llevaba", "llevará", "lleve", "llevó",

    # ── Comprar ───────────────────────────────────────────────────────────
    "compra", "compraba", "comprará", "compre", "compró",

    # ── Vender ────────────────────────────────────────────────────────────
    "vende", "vendía", "venderá", "venda", "vendió",

    # ── Abrir ─────────────────────────────────────────────────────────────
    "abre", "abría", "abrirá", "abra", "abrió",

    # ── Cerrar ────────────────────────────────────────────────────────────
    "cierra", "cerraba", "cerrará", "cierre", "cerró",

    # ── Empezar ───────────────────────────────────────────────────────────
    "empieza", "empezaba", "empezará", "empiece", "empezó",

    # ── Terminar ──────────────────────────────────────────────────────────
    "termina", "terminaba", "terminará", "termine", "terminó",

    # ── Estudiar ──────────────────────────────────────────────────────────
    "estudia", "estudiaba", "estudiará", "estudie", "estudió",

    # ── Jugar ─────────────────────────────────────────────────────────────
    "juega", "jugaba", "jugará", "juegue", "jugó",

    # ── Buscar ────────────────────────────────────────────────────────────
    "busca", "buscaba", "buscará", "busque", "buscó",

    # ── Encontrar ─────────────────────────────────────────────────────────
    "encuentra", "encontraba", "encontrará", "encuentre", "encontró",

    # ── Pagar ─────────────────────────────────────────────────────────────
    "paga", "pagaba", "pagará", "pague", "pagó",

    # ── Subir ─────────────────────────────────────────────────────────────
    "sube", "subía", "subirá", "suba", "subió",

    # ── Bajar ─────────────────────────────────────────────────────────────
    "baja", "bajaba", "bajará", "baje", "bajó",

    # ── Entrar ────────────────────────────────────────────────────────────
    "entra", "entraba", "entrará", "entre", "entró",

    # ── Quedar ────────────────────────────────────────────────────────────
    "queda", "quedaba", "quedará", "quede", "quedó",

    # ── Pasar ─────────────────────────────────────────────────────────────
    "pasa", "pasaba", "pasará", "pase", "pasó",

    # ── Tomar ─────────────────────────────────────────────────────────────
    "toma", "tomaba", "tomará", "tome", "tomó",

    # ── Usar ──────────────────────────────────────────────────────────────
    "usa", "usaba", "usará", "use", "usó",

    # ── Necesitar ─────────────────────────────────────────────────────────
    "necesita", "necesitaba", "necesitará", "necesite", "necesitó",

    # ── Ayudar ────────────────────────────────────────────────────────────
    "ayuda", "ayudaba", "ayudará", "ayude", "ayudó",

    # ── Cambiar ───────────────────────────────────────────────────────────
    "cambia", "cambiaba", "cambiará", "cambie", "cambió",

    # ── Creer ─────────────────────────────────────────────────────────────
    "cree", "creía", "creerá", "crea", "creyó",

    # ── Pensar ────────────────────────────────────────────────────────────
    "piensa", "pensaba", "pensará", "piense", "pensó",

    # ── Sentir ────────────────────────────────────────────────────────────
    "siente", "sentía", "sentirá", "sienta", "sintió",

    # ── Seguir ────────────────────────────────────────────────────────────
    "sigue", "seguía", "seguirá", "siga", "siguió",

    # ── Conocer ───────────────────────────────────────────────────────────
    "conoce", "conocía", "conocerá", "conozca", "conoció",

    # ── Recordar ──────────────────────────────────────────────────────────
    "recuerda", "recordaba", "recordará", "recuerde", "recordó",

    # ── Olvidar ───────────────────────────────────────────────────────────
    "olvida", "olvidaba", "olvidará", "olvide", "olvidó",

    # ── Preguntar ─────────────────────────────────────────────────────────
    "pregunta", "preguntaba", "preguntará", "pregunte", "preguntó",

    # ── Contestar ─────────────────────────────────────────────────────────
    "contesta", "contestaba", "contestará", "conteste", "contestó",

    # ── Explicar ──────────────────────────────────────────────────────────
    "explica", "explicaba", "explicará", "explique", "explicó",

    # ── Mostrar ───────────────────────────────────────────────────────────
    "muestra", "mostraba", "mostrará", "muestre", "mostró",

    # ── Esperar ───────────────────────────────────────────────────────────
    "espera", "esperaba", "esperará", "espere", "esperó",

    # ── Regresar ──────────────────────────────────────────────────────────
    "regresa", "regresaba", "regresará", "regrese", "regresó",

    # ── Revisar ───────────────────────────────────────────────────────────
    "revisa", "revisaba", "revisará", "revise", "revisó",

    # ── Lograr ────────────────────────────────────────────────────────────
    "logra", "lograba", "logrará", "logre", "logró",

    # ── Intentar ──────────────────────────────────────────────────────────
    "intenta", "intentaba", "intentará", "intente", "intentó",

    # ── Recibir ───────────────────────────────────────────────────────────
    "recibe", "recibía", "recibirá", "reciba", "recibió",

    # ── Enviar ────────────────────────────────────────────────────────────
    "envía", "enviaba", "enviará", "envíe", "envió",

    # ── Ganar ─────────────────────────────────────────────────────────────
    "gana", "ganaba", "ganará", "gane", "ganó",

    # ── Perder ────────────────────────────────────────────────────────────
    "pierde", "perdía", "perderá", "pierda", "perdió",

    # ── Caer ──────────────────────────────────────────────────────────────
    "cae", "caía", "caerá", "caiga", "cayó",

    # ── Crecer ────────────────────────────────────────────────────────────
    "crece", "crecía", "crecerá", "crezca", "creció",

    # ── Producir ──────────────────────────────────────────────────────────
    "produce", "producía", "producirá", "produzca", "produjo",

    # ── Incluir ───────────────────────────────────────────────────────────
    "incluye", "incluía", "incluirá", "incluya", "incluyó",

    # ── Permitir ──────────────────────────────────────────────────────────
    "permite", "permitía", "permitirá", "permita", "permitió",

    # ── Depender ──────────────────────────────────────────────────────────
    "depende", "dependía", "dependerá", "dependa", "dependió",

    # ── Resultar ──────────────────────────────────────────────────────────
    "resulta", "resultaba", "resultará", "resulte", "resultó",

    # ── Ocurrir ───────────────────────────────────────────────────────────
    "ocurre", "ocurría", "ocurrirá", "ocurra", "ocurrió",

    # ── Aparecer ──────────────────────────────────────────────────────────
    "aparece", "aparecía", "aparecerá", "aparezca", "apareció",

    # ── Ofrecer ───────────────────────────────────────────────────────────
    "ofrece", "ofrecía", "ofrecerá", "ofrezca", "ofreció",

    # ── Conseguir ─────────────────────────────────────────────────────────
    "consigue", "conseguía", "conseguirá", "consiga", "consiguió",

    # ── Obtener ───────────────────────────────────────────────────────────
    "obtiene", "obtenía", "obtendrá", "obtenga", "obtuvo",

    # ── Mantener ──────────────────────────────────────────────────────────
    "mantiene", "mantenía", "mantendrá", "mantenga", "mantuvo",

    # ── Entender ──────────────────────────────────────────────────────────
    "entiende", "entendía", "entenderá", "entienda", "entendió",

    # ── Atender ───────────────────────────────────────────────────────────
    "atiende", "atendía", "atenderá", "atienda", "atendió",

    # ── Volver ────────────────────────────────────────────────────────────
    "vuelve", "volvía", "volverá", "vuelva", "volvió",

    # ── Resolver ──────────────────────────────────────────────────────────
    "resuelve", "resolvía", "resolverá", "resuelva", "resolvió",

    # ── Devolver ──────────────────────────────────────────────────────────
    "devuelve", "devolvía", "devolverá", "devuelva", "devolvió",

    # ── Mover ─────────────────────────────────────────────────────────────
    "mueve", "movía", "moverá", "mueva", "movió",

    # ── Oír ───────────────────────────────────────────────────────────────
    "oye", "oía", "oirá", "oiga", "oyó",

    # ── Requerir ──────────────────────────────────────────────────────────
    "requiere", "requería", "requerirá", "requiera", "requirió",

    # ── Dirigir ───────────────────────────────────────────────────────────
    "dirige", "dirigía", "dirigirá", "dirija", "dirigió",

    # ── Decidir ───────────────────────────────────────────────────────────
    "decide", "decidía", "decidirá", "decida", "decidió",

    # ── Elegir ────────────────────────────────────────────────────────────
    "elige", "elegía", "elegirá", "elija", "eligió",

    # ── Pedir ─────────────────────────────────────────────────────────────
    "pide", "pedía", "pedirá", "pida", "pidió",

    # ── Repetir ───────────────────────────────────────────────────────────
    "repite", "repetía", "repetirá", "repita", "repitió",

    # ── Servir ────────────────────────────────────────────────────────────
    "sirve", "servía", "servirá", "sirva", "sirvió",

    # ── Sufrir ────────────────────────────────────────────────────────────
    "sufre", "sufría", "sufrirá", "sufra", "sufrió",

    # ── Cumplir ───────────────────────────────────────────────────────────
    "cumple", "cumplía", "cumplirá", "cumpla", "cumplió",

    # ── Surgir ────────────────────────────────────────────────────────────
    "surge", "surgía", "surgirá", "surja", "surgió",

    # ── Reducir ───────────────────────────────────────────────────────────
    "reduce", "reducía", "reducirá", "reduzca", "redujo",

    # ── Conducir ──────────────────────────────────────────────────────────
    "conduce", "conducía", "conducirá", "conduzca", "condujo",

    # ── Construir ─────────────────────────────────────────────────────────
    "construye", "construía", "construirá", "construya", "construyó",

    # ── Destruir ──────────────────────────────────────────────────────────
    "destruye", "destruía", "destruirá", "destruya", "destruyó",

    # ── Contribuir ────────────────────────────────────────────────────────
    "contribuye", "contribuía", "contribuirá", "contribuya", "contribuyó",

    # ── Distribuir ────────────────────────────────────────────────────────
    "distribuye", "distribuía", "distribuirá", "distribuya", "distribuyó",

    # ── Huir ──────────────────────────────────────────────────────────────
    "huye", "huía", "huirá", "huya", "huyó",

    # ── Pasados irregulares comunes ───────────────────────────────────────
    "quiso", "pudo", "supo", "tuvo", "vino", "dijo", "hizo",
    "puso", "trajo", "anduvo", "estuvo", "hubo", "cupo",
    "respondió", "contestó", "explicó", "preguntó", "llamó",
    "llegó", "salió", "entró", "subió", "bajó", "abrió",
    "cerró", "empezó", "terminó", "volvió", "pidió",
    "entendí", "entendió", "respondí", "respondió", "llegué", "llegó",
    "salí", "salió", "entré", "entró", "subí", "subió", "bajé", "bajó",
    "comí", "comió", "bebí", "bebió", "corrí", "corrió", "dormí", "durmió",
    "pedí", "pidió", "seguí", "siguió", "sentí", "sintió",
}

VERBOS_2DA = {
    # ── Ser / Estar ───────────────────────────────────────────────────────
    "eres", "fuiste", "eras", "serás", "seas",
    "estás", "estuviste", "estabas", "estarás", "estés",

    # ── Haber ─────────────────────────────────────────────────────────────
    "has", "habías", "habrás", "hayas",

    # ── Tener ─────────────────────────────────────────────────────────────
    "tienes", "tenías", "tendrás", "tengas", "tuviste",

    # ── Hacer ─────────────────────────────────────────────────────────────
    "haces", "hacías", "harás", "hagas", "hiciste",

    # ── Ir ────────────────────────────────────────────────────────────────
    "vas", "ibas", "irás", "vayas", "fuiste",

    # ── Venir ─────────────────────────────────────────────────────────────
    "vienes", "venías", "vendrás", "vengas", "viniste",

    # ── Poder ─────────────────────────────────────────────────────────────
    "puedes", "podías", "podrás", "puedas", "pudiste",

    # ── Querer ────────────────────────────────────────────────────────────
    "quieres", "querías", "querrás", "quieras", "quisiste",

    # ── Saber ─────────────────────────────────────────────────────────────
    "sabes", "sabías", "sabrás", "sepas", "supiste",

    # ── Decir ─────────────────────────────────────────────────────────────
    "dices", "decías", "dirás", "digas", "dijiste",

    # ── Ver ───────────────────────────────────────────────────────────────
    "ves", "veías", "verás", "veas", "viste",

    # ── Dar ───────────────────────────────────────────────────────────────
    "das", "dabas", "darás", "des", "diste",

    # ── Salir ─────────────────────────────────────────────────────────────
    "sales", "salías", "saldrás", "salgas", "saliste",

    # ── Llegar ────────────────────────────────────────────────────────────
    "llegas", "llegabas", "llegarás", "llegues", "llegaste",

    # ── Hablar ────────────────────────────────────────────────────────────
    "hablas", "hablabas", "hablarás", "hables", "hablaste",

    # ── Trabajar ──────────────────────────────────────────────────────────
    "trabajas", "trabajabas", "trabajarás", "trabajes", "trabajaste",

    # ── Vivir ─────────────────────────────────────────────────────────────
    "vives", "vivías", "vivirás", "vivas", "viviste",

    # ── Comer ─────────────────────────────────────────────────────────────
    "comes", "comías", "comerás", "comas", "comiste",

    # ── Beber ─────────────────────────────────────────────────────────────
    "bebes", "bebías", "beberás", "bebas", "bebiste",

    # ── Leer ──────────────────────────────────────────────────────────────
    "lees", "leías", "leerás", "leas", "leíste",

    # ── Escribir ──────────────────────────────────────────────────────────
    "escribes", "escribías", "escribirás", "escribas", "escribiste",

    # ── Correr ────────────────────────────────────────────────────────────
    "corres", "corrías", "correrás", "corras", "corriste",

    # ── Dormir ────────────────────────────────────────────────────────────
    "duermes", "dormías", "dormirás", "duermas", "dormiste",

    # ── Poner ─────────────────────────────────────────────────────────────
    "pones", "ponías", "pondrás", "pongas", "pusiste",

    # ── Traer ─────────────────────────────────────────────────────────────
    "traes", "traías", "traerás", "traigas", "trajiste",

    # ── Llevar ────────────────────────────────────────────────────────────
    "llevas", "llevabas", "llevarás", "lleves", "llevaste",

    # ── Comprar ───────────────────────────────────────────────────────────
    "compras", "comprabas", "comprarás", "compres", "compraste",

    # ── Abrir ─────────────────────────────────────────────────────────────
    "abres", "abrías", "abrirás", "abras", "abriste",

    # ── Buscar ────────────────────────────────────────────────────────────
    "buscas", "buscabas", "buscarás", "busques", "buscaste",

    # ── Encontrar ─────────────────────────────────────────────────────────
    "encuentras", "encontrabas", "encontrarás", "encuentres", "encontraste",

    # ── Estudiar ──────────────────────────────────────────────────────────
    "estudias", "estudiabas", "estudiarás", "estudies", "estudiaste",

    # ── Esperar ───────────────────────────────────────────────────────────
    "esperas", "esperabas", "esperarás", "esperes", "esperaste",

    # ── Usar ──────────────────────────────────────────────────────────────
    "usas", "usabas", "usarás", "uses", "usaste",

    # ── Necesitar ─────────────────────────────────────────────────────────
    "necesitas", "necesitabas", "necesitarás", "necesites", "necesitaste",

    # ── Creer ─────────────────────────────────────────────────────────────
    "crees", "creías", "creerás", "creas", "creíste",

    # ── Pensar ────────────────────────────────────────────────────────────
    "piensas", "pensabas", "pensarás", "pienses", "pensaste",

    # ── Sentir ────────────────────────────────────────────────────────────
    "sientes", "sentías", "sentirás", "sientas", "sentiste",

    # ── Conocer ───────────────────────────────────────────────────────────
    "conoces", "conocías", "conocerás", "conozcas", "conociste",

    # ── Recordar ──────────────────────────────────────────────────────────
    "recuerdas", "recordabas", "recordarás", "recuerdes", "recordaste",

    # ── Olvidar ───────────────────────────────────────────────────────────
    "olvidas", "olvidabas", "olvidarás", "olvides", "olvidaste",

    # ── Pedir ─────────────────────────────────────────────────────────────
    "pides", "pedías", "pedirás", "pidas", "pediste",

    # ── Volver ────────────────────────────────────────────────────────────
    "vuelves", "volvías", "volverás", "vuelvas", "volviste",

    # ── Seguir ────────────────────────────────────────────────────────────
    "sigues", "seguías", "seguirás", "sigas", "seguiste",

    # ── Entender ──────────────────────────────────────────────────────────
    "entiendes", "entendías", "entenderás", "entiendas", "entendiste",

    # ── Perder ────────────────────────────────────────────────────────────
    "pierdes", "perdías", "perderás", "pierdas", "perdiste",

    # ── Ganar ─────────────────────────────────────────────────────────────
    "ganas", "ganabas", "ganarás", "ganes", "ganaste",

    # ── Recibir ───────────────────────────────────────────────────────────
    "recibes", "recibías", "recibirás", "recibas", "recibiste",

    # ── Decidir ───────────────────────────────────────────────────────────
    "decides", "decidías", "decidirás", "decidas", "decidiste",

    # ── Elegir ────────────────────────────────────────────────────────────
    "eliges", "elegías", "elegirás", "elijas", "elegiste",

    # ── Cumplir ───────────────────────────────────────────────────────────
    "cumples", "cumplías", "cumplirás", "cumplas", "cumpliste",

    # ── Sufrir ────────────────────────────────────────────────────────────
    "sufres", "sufrías", "sufrirás", "sufras", "sufriste",

    # ── Debes ─────────────────────────────────────────────────────────────
    "debes", "debías", "deberás", "debas", "debiste",

    # ── Poder (adicionales) ───────────────────────────────────────────────
    "podías", "podrías",

    # ── Formas adicionales comunes ────────────────────────────────────────
    "harás", "vendrás", "dirás", "pondrás", "saldrás",
    "tendrás", "podrás", "querrás", "sabrás", "cabrás",
    "valdás", "habrás",
}

VERBOS_TIEMPO = {
    # ── Ser ───────────────────────────────────────────────────────────────
    "es", "era", "fue", "será", "siendo", "sido",

    # ── Estar ─────────────────────────────────────────────────────────────
    "está", "estaba", "estuvo", "estará", "estando",

    # ── Haber ─────────────────────────────────────────────────────────────
    "ha", "había", "hubo", "habrá", "habiendo",

    # ── Hacer ─────────────────────────────────────────────────────────────
    "hace", "hacía", "hizo", "hará", "haciendo",

    # ── Seguir ────────────────────────────────────────────────────────────
    "sigue", "seguía", "siguió", "seguirá", "siguiendo",

    # ── Continuar ─────────────────────────────────────────────────────────
    "continúa", "continuaba", "continuó", "continuará", "continuando",

    # ── Quedar ────────────────────────────────────────────────────────────
    "queda", "quedaba", "quedó", "quedará", "quedando",

    # ── Resultar ──────────────────────────────────────────────────────────
    "resulta", "resultaba", "resultó", "resultará", "resultando",

    # ── Llevar ────────────────────────────────────────────────────────────
    "lleva", "llevaba", "llevó", "llevará", "llevando",

    # ── Tener ─────────────────────────────────────────────────────────────
    "tiene", "tenía", "tuvo", "tendrá", "teniendo",

    # ── Pasar ─────────────────────────────────────────────────────────────
    "pasa", "pasaba", "pasó", "pasará", "pasando",

    # ── Durar ─────────────────────────────────────────────────────────────
    "dura", "duraba", "duró", "durará", "durando",

    # ── Tardar ────────────────────────────────────────────────────────────
    "tarda", "tardaba", "tardó", "tardará", "tardando",

    # ── Ocurrir ───────────────────────────────────────────────────────────
    "ocurre", "ocurría", "ocurrió", "ocurrirá", "ocurriendo",

    # ── Suceder ───────────────────────────────────────────────────────────
    "sucede", "sucedía", "sucedió", "sucederá", "sucediendo",

    # ── Transcurrir ───────────────────────────────────────────────────────
    "transcurre", "transcurría", "transcurrió", "transcurrirá",

    # ── Volver ────────────────────────────────────────────────────────────
    "vuelve", "volvía", "volvió", "volverá", "volviendo",

    # ── Empezar ───────────────────────────────────────────────────────────
    "empieza", "empezaba", "empezó", "empezará", "empezando",

    # ── Terminar ──────────────────────────────────────────────────────────
    "termina", "terminaba", "terminó", "terminará", "terminando",

    # ── Comenzar ──────────────────────────────────────────────────────────
    "comienza", "comenzaba", "comenzó", "comenzará", "comenzando",

    # ── Acabar ────────────────────────────────────────────────────────────
    "acaba", "acababa", "acabó", "acabará", "acabando",

    # ── Finalizar ─────────────────────────────────────────────────────────
    "finaliza", "finalizaba", "finalizó", "finalizará", "finalizando",

    # ── Iniciar ───────────────────────────────────────────────────────────
    "inicia", "iniciaba", "inició", "iniciará", "iniciando",

    # ── Aparecer ──────────────────────────────────────────────────────────
    "aparece", "aparecía", "apareció", "aparecerá", "apareciendo",

    # ── Existir ───────────────────────────────────────────────────────────
    "existe", "existía", "existió", "existirá", "existiendo",

    # ── Vivir ─────────────────────────────────────────────────────────────
    "vive", "vivía", "vivió", "vivirá", "viviendo",

    # ── Funcionar ─────────────────────────────────────────────────────────
    "funciona", "funcionaba", "funcionó", "funcionará", "funcionando",

    # ── Cambiar ───────────────────────────────────────────────────────────
    "cambia", "cambiaba", "cambió", "cambiará", "cambiando",

    # ── Crecer ────────────────────────────────────────────────────────────
    "crece", "crecía", "creció", "crecerá", "creciendo",

    # ── Mejorar ───────────────────────────────────────────────────────────
    "mejora", "mejoraba", "mejoró", "mejorará", "mejorando",

    # ── Aumentar ──────────────────────────────────────────────────────────
    "aumenta", "aumentaba", "aumentó", "aumentará", "aumentando",

    # ── Disminuir ─────────────────────────────────────────────────────────
    "disminuye", "disminuía", "disminuyó", "disminuirá", "disminuyendo",

    # ── Avanzar ───────────────────────────────────────────────────────────
    "avanza", "avanzaba", "avanzó", "avanzará", "avanzando",
}

VERBOS_PASADO_1RA = {
    # ── AR primera persona ────────────────────────────────────────────────
    "hable": "hablé", "camine": "caminé", "maneje": "manejé",
    "viaje": "viajé", "trabaje": "trabajé", "estudie": "estudié",
    "compre": "compré", "saque": "saqué", "busque": "busqué",
    "toque": "toqué", "entregue": "entregué", "explique": "expliqué",
    "practique": "practiqué", "platique": "platiqué", "empece": "empecé",
    "comence": "comencé", "almorce": "almorcé", "regrese": "regresé",
    "termine": "terminé", "tome": "tomé", "cene": "cené",
    "desayune": "desayuné", "pague": "pagué", "juegue": "jugué",
    "llegue": "llegué", "hable": "hablé", "llame": "llamé",
    "baje": "bajé", "subi": "subí", "sali": "salí",
    "prepare": "preparé", "levante": "levanté", "desperte": "desperté",
    "aproveche": "aproveché", "visite": "visité", "recorre": "recorrí",
    "encontre": "encontré", "entregue": "entregué", "ayude": "ayudé",
    "cambie": "cambié", "arregle": "arreglé", "limpie": "limpié",
    "cocine": "cociné", "madrugue": "madrugué", "trabaje": "trabajé",
    "escuche": "escuché", "mire": "miré", "espere": "esperé",
    "firme": "firmé", "pase": "pasé", "note": "noté",
    "marque": "marqué", "lance": "lancé", "avance": "avancé",
    "deje": "dejé", "lleve": "llevé", "saque": "saqué",
    "cante": "canté", "baile": "bailé", "dibuje": "dibujé",
    "pinte": "pinté", "corte": "corté", "doble": "doblé",
    "gane": "gané", "perdi": "perdí", "guarde": "guardé",
    "senale": "señalé", "apunte": "apunté", "calcule": "calculé",
    "revise": "revisé", "verifique": "verifiqué", "instale": "instalé",
    "configure": "configuré", "actualice": "actualicé",

    # ── ER/IR primera persona ─────────────────────────────────────────────
    "subi": "subí", "sali": "salí", "comi": "comí",
    "bebi": "bebí", "lei": "leí", "escribi": "escribí",
    "corri": "corrí", "vivi": "viví", "dormi": "dormí",
    "senti": "sentí", "pedi": "pedí", "recibi": "recibí",
    "abri": "abrí", "subi": "subí", "conduci": "conduje",
    "produci": "produje", "traduci": "traduje", "introduci": "introduje",
    "surgi": "surgí", "asisti": "asistí", "parti": "partí",
    "sali": "salí", "sufri": "sufrí", "decidi": "decidí",
    "defini": "definí", "permiti": "permití", "admiti": "admití",
    "omiti": "omití", "emiti": "emití", "repeti": "repetí",
    "consenti": "consentí", "preveni": "prevení", "conveni": "convení",

    # ── AR tercera persona ────────────────────────────────────────────────
    "hablo": "habló", "camino": "caminó", "manejo": "manejó",
    "viajo": "viajó", "trabajo": "trabajó", "estudio": "estudió",
    "compro": "compró", "busco": "buscó", "toco": "tocó",
    "entrego": "entregó", "explico": "explicó", "practico": "practicó",
    "platico": "platicó", "empezo": "empezó", "comenzo": "comenzó",
    "almorzo": "almorzó", "regreso": "regresó", "termino": "terminó",
    "tomo": "tomó", "ceno": "cenó", "desayuno": "desayunó",
    "pago": "pagó", "jugo": "jugó", "llego": "llegó",
    "llamo": "llamó", "bajo": "bajó", "subio": "subió",
    "salio": "salió", "preparo": "preparó", "levanto": "levantó",
    "desperto": "despertó", "aprovecho": "aprovechó", "visito": "visitó",
    "recorrio": "recorrió", "encontro": "encontró", "ayudo": "ayudó",
    "cambio": "cambió", "arreglo": "arregló", "limpio": "limpió",
    "nado": "nadó", "inicio": "inició",
    "cocino": "cocinó", "madrago": "madrogó", "escucho": "escuchó",
    "miro": "miró", "espero": "esperó", "firmo": "firmó",
    "paso": "pasó", "noto": "notó", "marco": "marcó",
    "lanzo": "lanzó", "avanzo": "avanzó", "dejo": "dejó",
    "llevo": "llevó", "saco": "sacó", "canto": "cantó",
    "bailo": "bailó", "dibujo": "dibujó", "pinto": "pintó",
    "corto": "cortó", "doblo": "dobló", "gano": "ganó",
    "perdio": "perdió", "guardo": "guardó", "señalo": "señaló",
    "apunto": "apuntó", "calculo": "calculó", "reviso": "revisó",
    "verifico": "verificó", "instalo": "instaló", "configuro": "configuró",
    "actualizo": "actualizó", "informo": "informó", "presento": "presentó",
    "comento": "comentó", "menciono": "mencionó", "indico": "indicó",
    "anuncio": "anunció", "confirmo": "confirmó", "nego": "negó",
    "acepto": "aceptó", "rechazo": "rechazó", "aprobo": "aprobó",
    "decidio": "decidió", "eligio": "eligió", "pidio": "pidió",
    "recibio": "recibió", "envio": "envió", "volvio": "volvió",
    "entro": "entró", "abrio": "abrió", "cerro": "cerró",
    "caso": "casó", "trato": "trató", "genero": "generó",
    "proceso": "procesó", "mostro": "mostró", "pregunto": "preguntó",
    "contesto": "contestó", "respondio": "respondió", "conto": "contó",
    "describio": "describió", "calculo": "calculó", "probo": "probó",
    "gusto": "gustó", "transporto": "transportó", "disgusto": "disgustó",
    "agrado": "agradó", "molesto": "molestó", "sorprendio": "sorprendió",
    "asombro": "asombró", "impresiono": "impresionó", "encanto": "encantó",
    "fascino": "fascinó", "intereso": "interesó", "preocupo": "preocupó",
    "asusto": "asustó", "aburrio": "aburrió", "canso": "cansó",
    "emociono": "emocionó", "receto": "recetó", "opero": "operó",
    "diagnostico": "diagnosticó", "examino": "examinó", "cobro": "cobró",
    "organizo": "organizó", "planifico": "planificó", "ejecuto": "ejecutó",
    "desarrollo": "desarrolló", "implemento": "implementó", "creo": "creó",
    "diseño": "diseñó", "publico": "publicó", "lanzo": "lanzó",
    "vendio": "vendió", "compro": "compró", "negocio": "negoció",
    "acordo": "acordó", "pacto": "pactó", "firmo": "firmó",
    "aprobo": "aprobó", "rechazo": "rechazó", "voto": "votó",
    "eligio": "eligió", "nomino": "nominó", "designo": "designó",
    "invito": "invitó", "asistio": "asistió", "participo": "participó",
    "colaboro": "colaboró", "apoyo": "apoyó", "financio": "financió",
    "invirtio": "invirtió", "gano": "ganó", "perdio": "perdió",
    "empatо": "empató", "marco": "marcó", "anoto": "anotó",
    "fallo": "falló", "erro": "erró", "acerto": "acertó",
    "mejoro": "mejoró", "empeoro": "empeoró", "aumento": "aumentó",
    "disminuyo": "disminuyó", "subio": "subió", "bajo": "bajó",
    "olvido": "olvidó", "marco": "marcó", "noto": "notó",
    "peso": "pesó", "cobro": "cobró", "monto": "montó",
    "fije": "fijé", "respeto": "respetó", "noto": "notó",
    "presto": "prestó", "engancho": "enganchó", "logro": "logró",
    "supero": "superó", "completo": "completó", "alcanzo": "alcanzó",
    "obtuvo": "obtuvo", "consiguio": "consiguió", "resolvio": "resolvió",
    "fixe": "fijé", "pregunte": "pregunté", "quede": "quedé",
    "logre": "logré", "logré": "logré", "enamoro": "enamoró", "apasiono": "apasionó",
    "enseño": "enseñó", "dedique": "dediqué", "dedico": "dedicó",
    "analizo": "analizó", "resumio": "resumió",
    "concluyo": "concluyó", "determino": "determinó", "establacio": "estableció",
    "radico": "radicó",
    "convoco": "convocó", "fabrico": "fabricó", "critico": "criticó",
    "clasifico": "clasificó", "unifico": "unificó",
    "identifico": "identificó", "justifico": "justificó",
    "adopto": "adoptó", "adapto": "adaptó", "reformo": "reformó",
    "promovio": "promovió", "retiro": "retiró",
}

VERBOS_FUTURO = {
    # ── AR ────────────────────────────────────────────────────────────────
    "hablaran": "hablarán", "caminaran": "caminarán", "manejaran": "manejarán",
    "viajaran": "viajarán", "trabajaran": "trabajarán", "estudiaran": "estudiarán",
    "compraran": "comprarán", "buscaran": "buscarán", "tocaran": "tocarán",
    "entregaran": "entregarán", "explicaran": "explicarán", "llegaran": "llegarán",
    "llamaran": "llamarán", "bajaran": "bajarán", "prepararan": "prepararán",
    "levantaran": "levantarán", "aprovecharan": "aprovecharán",
    "visitaran": "visitarán", "encontraran": "encontrarán",
    "ayudaran": "ayudarán", "cambiaran": "cambiarán", "arreglaran": "arreglarán",
    "limpiaran": "limpiarán", "cocinaran": "cocinarán", "escucharan": "escucharán",
    "miraran": "mirarán", "esperaran": "esperarán", "firmaran": "firmarán",
    "pasaran": "pasarán", "marcaran": "marcarán", "lanzaran": "lanzarán",
    "avanzaran": "avanzarán", "dejaran": "dejarán", "llevaran": "llevarán",
    "sacaran": "sacarán", "cantaran": "cantarán", "bailaran": "bailarán",
    "ganaran": "ganarán", "guardaran": "guardarán", "señalaran": "señalarán",
    "calcularan": "calcularán", "revisaran": "revisarán", "instalaran": "instalarán",
    "configuraran": "configurarán", "actualizaran": "actualizarán",
    "informaran": "informarán", "presentaran": "presentarán",
    "comentaran": "comentarán", "anunciaran": "anunciarán",
    "confirmaran": "confirmarán", "aceptaran": "aceptarán",
    "rechazaran": "rechazarán", "aprobaran": "aprobarán",
    "organizaran": "organizarán", "planearan": "planearán",
    "desarrollaran": "desarrollarán", "publicaran": "publicarán",
    "negociaran": "negociarán", "acordaran": "acordarán",
    "votaran": "votarán", "invitaran": "invitarán",
    "participaran": "participarán", "colaboraran": "colaborarán",
    "apoyaran": "apoyarán", "financiaran": "financiarán",
    "mejoraran": "mejorarán", "aumentaran": "aumentarán",
    "generaran": "generarán",
    "usaran": "usarán", "necesitaran": "necesitarán",
    "tomaran": "tomarán", "dejaran": "dejarán",
    "compraran": "comprarán", "vendaran": "venderán",
    "contaran": "contarán",

    # ── ER/IR ─────────────────────────────────────────────────────────────
    "comeran": "comerán", "beberan": "beberán", "correran": "correrán",
    "leeran": "leerán", "vendran": "vendrán", "tendran": "tendrán",
    "podran": "podrán", "querran": "querrán", "saldran": "saldrán",
    "haran": "harán", "seran": "serán", "estaran": "estarán",
    "iran": "irán", "diran": "dirán", "sabran": "sabrán",
    "trairan": "traerán", "veran": "verán", "pondran": "pondrán",
    "valdran": "valdrán", "cabran": "cabrán", "habran": "habrán",
    "viviран": "vivirán", "subiран": "subirán", "saliран": "salirán",
    "viviran": "vivirán", "subiran": "subirán", "saliran": "salirán",
    "escribiran": "escribirán", "recibiран": "recibirán",
    "recibiран": "recibirán", "recibiran": "recibirán",
    "abriран": "abrirán", "abriran": "abrirán",
    "sufriran": "sufrirán", "decidiран": "decidirán",
    "decidiран": "decidirán", "decidiran": "decidirán",
    "asistiran": "asistirán", "partiran": "partirán",
    "produciран": "producirán", "produciran": "producirán",
    "introduciран": "introducirán", "introduciran": "introducirán",
    "permitiran": "permitirán", "admitiран": "admitirán",
    "admitiran": "admitirán", "repetiран": "repetirán",
    "repetiran": "repetirán", "consentiран": "consentirán",
    "consentiran": "consentirán",

    # ── Primera persona singular ───────────────────────────────────────────
    "hablare": "hablaré", "caminare": "caminaré", "manejare": "manejaré",
    "viajare": "viajaré", "trabajare": "trabajaré", "estudiare": "estudiaré",
    "comprare": "compraré", "buscare": "buscaré", "llegare": "llegaré",
    "llamare": "llamaré", "preparare": "prepararé", "visitare": "visitaré",
    "encontrare": "encontraré", "ayudare": "ayudaré", "cambiare": "cambiaré",
    "escuchare": "escucharé", "esperare": "esperaré", "pasare": "pasaré",
    "ganare": "ganaré", "guardare": "guardaré", "revisare": "revisaré",
    "instalare": "instalaré", "informare": "informaré", "presentare": "presentaré",
    "aceptare": "aceptaré", "organizare": "organizaré", "desarrollare": "desarrollaré",
    "publicare": "publicaré", "mejorare": "mejoraré", "usare": "usaré",
    "terminare": "terminaré", "empezare": "empezaré", "continuare": "continuaré",
    "regresare": "regresaré", "olvidare": "olvidaré", "recordare": "recordaré",
    "cuidare": "cuidaré", "intentare": "intentaré", "lograre": "lograré",
    "volvere": "volveré", "comeré": "comeré", "vivire": "viviré",
    "saldré": "saldré", "saldre": "saldré", "habre": "habré",
    "tendre": "tendré", "podre": "podré", "querre": "querré",
    "sabre": "sabré", "vendre": "vendré", "pondre": "pondré",
    "dire": "diré", "ire": "iré", "vere": "veré",
    "hare": "haré", "sere": "seré", "estare": "estaré",
    "traere": "traeré", "cabre": "cabré", "valdre": "valdré",
    "funcionara": "funcionará", "mejorara": "mejorará",
    "cambiara": "cambiará", "crecera": "crecerá",
    "avanzara": "avanzará", "desarrollara": "desarrollará",
    "dara": "dará", "dare": "daré",
    "sobrara": "sobrará", "alcanzara": "alcanzará",
    "quedara": "quedará", "faltara": "faltará",
    "pare": "paré", "deje": "dejé",
    "dejara": "dejará", "lograra": "logrará", "sorprendera": "sorprenderá",
    "destinara": "destinará", "destinaran": "destinarán",
    "asignara": "asignará", "asignaran": "asignarán",
    "implementara": "implementará", "implementaran": "implementarán",
    "promovera": "promoverá", "promoveran": "promoverán",
    "ampliara": "ampliará", "ampliaran": "ampliarán",
    "reforzara": "reforzará", "reforzaran": "reforzarán",
    "creara": "creará", "crearan": "crearán",
    "anunciara": "anunciará", "anunciaran": "anunciarán",
    "presentara": "presentará", "presentaran": "presentarán",
    "entregara": "entregará", "entregaran": "entregarán",
    "iniciara": "iniciará", "iniciaran": "iniciarán",
}

PREPOSICIONES_LUGAR = {
    "en", "sobre", "bajo", "dentro", "fuera", "encima",
    "debajo", "junto", "cerca", "lejos", "delante", "detrás",
    "entre", "contra", "hacia", "desde"
}

CLITICOS = {"lo", "la", "le", "se", "me", "te", "nos", "les"}

ADJETIVOS_COMUNES = {
    # ── Estado físico ─────────────────────────────────────────────────────
    "roto", "rota", "rotos", "rotas",
    "dañado", "dañada", "dañados", "dañadas",
    "destruido", "destruida", "destruidos", "destruidas",
    "estropeado", "estropeada", "descompuesto", "descompuesta",
    "arreglado", "arreglada", "reparado", "reparada",
    "nuevo", "nueva", "nuevos", "nuevas",
    "viejo", "vieja", "viejos", "viejas",
    "usado", "usada", "desgastado", "desgastada",

    # ── Limpieza ──────────────────────────────────────────────────────────
    "limpio", "limpia", "limpios", "limpias",
    "sucio", "sucia", "sucios", "sucias",
    "ordenado", "ordenada", "desordenado", "desordenada",

    # ── Disponibilidad ────────────────────────────────────────────────────
    "disponible", "disponibles", "ocupado", "ocupada", "ocupados", "ocupadas",
    "libre", "libres", "lleno", "llena", "llenos", "llenas",
    "vacío", "vacía", "vacíos", "vacías", "vacio", "vacia",
    "abierto", "abierta", "abiertos", "abiertas",
    "cerrado", "cerrada", "cerrados", "cerradas",

    # ── Temperatura ───────────────────────────────────────────────────────
    "frío", "fría", "fríos", "frías", "frio", "fria",
    "caliente", "calientes", "tibio", "tibia",
    "templado", "templada", "helado", "helada",

    # ── Estado emocional/mental ───────────────────────────────────────────
    "listo", "lista", "listos", "listas",
    "cansado", "cansada", "cansados", "cansadas",
    "aburrido", "aburrida", "aburridos", "aburridas",
    "emocionado", "emocionada", "emocionados", "emocionadas",
    "preocupado", "preocupada", "preocupados", "preocupadas",
    "tranquilo", "tranquila", "tranquilos", "tranquilas",
    "nervioso", "nerviosa", "nerviosos", "nerviosas",
    "feliz", "felices", "triste", "tristes",
    "contento", "contenta", "contentos", "contentas",
    "enojado", "enojada", "enojados", "enojadas",
    "asustado", "asustada", "asustados", "asustadas",
    "sorprendido", "sorprendida", "sorprendidos", "sorprendidas",
    "confundido", "confundida", "confundidos", "confundidas",
    "solo", "sola", "solos", "solas",
    "acompañado", "acompañada",

    # ── Posición/lugar ────────────────────────────────────────────────────
    "parado", "parada", "parados", "paradas",
    "sentado", "sentada", "sentados", "sentadas",
    "acostado", "acostada", "acostados", "acostadas",
    "perdido", "perdida", "perdidos", "perdidas",
    "escondido", "escondida", "escondidos", "escondidas",

    # ── Tamaño/forma ──────────────────────────────────────────────────────
    "grande", "grandes", "pequeño", "pequeña", "pequeños", "pequeñas",
    "alto", "alta", "altos", "altas",
    "bajo", "baja", "bajos", "bajas",
    "gordo", "gorda", "gordos", "gordas",
    "delgado", "delgada", "delgados", "delgadas",
    "corto", "corta", "cortos", "cortas",
    "largo", "larga", "largos", "largas",

    # ── Calidad ───────────────────────────────────────────────────────────
    "bueno", "buena", "buenos", "buenas",
    "malo", "mala", "malos", "malas",
    "mejor", "peor", "igual", "iguales",
    "diferente", "diferentes", "similar", "similares",
    "correcto", "correcta", "incorrectos", "incorrecta",
    "exacto", "exacta", "exactos", "exactas",

    # ── Precio ────────────────────────────────────────────────────────────
    "caro", "cara", "caros", "caras",
    "barato", "barata", "baratos", "baratas",
    "costoso", "costosa", "económico", "económica",

    # ── Velocidad ─────────────────────────────────────────────────────────
    "rápido", "rápida", "rápidos", "rápidas",
    "lento", "lenta", "lentos", "lentas",

    # ── Facilidad ─────────────────────────────────────────────────────────
    "fácil", "fáciles", "difícil", "difíciles",
    "sencillo", "sencilla", "complicado", "complicada",
    "posible", "posibles", "imposible", "imposibles",

    # ── Seguridad ─────────────────────────────────────────────────────────
    "seguro", "segura", "seguros", "seguras",
    "peligroso", "peligrosa", "peligrosos", "peligrosas",

    # ── Salud ─────────────────────────────────────────────────────────────
    "sano", "sana", "sanos", "sanas",
    "enfermo", "enferma", "enfermos", "enfermas",
    "herido", "herida", "heridos", "heridas",
    "curado", "curada", "curados", "curadas",

    # ── Adverbios que siguen a está/esté ──────────────────────────────────
    "bien", "mal", "aquí", "ahí", "allí",
    "adentro", "afuera", "arriba", "abajo",
    "cerca", "lejos", "listo",

    # ── Estado de preparación/disposición ─────────────────────────────────
    "preparado", "preparada", "preparados", "preparadas",
    "dispuesto", "dispuesta", "dispuestos", "dispuestas",

    # ── Participios con rol adjetival ──────────────────────────────────────
    "llamado", "llamada", "llamados", "llamadas",
    "destinado", "destinada", "obligado", "obligada",
    "encargado", "encargada", "autorizado", "autorizada",
}

INTENSIFICADORES = {"más", "mas", "muy", "tan", "bastante", "poco", "bien", "mal"}

SALUDOS_COMA = [
    r'^(Hola)(?![,])',
    r'^(Buenos días)(?![,])',
    r'^(Buenas tardes)(?![,])',
    r'^(Buenas noches)(?![,])',
    r'^(Buen día)(?![,])',
    r'^(Estimado)(?![,])',
    r'^(Querido)(?![,])',
]

DEQUEISMO = [
    r'me parece de que', r'creo de que', r'pienso de que',
    r'opino de que', r'considero de que', r'siento de que',
    r'espero de que', r'imagino de que', r'supongo de que',
    r'insisto de que',
]

CONCORDANCIA = [
    (" yo tiene ", " yo tengo "),
    (" tu no ", " tú no "),
    (" en base a ", " con base en "),
    (" de acuerdo a ", " de acuerdo con "),
]

VERBOS_PREGUNTA = {
    "preguntó", "pregunta", "pregunté", "dime", "dinos",
    "explica", "explicó", "sabía", "sabe", "sabes",
    "ignora", "ignoraba", "desconoce", "averigua", "averiguó",
}

HOMOFONOS_VERBALES = [
    (r'\b(él|ella|usted|Juan|María|Pedro|Ana|Carlos|Luis|yo|tú)\b(\s+\w+)?\s+\btubo\b',
     lambda m: m.group(1) + (m.group(2) or '') + ' tuvo'),
    (r'\bhalla\b (mucha|mucho|más|bastante|suficiente|poca|poco|\w+ado\b|\w+ido\b)',
     lambda m: 'haya ' + m.group(1)),
    (r'\bque halla\b', 'que haya'),
    (r'\bvalla\b (a ver|al|a la|a buscar|a hacer|a comprar|a comer|a dormir|por|hacia|\w+ar\b|\w+er\b|\w+ir\b)',
     lambda m: 'vaya ' + m.group(1)),
]

HOMOFONOS_SIMPLES = {
    r'\bvien\b': 'bien',
    r'\baber\b': 'haber',
    r'\balla\b': 'allá',
    r'\bay\b(?! que)': 'hay',
    r'\bbaso\b': 'vaso',
    r'\bojala\b': 'ojalá',
    r'\bah\b(?= ido| estado| sido| tenido| podido| querido| dicho| hecho)': 'ha',
}


VERBOS_DESEO_PASADO = {
    "esperaba", "queria", "quería", "pedia", "pedía", "necesitaba",
    "requeria", "requería", "deseaba", "preferia", "prefería",
    "rogaba", "suplicaba", "ordenaba", "mandaba", "exigia", "exigía",
    "pidio", "pidió", "ordeno", "ordenó", "rogo", "rogó",
    "quiso", "deseo", "deseó",
}

# Verbos de anuncio: introducen futuro reportado ("dijo que haría") → no subjuntivo
VERBOS_ANUNCIO = {
    "anunció", "anuncio", "dijo", "informó", "informo", "confirmó",
    "confirmo", "declaró", "declaro", "comunicó", "comunico",
    "adelantó", "adelanto", "reveló", "revelo", "señaló", "señalo",
    "indicó", "indico", "aseguró", "aseguro", "sostuvo", "afirmó", "afirmo",
}

_SUBJUNTIVO_ANTE_QUE = {"de", "para", "sin", "antes", "a", "con"}
_CORTE_CLAUSULA = {
    "y", "o", "pero", "sino", "porque", "ya", "así", "entonces",
    "pues", "además", "mientras", "aunque",
}


def _es_subjuntivo_clausula(palabras: list, j: int) -> bool:
    """True si la palabra en posición j está en cláusula subjuntiva.

    Busca hacia atrás hasta 9 posiciones un 'que' precedido por
    preposición subordinante o verbo de deseo/expectativa.
    Devuelve False si el 'que' es introducido por verbo de anuncio
    (en ese caso el verbo siguiente es futuro reportado, no subjuntivo).
    """
    for k in range(j - 1, max(j - 10, -1), -1):
        w = re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabras[k]).lower()
        if w in _CORTE_CLAUSULA:
            break
        if w == "que" and k > 0:
            ante_que = re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabras[k - 1]).lower()
            # Verbo de anuncio → futuro reportado → no bloquear tilde
            if ante_que in VERBOS_ANUNCIO:
                return False
            if ante_que in _SUBJUNTIVO_ANTE_QUE or ante_que in VERBOS_DESEO_PASADO:
                return True
            break
    return False


def _limpiar_nucleo(palabra: str) -> str:
    return re.sub(r'^["\'\¿¡\(\[]+|["\'\?!,\.;:\)\]]+$', '', palabra).lower()


def _tildar(original: str, sin_tilde: str, con_tilde: str) -> str:
    """Solo agrega tilde. NUNCA usa capitalize() ni title()."""
    if original == sin_tilde:
        return con_tilde
    if original == sin_tilde.upper():
        return con_tilde.upper()
    if original[0].isupper() and original[1:].islower():
        return con_tilde[0].upper() + con_tilde[1:]
    return original


def _aplicar_tildes_ngram(text: str) -> str:
    parrafos = text.split('\n')
    return '\n'.join(_procesar_parrafo_ngram(p) for p in parrafos)


def _procesar_parrafo_ngram(text: str) -> str:
    palabras = text.split()
    cambios = []

    for i, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)

        sig_raw = palabras[i + 1] if i + 1 < len(palabras) else ""
        sig = re.sub(r'[^a-záéíóúüñ]', '', sig_raw.lower())
        dos_sig_raw = palabras[i + 2] if i + 2 < len(palabras) else ""
        dos_sig = re.sub(r'[^a-záéíóúüñ]', '', dos_sig_raw.lower())
        tres_sig_raw = palabras[i + 3] if i + 3 < len(palabras) else ""
        tres_sig = re.sub(r'[^a-záéíóúüñ]', '', tres_sig_raw.lower())

        match_pref = re.match(r'^(["\'\¿¡\(\[]*)', palabra)
        prefijo = match_pref.group(1) if match_pref else ""
        match_suf = re.search(r'(["\'\?!,\.;:\)\]]+)$', palabra)
        sufijo = match_suf.group(1) if match_suf else ""
        nucleo_orig = palabra[
            len(prefijo): len(palabra) - len(sufijo) if sufijo else len(palabra)
        ]

        if nucleo == "mas":
            if sig in MAS_BLOQUEADORES or palabra.endswith(","):
                continue
            # Si anterior es infinitivo → "esforzarme más", "trabajar más"
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior_nucleo = _limpiar_nucleo(anterior_raw)
            es_infinitivo_anterior = bool(re.search(r'\w+(?:ar|er|ir|rme|rte|rse|rnos)$', anterior_nucleo))
            if es_infinitivo_anterior:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            # Si anterior es verbo conjugado → "me guste más", "lo que más"
            es_verbo_anterior = bool(re.search(r'\w+(?:e|a|o|en|an|on)$', anterior_nucleo)) and len(anterior_nucleo) > 3
            if es_verbo_anterior and anterior_nucleo not in MAS_BLOQUEADORES:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            if sig == "de" and (dos_sig.isdigit() or dos_sig in MAS_SUSTANTIVOS_CANTIDAD):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))
                continue
            if sig not in MAS_ADJETIVOS_GRADO and \
               sig not in MAS_SUSTANTIVOS_CANTIDAD and \
               not sig.isdigit():
                continue
            cambios.append((i, prefijo + _tildar(nucleo_orig, "mas", "más") + sufijo))

        elif nucleo == "el":
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior_nucleo = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            if sig in CLITICOS and (
                dos_sig in VERBOS_3RA or dos_sig in VERBOS_2DA or
                tres_sig in VERBOS_3RA or tres_sig in VERBOS_2DA
            ):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig == "se" and dos_sig in VERBOS_3RA | VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in {"no", "ni", "nunca", "jamás"} and dos_sig in VERBOS_3RA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            ADVERBIOS_PRONOMBRE = {"también", "tampoco", "siempre", "nunca",
                                   "ya", "todavía", "aún", "solo", "sólo"}
            if sig in ADVERBIOS_PRONOMBRE:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if anterior_nucleo == "a" and (not sig or sufijo or sig[0].isupper()):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if anterior_nucleo == "a" and sig in {"quien", "quién", "que", "cual"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            if sig in {"quien", "quién"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            # "el señaló/analizó/..." — verbo pasado ya tildado por paso 5.5
            if sig in set(VERBOS_PASADO_1RA.values()):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            # "según él la IA / según él explicó" — preposición personal
            _PREP_PRONOMBRE = {"según", "segun"}
            if anterior_nucleo in _PREP_PRONOMBRE and (
                sig in VERBOS_3RA or
                sig in set(VERBOS_PASADO_1RA.values()) or
                sig in {"la", "los", "las", "un", "una"}
            ):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "el", "él") + sufijo))
                continue
            continue

        elif nucleo in ("esta", "este"):
            sin_t = nucleo
            con_t = "está" if nucleo == "esta" else "esté"
            es_gerundio = bool(re.search(r'\w+(?:ando|iendo)$', sig))
            if sig in PREPOSICIONES_LUGAR or \
               sig in ADJETIVOS_COMUNES or \
               sig in INTENSIFICADORES or \
               sig in VERBOS_3RA | VERBOS_2DA or \
               es_gerundio:
                cambios.append((i, prefijo + _tildar(nucleo_orig, sin_t, con_t) + sufijo))

        elif nucleo == "tu":
            # "tú que", "tú quien" → siempre pronombre
            if sig in {"que", "quien", "quién", "cual", "cuál"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))
                continue
            if "?" in text or "¿" in text:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))
                continue
            if sig in VERBOS_2DA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "tu", "tú") + sufijo))

        elif nucleo == "si":
            if i == 0 or palabra[0].isupper():
                continue

            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            CONJUNCIONES = {"pero", "aunque", "y", "o", "ni", "sino",
               "porque", "como", "mas", "se", "sé", "que",
               "pregunte", "pregunté", "pregunto", "preguntó"}
            if anterior in CONJUNCIONES:
                # Excepción: "respondió que sí", "dijo que sí"
                VERBOS_RESPUESTA = {"respondio", "respondió", "dijo", "contesto",
                                   "contestó", "afirmo", "afirmó", "confirmo", "confirmó"}
                anterior_a_anterior = _limpiar_nucleo(palabras[i-2]) if i > 1 else ""
                if anterior == "que" and anterior_a_anterior in VERBOS_RESPUESTA:
                    cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                    continue
                continue

            AFIRMACION_CONTEXTO = VERBOS_3RA | VERBOS_2DA | {"vaya", "viene", "claro"}
            if sig in AFIRMACION_CONTEXTO:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

            if anterior in {"para", "por", "en", "de", "a"} and sig in CLITICOS | {"mismo", "misma"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

            AFIRMACION_DIRECTA = {"yo", "claro", "pues", "bueno", "obvio"}
            if anterior in AFIRMACION_DIRECTA:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

            if sig in CLITICOS:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "si", "sí") + sufijo))
                continue

        elif nucleo == "se":
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())

            if anterior in {"no", "nunca", "jamás", "si", "sí", "yo", "lo"} and sig in {"si", "sí", "que", ""}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            if bool(re.search(r'\w+(?:ar|er|ir)$', sig)):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            # "solo sé", "yo sé" → verbo saber
            if anterior in {"solo", "sólo", "yo", "tampoco", "también"}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

            if anterior in {"ahora", "solo", "sólo", "tampoco", "también",
                            "no", "nunca", "jamás", "si", "sí", "yo", "lo"} and \
                sig in {"que", "si", "sí", ""}:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "se", "sé") + sufijo))
                continue

        elif nucleo == "cual":
            tiene_interrogacion = "?" in text or "¿" in text
            tokens_lista = [re.sub(r'[^a-záéíóúüñ]', '', p.lower()) for p in palabras]
            ventana = tokens_lista[max(0, i-5):i]
            tiene_verbo_pregunta = any(v in VERBOS_PREGUNTA for v in ventana)
            if tiene_interrogacion or tiene_verbo_pregunta:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "cual", "cuál") + sufijo))

        elif nucleo == "aun":
            if (sig in VERBOS_3RA or sig in VERBOS_2DA or
                    sig in VERBOS_TIEMPO or sig in {"no", "ni", "nunca"}):
                cambios.append((i, prefijo + _tildar(nucleo_orig, "aun", "aún") + sufijo))
        
        elif nucleo == "como":
            # "cómo" interrogativo indirecto — precedido de verbo de pregunta
            anterior_raw = palabras[i - 1] if i > 0 else ""
            anterior = re.sub(r'[^a-záéíóúüñ]', '', anterior_raw.lower())
            VERBOS_PREGUNTA_INDIRECTA = {
                "pregunto", "preguntó", "pregunta", "pregunté",
                "dime", "dinos", "explica", "explicó", "saber",
                "sabes", "sabe", "sabía", "ignora", "ignoraba",
                "cuenta", "contó", "describe", "describió",
                "averigua", "averiguó", "me", "te", "le", "nos"
            }
            if anterior in VERBOS_PREGUNTA_INDIRECTA or "?" in text or "¿" in text:
                cambios.append((i, prefijo + _tildar(nucleo_orig, "como", "cómo") + sufijo))

    resultado = palabras[:]
    for idx, nueva in cambios:
        resultado[idx] = nueva

    return " ".join(resultado)


def _proteger_subjuntivo(text: str) -> str:
    subjuntivos = [
        "realice", "realices", "realicen", "haga", "hagas", "hagan",
        "sea", "seas", "sean", "esté", "estés", "estén",
        "tenga", "tengas", "tengan", "pueda", "puedas", "puedan",
        "venga", "vengas", "vengan",
    ]
    for verbo in subjuntivos:
        text = re.sub(
            rf'\bque\b ({verbo})\b',
            lambda m: f'que __SUBJ_{m.group(1)}__',
            text, flags=re.IGNORECASE
        )
    return text


def _restaurar_subjuntivo(text: str) -> str:
    return re.sub(r'__SUBJ_(\w+)__', r'\1', text)


def correct_grammar(text: str) -> str:

    # 1. Homófonos simples PRIMERO — minúscula estricta
    for patron, correcto in HOMOFONOS_SIMPLES.items():
        def _reemplazar_casing(m, correcto=correcto):
            original = m.group(0)
            if original.isupper():
                return correcto.upper()
            return correcto.lower()
        text = re.sub(patron, _reemplazar_casing, text, flags=re.IGNORECASE)

    # 2. Homófonos verbales
    for patron, reemplazo in HOMOFONOS_VERBALES:
        if callable(reemplazo):
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)
        else:
            text = re.sub(patron, reemplazo, text, flags=re.IGNORECASE)

    # 3. Proteger subjuntivos
    text = _proteger_subjuntivo(text)

    # 4. Coma después de saludo inicial
    for patron in SALUDOS_COMA:
        text = re.sub(patron, lambda m: m.group(1) + ',', text)

    # 5. Coma antes de conjunciones adversativas
    text = re.sub(
        r'(?<![,]) \b(pero|aunque|sino)\b',
        lambda m: ', ' + m.group(1),
        text
    )

    # 5.1 Coma ante "quien" en cláusulas explicativas (relativo no restrictivo)
    _BLOQ_QUIEN = {"a", "para", "con", "de", "por", "sin", "ante", "sobre",
                   "tras", "se", "sé", "sabe", "sabes", "no", "es", "era",
                   "que", "lo", "al", "del", "ni", "hay"}
    def _fix_quien_comma(m):
        return m.group(0) if m.group(1).lower() in _BLOQ_QUIEN else m.group(1) + ', ' + m.group(2)
    text = re.sub(r'([^\s,]+) (quien)\b', _fix_quien_comma, text, flags=re.IGNORECASE)

    # 5.2 Comas alrededor de "por ejemplo" en el interior de una oración
    text = re.sub(
        r'(?<=[a-záéíóúüñA-ZÁÉÍÓÚÜÑ]) (por ejemplo) ',
        ', por ejemplo, ',
        text, flags=re.IGNORECASE
    )

    # 5.5 Verbos en pasado sin tilde
    BLOQUEADORES_SUBJ = {"para", "si", "aunque",
                         "ojalá", "el", "un", "la", "una", "mi", "tu", "su", "antes"}

    AMBIGUOS = {"trabajo", "estudio", "caso", "trato", "cambio",
            "inicio", "termino", "aumento", "bajo",
            "peso", "cobro", "monto", "noto", "camino", "regreso",
            "viaje", "avance", "seria", "proceso",
            "desarrollo", "ingreso", "progreso", "registro", "acceso",
            "apoyo", "empleo", "ensayo", "relevo", "relato", "cargo",
            "mando", "manejo", "arreglo", "ajuste", "rechazo", "retraso",
            "reemplazo", "rescate", "repaso", "reflejo", "remedio",
            "recurso", "riesgo", "resumen", "turno", "paso",
            "anuncio", "acuerdo", "intento", "aumento", "decreto",
            "impacto", "resultado", "efecto",
            "negocio",  # negociar (pasado) vs sustantivo "negocio"
            "indico",  # indicar (pasado) vs adjetivo geográfico "índico"
            "critico",  # criticar (pasado) vs adjetivo/sustantivo "crítico"
            "diagnostico",  # diagnosticar (pasado) vs sustantivo "diagnóstico"
            "diseño",  # diseñar (pasado) vs sustantivo "diseño"
            }

    # Formas esdrújulas correctas para palabras en AMBIGUOS cuando son sustantivos/adjetivos
    _FORMAS_ESDRUJULO = {
        "diagnostico": "diagnóstico",
        "critico": "crítico",
        "termino": "término",
    }

    VERBOS_PRESENTE_1RA = {"espero", "busco", "necesito", "quiero",
                       "deseo", "uso", "tomo", "como",
                       "bebo", "creo", "pienso", "siento", "digo",
                       "hago", "voy", "vengo", "tengo", "puedo",
                       "sé", "veo", "oigo", "pido", "sigo"}

    FORZADORES_PASADO = {"él", "ella", "usted", "ellos", "ellas", "ustedes"}

    DETERMINANTES_RELATIVOS = {"lo", "el", "la", "los", "las", "todo", 
                           "algo", "nada", "hasta", "para", "cuando"}

    def _es_futuro(palabra: str) -> bool:
        # Solo verdaderos futuros verbales: terminan en r + vocal acentuada (hablará, vendrá…)
        return bool(re.search(r'r[áéíóú][sn]?$', palabra.lower()))

    palabras = text.split()
    resultado = []
    for j, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)
        anterior = _limpiar_nucleo(palabras[j-1]) if j > 0 else ""
        anterior_orig = palabras[j-1] if j > 0 else ""
        anterior_a_que = _limpiar_nucleo(palabras[j-2]) if j > 1 else ""
        tres_antes = _limpiar_nucleo(palabras[j-3]) if j > 2 else ""
        siguiente = _limpiar_nucleo(palabras[j+1]) if j + 1 < len(palabras) else ""
        anterior_es_futuro = _es_futuro(anterior_orig) if anterior_orig else False

        # Cuando la palabra termina en puntuación de fin de oración (.?!), el siguiente
        # token pertenece a otra oración y no debe usarse como contexto gramatical
        # (RAE: el sustantivo "estudio" en "regiones de estudio. El foro" no es verbo).
        siguiente_adj = "" if re.search(r'[.?!]+$', palabra) else siguiente

        # Cláusula subjuntiva detectada por lookback → nunca tildar
        if _es_subjuntivo_clausula(palabras, j):
            resultado.append(palabra)
            continue

        # Verificar si "que" anterior es pronombre relativo
        # ej: "todo lo que pasó", "algo que ocurrió"
        que_es_relativo = (anterior == "que" and anterior_a_que in DETERMINANTES_RELATIVOS)

        # Bloqueadores efectivos — si "que" es relativo, no bloquea
        bloqueadores_efectivos = BLOQUEADORES_SUBJ - {"que"} if que_es_relativo else BLOQUEADORES_SUBJ

        # Verbos presente primera persona — lógica especial
        if nucleo in VERBOS_PRESENTE_1RA:
            # Sigue "que" → presente → no tildar
            if siguiente in {"que", "poder", "hacer", "ir", "venir", "ser", "estar"}:
                resultado.append(palabra)
                continue
            # Inicio de oración o precedido de "yo" → presente → no tildar
            if anterior in {"yo", ""} or j == 0:
                resultado.append(palabra)
                continue
            # Precedido de pronombre sujeto o sustantivo → pasado → tildar
            if anterior_orig in FORZADORES_PASADO or (
                anterior not in {"y", "o", "pero", "aunque", "sino", "que",
                                  "si", "porque", "como", "cuando", "donde"}
                and len(anterior) > 2
            ):
                if nucleo in VERBOS_PASADO_1RA:
                    corregido = VERBOS_PASADO_1RA[nucleo]
                    if palabra[0].isupper():
                        corregido = corregido[0].upper() + corregido[1:]
                    resultado.append(corregido)
                    continue
            resultado.append(palabra)
            continue

        if nucleo in VERBOS_PASADO_1RA and (
            anterior not in bloqueadores_efectivos or
            anterior_orig in FORZADORES_PASADO or
            (anterior == "el" and nucleo not in AMBIGUOS)
        ) and not anterior_es_futuro:
            _AMBIGUOS_BLOQ = {"el", "al", "un", "la", "una",
                              "mi", "tu", "su", "del", "este",
                              "ese", "aquel", "nuestro", "cada", "de",
                              "a", "por", "para", "con", "sin",
                              "costo", "costó", "habia", "había",
                              "costado", "escolar", "nuevo",
                              "duro", "mucho", "poco",
                              "incluye", "incluyen", "incluía"}
            # Adjetivos que aparecen entre determinante y sustantivo en "DET ADJ SUST":
            # solo ellos habilitan la búsqueda dos posiciones atrás (anterior_a_que).
            # Sujetos-sustantivo como "médico", "juez", "rector" no están aquí → no
            # alcanzan hasta el "el" que los precede para confundir verbo con sustantivo.
            _MODS_PREVIOS = {"buen", "gran", "mal", "bien", "mejor", "peor",
                             "primer", "último", "cierto", "cierta",
                             "propio", "propia", "mismo", "misma"}
            _SUFIJOS_ADJ = ("al", "oso", "osa", "ico", "ica", "ivo", "iva",
                            "ble", "ante", "iente", "ado", "ada", "ido", "ida")
            _ARTS_DIRECTOS = {"el", "la", "los", "las", "un", "una", "al", "del"}
            if nucleo in AMBIGUOS and siguiente == "que" and anterior not in _ARTS_DIRECTOS:
                # "SUJETO verbo que [cláusula]" → verbo pasado introduce cláusula sustantiva
                corregido = VERBOS_PASADO_1RA[nucleo]
                if palabra[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                resultado.append(corregido)
            elif (nucleo in AMBIGUOS and nucleo in _GEONOMBRES_GEOGRAFICOS
                  and siguiente != "que"
                  and anterior_orig not in FORZADORES_PASADO):
                # RAE: adjetivo geográfico (ej: "océano índico") → preservar sin tilde verbal;
                # postprocess lo capitalizará como nombre propio geográfico.
                resultado.append(palabra)
            elif nucleo in AMBIGUOS and siguiente_adj not in {
                "la", "el", "los", "las", "un", "una", "unas", "unos"
            } and (siguiente_adj != "" or anterior in _AMBIGUOS_BLOQ) and (
                anterior in _AMBIGUOS_BLOQ or
                (anterior_a_que in {"el", "al", "un", "la", "una", "mi", "tu",
                                    "su", "del", "este", "ese", "aquel",
                                    "nuestro", "cada", "de", "por", "para", "con"}
                 and (anterior in _AMBIGUOS_BLOQ or anterior in _MODS_PREVIOS)) or
                (len(siguiente_adj) >= 4 and
                 any(siguiente_adj.endswith(s) for s in _SUFIJOS_ADJ))
            ):
                # Sustantivo/adjetivo: aplicar forma esdrújula si corresponde
                if nucleo in _FORMAS_ESDRUJULO:
                    _m_suf_e = re.search(r'(["\'\?!,\.;:\)\]]+)$', palabra)
                    _suf_e = _m_suf_e.group(1) if _m_suf_e else ""
                    esdruj_form = _FORMAS_ESDRUJULO[nucleo]
                    if palabra[0].isupper():
                        esdruj_form = esdruj_form[0].upper() + esdruj_form[1:]
                    resultado.append(esdruj_form + _suf_e)
                else:
                    resultado.append(palabra)
            elif (nucleo in AMBIGUOS and
                  siguiente == "" and
                  anterior in {"y", "o", "ni", "e"} and
                  anterior_a_que not in VERBOS_PASADO_1RA):
                # Último elemento de enumeración nominal tras conjunción coordinante:
                # "investigación, innovación y desarrollo" → sustantivo, no verbo.
                resultado.append(palabra)
            else:
                # Preservar puntuación final (ej: "estudió." cuando es verbo ante punto)
                _m_suf_verbo = re.search(r'["\'\?!,\.;:\)\]]+$', palabra)
                _suf_verbo = _m_suf_verbo.group(0) if _m_suf_verbo else ""
                corregido = VERBOS_PASADO_1RA[nucleo]
                if palabra[0].isupper():
                    corregido = corregido[0].upper() + corregido[1:]
                resultado.append(corregido + _suf_verbo)
        else:
            resultado.append(palabra)
    text = " ".join(resultado)

    # 5.6 Verbos en futuro sin tilde
    palabras = text.split()
    resultado = []
    for k, palabra in enumerate(palabras):
        nucleo = _limpiar_nucleo(palabra)
        # Cláusula subjuntiva → no tildar como futuro
        if _es_subjuntivo_clausula(palabras, k):
            resultado.append(palabra)
            continue
        if nucleo in VERBOS_FUTURO:
            corregido = VERBOS_FUTURO[nucleo]
            if palabra[0].isupper():
                corregido = corregido[0].upper() + corregido[1:]
            resultado.append(corregido)
        else:
            resultado.append(palabra)
    text = " ".join(resultado)

    # 6. Tildes por N-grams
    text = _aplicar_tildes_ngram(text)

    # 7. Dequeísmo
    for patron in DEQUEISMO:
        correcto = patron.replace(' de que', ' que')
        text = re.sub(patron, correcto, text, flags=re.IGNORECASE)

    # 8. Concordancia
    for incorrecto, correcto in CONCORDANCIA:
        text = text.replace(incorrecto, correcto)

    # 9. Sino vs si no
    text = re.sub(
        r'\bsino\b (se|me|te|le|lo|la|les|las|nos|viene|va|puede|quiere|tiene|dan|hay)',
        lambda m: 'si no ' + m.group(1),
        text
    )
    text = re.sub(
        r',\s*si no\b (?!se |me |te |le |lo |la |les |las |viene |va |puede |quiere |tiene )',
        ', sino ',
        text
    )

    # 10. Restaurar subjuntivos
    text = _restaurar_subjuntivo(text)

    return text