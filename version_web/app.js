const $ = id => document.getElementById(id);
let selected = null, worker = null, result = null;
$('audio').addEventListener('change', e => {
  selected = e.target.files[0] || null;
  $('filename').textContent = selected ? selected.name : 'Selecciona tu grabación';
  $('fileinfo').textContent = selected ? `${(selected.size / 1048576).toFixed(1)} MB · WAV` : 'Compatible con WAV PCM y flotante sin comprimir.';
  $('analyze').disabled = !selected;
});
$('analyze').addEventListener('click', () => {
  const sensitivity = Number($('sensitivity').value), distance = Number($('distance').value), highpass = Number($('highpass').value);
  if (!selected || !Number.isFinite(sensitivity) || sensitivity <= 0 || !Number.isFinite(distance) || distance < 1 || !Number.isFinite(highpass) || highpass < 0) { alert('Revisa que los parámetros tengan valores válidos.'); return; }
  if (!window.Worker) { alert('Tu navegador no admite el procesamiento necesario.'); return; }
  $('analyze').disabled = true; $('progressArea').hidden = false; $('output').hidden = true; $('empty').hidden = false; $('status').textContent = 'Preparando audio…'; $('bar').style.width = '0%';
  try { worker = new Worker('worker.js'); } catch (e) { fail('No se pudo iniciar el análisis. Abre la página con un servidor local; revisa el archivo LEEME.'); return; }
  worker.onmessage = ({data}) => {
    if (data.error) { fail(data.error); return; }
    if (data.progress !== undefined) { const pct = Math.round(data.progress * 100); $('bar').style.width = pct + '%'; $('percentage').textContent = pct + ' %'; $('status').textContent = 'Analizando grabación…'; return; }
    result = data; worker.terminate(); worker = null; $('analyze').disabled = false; $('status').textContent = 'Análisis completado'; $('percentage').textContent = '100 %'; $('bar').style.width = '100%'; showResult();
  };
  worker.onerror = () => fail('No se pudo iniciar el análisis. Revisa que la página esté abierta desde un servidor local.');
  worker.postMessage({file: selected, sensitivity, distance, highpass});
});
function fail(message) { if (worker) worker.terminate(); worker = null; $('analyze').disabled = !selected; $('status').textContent = 'No se pudo analizar'; alert(message); }
function showResult() {
  $('empty').hidden = true; $('output').hidden = false;
  $('total').textContent = result.counts.reduce((a,b)=>a+b,0).toLocaleString('es-PE');
  const sec = Math.floor(result.duration); $('duration').textContent = `${Math.floor(sec/60)}:${String(sec%60).padStart(2,'0')}`;
  $('rate').textContent = (result.sampleRate / 1000).toLocaleString('es-PE', {maximumFractionDigits:2});
  $('rows').replaceChildren(); result.counts.forEach((count,i)=> { const tr = document.createElement('tr'); [i+1, `${Math.min(60, Math.max(0,result.duration-i*60)).toFixed(1)} s`, count].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td)});$('rows').append(tr) });
  draw();
}
function draw() {
  if (!result || $('output').hidden) return;
  const canvas = $('chart'), rect = canvas.getBoundingClientRect(), scale = window.devicePixelRatio || 1; canvas.width = Math.round(rect.width*scale); canvas.height = Math.round(rect.height*scale);
  const c = canvas.getContext('2d'); c.scale(scale,scale); const w=rect.width,h=rect.height,left=38,top=20,bottom=35, plotW=w-left-10, plotH=h-top-bottom,max=Math.max(1,...result.counts);
  c.font='10px Arial'; c.fillStyle='#8a9e95'; c.strokeStyle='#edf1ec'; for(let i=0;i<=4;i++){const y=top+plotH*i/4;c.beginPath();c.moveTo(left,y);c.lineTo(w-10,y);c.stroke();c.fillText(String(Math.round(max*(1-i/4))),2,y+3)}
  const slot=plotW/result.counts.length; c.fillStyle='#4d9a79';result.counts.forEach((v,i)=>{let bh=plotH*v/max;c.fillRect(left+i*slot+slot*.13,top+plotH-bh,Math.max(1,slot*.74),bh)});
  c.fillStyle='#8a9e95';const stride=Math.max(1,Math.ceil(result.counts.length/12));result.counts.forEach((_,i)=>{if(i%stride===0)c.fillText(String(i+1),left+i*slot, h-14)});
}
window.addEventListener('resize',draw);
$('download').addEventListener('click',()=>{if(!result)return; let lines=['Minuto;Duración (s);Clics detectados'];result.counts.forEach((n,i)=>lines.push(`${i+1};${Math.min(60,Math.max(0,result.duration-i*60)).toFixed(3).replace('.',',')};${n}`));const a=document.createElement('a');a.href=URL.createObjectURL(new Blob(['\ufeff'+lines.join('\r\n')],{type:'text/csv;charset=utf-8'}));a.download=selected.name.replace(/\.[^.]+$/,'')+'_clics.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)});
