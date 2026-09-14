from pathlib import Path
import hashlib
import re

INDEX=Path('index.html')
SW=Path('sw.js')
GIF=Path('assets/egypt/mage/power-special.gif')
MARKER='EGYPT MAGE DAMAGE-EDGE + SINGLE POWER CYCLE 2026-09-13'
SPEED_FACTOR=0.82

text=INDEX.read_text(encoding='utf-8')
if MARKER in text:
    print('Egypt mage damage-edge/power patch already applied.')
    raise SystemExit(0)


def rep(old,new,label,count=1):
    global text
    if old not in text:
        raise SystemExit(f'Missing anchor: {label}')
    text=text.replace(old,new,count)

# ---------------------------------------------------------
# 1) Emergency special triggers become damage-edge based.
#    Staying at <=50% HP or at 0 shield cannot repeatedly fire specials.
# ---------------------------------------------------------
rep(
"pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,",
"pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,\n egyptSpecialObservedHp:null,egyptSpecialObservedShield:null,egyptHpTriggerPending:false,egyptShieldTriggerPending:false,",
'entity Egypt mage trigger state'
)

rep(
"e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;",
"e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;\n if(e.clan==='egypt'){e.egyptSpecialObservedHp=e.hp;e.egyptSpecialObservedShield=e.shield;e.egyptHpTriggerPending=false;e.egyptShieldTriggerPending=false;}",
'spawn Egypt mage trigger baseline'
)

rep(
"   out.mageCycle=Number(e.mageCycle)||0;\n   if(e.pendingMageAttack){",
"   out.mageCycle=Number(e.mageCycle)||0;\n   out.egyptSpecialObservedHp=Number.isFinite(Number(e.egyptSpecialObservedHp))?Number(e.egyptSpecialObservedHp):null;\n   out.egyptSpecialObservedShield=Number.isFinite(Number(e.egyptSpecialObservedShield))?Number(e.egyptSpecialObservedShield):null;\n   out.egyptHpTriggerPending=!!e.egyptHpTriggerPending;\n   out.egyptShieldTriggerPending=!!e.egyptShieldTriggerPending;\n   if(e.pendingMageAttack){",
'network Egypt mage trigger state'
)

helper='''function updateEgyptMageDamageSpecialTriggers(e){
 if(!e||e.clan!=='egypt')return;
 const hp=Math.max(0,Number(e.hp)||0),shield=Math.max(0,Number(e.shield)||0);
 const maxHp=Math.max(1,Number(e.maxHp)||1);
 const prevHp=Number(e.egyptSpecialObservedHp);
 const prevShield=Number(e.egyptSpecialObservedShield);
 // Primeira observação/host novo só estabelece a linha de base; não inventa dano antigo.
 if(Number.isFinite(prevHp)){
   // HP só arma novamente quando houve NOVA perda de vida e o Mago está em <=50%.
   if(hp<prevHp&&hp<=maxHp*.50)e.egyptHpTriggerPending=true;
 }
 if(Number.isFinite(prevShield)){
   // Escudo só arma no evento de cruzar de >0 para 0. Permanecer zerado não rearma.
   if(prevShield>0&&shield<=0)e.egyptShieldTriggerPending=true;
 }
 e.egyptSpecialObservedHp=hp;
 e.egyptSpecialObservedShield=shield;
}
'''
anchor='function countLivingEgyptSummonsForMage(mageId){'
if anchor not in text: raise SystemExit('Missing anchor: Egypt mage summon counter')
text=text.replace(anchor,helper+anchor,1)

rep(
"   e.mageCycle=0;\n   addWarGoalProgress(e.team,'specials');",
"   e.mageCycle=0;\n   if(egypt){\n     // Consome os gatilhos emergenciais deste evento. Eles só rearmam com NOVO dano.\n     e.egyptHpTriggerPending=false;\n     e.egyptShieldTriggerPending=false;\n     e.egyptSpecialObservedHp=Math.max(0,Number(e.hp)||0);\n     e.egyptSpecialObservedShield=Math.max(0,Number(e.shield)||0);\n   }\n   addWarGoalProgress(e.team,'specials');",
'consume Egypt emergency triggers'
)

rep(
" const now=performance.now();\n if(e.pendingMageAttack){e.moving=false;return}",
" const now=performance.now();\n if(e.clan==='egypt')updateEgyptMageDamageSpecialTriggers(e);\n if(e.pendingMageAttack){e.moving=false;return}",
'capture damage while mage attack is active'
)

old_ai='''   if(e.clan==='egypt'){
     // Egito: o especial fica devido quando QUALQUER uma destas condições ocorre:
     // 1) 4 ataques normais completos (o 5º ataque elegível vira especial);
     // 2) o escudo chega a zero;
     // 3) a vida chega a 50% ou menos.
     // A trava continua INDIVIDUAL: contam apenas guerreiros que ESTE mago invocou.
     // Se ainda houver 2 ou mais vivos, o especial nem entra no estado visual e o mago
     // continua atacando normalmente até restar no máximo 1 dos seus próprios invocados.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const shieldDown=(Number(e.shield)||0)<=0;
     const halfHealth=Number(e.hp)<=Number(e.maxHp)*0.50;
     const specialDue=cycleDue||shieldDown||halfHealth;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''
new_ai='''   if(e.clan==='egypt'){
     // Egito: 4 normais continuam tornando o 5º ataque elegível especial.
     // Escudo zerado e HP <=50% agora são EVENTOS de dano, não estados permanentes:
     // sem novo dano, a mesma condição não dispara outro especial depois do cooldown.
     // Se o evento ocorrer enquanto há 2+ invocados próprios vivos, fica pendente sem trocar GIF;
     // quando restar <=1, um único especial consome os eventos pendentes.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const damageDue=!!e.egyptShieldTriggerPending||!!e.egyptHpTriggerPending;
     const specialDue=cycleDue||damageDue;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''
rep(old_ai,new_ai,'edge-trigger Egypt mage AI')

# ---------------------------------------------------------
# 2) Egypt special power is materially smaller and grows much less.
# ---------------------------------------------------------
old_size='''     // Cresce de forma contínua e um pouco mais que antes.
     const grow=.90+progress*.30;
     const size=(MAGE_SPECIAL_RADIUS*2)*zoom*grow,imgX=p.originX??e.x,imgY=p.originY??e.y;'''
new_size='''     // Poder do Egito é menor e quase não aumenta durante o GIF.
     // O Mago Guerreiro mantém o dimensionamento anterior.
     const egyptSpecial=e.clan==='egypt';
     const grow=egyptSpecial?(.94+progress*.08):(.90+progress*.30);
     const powerScale=egyptSpecial?.78:1;
     const size=(MAGE_SPECIAL_RADIUS*2)*zoom*grow*powerScale,imgX=p.originX??e.x,imgY=p.originY??e.y;'''
rep(old_size,new_size,'Egypt special power size/growth')

# Revision marker.
rep(
'/* EGYPT MAGE SHIELD + HALF-HP SPECIAL TRIGGERS 2026-09-13 */',
'/* EGYPT MAGE SHIELD + HALF-HP SPECIAL TRIGGERS 2026-09-13 */\n/* '+MARKER+' */',
'revision marker'
)

# ---------------------------------------------------------
# 3) Speed up the actual GIF frame delays, losslessly, and remove the GIF loop
#    application extension. Image data/palettes are copied byte-for-byte.
# ---------------------------------------------------------
def transform_gif_losslessly(raw: bytes):
    if raw[:6] not in (b'GIF87a',b'GIF89a'):
        raise SystemExit('Invalid GIF header')
    if len(raw)<13:
        raise SystemExit('GIF too short')
    pos=13
    packed=raw[10]
    if packed&0x80:
        pos += 3*(2**((packed&0x07)+1))
    out=bytearray(raw[:pos])
    total_cs=0
    frames=0
    removed_loop=False
    while pos<len(raw):
        tag=raw[pos]
        if tag==0x3B: # trailer
            out.extend(raw[pos:pos+1]);pos+=1;break
        if tag==0x21: # extension
            if pos+2>=len(raw): raise SystemExit('Truncated GIF extension')
            label=raw[pos+1]
            if label==0xF9: # Graphics Control Extension
                if pos+8>len(raw) or raw[pos+2]!=4: raise SystemExit('Malformed GCE')
                block=bytearray(raw[pos:pos+8])
                delay=block[4]|(block[5]<<8)
                if delay>0:
                    new_delay=max(1,int(round(delay*SPEED_FACTOR)))
                    block[4]=new_delay&0xFF;block[5]=(new_delay>>8)&0xFF
                else:
                    new_delay=0
                total_cs+=new_delay;frames+=1
                out.extend(block);pos+=8;continue
            # Generic extension: fixed-size first block followed by sub-blocks.
            if pos+3>len(raw): raise SystemExit('Truncated extension header')
            first_size=raw[pos+2]
            first_end=pos+3+first_size
            if first_end>len(raw): raise SystemExit('Truncated extension body')
            app_id=raw[pos+3:first_end] if label==0xFF else b''
            j=first_end
            while True:
                if j>=len(raw): raise SystemExit('Truncated extension sub-block')
                size=raw[j];j+=1
                if size==0: break
                j+=size
                if j>len(raw): raise SystemExit('Truncated extension payload')
            if label==0xFF and (app_id.startswith(b'NETSCAPE2.0') or app_id.startswith(b'ANIMEXTS1.0')):
                removed_loop=True
            else:
                out.extend(raw[pos:j])
            pos=j;continue
        if tag==0x2C: # image descriptor
            if pos+10>len(raw): raise SystemExit('Truncated image descriptor')
            desc_packed=raw[pos+9]
            j=pos+10
            if desc_packed&0x80:
                j += 3*(2**((desc_packed&0x07)+1))
            if j>=len(raw): raise SystemExit('Truncated local palette/LZW')
            j+=1 # LZW min code size
            while True:
                if j>=len(raw): raise SystemExit('Truncated image data')
                size=raw[j];j+=1
                if size==0: break
                j+=size
                if j>len(raw): raise SystemExit('Truncated image payload')
            out.extend(raw[pos:j]);pos=j;continue
        raise SystemExit(f'Unexpected GIF block tag 0x{tag:02x} at {pos}')
    if frames<1 or total_cs<1:
        raise SystemExit('No timed GIF frames found')
    return bytes(out),frames,total_cs*10,removed_loop

raw=GIF.read_bytes()
new_gif,frame_count,new_duration_ms,removed_loop=transform_gif_losslessly(raw)
GIF.write_bytes(new_gif)
new_rev=hashlib.sha256(new_gif).hexdigest()[:20]

# Accurate fallback duration even if the GIF runtime measurement has not finished yet.
text,n=re.subn(r'let EGYPT_MAGE_POWER_SPECIAL_DURATION=\d+;',f'let EGYPT_MAGE_POWER_SPECIAL_DURATION={new_duration_ms};',text,count=1)
if n!=1: raise SystemExit('Could not update Egypt special power fallback duration')

old_rev='60bbad838976f14c156e'
if old_rev not in text:
    raise SystemExit('Old Egypt special power revision not found in index')
text=text.replace(old_rev,new_rev,1)

sw=SW.read_text(encoding='utf-8')
if old_rev not in sw:
    raise SystemExit('Old Egypt special power revision not found in service worker')
sw=sw.replace(old_rev,new_rev,1)

INDEX.write_text(text,encoding='utf-8')
SW.write_text(sw,encoding='utf-8')
print(f'Updated Egypt special power: {frame_count} timed frames, {new_duration_ms} ms, loop extension removed={removed_loop}, revision={new_rev}')
