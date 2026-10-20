# 🐆 UNACH NormaBot - Asistente de Reglamentos y Normatividad para Alumnos

Sistema de Inteligencia Artificial desarrollado con arquitectura **Modelo - Vista - Controlador (MVC)**, diseñado específicamente para responder preguntas de estudiantes y de la comunidad universitaria sobre las **Reglas, Normas, Estatutos, Procedimientos y Formatos** de la **Universidad Autónoma de Chiapas (UNACH)**.

**100% Gratuito:** Funciona tanto en la nube (mediante la clave gratuita de Google AI Studio) como de forma **100% Offline** en tu computadora sin necesidad de pagar ni registrar tarjetas.

---

## 🏛️ Arquitectura del Sistema (MVC)

El proyecto sigue estrictamente el patrón de diseño **Modelo - Vista - Controlador**:

```
Preguntas y respuestas/
├── app.py                      # Punto de entrada / Fábrica de la aplicación Flask
├── indexer.py                  # CLI independiente para construir y probar la base de conocimiento
├── config.py                   # Configuración central (Rutas, categorías UNACH, puertos)
│
├── models/                     # --- MODELO (Lógica de Datos, Extracción, Indexación e IA) ---
│   ├── document_parser.py      # Extractor multi-formato (PDF, DOCX, XLSX, TXT, Imágenes con OCR)
│   ├── chunker.py              # Segmentador inteligente por Artículos, Capítulos y Títulos
│   ├── knowledge_base.py       # Base de conocimiento con recuperación híbrida BM25 y caché JSON
│   └── ai_engine.py            # Motor Dual: Google Gemini 2.5 Flash (Gratis) + Motor Local Offline
│
├── controllers/                # --- CONTROLADOR (Orquestación y Rutas de la API) ---
│   ├── chat_controller.py      # Control de consultas, recuperación RAG y sugerencias dinámicas
│   ├── document_controller.py  # Catálogo de documentos, estadísticas y re-indexación
│   └── settings_controller.py  # Gestión de clave Gemini, cambio de motor y prueba de conexión
│
├── views/                      # --- VISTA (Interfaz Gráfica de Usuario) ---
│   ├── templates/
│   │   └── index.html          # Interfaz web SPA moderna, responsiva y temática UNACH
│   └── static/
│       ├── css/
│       │   └── style.css       # Sistema de diseño (Paleta Azul/Oro UNACH, Glassmorphism)
│       └── js/
│           ├── api.js          # Cliente de comunicación con los Controladores
│           └── app.js          # Lógica interactiva (Chat, Voz/Micrófono, TTS, Modales)
│
├── data/                       # --- ALMACENAMIENTO DE DATOS ---
│   ├── unach_knowledge_base.json # Índice semántico precalculado (3,021 fragmentos indexados)
│   └── settings.json           # Configuración del usuario y claves persistentes
│
└── Reglamentos, Normas y Procedimientos de la UNACH/ # Documentos oficiales (51 archivos)
```

---

## 💎 ¿Cómo funciona el modo 100% Gratuito?

El sistema cuenta con dos motores a tu elección:

### Opción 1: Google Gemini 2.5 Flash (100% Gratis - Recomendado)
* Proporciona respuestas naturales, empáticas y detalladas para los estudiantes con citas precisas de artículos.
* La clave se obtiene gratis en 30 segundos en [Google AI Studio](https://aistudio.google.com/app/apikey) iniciando sesión con tu cuenta de Google.
* **No requiere tarjeta de crédito ni pagos**.
* Puedes ingresar tu clave directamente desde el modal de Configuración (⚙️) en la interfaz web.

### Opción 2: Motor Semántico Local UNACH (100% Offline - Sin Clave ni Internet)
* No requiere internet, cuentas ni claves API.
* Analiza y extrae las cláusulas, deberes, derechos y procedimientos directamente de tu computadora usando el índice BM25 y filtros de normalización en español.
* Cita el documento, página y artículo correspondiente.

---

## 🚀 Puesta en Marcha

### 1. Iniciar la Aplicación Web
En tu terminal de PowerShell, ejecuta:

```powershell
python app.py
```

Abre tu navegador (Google Chrome o Microsoft Edge) y visita:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🛠️ Herramienta CLI de Indexación (`indexer.py`)

Puedes probar y gestionar la base de datos directamente desde la terminal:

```powershell
# Ver estado del índice
python indexer.py

# Probar una búsqueda semántica de prueba
python indexer.py --search "requisitos de servicio social"
python indexer.py --search "lineamientos de inteligencia artificial"

# Forzar una re-indexación si agregas nuevos documentos a la carpeta
python indexer.py --reindex
```

---

## 🎓 Características Especiales para Alumnos UNACH

1. **Citas de Artículos Oficiales**: Cada respuesta incluye un botón desplegable `📚 Ver Fuentes y Artículos UNACH` que muestra los artículos y páginas de donde se obtuvo la respuesta.
2. **Consultas por Voz (Micrófono)**: Los alumnos pueden presionar el botón del micrófono y dictar su pregunta.
3. **Lectura en Voz Alta (TTS)**: Botón `🔊 Escuchar` para reproducir la respuesta mediante síntesis de voz en español.
4. **Preguntas Rápidas y Categorías**: Acceso directo a Servicio Social, Estatuto Integral, Lineamientos de Inteligencia Artificial (IA), Tribunal Universitario, Protocolo de Género y formatos administrativos.
5. **Explorador de Documentos**: Botón `📚 51 Documentos` en el encabezado con buscador en tiempo real para examinar cualquier reglamento.

---

*"Por la Conciencia de la Necesidad de Servir" - UNACH*
