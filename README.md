# Ortograf IA

Corrector ortográfico y gramatical inteligente con IA. Analiza textos en tiempo real, detecta errores ortográficos, evalúa gramática y redacción, y devuelve el texto corregido con sugerencias de mejora.

---

## Vista previa

> 🚧 Proyecto en desarrollo activo — `v0.1.0`

---

## Características

- Interfaz tipo chat para una experiencia natural e intuitiva
- Corrección ortográfica y gramatical en tiempo real
- Evaluación de redacción con sugerencias de mejora
- Respuesta de la IA con el texto corregido y explicación de cambios
- Diseño oscuro y moderno, responsive para móvil y desktop

---

## Tecnologías

**Frontend**
- Vite
- JavaScript Vanilla (sin frameworks)
- HTML5 semántico con metodología BEM
- CSS modular con variables y diseño responsive

**Backend** *(en desarrollo)*
- Python
- FastAPI
- Integración con IA para análisis de texto

---

## Estructura del proyecto

```
ortograf-ia/
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/          # Comunicación con el backend
│   │   ├── assets/       # Imágenes e íconos
│   │   ├── state/        # Estado de la aplicación
│   │   ├── styles/       # CSS modular
│   │   ├── utils/        # Funciones utilitarias
│   │   └── main.js       # Punto de entrada
│   └── index.html
└── backend/
    └── app/
        ├── routes/
        └── services/
```

---

## Instalación y uso

### Requisitos

- Node.js 18+
- Python 3.10+

### Frontend

```bash
cd frontend
npm install
npm run dev
```

La app estará disponible en `http://localhost:5173`

### Backend

```bash
cd backend
pip install -r requirements.txt
python app/main.py
```

El servidor estará disponible en `http://localhost:8000`

---

## Roadmap

- [x] Interfaz base del chat
- [x] Envío y visualización de mensajes
- [x] Indicador de respuesta de la IA
- [x] Separación en módulos JS
- [ ] Textarea con autoexpansión
- [ ] Backend conectado con IA real
- [ ] Corrector en tiempo real en el input
- [ ] Sistema de login
- [ ] Historial de conversaciones

---

## Versiones

| Versión | Estado | Descripción |
|---|---|---|
| `0.1.0` | ✅ Actual | Interfaz funcional, lógica base del chat |
| `0.2.0` | 🔜 | Corrector en tiempo real en el input |
| `0.3.0` | 🔜 | Backend conectado con IA real |
| `1.0.0` | 🔜 | Versión completa con login e historial |

---

## Autor

**Jonathan Hernández**  
Proyecto académico y de portafolio personal.
