"""Detección inicial de clics en WAV largos, procesados por bloques."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import soundfile as sf
from scipy import signal


@dataclass
class AnalysisResult:
    source: str
    sample_rate: int
    channels: int
    duration_seconds: float
    counts_per_minute: list[int]
    event_times_seconds: list[float]
    rms_dbfs: list[float | None]
    dominant_hz: list[float | None]


def analyze_wav(
    path: str | Path,
    *,
    sensitivity: float = 7.0,
    refractory_ms: float = 15.0,
    highpass_hz: float = 1000.0,
    block_frames: int = 262_144,
    progress: Callable[[float], None] | None = None,
) -> AnalysisResult:
    """Detect transient clicks using a filtered 1 ms RMS envelope.

    The audio itself is read incrementally; only one minute of the compact
    envelope is retained at a time. Sensitivity is the robust-MAD multiplier.
    """
    path = Path(path)
    with sf.SoundFile(path) as audio:
        sample_rate = int(audio.samplerate)
        channels = int(audio.channels)
        total_frames = int(audio.frames)
        duration = total_frames / sample_rate if sample_rate else 0.0
        if total_frames == 0:
            raise ValueError("El archivo no contiene audio.")

        if highpass_hz < 0 or highpass_hz >= sample_rate / 2:
            raise ValueError(
                f"El filtro debe estar entre 0 y Nyquist ({sample_rate / 2:.0f} Hz)."
            )
        sos = (
            signal.butter(4, highpass_hz, btype="highpass", fs=sample_rate, output="sos")
            if highpass_hz > 0
            else None
        )
        zi = signal.sosfilt_zi(sos) * 0.0 if sos is not None else None

        # Keep envelope windows aligned across arbitrary audio block boundaries.
        frame_width = max(1, round(sample_rate * 0.001))
        samples_carry = np.empty(0, dtype=np.float32)
        current_minute = 0
        minute_envelope: list[np.ndarray] = []
        counts: list[int] = []
        event_times: list[float] = []
        envelope_frame_index = 0
        # Spectral statistics describe the whole filtered minute, not just clicks.
        energy = np.zeros((total_frames + 60 * sample_rate - 1) // (60 * sample_rate))
        sample_counts = np.zeros(len(energy), dtype=np.int64)
        fft_size = 2048
        spectra = np.zeros((len(energy), fft_size // 2 + 1), dtype=np.float64)
        spectrum_weights = np.zeros(len(energy), dtype=np.int64)
        audio_position = 0

        def finish_minute(envelope_parts: list[np.ndarray], minute_index: int) -> None:
            if envelope_parts:
                envelope = np.concatenate(envelope_parts)
            else:
                envelope = np.empty(0, dtype=np.float32)
            if envelope.size == 0:
                counts.append(0)
                return
            median = float(np.median(envelope))
            mad = float(np.median(np.abs(envelope - median)))
            # Fall back to a tiny scale-relative floor for near-silent recordings.
            floor = max(float(np.max(envelope)) * 1e-6, np.finfo(np.float32).eps)
            threshold = median + max(float(sensitivity) * 1.4826 * mad, floor)
            distance = max(1, round(refractory_ms))
            peaks, _ = signal.find_peaks(envelope, height=threshold, distance=distance)
            counts.append(int(peaks.size))
            event_times.extend((minute_index * 60.0 + peaks * frame_width / sample_rate).tolist())

        while True:
            chunk = audio.read(block_frames, dtype="float32", always_2d=True)
            if chunk.size == 0:
                break
            mono = np.mean(chunk, axis=1, dtype=np.float32)
            if sos is not None:
                mono, zi = signal.sosfilt(sos, mono, zi=zi)
            cursor_samples = 0
            while cursor_samples < len(mono):
                minute = audio_position // (60 * sample_rate)
                take = min(len(mono) - cursor_samples, (minute + 1) * 60 * sample_rate - audio_position)
                part = mono[cursor_samples:cursor_samples + take]
                energy[minute] += np.dot(part.astype(np.float64), part.astype(np.float64))
                sample_counts[minute] += take
                if take >= 2:
                    _, power = signal.welch(part, fs=sample_rate, nperseg=min(fft_size, take), nfft=fft_size)
                    spectra[minute] += power * take
                    spectrum_weights[minute] += take
                audio_position += take
                cursor_samples += take
            if samples_carry.size:
                mono = np.concatenate((samples_carry, mono))
            complete = (mono.size // frame_width) * frame_width
            if complete:
                frames = mono[:complete].reshape(-1, frame_width)
                envelope = np.sqrt(np.mean(frames * frames, axis=1, dtype=np.float32))
            else:
                envelope = np.empty(0, dtype=np.float32)
            samples_carry = mono[complete:].copy()

            # Split envelope at exact minute boundaries; this also handles rates
            # where 60 seconds is not an integer number of 1 ms frames.
            cursor = 0
            while cursor < envelope.size:
                absolute_sample = envelope_frame_index * frame_width
                absolute_time = absolute_sample / sample_rate
                minute_for_frame = int(absolute_time // 60)
                if minute_for_frame != current_minute:
                    finish_minute(minute_envelope, current_minute)
                    minute_envelope = []
                    current_minute = minute_for_frame
                samples_until_boundary = (current_minute + 1) * 60 * sample_rate - absolute_sample
                frames_until_boundary = max(1, (samples_until_boundary + frame_width - 1) // frame_width)
                consumed = min(envelope.size - cursor, frames_until_boundary)
                minute_envelope.append(envelope[cursor : cursor + consumed])
                envelope_frame_index += consumed
                cursor += consumed

            if progress:
                progress(min(1.0, audio.tell() / total_frames))

        # A final partial envelope frame represents the last samples.
        if samples_carry.size:
            partial = np.sqrt(np.mean(samples_carry * samples_carry, dtype=np.float32))
            minute_envelope.append(np.array([partial], dtype=np.float32))
        if minute_envelope or not counts:
            finish_minute(minute_envelope, current_minute)

    # A 60-minute recording with a partial final minute has one value per
    # started minute; reports call this the minute containing the event.
    return AnalysisResult(
        source=str(path),
        sample_rate=sample_rate,
        channels=channels,
        duration_seconds=duration,
        counts_per_minute=counts,
        event_times_seconds=event_times,
        rms_dbfs=[float(10 * np.log10(e / n)) if e > 0 and n else None for e, n in zip(energy, sample_counts)],
        dominant_hz=[float(np.argmax(spectrum[1:]) + 1) * sample_rate / fft_size
                     if weight and np.any(spectrum[1:] > 0) else None
                     for spectrum, weight in zip(spectra, spectrum_weights)],
    )


def save_csv(result: AnalysisResult, output_path: str | Path) -> None:
    """Write the per-minute click counts to CSV."""
    output_path = Path(output_path)
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle, delimiter=";")
        writer.writerow(EXPORT_HEADERS)
        for row in export_rows(result):
            writer.writerow([str(round(value, 3)).replace('.', ',') if isinstance(value, float) else value for value in row])


EXPORT_HEADERS = ["Minuto", "Duración (s)", "Clics detectados", "Nivel RMS filtrado (dBFS)", "Frecuencia dominante (Hz)", "Frecuencia dominante (kHz)"]


def export_rows(result: AnalysisResult):
    for i, count in enumerate(result.counts_per_minute):
        hz = result.dominant_hz[i]
        yield [i + 1, min(60.0, max(0.0, result.duration_seconds - i * 60)), count,
               result.rms_dbfs[i], hz, hz / 1000 if hz is not None else None]


def save_excel(result: AnalysisResult, output_path: str | Path) -> None:
    from openpyxl import Workbook
    from openpyxl.worksheet.table import Table, TableStyleInfo

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Resultados"
    sheet.append(EXPORT_HEADERS)
    for row in export_rows(result):
        sheet.append(row)
    table = Table(displayName="ResultadosAudio", ref=f"A1:F{sheet.max_row}")
    table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    sheet.add_table(table)
    sheet.freeze_panes = "A2"
    for column, width in {"A": 12, "B": 18, "C": 20, "D": 28, "E": 29, "F": 30}.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2, min_col=2, max_col=6):
        for cell in row:
            if cell.column != 3:
                cell.number_format = "0.00"
    notes = workbook.create_sheet("Interpretación")
    for line in ["Medidas calculadas sobre la señal filtrada y mezclada a mono.",
                 "La frecuencia dominante corresponde al audio del minuto completo, incluidos ruidos; no identifica la frecuencia de cada clic.",
                 "dBFS es nivel digital RMS relativo a escala completa, no presión sonora ni dB SPL calibrados.",
                 "Una celda vacía indica ausencia de señal medible. El último minuto puede estar incompleto."]:
        notes.append([line])
    notes.column_dimensions["A"].width = 110
    workbook.save(output_path)

