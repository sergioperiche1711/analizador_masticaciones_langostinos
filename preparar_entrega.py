"""Empaqueta la carpeta portátil y registra versiones, licencias y SHA-256."""
from pathlib import Path
import importlib.metadata as md
import hashlib, shutil, json

target=Path('dist/ZounD')
if not (target/'ZounD.exe').is_file(): raise RuntimeError('Primero compila ZounD.')
shutil.copy2('PORTABLE.md',target/'LEEME.md')
versions={}
licenses=target/'Licencias'; licenses.mkdir(exist_ok=True)
for name in ['numpy','scipy','soundfile','cffi','matplotlib','openpyxl','pillow','contourpy','cycler','fonttools','kiwisolver','packaging','pyparsing','python-dateutil','six','et-xmlfile','pyinstaller']:
    d=md.distribution(name); versions[name]=d.version
    for f in d.files or []:
        if any(x in str(f).lower() for x in ('license','licence','copying')) and '.dist-info' in str(f):
            src=Path(d.locate_file(f))
            if src.is_file():
                dest=licenses/name/Path(str(f)); dest.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dest)
runtime=Path('python-completo/python')
for src in runtime.glob('LICENSE*'): shutil.copy2(src,licenses/src.name)
(target/'Versiones.json').write_text(json.dumps(versions,indent=2),encoding='utf-8')
if Path('verificacion/resultados.json').is_file(): shutil.copy2('verificacion/resultados.json',target/'Pruebas-sinteticas.json')
delivery=Path('entrega'); delivery.mkdir(exist_ok=True)
archive=Path(shutil.make_archive(str(delivery/'ZounD-1.0-Windows-x64'),'zip','dist','ZounD'))
sha=hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()
(delivery/'ZounD-1.0-SHA256.txt').write_text(f'{sha}  {archive.name}\n',encoding='utf-8')
print(json.dumps({'zip':str(archive.resolve()),'bytes':archive.stat().st_size,'sha256':sha}))
