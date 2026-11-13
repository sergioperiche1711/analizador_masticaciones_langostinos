# Versión web experimental

Para probarlo en esta computadora, haz doble clic en `Abrir vista previa.bat`. Si el navegador se abre antes de que esté listo, recarga la página. Mantén la ventana de comandos abierta mientras uses la aplicación; ciérrala para detener la vista previa.

También puedes abrir una terminal en esta carpeta y ejecutar `python -m http.server 8000` o `py -3 -m http.server 8000`. En la computadora de este proyecto puedes usar `..\python-completo\python\python.exe -m http.server 8000`. Abre `http://localhost:8000` en el navegador. Ctrl+C detiene el servidor.

Selecciona un WAV PCM o flotante sin comprimir y pulsa Analizar. El archivo se lee por bloques dentro del navegador y no se envía a un servidor. Admite RIFF WAV (no RF64), PCM de 8, 16, 24 y 32 bits y flotante de 32 y 64 bits. La frecuencia de muestreo debe ser mayor que el doble del valor del filtro. Archivos estéreo se promedian a mono.

Los resultados son eventos candidatos, no masticaciones confirmadas. El algoritmo calcula un umbral por minuto con una envolvente RMS y MAD. El filtro de esta versión tiene una implementación distinta al de Python, por lo que los resultados no son necesariamente iguales. La frecuencia dominante y dB de la versión de escritorio aún no se incluyen. El CSV utiliza punto y coma; no contiene formato de tabla de Excel.

Esta es una versión local para revisión. Para que otra persona abra una dirección web desde otra computadora, es necesario publicarla en un servicio de alojamiento y verificar si la red de su empresa permite acceder.
