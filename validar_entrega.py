"""Pruebas reproducibles del motor y exportación; no validación biológica."""
from pathlib import Path
import json, time, threading
import numpy as np
import soundfile as sf
import psutil
from openpyxl import load_workbook
from detector import analyze_wav, save_excel, AnalysisCancelled

out=Path('verificacion'); out.mkdir(exist_ok=True)
report={}
for rate in [8000,44100,48000]:
    x=np.zeros(rate*62,dtype=np.float32)
    for t in [1,59.999,60.001,61]: x[round(t*rate)]=.8
    p=out/f'boundary_{rate}.wav'; sf.write(p,x,rate)
    r=analyze_wav(p,highpass_hz=0,block_frames=100003)
    assert sum(r.counts_per_minute)==3, (rate,r.counts_per_minute)
    assert len(r.counts_per_minute)==2
    assert all(np.diff(r.event_times_seconds)>=.0149)
    report[f'boundary_{rate}']=r.counts_per_minute
tone=.1*np.sin(2*np.pi*1000*np.arange(48000*2)/48000)
sf.write(out/'tone.wav',tone,48000)
r=analyze_wav(out/'tone.wav',highpass_hz=0)
assert abs(r.rms_dbfs[0]+23.0103)<.02
assert abs(r.mean_hz[0]-1000)<24
save_excel(r,out/'informe.xlsx')
w=load_workbook(out/'informe.xlsx'); assert w['Resultados']['G2'].value==r.mean_hz[0]/1e6
assert len(w['Resultados'].tables)==1 and 'Eventos' in w.sheetnames
report['excel']='ok'; report['tone_rms']=r.rms_dbfs
sf.write(out/'tone.mp3',tone,48000,format='MP3')
r=analyze_wav(out/'tone.mp3',highpass_hz=0); assert abs(r.duration_seconds-2)<.1
report['mp3']='decoded and analyzed'
try:
    analyze_wav(out/'tone.wav',cancel=lambda:True)
    raise AssertionError('Cancel did not work')
except AnalysisCancelled: report['cancel']='ok'
rate=32000
minute=np.zeros(rate*60,dtype=np.float32); minute[rate]=.8
p=out/'two_hours.wav'
if not p.is_file() or p.stat().st_size != 460800044:
    with sf.SoundFile(p,'w',samplerate=rate,channels=1,subtype='PCM_16') as f:
        for i in range(120): f.write(minute)
peak=[0]; stop=threading.Event()
def monitor():
    while not stop.wait(.1): peak[0]=max(peak[0],psutil.Process().memory_info().rss)
t=threading.Thread(target=monitor); t.start(); start=time.perf_counter()
r=analyze_wav(p,highpass_hz=0)
stop.set(); t.join()
assert len(r.counts_per_minute)==120 and all(c==1 for c in r.counts_per_minute)
report['two_hours']={'bytes':p.stat().st_size,'seconds_processing':round(time.perf_counter()-start,2),'peak_rss_MiB':round(peak[0]/1048576,1),'clicks':sum(r.counts_per_minute)}
(out/'resultados.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
