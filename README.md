# Asistente Virtual para una Peluquería con IA

Aplicación de escritorio en Python y Tkinter que responde preguntas sobre los servicios de una peluquería con Gemini. El asistente lee los datos desde `servicios.txt`, los incluye como contexto en cada consulta y procesa la respuesta JSON antes de mostrarla.

## Requisitos

- Python 3.10 o superior.
- Tkinter, normalmente incluido con Python en Windows y macOS. En algunas distribuciones Linux se instala aparte (`python3-tk`).
- Una API Key de Gemini creada en [Google AI Studio](https://aistudio.google.com/app/apikey).

## Instalación y configuración

Abre una terminal en la carpeta del proyecto y ejecuta:

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Copia `.env.example` a `.env` y pega tu clave. En la carpeta entregada ya hay un `.env` local vacío que puedes editar directamente:

```dotenv
GEMINI_API_KEY=tu_clave_real
```

`.env` está en `.gitignore`. No lo compartas ni lo subas a GitHub. El repositorio incluye `.env.example` sin secretos para documentar la variable necesaria.

## Ejecución

```bash
python asistente_gui.py
```

También se puede iniciar con `python main.py`. `servicios.txt` contiene datos ficticios de ejemplo para la práctica. Sustitúyelos por los datos reales antes de usar o presentar el asistente como un negocio real.

## Cómo funciona

1. Tkinter recoge la pregunta y la muestra en la conversación.
2. Un hilo de trabajo lee `servicios.txt` y construye un prompt delimitado que explica al modelo que debe ceñirse a esos datos.
3. `python-dotenv` carga `.env`; la clave se obtiene con `os.getenv`, nunca se escribe en el código.
4. El SDK oficial `google-genai` realiza una petición a `gemini-3.5-flash-lite`, un modelo de baja latencia, solicitando JSON estructurado con el campo `respuesta`, razonamiento mínimo y respuesta breve. Cada petición tiene un límite de 12 segundos. Si el principal devuelve 503, 504 o excede ese tiempo, la aplicación intenta con `gemini-3.6-flash`.
5. `json.loads` valida el texto JSON y se extrae `respuesta` para mostrar únicamente el mensaje al usuario.
6. Una cola comunica el resultado al hilo de Tkinter, evitando que la ventana se bloquee durante la llamada de red. Un temporizador de 45 segundos recupera la interfaz incluso si una llamada externa no termina; los resultados que lleguen después de ese límite se ignoran.

El modelo ya está preentrenado. Esta práctica no lo vuelve a entrenar: le proporciona el contexto del salón en cada consulta (aprendizaje en contexto). El contenido de `servicios.txt` es la fuente de verdad para precios y horarios.

## Estructura

```text
asistente-peluqueria-ia/
├── asistente_gui.py       # Interfaz Tkinter y ejecución en segundo plano
├── gemini_client.py      # Contexto, conexión con Gemini y lectura JSON
├── main.py               # Punto de entrada alternativo
├── servicios.txt         # Datos editables del salón
├── requirements.txt      # Dependencias de Python
├── .env.example          # Plantilla pública de configuración
├── .env                  # Clave local; ignorada por Git
├── .gitignore
├── README.md
├── DEFENSA_ORAL.md       # Guía breve para explicar y defender el proyecto
└── test_gemini_client.py # Pruebas locales sin llamadas ni clave real
```

## Comprobación local

Las pruebas incluidas no necesitan API Key ni conexión a Gemini:

```bash
python -m unittest -v
```

La llamada real a Gemini requiere configurar una clave válida y conexión a Internet. La disponibilidad, cuotas y condiciones de uso dependen de Google AI Studio y del proyecto asociado a la clave.

## Publicar en GitHub

Inicializa el repositorio desde esta carpeta, revisa los archivos y confirma los cambios. Antes de publicar puedes comprobar que `.env` está ignorado con `git check-ignore .env`. Sube `.env.example`, nunca `.env` ni la clave real.


## Documentación técnica

- [SDK oficial de Google GenAI para Python](https://ai.google.dev/gemini-api/docs/libraries)
- [Respuestas estructuradas JSON](https://ai.google.dev/gemini-api/docs/structured-output)
- [Modelos Gemini disponibles](https://ai.google.dev/gemini-api/docs/models)
- [Errores de la API y reintentos](https://ai.google.dev/gemini-api/docs/api-errors)
- [Control del nivel de razonamiento](https://ai.google.dev/gemini-api/docs/thinking)
- [Gemini 3.5 Flash-Lite, optimizado para baja latencia](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)


