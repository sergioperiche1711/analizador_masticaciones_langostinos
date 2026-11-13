# ZounD 1.0 — edición portátil

## Abrir

Descomprime el ZIP completo en una carpeta con permiso de lectura y escritura. Abre `ZounD.exe`. Conserva la carpeta `_internal` junto al ejecutable. No necesitas instalar Python, conectarte a Internet ni tener Excel para generar un informe.

La versión 1.0 incorpora un diseño neutro, botones separados para Excel y CSV y un resumen con duración y canal, sin mostrar el total de candidatos. El conteo experimental por minuto se conserva en el gráfico y en los informes.

Esta compilación apunta a Windows 10 y 11 de 64 bits. No se declara compatibilidad probada con otros sistemas. Windows 8 requeriría otro entorno de compilación y pruebas en ese sistema; Windows 9 no fue una versión comercial. Una empresa puede exigir aprobación de TI incluso para una aplicación portátil.

## Analizar

1. Selecciona WAV o MP3 de hasta dos horas y aproximadamente 500 MiB.
2. Selecciona el canal del hidrófono (1 por defecto). No se mezclan canales con posible cancelación de fase.
3. Ajusta sensibilidad MAD, separación mínima en milisegundos y filtro pasa-altos en Hz. Los valores iniciales no son una calibración biológica.
4. Pulsa Analizar. Puedes cancelar. La señal original se lee por bloques, sin modificaciones. Se conserva una envolvente reducida en memoria para revisión.
5. Revisa segmentos de diez segundos en la pestaña Revisar detecciones. Las marcas son candidatos acústicos.
6. Usa los botones Excel (.xlsx) o CSV, ubicados arriba a la derecha y habilitados al finalizar un análisis. Excel incluye tabla, tiempos individuales y configuración; CSV contiene los parámetros numéricos por minuto con separador punto y coma. Las exportaciones no incluyen gráficos, tasa equivalente ni porcentaje de muestras próximas a saturación.

## Interpretación

- Clics detectados: eventos candidatos; pueden incluir burbujas, impactos y maquinaria. No es un conteo validado de masticaciones.
- Duración: segundos del intervalo. El último minuto puede ser parcial.
- RMS filtrado (dBFS): 20 log10 del RMS digital filtrado respecto a amplitud 1. No equivale a presión sonora bajo el agua. Silencio se exporta como celda vacía.
- Frecuencia media: promedio de frecuencias ponderado por potencia del espectro Welch del minuto filtrado completo, con 2048 puntos, sin la componente continua. Incluye ruido; no es el promedio de frecuencias de cada clic. Resolución = muestreo / 2048. kHz = Hz / 1000; MHz = Hz / 1000000. No se miden frecuencias superiores a la mitad del muestreo.
- MP3: la compresión con pérdida puede alterar impulsos y niveles. Preferir WAV original para validación y calibración.

El umbral MAD se estima por minuto. La selección de picos y separación se aplica globalmente sobre la envolvente para evitar reiniciarla al cambiar de minuto. El tiempo de cada evento corresponde a una ventana RMS de aproximadamente 1 ms, no al máximo exacto de una muestra.

## Seguridad y firma

El programa no contiene funciones de subida de archivos, actualización automática, descarga ni acceso a credenciales. Usa bibliotecas de código abierto empaquetadas con PyInstaller, sin UPX. Esto no constituye una garantía absoluta contra vulnerabilidades ni falsos positivos de antivirus.

El autor aún no dispone de un certificado de firma de código. El ejecutable se entrega sin firma Authenticode. SHA-256 identifica el archivo y detecta modificaciones al compararlo con una referencia confiable; no acredita identidad ni ausencia de malware. Para una distribución comercial se requiere un certificado o servicio de firma y validación adicional, incluida revisión por TI de la empresa. No desactives las protecciones del equipo para ejecutarlo.

## Limitaciones y validación

Las pruebas sintéticas comprueban cálculos y funcionamiento, no la identificación de masticaciones. Falta validación con audios etiquetados de la empresa y pruebas independientes en Windows 10/11. No se afirma compatibilidad con cualquier PC ni una tasa de acierto biológica.

El detector es dependiente de sensibilidad, ruido, separación y banda elegida. Para comercializarlo como contador de masticaciones hay que medir precisión, omisiones y error por minuto con grabaciones distintas de las usadas para ajustar los parámetros.
