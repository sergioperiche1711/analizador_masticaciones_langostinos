"""Comprobaciones de interfaz y exportación de ZounD 1.0."""
import csv
import tkinter as tk
from pathlib import Path
from unittest.mock import patch
import soundfile as sf
import numpy as np
from openpyxl import load_workbook
from desktop import Desktop
from detector import analyze_wav, EXPORT_HEADERS

folder=Path('verificacion'); folder.mkdir(exist_ok=True)
path=folder/'v1_tono.wav'; rate=48000
sf.write(path,.1*np.sin(2*np.pi*1000*np.arange(rate*2)/rate),rate)
r=analyze_wav(path,highpass_hz=0)
root=tk.Tk(); root.withdraw(); ui=Desktop(root)
assert str(ui.export_button['state'])=='disabled'
assert str(ui.csv_button['state'])=='disabled'
ui.result=r; ui.set_busy(False); ui.show_result(); root.update()
assert 'candidatos' not in ui.status.get()
assert ui.duration_text.get()=='00:00:02'
assert ui.channel_text.get()=='1'
assert str(ui.export_button['state'])=='normal'
for kind in ('xlsx','csv'):
    destination=folder/f'ZounD-prueba.{kind}'
    with patch('desktop.filedialog.asksaveasfilename',return_value=str(destination)):
        ui.export(kind)
    assert destination.is_file()
with (folder/'ZounD-prueba.csv').open(encoding='utf-8-sig') as f:
    rows=list(csv.reader(f,delimiter=';'))
assert rows[0]==EXPORT_HEADERS and len(rows[1])==7
assert not any('Tasa equivalente' in v or 'saturación' in v for v in rows[0])
book=load_workbook(folder/'ZounD-prueba.xlsx')
assert book['Resultados'].max_column==7
assert list(book['Resultados'].values)[0]==tuple(EXPORT_HEADERS)
assert book['Resultados'].tables['ResultadosAudio'].ref=='A1:G2'
import zipfile
with zipfile.ZipFile(folder/'ZounD-prueba.xlsx') as z:
    assert not any(name.startswith('xl/charts/') for name in z.namelist())
assert abs(book['Resultados']['G2'].value-r.mean_hz[0]/1e6)<1e-12
assert book['Interpretación']['A1'].value.startswith('ZounD 1.0')
ui.set_busy(True)
assert str(ui.export_button['state'])=='disabled'
assert str(ui.csv_button['state'])=='disabled'
root.destroy()
print('ZounD 1.0: interfaz, resumen, estados de botones, Excel y CSV correctos.')
