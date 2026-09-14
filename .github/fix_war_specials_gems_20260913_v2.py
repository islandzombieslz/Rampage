from pathlib import Path
import hashlib
import re

INDEX = Path('index.html')
SW = Path('sw.js')
GIF = Path('assets/egypt/mage/power-special.gif')
text = INDEX.read_text(encoding='utf-8')
sw = SW.read_text(encoding='utf-8')
MARKER = 'WAR SPECIALS + GEMS STABILITY 2026-09-13'


def replace_once(old, new, label):
    global text
    if new in text:
        return
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 old block, found {count}')
    text = text.replace(old, new, 1)


def insert_before(anchor, addition, label):
    global text
    if addition.strip() in text:
        return
    count = text.count(anchor)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly 1 anchor, found {count}')
    text = text.replace(anchor, addition + anchor, 1)


def replace_between(start_anchor, end_anchor, new_block, label):
    global text
    if new_block.strip() in text:
        return
    start = text.find(start_anchor)
    end = text.find(end_anchor, start + 1)
    if start < 0 or end < 0:
        raise SystemExit(f'{label}: anchors not found')
    text = text[:start] + new_block + text[end:]


# ---------- marker ----------
if MARKER not in text:
    anchor = '/* EGYPT MAGE DAMAGE-EDGE + SINGLE POWER CYCLE 2026-09-13 */'
    if anchor not in text:
        raise SystemExit('marker anchor missing')
    text = text.replace(anchor, anchor + '\n/* ' + MARKER + ' */', 1)


# ---------- stable starting gems, config cap 5000 only ----------
insert_before(
    'function clamp(v,a,b){return Math.max(a,Math.min(b,v))}\n',
    '''function normalizeWarStartingGems(value){
 const n=Number(value);
 const safe=Number.isFinite(n)?n:500;
 return Math.round(clamp(safe,300,5000)/100)*100;
}
''',
    'normalizeWarStartingGems'
)

replace_once(
    "if(b.dataset.target==='gems') state.gems=clamp(state.gems+dir*100,300,3000);",
    "if(b.dataset.target==='gems') state.gems=normalizeWarStartingGems((Number(state.gems)||300)+dir*100);",
    'gems stepper limit'
)

replace_once(
    '''        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{
          this.roomCache[key]=s.exists()?s.val():null;''',
    '''        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{
          if(this.roomId!==code)return;
          this.roomCache[key]=s.exists()?s.val():null;''',
    'stale room callback guard'
)

replace_once(
    '''      // Clique repetido durante a criação reutiliza a mesma sala, nunca cria outra por cima.
      if(this.roomId)return {code:this.roomId,offline:false,reused:true};
      const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:snapshot.gems};''',
    '''      const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:normalizeWarStartingGems(snapshot.gems)};
      // Uma sala antiga nunca pode reutilizar configurações anteriores numa criação nova.
      if(this.roomId)await this.leaveRoom();''',
    'fresh room settings'
)

replace_once(
    ''' if(room.settings){state.mode=room.settings.mode??state.mode;state.pveTime=room.settings.pveTime??state.pveTime;state.warTime=room.settings.warTime??state.warTime;state.rounds=room.settings.rounds??state.rounds;state.difficulty=room.settings.difficulty??state.difficulty;state.speed=room.settings.speed??state.speed;state.gems=room.settings.gems??state.gems}''',
    ''' if(room.settings){
   state.mode=room.settings.mode??state.mode;state.pveTime=room.settings.pveTime??state.pveTime;state.warTime=room.settings.warTime??state.warTime;state.rounds=room.settings.rounds??state.rounds;state.difficulty=room.settings.difficulty??state.difficulty;state.speed=room.settings.speed??state.speed;
   state.gems=normalizeWarStartingGems(room.settings.gems??state.gems);
   const gemsLabel=$('#gemsVal');if(gemsLabel)gemsLabel.textContent=state.gems;
 }''',
    'room settings gems sync'
)

replace_once(
    '''    const res=await NetworkAdapter.createRoom({...state}); state.roomCode=res.code; $('#roomCode').textContent=res.code;''',
    '''    if(state.mode==='war'){
      const visibleGems=Number($('#gemsVal')?.textContent);
      state.gems=normalizeWarStartingGems(Number.isFinite(visibleGems)?visibleGems:state.gems);
      $('#gemsVal').textContent=state.gems;
    }
    const roomSnapshot={...state,gems:normalizeWarStartingGems(state.gems)};
    const res=await NetworkAdapter.createRoom(roomSnapshot); state.roomCode=res.code; $('#roomCode').textContent=res.code;''',
    'create room gems freeze'
)

replace_once(
    '''function startWarMode(){
 state.round=1;state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;state.running=true;state.entities=[];state.particles=[];state.dragonProjectiles=[];''',
    '''function startWarMode(){
 state.gems=normalizeWarStartingGems(state.gems);
 state.round=1;state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;state.running=true;state.entities=[];state.particles=[];state.dragonProjectiles=[];''',
    'war start gems normalization'
)


# ---------- Warrior Mage 50%-HP edge + 5 normals then 6th special ----------
replace_once(
    ''' pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,
 egyptSpecialObservedHp:null,egyptSpecialObservedShield:null,egyptHpTriggerPending:false,egyptShieldTriggerPending:false,''',
    ''' pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,
 warriorMageSpecialObservedHp:null,warriorMageHpTriggerPending:false,
 egyptSpecialObservedHp:null,egyptSpecialObservedShield:null,egyptHpTriggerPending:false,egyptShieldTriggerPending:false,''',
    'mage base trigger fields'
)

replace_once(
    '''   out.mageCycle=Number(e.mageCycle)||0;
   out.egyptSpecialObservedHp=Number.isFinite(Number(e.egyptSpecialObservedHp))?Number(e.egyptSpecialObservedHp):null;''',
    '''   out.mageCycle=Number(e.mageCycle)||0;
   out.warriorMageSpecialObservedHp=Number.isFinite(Number(e.warriorMageSpecialObservedHp))?Number(e.warriorMageSpecialObservedHp):null;
   out.warriorMageHpTriggerPending=!!e.warriorMageHpTriggerPending;
   out.egyptSpecialObservedHp=Number.isFinite(Number(e.egyptSpecialObservedHp))?Number(e.egyptSpecialObservedHp):null;''',
    'mage trigger network fields'
)

replace_once(
    ''' e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;
 if(e.clan==='egypt'){e.egyptSpecialObservedHp=e.hp;e.egyptSpecialObservedShield=e.shield;e.egyptHpTriggerPending=false;e.egyptShieldTriggerPending=false;}
 state.entities.push(e);return e;''',
    ''' e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;
 if(e.clan==='egypt'){e.egyptSpecialObservedHp=e.hp;e.egyptSpecialObservedShield=e.shield;e.egyptHpTriggerPending=false;e.egyptShieldTriggerPending=false;}
 else{e.warriorMageSpecialObservedHp=e.hp;e.warriorMageHpTriggerPending=false;}
 state.entities.push(e);return e;''',
    'spawn mage trigger init'
)

replace_once(
    '''   if(egypt){
     // Consome os gatilhos emergenciais deste evento. Eles só rearmam com NOVO dano.
     e.egyptHpTriggerPending=false;
     e.egyptShieldTriggerPending=false;
     e.egyptSpecialObservedHp=Math.max(0,Number(e.hp)||0);
     e.egyptSpecialObservedShield=Math.max(0,Number(e.shield)||0);
   }
   addWarGoalProgress(e.team,'specials');''',
    '''   if(egypt){
     // Consome os gatilhos emergenciais deste evento. Eles só rearmam com NOVO dano.
     e.egyptHpTriggerPending=false;
     e.egyptShieldTriggerPending=false;
     e.egyptSpecialObservedHp=Math.max(0,Number(e.hp)||0);
     e.egyptSpecialObservedShield=Math.max(0,Number(e.shield)||0);
   }else{
     // 50% do Mago Guerreiro é evento de cruzamento, não estado permanente.
     e.warriorMageHpTriggerPending=false;
     e.warriorMageSpecialObservedHp=Math.max(0,Number(e.hp)||0);
   }
   addWarGoalProgress(e.team,'specials');''',
    'consume warrior mage hp trigger'
)

insert_before(
    'function countLivingEgyptSummonsForMage(mageId){',
    '''function updateWarriorMageDamageSpecialTrigger(e){
 if(!e||e.clan==='egypt')return;
 const hp=Math.max(0,Number(e.hp)||0),maxHp=Math.max(1,Number(e.maxHp)||1);
 const prevHp=Number(e.warriorMageSpecialObservedHp);
 // Arma uma vez ao cruzar de >50% para <=50% por dano.
 // Permanecer abaixo de 50% não dispara especiais repetidos.
 if(Number.isFinite(prevHp)&&prevHp>maxHp*.50&&hp<=maxHp*.50&&hp<prevHp){
   e.warriorMageHpTriggerPending=true;
 }
 e.warriorMageSpecialObservedHp=hp;
}
''',
    'warrior mage hp trigger helper'
)


# ---------- Egypt Mage special: 3 shieldless summons ----------
replace_between(
    'function spawnEgyptMageWarriors(e,p){',
    'function updateMageAttackState(e,now){',
    '''function spawnEgyptMageWarriors(e,p){
 const ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;
 const base=(Number(e.mageAttackSerial)||0)*.37;
 for(let i=0;i<3;i++){
   const angle=base+(Math.PI*2/3)*i;
   const radius=62+(i%2)*30;
   const x=clamp(ox+Math.cos(angle)*radius,45,state.world.w-45);
   const y=clamp(oy+Math.sin(angle)*radius,45,state.world.h-45);
   const variant=i%2===0?'male':'female';
   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);
   summon.shield=0;
   summon.maxShield=0;
 }
}
''',
    'three shieldless Egypt summons'
)


# ---------- coherent Mage AI rules ----------
replace_between(
    'function aiFightMage(e,dt,forcedTeam,preparedCandidates=null){',
    'function aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates=null){',
    '''function aiFightMage(e,dt,forcedTeam,preparedCandidates=null){
 if(!e.alive||e.knockTime>0){e.moving=false;return}
 const now=performance.now();
 if(e.clan==='egypt')updateEgyptMageDamageSpecialTriggers(e);
 else updateWarriorMageDamageSpecialTrigger(e);
 if(e.pendingMageAttack){e.moving=false;return}
 const candidates=preparedCandidates||state.entities;
 const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);
 if(!target){e.moving=false;e.target=null;return}
 e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;
 if(e.attackCooldown<=0&&!e.pendingMageAttack){
   if(e.clan==='egypt'){
     // Egito: 4 normais; o 5º ataque elegível é especial.
     // Gatilhos de escudo/HP continuam sendo eventos e a trava de invocados é individual.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const damageDue=!!e.egyptShieldTriggerPending||!!e.egyptHpTriggerPending;
     const specialDue=cycleDue||damageDue;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{
     // Mago Guerreiro: 5 normais; o 6º ataque elegível é especial.
     // Também dispara uma vez ao cruzar 50% de HP. A antiga regra de aglomeração foi removida.
     const cycleDue=(Number(e.mageCycle)||0)>=5;
     const hpDue=!!e.warriorMageHpTriggerPending;
     if(e.specialCooldown<=0&&(cycleDue||hpDue)){
       if(startMageAttack(e,'special',target))return;
     }
   }
   if(d>=185&&d<=285){startMageAttack(e,'normal',target);return}
 }
 if(d<175){e.x-=dx/d*e.speed*dt;e.y-=dy/d*e.speed*dt;e.moving=true}
 else if(d>285){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}
 else e.moving=false;
 e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);
}


''',
    'mage AI rules'
)


# ---------- 50% knockback force while target is in any special ----------
insert_before(
    'function applyCombatHit(target,attacker,amount,options={}){',
    '''function entityHasActiveSpecial(e,now=performance.now()){
 if(!e?.alive)return false;
 if(e.type==='mage')return e.pendingMageAttack?.kind==='special'&&Number(e.pendingMageAttack.endAt)>now;
 if(e.type==='golem')return e.pendingGolemAttack?.kind==='special'&&Number(e.pendingGolemAttack.endAt)>now;
 if(e.type==='brownWarrior')return e.pendingBrownAttack?.kind==='special'&&Number(e.pendingBrownAttack.endAt)>now;
 if(e.type==='king')return !!e.pendingKingSpecial&&Number(e.pendingKingSpecial.endAt)>now;
 return false;
}
''',
    'special knockback helper'
)

replace_once(
    ''' }
 if(applyKnockback){
   target.knockTime=knockTime;''',
    ''' }
 // Durante qualquer especial ativo, o alvo recebe só 50% da força de empurrão.
 if(entityHasActiveSpecial(target))knockForce*=.50;
 if(applyKnockback){
   target.knockTime=knockTime;''',
    'special knockback reduction'
)


# ---------- Egypt special power much smaller ----------
replace_once(
    '''     const grow=egyptSpecial?(.94+progress*.08):(.90+progress*.30);
     const powerScale=egyptSpecial?.78:1;''',
    '''     const grow=egyptSpecial?(.96+progress*.02):(.90+progress*.30);
     const powerScale=egyptSpecial?.50:1;''',
    'Egypt power scale'
)


# ---------- Trim Egypt power to one visual revolution (~25 frames) ----------
def subblocks_end(data, pos):
    while True:
        if pos >= len(data):
            raise SystemExit('GIF subblock overflow')
        size = data[pos]
        pos += 1
        if size == 0:
            return pos
        pos += size
        if pos > len(data):
            raise SystemExit('GIF subblock data overflow')


def trim_gif_one_cycle(data, max_frames=25):
    if data[:6] not in (b'GIF87a', b'GIF89a'):
        raise SystemExit('Invalid GIF header')
    if len(data) < 13:
        raise SystemExit('GIF too short')
    packed = data[10]
    pos = 13
    if packed & 0x80:
        pos += 3 * (2 ** ((packed & 0x07) + 1))

    # Match Warrior Mage behavior: GIF itself may loop; JS removes it before cycle 2.
    out = bytearray(data[:pos])
    out.extend(b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
    frames = 0

    while pos < len(data):
        if frames >= max_frames:
            break
        marker = data[pos]
        if marker == 0x3B:
            break
        if marker == 0x21:
            start = pos
            if pos + 2 > len(data):
                raise SystemExit('Bad GIF extension')
            label = data[pos + 1]
            pos += 2
            if label == 0xF9:
                if pos >= len(data):
                    raise SystemExit('Bad GCE')
                size = data[pos]
                pos += 1 + size
                if pos >= len(data) or data[pos] != 0:
                    raise SystemExit('Bad GCE terminator')
                pos += 1
            else:
                pos = subblocks_end(data, pos)
            block = data[start:pos]
            if b'NETSCAPE2.0' not in block and b'ANIMEXTS1.0' not in block:
                out.extend(block)
            continue
        if marker == 0x2C:
            start = pos
            if pos + 10 > len(data):
                raise SystemExit('Bad image descriptor')
            packed_img = data[pos + 9]
            pos += 10
            if packed_img & 0x80:
                pos += 3 * (2 ** ((packed_img & 0x07) + 1))
            if pos >= len(data):
                raise SystemExit('Missing LZW code size')
            pos += 1
            pos = subblocks_end(data, pos)
            out.extend(data[start:pos])
            frames += 1
            continue
        raise SystemExit(f'Unexpected GIF marker 0x{marker:02x} at {pos}')

    if frames != max_frames:
        raise SystemExit(f'Expected {max_frames} frames, got {frames}')
    out.append(0x3B)
    return bytes(out), frames


def gif_duration_ms(data):
    total = 0
    for i in range(len(data) - 7):
        if data[i:i+3] == b'\x21\xf9\x04':
            total += (data[i+4] | (data[i+5] << 8)) * 10
    return total


raw = GIF.read_bytes()
# Runtime is still the original 73-frame asset when this patch first runs.
# If the exact 25-frame output already exists, retain it idempotently.
frame_markers = raw.count(b'\x2c')
if frame_markers == 25 and b'NETSCAPE2.0' in raw:
    trimmed = raw
    frame_count = 25
else:
    trimmed, frame_count = trim_gif_one_cycle(raw, 25)
    GIF.write_bytes(trimmed)

power_ms = gif_duration_ms(trimmed)
if not (650 <= power_ms <= 950):
    raise SystemExit(f'Unexpected trimmed Egypt power duration: {power_ms} ms')
text = re.sub(r'let EGYPT_MAGE_POWER_SPECIAL_DURATION=\d+;', f'let EGYPT_MAGE_POWER_SPECIAL_DURATION={power_ms};', text, count=1)

revision = hashlib.sha256(trimmed).hexdigest()[:20]
pattern = r'("assets/egypt/mage/power-special\.gif":")[0-9a-f]+(")'
text, n1 = re.subn(pattern, rf'\g<1>{revision}\g<2>', text, count=1)
sw, n2 = re.subn(pattern, rf'\g<1>{revision}\g<2>', sw, count=1)
if n1 != 1 or n2 != 1:
    raise SystemExit(f'Failed to update asset revisions index={n1} sw={n2}')

INDEX.write_text(text, encoding='utf-8')
SW.write_text(sw, encoding='utf-8')
print(f'Applied patch. Egypt power: {frame_count} frames, {power_ms} ms, revision={revision}')
