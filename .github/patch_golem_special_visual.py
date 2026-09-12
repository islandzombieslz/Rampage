from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')

old="""function validGifDuration(ms,fallback){
 return Number.isFinite(ms)&&ms>=250&&ms<=20000?ms:fallback;
}
"""
new="""function validGifDuration(ms,fallback){
 return Number.isFinite(ms)&&ms>=250&&ms<=20000?ms:fallback;
}

// Alguns GIFs exportados usam um frame final com delay enorme apenas para
// segurar a última pose antes do loop. Esse tempo não deve manter o estado
// de ataque ativo. Para animações de golpe, soma só os frames realmente ativos.
function gifActionDurationMs(buffer,maxFrameDelayMs=2000){
 const b=new Uint8Array(buffer);let total=0;
 for(let i=0;i+7<b.length;i++){
   if(b[i]===0x21&&b[i+1]===0xF9&&b[i+2]===0x04){
     const delayMs=(b[i+4]|(b[i+5]<<8))*10;
     if(delayMs<=maxFrameDelayMs)total+=delayMs;
   }
 }
 return total;
}
"""
if t.count(old)!=1:
    raise SystemExit(f'validGifDuration anchor count={t.count(old)}')
t=t.replace(old,new,1)

old="const duration=gifCycleDurationMs(buf);"
new="const duration=key==='golemSpecial'?gifActionDurationMs(buf):gifCycleDurationMs(buf);"
if t.count(old)!=1:
    raise SystemExit(f'gif duration anchor count={t.count(old)}')
t=t.replace(old,new,1)

old=".entity-visual.brown-warrior-visual .entity-body{left:0;top:-9px;width:110px;height:110px;object-fit:contain}"
new=".entity-visual.brown-warrior-visual .entity-body{left:0;top:0;width:110px;height:110px;object-fit:contain}"
if t.count(old)!=1:
    raise SystemExit(f'brown body CSS anchor count={t.count(old)}')
t=t.replace(old,new,1)

p.write_text(t,encoding='utf-8')
print('Patched Golem special active duration and Brown Warrior vertical offset.')
