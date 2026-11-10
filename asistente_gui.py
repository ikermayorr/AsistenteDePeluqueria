"""Interfaz Tkinter del asistente de la peluquería."""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from gemini_client import responder_consulta

TIEMPO_LIMITE_UI_MS = 45_000


class AsistentePeluqueriaApp:
    """Ventana principal. La petición web se ejecuta fuera del hilo gráfico."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Luna · Asistente de peluquería")
        self.root.geometry("880x700")
        self.root.minsize(620, 520)
        self.root.configure(bg="#f5f3f9")
        self.resultados: queue.Queue[tuple[int, str, str]] = queue.Queue()
        self._contador_solicitudes = 0
        self._solicitud_activa: int | None = None
        self._crear_interfaz()
        self._revisar_resultados()

    def _crear_interfaz(self) -> None:
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except tk.TclError:
            pass
        acento = "#7154b8"
        estilo.configure("TEntry", fieldbackground="white", foreground="#292433",
                          insertcolor=acento, bordercolor="#e5e0ec", padding=(12, 11))
        estilo.configure("Enviar.TButton", font=("Segoe UI", 10, "bold"), padding=(18, 11),
                         background=acento, foreground="white", borderwidth=0)
        estilo.map("Enviar.TButton", background=[("active", "#5d419f"), ("disabled", "#b9b2c7")],
                   foreground=[("disabled", "#f8f7fa")])
        estilo.configure("Estado.TLabel", background="#f5f3f9", foreground="#777183",
                         font=("Segoe UI", 9))

        contenedor = tk.Frame(self.root, bg="#f5f3f9", padx=30, pady=24)
        contenedor.pack(fill="both", expand=True)
        contenedor.columnconfigure(0, weight=1)
        contenedor.rowconfigure(1, weight=1)
        cabecera = tk.Frame(contenedor, bg="#f5f3f9")
        cabecera.grid(row=0, column=0, sticky="ew", pady=(0, 18))
        marca = tk.Frame(cabecera, bg="#eee9f7", padx=11, pady=6)
        marca.pack(anchor="w", pady=(0, 10))
        tk.Label(marca, text="✦  LUNA  ·  ASISTENTE IA", font=("Segoe UI", 9, "bold"),
                 fg=acento, bg="#eee9f7").pack()
        tk.Label(cabecera, text="Tu peluquería, siempre a mano",
                 font=("Segoe UI", 23, "bold"), fg="#292433", bg="#f5f3f9").pack(anchor="w")
        tk.Label(cabecera, text="Resuelve tus dudas sobre servicios, precios y horarios.",
                 font=("Segoe UI", 10), fg="#777183", bg="#f5f3f9").pack(anchor="w", pady=(5, 0))

        tarjeta = tk.Frame(contenedor, bg="white", highlightbackground="#e8e4ed", highlightthickness=1)
        barra_chat = tk.Frame(tarjeta, bg="white", padx=18, pady=12)
        barra_chat.pack(fill="x")
        tk.Label(barra_chat, text="CONVERSACIÓN", font=("Segoe UI", 8, "bold"),
                 fg="#8c8498", bg="white").pack(side="left")
        self.chat = scrolledtext.ScrolledText(
            tarjeta, wrap="word", state="disabled", font=("Segoe UI", 10),
            bg="white", fg="#292433", relief="flat", borderwidth=0,
            padx=18, pady=12, spacing1=5, spacing3=10, selectbackground="#ded5f0",
        )
        self.chat.pack(fill="both", expand=True, padx=(5, 8), pady=(0, 8))
        self.chat.tag_configure("usuario", foreground=acento, font=("Segoe UI", 10, "bold"))
        self.chat.tag_configure("asistente", foreground="#393444")
        self.chat.tag_configure("error", foreground="#b34d56")
        self._anadir_mensaje("asistente", "¡Hola! Soy el asistente de Luna. ¿En qué puedo ayudarte?")

        pie = tk.Frame(contenedor, bg="#f5f3f9")
        pie.grid(row=2, column=0, sticky="ew", pady=(15, 0))
        tk.Label(pie, text="TU MENSAJE", font=("Segoe UI", 8, "bold"),
                 fg="#8c8498", bg="#f5f3f9").pack(anchor="w", pady=(0, 6))
        fila = tk.Frame(pie, bg="#f5f3f9")
        fila.pack(fill="x")
        self.entrada = ttk.Entry(fila, font=("Segoe UI", 10))
        self.entrada.pack(side="left", fill="x", expand=True, ipady=9)
        self.entrada.bind("<Return>", self._enviar_evento)
        self.boton = ttk.Button(fila, text="Enviar  →", style="Enviar.TButton", command=self._enviar)
        self.boton.pack(side="left", padx=(10, 0))
        self.estado = ttk.Label(contenedor, text="Conectado a Gemini cuando configures tu API Key.", style="Estado.TLabel")
        self.estado.grid(row=3, column=0, sticky="w", pady=(9, 0))
        # El pie se reserva antes de expandir la tarjeta para que el campo
        # de entrada y el botón nunca queden fuera de la ventana.
        tarjeta.grid(row=1, column=0, sticky="nsew")
        self.entrada.focus_set()

    def _anadir_mensaje(self, quien: str, texto: str) -> None:
        self.chat.configure(state="normal")
        etiqueta = "Tú" if quien == "usuario" else "Luna"
        tag = quien if quien in {"usuario", "asistente", "error"} else "asistente"
        self.chat.insert("end", f"{etiqueta}: ", tag)
        self.chat.insert("end", f"{texto}\n\n", tag)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _enviar_evento(self, _evento: tk.Event) -> str:
        self._enviar()
        return "break"

    def _enviar(self) -> None:
        pregunta = self.entrada.get().strip()
        if not pregunta:
            return
        self.entrada.delete(0, "end")
        self._anadir_mensaje("usuario", pregunta)
        self.boton.configure(state="disabled")
        self.entrada.configure(state="disabled")
        self.estado.configure(text="Consultando Gemini; puede tardar hasta unos 30 segundos…")
        self._contador_solicitudes += 1
        solicitud_id = self._contador_solicitudes
        self._solicitud_activa = solicitud_id
        self.root.after(TIEMPO_LIMITE_UI_MS, self._marcar_tiempo_agotado, solicitud_id)
        threading.Thread(target=self._consultar, args=(solicitud_id, pregunta), daemon=True).start()

    def _consultar(self, solicitud_id: int, pregunta: str) -> None:
        # Tkinter no es seguro entre hilos: el worker solo deja el resultado en la cola.
        try:
            respuesta = responder_consulta(pregunta)
            self.resultados.put((solicitud_id, "ok", respuesta))
        except Exception as error:  # los detalles se convierten en un mensaje entendible
            self.resultados.put((solicitud_id, "error", str(error)))

    def _restaurar_entrada(self) -> None:
        """Devuelve el control al usuario después de terminar o agotar el tiempo."""
        self.boton.configure(state="normal")
        self.entrada.configure(state="normal")
        self.entrada.focus_set()

    def _marcar_tiempo_agotado(self, solicitud_id: int) -> None:
        """Evita que la GUI quede bloqueada si una llamada externa no termina."""
        if self._solicitud_activa != solicitud_id:
            return
        self._solicitud_activa = None
        self._anadir_mensaje(
            "error",
            "La consulta ha tardado demasiado. Comprueba la conexión y vuelve a intentarlo.",
        )
        self.estado.configure(text="Tiempo agotado; puedes volver a intentarlo.")
        self._restaurar_entrada()

    def _revisar_resultados(self) -> None:
        try:
            while True:
                solicitud_id, tipo, texto = self.resultados.get_nowait()
                # Ignora el resultado tardío de una solicitud ya marcada como timeout.
                if solicitud_id != self._solicitud_activa:
                    continue
                self._solicitud_activa = None
                self._anadir_mensaje("asistente" if tipo == "ok" else "error", texto)
                self._restaurar_entrada()
                self.estado.configure(text="Lista para ayudarte.")
        except queue.Empty:
            pass
        self.root.after(100, self._revisar_resultados)


def main() -> None:
    ventana = tk.Tk()
    AsistentePeluqueriaApp(ventana)
    ventana.mainloop()


if __name__ == "__main__":
    main()




