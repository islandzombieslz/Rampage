from pathlib import Path
import hashlib
import re

INDEX=Path('index.html')
SW=Path('sw.js')
GIF=Path('assets/egypt/mage/power-special.gif')
text=INDEX.read_text(encoding='utf-8')
sw=SW.read_text(encoding='utf-8')

MARKER='WAR SPECIALS + GEMS STABILITY 2026-09-13'


def replace_once(old,new,label):
    global text
    if new in text:
        return
    n=text.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected exactly 1 old block, found {n}')
    text=text.replace(old,new,1)


def insert_before(anchor,addition,label):
    global text
    if addition.strip() in text:
        return
    n=text.count(anchor)
    if n!=1:
        raise SystemExit(f'{label}: anchor count {n}')
    text=text.replace(anchor,addition+anchor,1)


def replace_between(start_anchor,end_anchor,new_block,label):
    global text
    if new_block.strip() in text:
        return
    start=text.find(start_anchor)
    end=text.find(end_anchor,start+1)
    if start<0 or end<0:
        raise SystemExit(f'{label}: anchors not found')
    text=text[:start]+new_block+text[end:]


# Marker for later validation.
if MARKER not in text:
    anchor='/* EGYPT MAGE DAMAGE-EDGE + SINGLE POWER CYCLE 2026-09-13 */'
    if anchor not in text:
        raise SystemExit('marker anchor missing')
    text=text.replace(anchor,anchor+'\n/* '+MARKER+' */',1)

# Starting gems are configuration-only capped at 5k. Match gems remain uncapped.
insert_before(
    'function clamp(v,a,b){return Math.max(a,Math.min(b,v))}\n',
    "function normalizeWarStartingGems(value){\n const n=Number(value);\n const safe=Number.isFinite(n)?n:500;\n return Math.round(clamp(safe,300,5000)/100)*100;\n}\n",
    'normalizeWarStartingGems'
)
replace_once(
    "if(b.dataset.target==='gems') state.gems=clamp(state.gems+dir*100,300,3000);",
    "if(b.dataset.target==='gems') state.gems=normalizeWarStartingGems((Number(state.gems)||300)+dir*100);",
    'gems stepper limit'
)

# Never let callbacks from a room already left overwrite current configuration.
replace_once(
    "        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{\n          this.roomCache[key]=s.exists()?s.val():null;",
    "        const unsubscribe=F.onValue(F.ref(F.firebaseDb,`rooms/${code}/${key}`),s=>{\n          if(this.roomId!==code)return;\n          this.roomCache[key]=s.exists()?s.val():null;",
    'stale room callback guard'
)

# A lingering room must never silently reuse old settings. Close it and create a fresh room.
replace_once(
    "      // Clique repetido durante a criação reutiliza a mesma sala, nunca cria outra por cima.\n      if(this.roomId)return {code:this.roomId,offline:false,reused:true};\n      const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:snapshot.gems};",
    "      const settings={mode:snapshot.mode,pveTime:snapshot.pveTime,warTime:snapshot.warTime,rounds:snapshot.rounds,difficulty:snapshot.difficulty,speed:snapshot.speed,gems:normalizeWarStartingGems(snapshot.gems)};\n      // Se uma sala antiga ainda estiver ligada por atraso de navegação, encerra antes de criar.\n      // Isso impede reutilizar settings antigos (principalmente gemas) numa partida nova.\n      if(this.roomId)await this.leaveRoom();",
    'fresh room settings'
)

# Keep displayed config and room state aligned.
replace_once(
    " if(room.settings){state.mode=room.settings.mode??state.mode;state.pveTime=room.settings.pveTime??state.pveTime;state.warTime=room.settings.warTime??state.warTime;state.rounds=room.settings.rounds??state.rounds;state.difficulty=room.settings.difficulty??state.difficulty;state.speed=room.settings.speed??state.speed;state.gems=room.settings.gems??state.gems}",
    " if(room.settings){\n   state.mode=room.settings.mode??state.mode;state.pveTime=room.settings.pveTime??state.pveTime;state.warTime=room.settings.warTime??state.warTime;state.rounds=room.settings.rounds??state.rounds;state.difficulty=room.settings.difficulty??state.difficulty;state.speed=room.settings.speed??state.speed;\n   state.gems=normalizeWarStartingGems(room.settings.gems??state.gems);\n   const gemsLabel=$('#gemsVal');if(gemsLabel)gemsLabel.textContent=state.gems;\n }",
    'room settings gems sync'
)

# On create, the number the user can actually see wins over any stale internal value.
replace_once(
    "    const res=await NetworkAdapter.createRoom({...state}); state.roomCode=res.code; $('#roomCode').textContent=res.code;",
    "    if(state.mode==='war'){\n      const visibleGems=Number($('#gemsVal')?.textContent);\n      state.gems=normalizeWarStartingGems(Number.isFinite(visibleGems)?visibleGems:state.gems);\n      $('#gemsVal').textContent=state.gems;\n    }\n    const roomSnapshot={...state,gems:normalizeWarStartingGems(state.gems)};\n    const res=await NetworkAdapter.createRoom(roomSnapshot); state.roomCode=res.code; $('#roomCode').textContent=res.code;",
    'create room gems freeze'
)
replace_once(
    "function startWarMode(){\n state.round=1;state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;state.running=true;state.entities=[];state.particles=[];state.dragonProjectiles=[];",
    "function startWarMode(){\n state.gems=normalizeWarStartingGems(state.gems);\n state.round=1;state.phase='prep';state.prepLeft=15;state.timeLeft=state.warTime;state.running=true;state.entities=[];state.particles=[];state.dragonProjectiles=[];",
    'war start gems normalization'
)

# Generic Warrior Mage gets a one-shot 50% HP trigger in addition to 5-normal -> 6th-special cycle.
replace_once(
    " pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,\n egyptSpecialObservedHp:null,egyptSpecialObservedShield:null,egyptHpTriggerPending:false,egyptShieldTriggerPending:false,",
    " pendingMageAttack:null,mageAttackKind:null,mageAttackSerial:0,mageCycle:0,\n warriorMageSpecialObservedHp:null,warriorMageHpTriggerPending:false,\n egyptSpecialObservedHp:null,egyptSpecialObservedShield:null,egyptHpTriggerPending:false,egyptShieldTriggerPending:false,",
    'mage base trigger fields'
)
replace_once(
    "   out.mageCycle=Number(e.mageCycle)||0;\n   out.egyptSpecialObservedHp=Number.isFinite(Number(e.egyptSpecialObservedHp))?Number(e.egyptSpecialObservedHp):null;",
    "   out.mageCycle=Number(e.mageCycle)||0;\n   out.warriorMageSpecialObservedHp=Number.isFinite(Number(e.warriorMageSpecialObservedHp))?Number(e.warriorMageSpecialObservedHp):null;\n   out.warriorMageHpTriggerPending=!!e.warriorMageHpTriggerPending;\n   out.egyptSpecialObservedHp=Number.isFinite(Number(e.egyptSpecialObservedHp))?Number(e.egyptSpecialObservedHp):null;",
    'mage trigger network fields'
)
replace_once(
    " e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;\n if(e.clan==='egypt'){e.egyptSpecialObservedHp=e.hp;e.egyptSpecialObservedShield=e.shield;e.egyptHpTriggerPending=false;e.egyptShieldTriggerPending=false;}\n state.entities.push(e);return e;",
    " e.speed=state.mode==='war'?92*WAR_TROOP_SPEED_MULTIPLIER:92;e.attackCooldown=0;e.mageCycle=0;\n if(e.clan==='egypt'){e.egyptSpecialObservedHp=e.hp;e.egyptSpecialObservedShield=e.shield;e.egyptHpTriggerPending=false;e.egyptShieldTriggerPending=false;}\n else{e.warriorMageSpecialObservedHp=e.hp;e.warriorMageHpTriggerPending=false;}\n state.entities.push(e);return e;",
    'spawn mage trigger init'
)
replace_once(
    "   if(egypt){\n     // Consome os gatilhos emergenciais deste evento. Eles só rearmam com NOVO dano.\n     e.egyptHpTriggerPending=false;\n     e.egyptShieldTriggerPending=false;\n     e.egyptSpecialObservedHp=Math.max(0,Number(e.hp)||0);\n     e.egyptSpecialObservedShield=Math.max(0,Number(e.shield)||0);\n   }\n   addWarGoalProgress(e.team,'specials');",
    "   if(egypt){\n     // Consome os gatilhos emergenciais deste evento. Eles só rearmam com NOVO dano.\n     e.egyptHpTriggerPending=false;\n     e.egyptShieldTriggerPending=false;\n     e.egyptSpecialObservedHp=Math.max(0,Number(e.hp)||0);\n     e.egyptSpecialObservedShield=Math.max(0,Number(e.shield)||0);\n   }else{\n     // O gatilho de 50% do Mago Guerreiro é um evento, não um estado permanente.\n     e.warriorMageHpTriggerPending=false;\n     e.warriorMageSpecialObservedHp=Math.max(0,Number(e.hp)||0);\n   }\n   addWarGoalProgress(e.team,'specials');",
    'consume warrior mage hp trigger'
)

insert_before(
    'function countLivingEgyptSummonsForMage(mageId){',
    "function updateWarriorMageDamageSpecialTrigger(e){\n if(!e||e.clan==='egypt')return;\n const hp=Math.max(0,Number(e.hp)||0),maxHp=Math.max(1,Number(e.maxHp)||1);\n const prevHp=Number(e.warriorMageSpecialObservedHp);\n // Dispara ao CRUZAR 50% por dano. Ficar parado abaixo de 50% não rearma.\n // Se for curado acima de 50%, uma futura nova queda pode disparar novamente.\n if(Number.isFinite(prevHp)&&prevHp>maxHp*.50&&hp<=maxHp*.50&&hp<prevHp){\n   e.warriorMageHpTriggerPending=true;\n }\n e.warriorMageSpecialObservedHp=hp;\n}\n",
    'warrior mage hp trigger helper'
)

# Egypt special summons exactly 3 shieldless warriors (HP bar only).
replace_between(
    'function spawnEgyptMageWarriors(e,p){',
    'function updateMageAttackState(e,now){',
    "function spawnEgyptMageWarriors(e,p){\n const ox=Number(p.originX)||e.x,oy=Number(p.originY)||e.y;\n const base=(Number(e.mageAttackSerial)||0)*.37;\n for(let i=0;i<3;i++){\n   const angle=base+(Math.PI*2/3)*i;\n   const radius=62+(i%2)*30;\n   const x=clamp(ox+Math.cos(angle)*radius,45,state.world.w-45);\n   const y=clamp(oy+Math.sin(angle)*radius,45,state.world.h-45);\n   const variant=i%2===0?'male':'female';\n   const summon=spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);\n   summon.shield=0;\n   summon.maxShield=0;\n }\n}\n",
    'three shieldless Egypt summons'
)

# Replace Mage AI as one coherent block: Egypt preserved; Warrior Mage = 5 normals -> 6th special + 50% crossing.
replace_between(
    'function aiFightMage(e,dt,forcedTeam,preparedCandidates=null){',
    'function aiFightBrownWarrior(e,dt,forcedTeam,preparedCandidates=null){',
    "function aiFightMage(e,dt,forcedTeam,preparedCandidates=null){\n if(!e.alive||e.knockTime>0){e.moving=false;return}\n const now=performance.now();\n if(e.clan==='egypt')updateEgyptMageDamageSpecialTriggers(e);\n else updateWarriorMageDamageSpecialTrigger(e);\n if(e.pendingMageAttack){e.moving=false;return}\n const candidates=preparedCandidates||state.entities;\n const target=nearestEngageableCandidate(e,candidates,forcedTeam,false);\n if(!target){e.moving=false;e.target=null;return}\n e.target=target;const dx=target.x-e.x,dy=target.y-e.y,d=Math.hypot(dx,dy)||1;e.heading=Math.atan2(dy,dx);if(Math.abs(dx)>4)e.facing=dx<0?-1:1;\n if(e.attackCooldown<=0&&!e.pendingMageAttack){\n   if(e.clan==='egypt'){\n     // Egito: 4 ataques normais -> o 5º elegível é especial.\n     // Gatilhos de escudo/HP continuam por evento de dano e a trava de invocados é individual.\n     const cycleDue=(Number(e.mageCycle)||0)>=4;\n     const damageDue=!!e.egyptShieldTriggerPending||!!e.egyptHpTriggerPending;\n     const specialDue=cycleDue||damageDue;\n     const summonsAlive=countLivingEgyptSummonsForMage(e.id);\n     if(e.specialCooldown<=0&&summonsAlive<=1&&specialDue){\n       if(startMageAttack(e,'special',target))return;\n     }\n   }else{\n     // Mago Guerreiro: exatamente 5 ataques normais; o 6º elegível é especial.\n     // Também usa um único gatilho ao cruzar 50% de HP por dano. A antiga regra\n     // de aglomeração/"quase morrendo" foi removida.\n     const cycleDue=(Number(e.mageCycle)||0)>=5;\n     const hpDue=!!e.warriorMageHpTriggerPending;\n     if(e.specialCooldown<=0&&(cycleDue||hpDue)){\n       if(startMageAttack(e,'special',target))return;\n     }\n   }\n   if(d>=185&&d<=285){startMageAttack(e,'normal',target);return}\n }\n if(d<175){e.x-=dx/d*e.speed*dt;e.y-=dy/d*e.speed*dt;e.moving=true}\n else if(d>285){e.x+=dx/d*e.speed*dt;e.y+=dy/d*e.speed*dt;e.moving=true}\n else e.moving=false;\n e.x=clamp(e.x,40,state.world.w-40);e.y=clamp(e.y,40,state.world.h-40);\n}\n\n\n",
    'mage AI rules'
)

# During any active special, received knockback force is halved.
insert_before(
    'function applyCombatHit(target,attacker,amount,options={}){',
    "function entityHasActiveSpecial(e,now=performance.now()){\n if(!e?.alive)return false;\n if(e.type==='mage')return e.pendingMageAttack?.kind==='special'&&Number(e.pendingMageAttack.endAt)>now;\n if(e.type==='golem')return e.pendingGolemAttack?.kind==='special'&&Number(e.pendingGolemAttack.endAt)>now;\n if(e.type==='brownWarrior')return e.pendingBrownAttack?.kind==='special'&&Number(e.pendingBrownAttack.endAt)>now;\n if(e.type==='king')return !!e.pendingKingSpecial&&Number(e.pendingKingSpecial.endAt)>now;\n return false;\n}\n",
    'special knockback helper'
)
replace_once(
    " }\n if(applyKnockback){\n   target.knockTime=knockTime;",
    " }\n // Enquanto o ALVO está executando um especial, qualquer empurrão recebido perde 50% da força.\n if(entityHasActiveSpecial(target))knockForce*=.50;\n if(applyKnockback){\n   target.knockTime=knockTime;",
    'special knockback reduction'
)

# Egypt power is much smaller and essentially does not grow.
replace_once(
    "     const grow=egyptSpecial?(.94+progress*.08):(.90+progress*.30);\n     const powerScale=egyptSpecial?.78:1;",
    "     const grow=egyptSpecial?(.96+progress*.02):(.90+progress*.30);\n     const powerScale=egyptSpecial?.50:1;",
    'Egypt power scale'
)

# Trim Egypt power GIF to ONE visual revolution (~25 frames / ~790 ms) without re-encoding.
# Analysis showed a strong visual period at 24-26 frames; 25 is the center/best practical cycle.
def subblocks_end(data,pos):
    while True:
        if pos>=len(data): raise SystemExit('GIF subblock overflow')
        size=data[pos]; pos+=1
        if size==0: return pos
        pos+=size
        if pos>len(data): raise SystemExit('GIF subblock data overflow')


def trim_gif_one_cycle(data,max_frames=25):
    if data[:6] not in (b'GIF87a',b'GIF89a'):
        raise SystemExit('Invalid GIF header')
    if len(data)<13: raise SystemExit('GIF too short')
    packed=data[10]
    pos=13
    if packed & 0x80:
        pos += 3*(2**((packed & 0x07)+1))
    prefix=data[:pos]
    # Match the working Warrior Mage asset: source is allowed to loop, JS ends it before cycle 2.
    loop_ext=b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00'
    out=bytearray(prefix)
    out.extend(loop_ext)
    frames=0
    while pos<len(data):
        if frames>=max_frames: break
        marker=data[pos]
        if marker==0x3B:
            break
        if marker==0x21:
            start=pos
            if pos+2>len(data): raise SystemExit('bad extension')
            label=data[pos+1]
            pos+=2
            if label==0xF9:
                if pos>=len(data): raise SystemExit('bad GCE')
                size=data[pos]
                pos+=1+size
                if pos>=len(data) or data[pos]!=0: raise SystemExit('bad GCE terminator')
                pos+=1
            else:
                # All non-GCE extensions consist of one or more subblocks after the label.
                pos=subblocks_end(data,pos)
            block=data[start:pos]
            # Remove any previous looping application extension; we inserted one canonical copy above.
            if b'NETSCAPE2.0' not in block and b'ANIMEXTS1.0' not in block:
                out.extend(block)
            continue
        if marker==0x2C:
            start=pos
            if pos+10>len(data): raise SystemExit('bad image descriptor')
            packed_img=data[pos+9]
            pos+=10
            if packed_img & 0x80:
                pos += 3*(2**((packed_img & 0x07)+1))
            if pos>=len(data): raise SystemExit('missing LZW size')
            pos+=1
            pos=subblocks_end(data,pos)
            out.extend(data[start:pos])
            frames+=1
            continue
        raise SystemExit(f'Unexpected GIF marker 0x{marker:02x} at {pos}')
    if frames<max_frames:
        # Already-trimmed file is acceptable if it has exactly the intended frame count.
        if frames!=max_frames:
            raise SystemExit(f'Expected at least {max_frames} GIF frames, got {frames}')
    out.append(0x3B)
    return bytes(out),frames

raw=GIF.read_bytes()
trimmed,frame_count=trim_gif_one_cycle(raw,25)
GIF.write_bytes(trimmed)

# First 25 accelerated frames total 790 ms; also calculate from actual GCE blocks for safety.
def gif_duration_ms(data):
    total=0
    for i in range(len(data)-7):
        if data[i:i+3]==b'\x21\xf9\x04':
            total += (data[i+4] | (data[i+5]<<8))*10
    return total

power_ms=gif_duration_ms(trimmed)
if not (650<=power_ms<=950):
    raise SystemExit(f'Unexpected trimmed Egypt power duration: {power_ms} ms')
text=re.sub(r'let EGYPT_MAGE_POWER_SPECIAL_DURATION=\d+;',f'let EGYPT_MAGE_POWER_SPECIAL_DURATION={power_ms};',text,count=1)

# Update persistent cache revisions for the modified GIF.
revision=hashlib.sha256(trimmed).hexdigest()[:20]
pattern=r'("assets/egypt/mage/power-special\.gif":")[0-9a-f]+(")'
text,n1=re.subn(pattern,rf'\g<1>{revision}\g<2>',text,count=1)
sw,n2=re.subn(pattern,rf'\g<1>{revision}\g<2>',sw,count=1)
if n1!=1 or n2!=1:
    raise SystemExit(f'Failed to update asset revisions index={n1} sw={n2}')

INDEX.write_text(text,encoding='utf-8')
SW.write_text(sw,encoding='utf-8')
print(f'Applied patch. Egypt power: {frame_count} frames, {power_ms} ms, revision={revision}')
