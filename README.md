# Analizador de clics de langostino

Aplicación de escritorio inicial para WAV mono o estéreo. Lee el audio en bloques, detecta transitorios y grafica el número detectado en cada minuto. También puede exportar esos conteos a CSV.

La exportación predeterminada es Excel (.xlsx), con una tabla y filtros. También se puede guardar como CSV con punto y coma, adecuado para muchas configuraciones de Excel en español. Cada fila incluye la duración del intervalo, los clics detectados, el nivel RMS digital (dBFS) y la frecuencia dominante (Hz y kHz). Estas dos últimas medidas describen el audio filtrado del minuto completo, incluido el ruido; no identifican cada clic. El nivel dBFS no es presión sonora calibrada en dB SPL. La frecuencia dominante es una estimación espectral con 2048 puntos y su resolución depende de la frecuencia de muestreo. Para silencio, se deja la celda vacía.

## Instalación

La descarga de GitHub contiene el código, pero no incluye Python ni sus bibliotecas. En Windows de 64 bits:

1. Instala [Python](https://www.python.org/downloads/windows/) 3.10 o posterior. Durante la instalación, activa la opción para agregar Python al PATH y asegúrate de incluir el lanzador `py` y Tcl/Tk.
2. Descomprime el proyecto si lo descargaste como ZIP. Abre la carpeta que contiene `app.py`.
3. Con conexión a Internet, haz doble clic en **Instalar dependencias.bat** y espera el mensaje de instalación completada. Este paso se hace una vez y crea un entorno `.venv` en la carpeta.
4. Haz doble clic en **Abrir analizador.bat**, selecciona un WAV y pulsa **Analizar**.

Si tienes una copia portátil que incluye la carpeta `python-completo`, puedes abrir directamente **Abrir analizador.bat**. Esta carpeta no se incluye en GitHub.

Para instalarlo en otro equipo con Python 3.10 o posterior, abre PowerShell en esta carpeta y ejecuta:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Ajustes

- **Sensibilidad (MAD):** bajar el valor detecta sonidos más débiles y puede aumentar falsos positivos; subirlo exige picos más marcados.
- **Separación mínima:** evita contar las oscilaciones de un solo clic como varios eventos. El valor inicial es 15 ms.
- **Filtro pasa-altos:** reduce sonidos graves y ruido de manejo. El corte depende del hidrofono, la especie y la grabación; 0 lo desactiva.

Los valores iniciales son puntos de partida, no una calibración biológica. Conviene ajustar los parámetros escuchando segmentos representativos y comparando detecciones con conteos manuales. La aplicación reporta eventos detectados por minuto, también en el último minuto parcial.

## Archivos grandes

El WAV se procesa por bloques de 262.144 muestras y no se carga completo en memoria. Se mantiene solo una envolvente reducida para calcular el umbral de cada minuto; el WAV original queda intacto.

## Limitación de esta versión

El detector usa un umbral estadístico sobre la envolvente RMS de 1 ms y un tiempo refractario. Ruidos de fondo impulsivos pueden parecer clics. Para obtener conteos fiables en el uso real, hay que calibrar el filtro, la sensibilidad y la separación mínima usando grabaciones etiquetadas, y confirmar visual o auditivamente una muestra de los eventos.
