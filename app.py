"""Interfaz sencilla para contar clics de langostino en grabaciones WAV."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from detector import AnalysisResult, analyze_wav, save_csv


class AudioClickApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Analizador de clics de langostino")
        self.root.geometry("1000x690")
        self.file_path: Path | None = None
        self.result: AnalysisResult | None = None
        self.busy = False

        controls = ttk.Frame(root, padding=12)
        controls.pack(fill="x")
        self.file_label = ttk.Label(controls, text="Selecciona un archivo WAV", width=54)
        self.file_label.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        ttk.Button(controls, text="Elegir WAV…", command=self.choose_file).grid(row=0, column=3, padx=6)

        ttk.Label(controls, text="Sensibilidad (MAD)").grid(row=1, column=0, sticky="w")
        self.sensitivity = tk.StringVar(value="7.0")
        ttk.Entry(controls, textvariable=self.sensitivity, width=9).grid(row=1, column=1, sticky="w")
        ttk.Label(controls, text="Separación mínima (ms)").grid(row=1, column=2, sticky="e", padx=(12, 4))
        self.refractory = tk.StringVar(value="15")
        ttk.Entry(controls, textvariable=self.refractory, width=9).grid(row=1, column=3, sticky="w")
        ttk.Label(controls, text="Filtro pasa-altos (Hz; 0 = apagado)").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.highpass = tk.StringVar(value="1000")
        ttk.Entry(controls, textvariable=self.highpass, width=9).grid(row=2, column=1, sticky="w", pady=(8, 0))
        self.analyze_button = ttk.Button(controls, text="Analizar", command=self.start_analysis)
        self.analyze_button.grid(row=2, column=3, sticky="e", pady=(8, 0))

        self.status = tk.StringVar(value="Listo")
        ttk.Label(root, textvariable=self.status, padding=(12, 0)).pack(anchor="w")
        self.progress = ttk.Progressbar(root, mode="determinate", maximum=100)
        self.progress.pack(fill="x", padx=12, pady=6)

        self.figure = Figure(figsize=(9, 5), dpi=100)
        self.axes = self.figure.add_subplot(111)
        self.axes.set_title("Clics por minuto")
        self.axes.set_xlabel("Minuto de grabación")
        self.axes.set_ylabel("Número de clics")
        self.axes.grid(True, alpha=0.25)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=12)
        toolbar = NavigationToolbar2Tk(self.canvas, root, pack_toolbar=False)
        toolbar.update()
        toolbar.pack(fill="x", padx=12)
        self.save_button = ttk.Button(root, text="Guardar conteo como CSV…", command=self.export_csv, state="disabled")
        self.save_button.pack(anchor="e", padx=12, pady=10)

    def choose_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar grabación WAV",
            filetypes=[("Audio WAV", "*.wav *.wave"), ("Todos los archivos", "*.*")],
        )
        if path:
            self.file_path = Path(path)
            self.file_label.configure(text=str(self.file_path))

    def start_analysis(self) -> None:
        if self.busy:
            return
        if not self.file_path:
            messagebox.showinfo("Falta el archivo", "Primero selecciona una grabación WAV.")
            return
        try:
            sensitivity = float(self.sensitivity.get())
            refractory = float(self.refractory.get())
            highpass = float(self.highpass.get())
            if sensitivity <= 0 or refractory <= 0 or highpass < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Parámetros inválidos", "Usa valores numéricos positivos; el filtro puede ser 0.")
            return
        self.busy = True
        self.analyze_button.configure(state="disabled")
        self.save_button.configure(state="disabled")
        self.progress["value"] = 0
        self.status.set("Analizando por bloques…")
        threading.Thread(
            target=self._analyze_worker,
            args=(self.file_path, sensitivity, refractory, highpass),
            daemon=True,
        ).start()

    def _analyze_worker(self, path: Path, sensitivity: float, refractory: float, highpass: float) -> None:
        try:
            result = analyze_wav(
                path,
                sensitivity=sensitivity,
                refractory_ms=refractory,
                highpass_hz=highpass,
                progress=lambda value: self.root.after(0, self.progress.configure, {"value": value * 100}),
            )
            self.root.after(0, self._show_result, result)
        except Exception as exc:
            self.root.after(0, self._show_error, str(exc))

    def _show_result(self, result: AnalysisResult) -> None:
        self.busy = False
        self.analyze_button.configure(state="normal")
        self.result = result
        self.axes.clear()
        minutes = list(range(1, len(result.counts_per_minute) + 1))
        self.axes.bar(minutes, result.counts_per_minute, width=0.85, color="#187d83")
        self.axes.set_title("Clics detectados por minuto")
        self.axes.set_xlabel("Minuto de grabación")
        self.axes.set_ylabel("Número de clics")
        self.axes.grid(True, axis="y", alpha=0.25)
        self.axes.set_xlim(0.5, max(1.5, len(minutes) + 0.5))
        self.figure.tight_layout()
        self.canvas.draw_idle()
        total = sum(result.counts_per_minute)
        self.status.set(
            f"Terminado: {len(minutes)} min · {total:,} clics · "
            f"{result.sample_rate:,} Hz · {result.channels} canal(es)"
        )
        self.progress["value"] = 100
        self.save_button.configure(state="normal")

    def _show_error(self, message: str) -> None:
        self.busy = False
        self.analyze_button.configure(state="normal")
        self.status.set("No se pudo analizar el archivo")
        messagebox.showerror("Error de análisis", message)

    def export_csv(self) -> None:
        if self.result is None:
            return
        default_name = f"{Path(self.result.source).stem}_clics_por_minuto.csv"
        path = filedialog.asksaveasfilename(
            title="Guardar conteo", defaultextension=".csv", initialfile=default_name,
            filetypes=[("CSV", "*.csv")],
        )
        if path:
            try:
                save_csv(self.result, path)
                self.status.set(f"CSV guardado: {path}")
            except OSError as exc:
                messagebox.showerror("No se pudo guardar", str(exc))


if __name__ == "__main__":
    root = tk.Tk()
    AudioClickApp(root)
    root.mainloop()

