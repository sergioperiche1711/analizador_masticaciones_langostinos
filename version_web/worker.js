/* The file stays in the browser. WAV is decoded incrementally in a worker. */
self.onmessage = async ({data}) => { try { await analyze(data); } catch (e) { self.postMessage({error: e.message || 'No se pudo leer el archivo WAV.'}); } };
const fourcc = (v, offset) => String.fromCharCode(...new Uint8Array(v.buffer, v.byteOffset + offset, 4));
async function view(file, start, length) { return new DataView(await file.slice(start, start + length).arrayBuffer()); }
async function analyze({file, sensitivity, distance, highpass}) {
  const head = await view(file,0,12);
  if (head.byteLength < 12 || fourcc(head,0)!=='RIFF' || fourcc(head,8)!=='WAVE') throw Error('Este archivo no es un WAV RIFF compatible.');
  let pos=12, format=null, dataStart=null, dataLength=null;
  while(pos+8<=file.size) {
    const h=await view(file,pos,8), id=fourcc(h,0), size=h.getUint32(4,true), start=pos+8;
    if(start+size>file.size) throw Error('El WAV está incompleto o tiene un encabezado inválido.');
    if(id==='fmt ') {
      if(size<16) throw Error('El formato WAV es inválido.');
      const f=await view(file,start,Math.min(size,40));
      let code=f.getUint16(0,true); const channels=f.getUint16(2,true), rate=f.getUint32(4,true), align=f.getUint16(12,true), bits=f.getUint16(14,true);
      if(code===0xfffe && size>=40) { const guid=Array.from(new Uint8Array(f.buffer, f.byteOffset+24, 16)); const tail=[0,0,16,0,128,0,0,170,0,56,155,113]; if(guid.slice(4).every((x,i)=>x===tail[i])) code=f.getUint32(24,true); }
      format={code,channels,rate,align,bits};
    }
    if(id==='data') { dataStart=start; dataLength=size; }
    if(format && dataStart!==null) break;
    pos=start+size+(size%2);
  }
  if(!format || dataStart===null) throw Error('No se encontró el formato o el audio en el WAV.');
  const {code,channels,rate,align,bits}=format, bytes=bits/8;
  if(!channels || !rate || !Number.isInteger(bytes) || align!==bytes*channels || !((code===1 && [8,16,24,32].includes(bits)) || (code===3 && [32,64].includes(bits)))) throw Error('Formato WAV no admitido. Usa WAV PCM de 8, 16, 24 o 32 bits, o WAV flotante de 32 o 64 bits.');
  if(highpass >= rate/2) throw Error(`El filtro debe ser menor que ${rate/2} Hz (la mitad de la frecuencia de muestreo).`);
  const totalFrames=Math.floor(dataLength/align); if(!totalFrames) throw Error('El archivo no contiene muestras de audio.');
  const duration=totalFrames/rate, frameWidth=Math.max(1,Math.round(rate*.001)), frameSeconds=frameWidth/rate;
  let sums=0, samples=0, env=[], counts=[], frameIndex=0, minute=0, prevX=0, prevY=0;
  // One-pole high-pass filter. This is not identical to the Python filter.
  const a=highpass ? Math.exp(-2*Math.PI*highpass/rate) : 0;
  function median(values){if(!values.length)return 0;values.sort((x,y)=>x-y);const m=values.length>>1;return values.length%2?values[m]:(values[m-1]+values[m])/2}
  function finish() {
    if(!env.length){counts.push(0);return;}
    const med=median(env.slice()), mad=median(env.map(x=>Math.abs(x-med))), max=env.reduce((a,b)=>Math.max(a,b),0), threshold=med+Math.max(sensitivity*1.4826*mad,max*1e-6,1.1920929e-7);
    let candidates=[];
    for(let i=1;i<env.length-1;i++) if(env[i]>=threshold && env[i]>env[i-1] && env[i]>=env[i+1]) candidates.push(i);
    // As with SciPy, keep the strongest peak when candidates are too close.
    candidates.sort((a,b)=>env[b]-env[a]); const selected=new Uint8Array(env.length), gap=Math.max(1,Math.ceil(distance/1000/frameSeconds));
    for(const i of candidates){let valid=true;for(let j=Math.max(0,i-gap+1);j<=Math.min(env.length-1,i+gap-1);j++)if(selected[j]){valid=false;break}if(valid)selected[i]=1;}
    counts.push(selected.reduce((sum,x)=>sum+x,0)); env=[];
  }
  function addEnvelope(value) {const minuteForFrame=Math.floor(frameIndex*frameSeconds/60);if(minuteForFrame!==minute){finish();minute=minuteForFrame}env.push(value);frameIndex++;}
  const blockFrames=Math.max(1,Math.floor(1048576/align));
  for(let offset=0;offset<totalFrames;offset+=blockFrames){
    const n=Math.min(blockFrames,totalFrames-offset), chunk=await view(file,dataStart+offset*align,n*align);
    for(let i=0;i<n;i++){
      let x=0;
      for(let ch=0;ch<channels;ch++){
        const p=i*align+ch*bytes; let v;
        if(code===3) v=bits===32?chunk.getFloat32(p,true):chunk.getFloat64(p,true);
        else if(bits===8)v=(chunk.getUint8(p)-128)/128;
        else if(bits===16)v=chunk.getInt16(p,true)/32768;
        else if(bits===24){v=chunk.getUint8(p)|(chunk.getUint8(p+1)<<8)|(chunk.getUint8(p+2)<<16);if(v&0x800000)v-=0x1000000;v/=8388608;}
        else v=chunk.getInt32(p,true)/2147483648;
        if(!Number.isFinite(v)) throw Error('El WAV contiene muestras no válidas.');x+=v/channels;
      }
      if(highpass){const y=a*(prevY+x-prevX);prevX=x;prevY=y;x=y;}
      sums+=x*x; samples++;if(samples===frameWidth){addEnvelope(Math.sqrt(sums/samples));sums=0;samples=0;}
    }
    self.postMessage({progress:(offset+n)/totalFrames});
  }
  if(samples) addEnvelope(Math.sqrt(sums/samples)); if(env.length) finish();
  self.postMessage({counts,duration,sampleRate:rate,channels});
}
