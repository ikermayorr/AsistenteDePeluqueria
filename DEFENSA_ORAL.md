# Guía para defender el proyecto

## Explicación de 45 segundos

«He creado una aplicación de escritorio con Tkinter para una peluquería. El usuario escribe una pregunta; Python lee `servicios.txt`, construye un contexto y lo envía a Gemini mediante el SDK oficial `google-genai`. La respuesta se solicita en JSON con una estructura definida. Después la valido con `json.loads` y muestro solamente el campo `respuesta`. La llamada se hace en otro hilo para que la ventana no se quede congelada. La clave se carga desde `.env` con `python-dotenv` y `os.getenv`, y Git la excluye mediante `.gitignore`.»

## Recorrido del código

- `asistente_gui.py`: crea ventana, conversación, entrada, botón y scroll. Al enviar, desactiva el botón e inicia un hilo. Una cola devuelve el resultado al hilo principal, que es el único que actualiza Tkinter.
- `gemini_client.py`: `cargar_servicios` lee UTF-8; `responder_consulta` carga la clave, delimita los datos en el prompt y llama al modelo; `procesar_respuesta_json` convierte el JSON en un texto limpio.
- `servicios.txt`: contexto editable. Si cambian los precios, se modifica este archivo sin tocar el código.
- `.env`: contiene la clave local. `load_dotenv` la carga en el entorno del proceso y `os.getenv` la recupera.
- `.gitignore`: impide que Git incluya `.env`; `.env.example` sí se comparte porque solo contiene un marcador, nunca una clave válida.

## Preguntas típicas

**¿Se está entrenando Gemini con los servicios?**  
No. El entrenamiento modifica los parámetros del modelo y requiere un proceso y datos preparados. Aquí se usa un modelo ya preentrenado y se le pasa contexto en el prompt en cada consulta. Es aprendizaje en contexto; el texto no cambia el modelo.

**¿Cómo sabe Gemini los precios?**  
El programa lee `servicios.txt` y añade su contenido a la consulta. El prompt le ordena usar esos datos como fuente de verdad, no inventar precios y reconocer cuando falta información.

**¿Por qué se usa JSON?**  
Se pide un objeto estructurado con una propiedad `respuesta`. `json.loads` convierte el texto JSON en un diccionario Python; después se valida que la propiedad exista y sea texto. La interfaz enseña ese texto, no las llaves ni el JSON crudo.

**¿Qué hace `os.getenv`?**  
Busca el valor de una variable de entorno y devuelve `None` si no existe. Así la clave no queda escrita en el código compartido. `python-dotenv` carga las variables del archivo `.env` durante el desarrollo local.

**¿El `.gitignore` protege la clave si ya se subió?**  
No. Solo evita que Git añada el archivo en futuras operaciones. Si una clave se publicó, hay que revocarla en Google AI Studio y crear otra.

**¿Por qué usar un hilo?**  
La petición de red tarda. Si se hiciera en el hilo de Tkinter, la ventana no respondería hasta terminar. El hilo secundario hace la llamada y la cola permite que Tkinter actualice la pantalla de forma segura.

**¿Qué ocurre si falla la red, falta el archivo o Gemini devuelve un JSON incorrecto?**  
Se genera un error claro; la GUI lo recoge y lo muestra sin cerrarse. El botón vuelve a habilitarse para probar otra vez.

**¿Qué significa un error 503/504 o un timeout y qué hace el proyecto?**  
503 indica saturación temporal; 504 o timeout significa que la petición no terminó a tiempo. El programa intenta con `gemini-3.6-flash` si falla el modelo principal `gemini-3.5-flash-lite`. Este modelo está optimizado para baja latencia; usamos razonamiento mínimo y una respuesta corta. La interfaz tiene un temporizador de 45 segundos: si una llamada no termina, muestra un aviso, recupera el botón e ignora cualquier resultado que llegue tarde.

**¿La app reserva citas?**  
No. Solo informa y recomienda llamar al salón para comprobar disponibilidad.

**¿Qué tendrías que cambiar para otra peluquería?**  
Editar `servicios.txt`; la API, el JSON y la interfaz pueden mantenerse.

## Demostración sugerida

1. Mostrar que la ventana se abre y preguntar «¿Cuánto cuesta el corte de mujer?».
2. Preguntar por el horario del sábado.
3. Preguntar por un dato no incluido y observar que el asistente reconoce que no lo sabe.
4. Abrir `servicios.txt` y mostrar que los datos vienen de ese fichero.
5. Mostrar `.env.example` y `.gitignore` sin revelar ninguna clave privada.
6. Explicar el camino GUI → contexto → Gemini → JSON → GUI.
