"""ZounD 1.0: interfaz local para WAV y MP3.

Ejecución: mantén desktop.py y detector.py en la misma carpeta y ejecuta:
    python -m pip install numpy scipy soundfile matplotlib openpyxl
    python desktop.py

Se requiere Python con tkinter (incluido habitualmente en Python para Windows).
Dependencias: NumPy (cálculo), SciPy (procesamiento de señales), SoundFile
(lectura de audio), Matplotlib (gráficos) y OpenPyXL (exportación Excel).
"""
import math
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import numpy as np
import soundfile as sf
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from detector import analyze_wav, save_excel, save_csv, AnalysisCancelled

class Desktop:
    def __init__(self, root):
        self.root=root; self.path=None; self.result=None; self.busy=False
        self.events=queue.Queue(); self.cancel=threading.Event()
        root.title('ZounD 1.0 · Análisis acústico'); root.geometry('1180x740'); root.minsize(1000,640)
        root.configure(background='#eef0f3')
        root.option_add('*Font', ('Segoe UI', 10))
        style=ttk.Style(); style.theme_use('clam')
        style.configure('.', font=('Segoe UI',10), background='#eef0f3', foreground='#252b36')
        style.configure('TFrame',background='#eef0f3')
        style.configure('Panel.TFrame',background='#ffffff')
        style.configure('TLabel',background='#eef0f3',foreground='#252b36')
        style.configure('Panel.TLabel',background='#ffffff')
        style.configure('Muted.TLabel',foreground='#737b88',background='#ffffff',font=('Segoe UI',9))
        style.configure('Section.TLabel',background='#ffffff',foreground='#747d8c',font=('Segoe UI',9,'bold'))
        style.configure('Metric.TLabel',background='#ffffff',foreground='#283345',font=('Segoe UI',23,'bold'))
        style.configure('TButton',padding=(14,10),background='#e8ebf0',foreground='#303949',borderwidth=0,font=('Segoe UI',10))
        style.map('TButton',background=[('active','#dce1e9'),('disabled','#f0f2f5')],foreground=[('disabled','#a0a7b2')])
        style.configure('Primary.TButton',background='#34445b',foreground='white',font=('Segoe UI',10,'bold'))
        style.map('Primary.TButton',background=[('disabled','#dce1e8'),('active','#465a76')],foreground=[('disabled','#8b95a4')])
        style.configure('TEntry',fieldbackground='#f5f6f8',foreground='#263247',bordercolor='#dce1e7',padding=9)
        style.configure('TNotebook',background='#ffffff',borderwidth=0)
        style.configure('TNotebook.Tab',background='#eef0f4',padding=(18,12),borderwidth=0)
        style.map('TNotebook.Tab',background=[('selected','#ffffff')],foreground=[('selected','#243750')])
        style.configure('Horizontal.TProgressbar',troughcolor='#e1e5eb',background='#6d819d',borderwidth=0)
        head=ttk.Frame(root,padding=(28,20,28,18)); head.pack(fill='x')
        brand=ttk.Frame(head); brand.pack(side='left')
        ttk.Label(brand,text='ZounD',font=('Segoe UI',29,'bold'),foreground='#283345').pack(anchor='w')
        ttk.Label(brand,text='ESTUDIO DE ANÁLISIS ACÚSTICO',font=('Segoe UI',8),foreground='#7b8492').pack(anchor='w')
        ttk.Label(head,text='VERSIÓN 1.0  /  PROCESAMIENTO LOCAL',font=('Segoe UI',9),foreground='#737d8d').pack(side='right')
        body=ttk.Frame(root,padding=(20,0,20,0)); body.pack(fill='both',expand=True)
        sidebar=ttk.Frame(body,style='Panel.TFrame',padding=22,width=275); sidebar.pack(side='left',fill='y',padx=(0,16)); sidebar.pack_propagate(False)
        box=sidebar
        ttk.Label(box,text='01  ARCHIVO DE AUDIO',style='Section.TLabel').pack(anchor='w',pady=(0,15))
        self.choose=ttk.Button(box,text='Elegir audio…',command=self.choose_file); self.choose.pack(fill='x')
        self.file_label=ttk.Label(box,text='Selecciona un archivo WAV o MP3.',wraplength=226,style='Muted.TLabel'); self.file_label.pack(anchor='w',pady=(12,18))
        ttk.Separator(box).pack(fill='x',pady=(0,18))
        ttk.Label(box,text='02  CONFIGURACIÓN',style='Section.TLabel').pack(anchor='w',pady=(0,12))
        fields=ttk.Frame(box,style='Panel.TFrame'); fields.pack(fill='x')
        fields.columnconfigure(0,weight=1); fields.columnconfigure(1,weight=1)
        self.vars=[]; self.inputs=[]
        for col,(name,value) in enumerate([('Sensibilidad MAD','7'),('Separación (ms)','15'),('Pasa-altos (Hz)','1000'),('Canal (1, 2…)','1')]):
            field=ttk.Frame(fields,style='Panel.TFrame'); field.grid(row=col//2,column=col%2,sticky='ew',padx=(0,8) if col%2==0 else (0,0),pady=(0,14))
            ttk.Label(field,text=name,style='Muted.TLabel').pack(anchor='w',pady=(0,5))
            v=tk.StringVar(value=value); self.vars.append(v); e=ttk.Entry(field,textvariable=v,width=9); e.pack(fill='x'); self.inputs.append(e)
        actions=ttk.Frame(box,style='Panel.TFrame'); actions.pack(fill='x',pady=(10,0))
        self.run=ttk.Button(actions,text='Analizar',command=self.start,style='Primary.TButton'); self.run.pack(side='left',fill='x',expand=True,padx=(0,8))
        self.stop=ttk.Button(actions,text='Cancelar',command=self.cancel.set,state='disabled'); self.stop.pack(side='left')
        ttk.Label(box,text='MAD menor: más detecciones.\nPasa-altos 0: filtro desactivado.',wraplength=226,style='Muted.TLabel').pack(anchor='w',pady=(14,0))
        main=ttk.Frame(body); main.pack(side='left',fill='both',expand=True)
        summary=ttk.Frame(main,style='Panel.TFrame',padding=20); summary.pack(fill='x',pady=(0,16))
        duration_box=ttk.Frame(summary,style='Panel.TFrame'); duration_box.pack(side='left',padx=(0,35))
        ttk.Label(duration_box,text='DURACIÓN DEL AUDIO',style='Section.TLabel').pack(anchor='w')
        self.duration_text=tk.StringVar(value='—'); ttk.Label(duration_box,textvariable=self.duration_text,style='Metric.TLabel').pack(anchor='w',pady=(5,0))
        channel_box=ttk.Frame(summary,style='Panel.TFrame'); channel_box.pack(side='left')
        ttk.Label(channel_box,text='CANAL ANALIZADO',style='Section.TLabel').pack(anchor='w')
        self.channel_text=tk.StringVar(value='—'); ttk.Label(channel_box,textvariable=self.channel_text,style='Metric.TLabel').pack(anchor='w',pady=(5,0))
        exports=ttk.Frame(summary,style='Panel.TFrame'); exports.pack(side='right')
        ttk.Label(exports,text='EXPORTAR RESULTADOS',style='Section.TLabel').pack(anchor='e',pady=(0,8))
        buttons=ttk.Frame(exports,style='Panel.TFrame'); buttons.pack()
        self.export_button=ttk.Button(buttons,text='Excel (.xlsx)',command=lambda:self.export('xlsx'),state='disabled',style='Primary.TButton'); self.export_button.pack(side='left',padx=(0,8))
        self.csv_button=ttk.Button(buttons,text='CSV',command=lambda:self.export('csv'),state='disabled'); self.csv_button.pack(side='left')
        tabs=ttk.Notebook(main); tabs.pack(fill='both',expand=True)
        graph=ttk.Frame(tabs,style='Panel.TFrame'); review=ttk.Frame(tabs,style='Panel.TFrame'); tabs.add(graph,text='Actividad por minuto'); tabs.add(review,text='Revisar detecciones')
        self.fig=Figure(figsize=(9,4),dpi=100,facecolor='white'); self.ax=self.fig.add_subplot(111); self.canvas=FigureCanvasTkAgg(self.fig,master=graph)
        toolbar=NavigationToolbar2Tk(self.canvas,graph,pack_toolbar=False); toolbar.configure(background='#f5f6f8'); toolbar.update(); toolbar.pack(side='bottom',fill='x'); self.canvas.get_tk_widget().pack(fill='both',expand=True)
        strip=ttk.Frame(review,padding=12,style='Panel.TFrame'); strip.pack(fill='x'); ttk.Label(strip,text='Inicio del segmento (s)',style='Panel.TLabel').pack(side='left')
        self.segment=tk.StringVar(value='0'); ttk.Entry(strip,textvariable=self.segment,width=12).pack(side='left',padx=8); ttk.Button(strip,text='Mostrar 10 segundos',command=self.show_segment).pack(side='left')
        ttk.Label(review,text='Una marca no confirma una masticación.',padding=8,style='Muted.TLabel').pack(anchor='w')
        self.rf=Figure(figsize=(9,4),dpi=100,facecolor='white'); self.ra=self.rf.add_subplot(111); self.rc=FigureCanvasTkAgg(self.rf,master=review); self.rc.get_tk_widget().pack(fill='both',expand=True)
        self.style_axes(self.ax); self.style_axes(self.ra)
        self.ax.text(.5,.5,'Selecciona un audio y pulsa Analizar',ha='center',va='center',transform=self.ax.transAxes,color='#8c95a2',fontsize=12)
        bottom=ttk.Frame(root,padding=(22,12,22,14)); bottom.pack(side='bottom',fill='x',before=body)
        self.status=tk.StringVar(value='Listo para analizar'); ttk.Label(bottom,textvariable=self.status,wraplength=760).pack(anchor='w')
        self.progress=ttk.Progressbar(bottom,maximum=100); self.progress.pack(fill='x',pady=8)
        ttk.Label(bottom,text='Procesamiento local  ·  Detector experimental  ·  dBFS no es presión sonora calibrada',foreground='#7d8591',font=('Segoe UI',9)).pack(anchor='w')
        root.after(150,self.poll); root.protocol('WM_DELETE_WINDOW',self.close)

    @staticmethod
    def style_axes(ax):
        ax.set_facecolor('#ffffff')
        for side in ('top','right'): ax.spines[side].set_visible(False)
        for side in ('left','bottom'): ax.spines[side].set_color('#dfe3e9')
        ax.tick_params(colors='#798392',labelsize=9)
        ax.xaxis.label.set_color('#657184'); ax.yaxis.label.set_color('#657184')
        ax.title.set_color('#34445b')
        ax.grid(axis='y',color='#e9ecf1',linewidth=.7); ax.set_axisbelow(True)

    def close(self):
        if self.busy and not messagebox.askyesno('Cerrar','¿Cancelar el análisis y cerrar?'): return
        self.cancel.set(); self.root.destroy()

    def choose_file(self):
        p=filedialog.askopenfilename(filetypes=[('WAV / MP3','*.wav *.wave *.mp3')])
        if not p: return
        try:
            info=sf.info(p)
            if info.duration>7200.1 or Path(p).stat().st_size>550_000_000: raise ValueError('Límite: 2 horas y aproximadamente 500 MiB.')
            self.path=Path(p); self.file_label.configure(text=f'{self.path.name}\n{info.samplerate:,} Hz · {info.channels} canales')
            self.result=None; self.set_busy(False)
            self.duration_text.set(self.format_duration(info.duration)); self.channel_text.set('—')
            self.ax.clear(); self.ra.clear(); self.style_axes(self.ax); self.style_axes(self.ra)
            self.canvas.draw_idle(); self.rc.draw_idle(); self.status.set('Archivo seleccionado · listo para analizar'); self.progress['value']=0
        except Exception as e: messagebox.showerror('No se puede leer',str(e))

    def set_busy(self,b):
        self.busy=b
        for item in [self.choose,self.run,*self.inputs]: item.configure(state='disabled' if b else 'normal')
        self.stop.configure(state='normal' if b else 'disabled')
        for button in (self.export_button,self.csv_button): button.configure(state='normal' if self.result and not b else 'disabled')

    def start(self):
        if not self.path or self.busy: return
        try:
            a,b,c=[float(v.get().replace(',','.')) for v in self.vars[:3]]; ch=int(self.vars[3].get())-1
            if not all(math.isfinite(v) for v in (a,b,c)) or a<=0 or b<=0 or c<0 or ch<0: raise ValueError('Parámetros inválidos.')
        except ValueError as e: messagebox.showerror('Configuración',str(e)); return
        self.result=None; self.set_busy(True); self.cancel.clear(); self.progress['value']=0; self.status.set('Analizando por bloques…')
        self.channel_text.set('—'); self.ax.clear(); self.style_axes(self.ax); self.canvas.draw_idle(); self.ra.clear(); self.style_axes(self.ra); self.rc.draw_idle()
        threading.Thread(target=self.work,args=(self.path,a,b,c,ch),daemon=True).start()

    def work(self,path,a,b,c,ch):
        try:
            r=analyze_wav(path,sensitivity=a,refractory_ms=b,highpass_hz=c,channel=ch,cancel=self.cancel.is_set,progress=lambda p:self.events.put(('progress',p)))
            self.events.put(('result',r))
        except AnalysisCancelled: self.events.put(('cancel',None))
        except Exception as e: self.events.put(('error',str(e)))

    def poll(self):
        try:
            while True:
                kind,value=self.events.get_nowait()
                if kind=='progress': self.progress['value']=100*value
                elif kind=='result': self.result=value; self.set_busy(False); self.show_result()
                else:
                    self.set_busy(False); self.status.set('Cancelado' if kind=='cancel' else 'Error de análisis')
                    if kind=='error': messagebox.showerror('Error',value)
        except queue.Empty: pass
        self.root.after(150,self.poll)

    def show_result(self):
        r=self.result; self.ax.clear(); self.ax.bar(np.arange(len(r.counts_per_minute))+1,r.counts_per_minute,color='#73859c',width=.65)
        self.ax.set(xlabel='Minuto (último intervalo puede ser parcial)',ylabel='Clics detectados · experimental',title='Actividad acústica'); self.style_axes(self.ax); self.fig.tight_layout(); self.canvas.draw_idle()
        self.duration_text.set(self.format_duration(r.duration_seconds)); self.channel_text.set(str(r.settings['Canal (desde 1)']))
        self.status.set(f'Análisis completado · {r.duration_seconds/60:.2f} minutos · canal {r.settings["Canal (desde 1)"]}')
        self.segment.set('0'); self.show_segment()

    @staticmethod
    def format_duration(seconds):
        total=int(seconds)
        return f'{total//3600:02d}:{total%3600//60:02d}:{total%60:02d}'

    def show_segment(self):
        if not self.result: return
        r=self.result
        try:
            start=float(self.segment.get().replace(',','.'))
            if not math.isfinite(start) or not 0<=start<r.duration_seconds: raise ValueError()
        except ValueError: messagebox.showinfo('Segmento','Introduce un segundo dentro de la grabación.'); return
        a=int(start/r.envelope_step); b=min(len(r.envelope),int((start+10)/r.envelope_step)); times=np.arange(a,b)*r.envelope_step
        self.ra.clear(); self.ra.plot(times,r.envelope[a:b],color='#687d98',linewidth=.8)
        events=np.array(r.event_times_seconds); events=events[(events>=start)&(events<start+10)]; indexes=np.rint(events/r.envelope_step).astype(int)
        self.ra.scatter(events,r.envelope[indexes],color='#a17b64',s=24,label='Detecciones experimentales'); self.ra.set(xlabel='Tiempo (s)',ylabel='RMS digital por ventana ~1 ms'); self.style_axes(self.ra); self.ra.legend(frameon=False,fontsize=9); self.rf.tight_layout(); self.rc.draw_idle()

    def export(self,kind='xlsx'):
        if not self.result: return
        path=filedialog.asksaveasfilename(defaultextension='.'+kind,initialfile=Path(self.result.source).stem+'_ZounD',filetypes=[('Excel con tabla de resultados','*.xlsx')] if kind=='xlsx' else [('CSV','*.csv')])
        if path:
            try:
                (save_csv if Path(path).suffix.lower()=='.csv' else save_excel)(self.result,path); self.status.set(f'Exportado: {path}')
            except Exception as e: messagebox.showerror('No se pudo exportar',str(e))

if __name__=='__main__':
    import sys
    if '--self-check' in sys.argv:
        import json
        root=tk.Tk(); root.withdraw(); app=Desktop(root); root.update(); root.destroy()
        Path(sys.argv[sys.argv.index('--self-check')+1]).write_text(json.dumps({'interface':'ok','formats':sf.available_formats()}),encoding='utf-8')
    else:
        root=tk.Tk(); Desktop(root); root.mainloop()
