from pathlib import Path
import re

path=Path('index.html')
text=path.read_text(encoding='utf-8')


def rep(old,new,label,count=1):
    global text
    if old not in text:
        raise SystemExit(f'Missing anchor: {label}')
    text=text.replace(old,new,count)

# ---------------------------------------------------------
# 1-3) Egypt visual tuning only (no gameplay hitbox change)
# ---------------------------------------------------------
rep('''/* Egito: apenas escala visual. Hitbox, alcance, velocidade e atributos não mudam. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-body{
  width:96px;
  height:113px;
  left:-9px;
  top:-10px;
}
/* A espada egípcia estava grande em relação ao corpo. Mantém o pivô perto
   do mesmo ponto visual, mas reduz o sprite. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-sword{
  width:22px;
  height:64px;
  left:28px;
  top:8px;
}

/* Mago/Maga do Egito maiores sem alterar a caixa física da entidade. */
.entity-visual.mage-visual.egypt-unit .entity-body{
  width:108px;
  height:128px;
  left:-10px;
  top:-12px;
}
.entity-visual.mage-visual.egypt-unit .entity-mage-special{
  width:128px !important;
  height:151px !important;
  left:-20px !important;
  top:-24px !important;
}
/* Cajado egípcio menor; animações/rotação continuam usando a mesma lógica. */
.entity-visual.mage-visual.egypt-unit .mage-staff{
  width:68px;
  height:80px;
  left:32px;
  top:4px;
}
''','''/* Egito: apenas escala visual. Hitbox, alcance, velocidade e atributos não mudam. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-body{
  width:104px;
  height:123px;
  left:-13px;
  top:-15px;
}
/* Espada egípcia: desfaz a redução anterior e fica maior que a espada padrão. */
.entity-visual.egypt-unit:not(.mage-visual) .entity-sword{
  width:34px;
  height:98px;
  left:24px;
  top:-8px;
}

/* Mago/Maga do Egito um pouco maiores, mantendo a caixa física original. */
.entity-visual.mage-visual.egypt-unit .entity-body{
  width:118px;
  height:140px;
  left:-15px;
  top:-18px;
}
.entity-visual.mage-visual.egypt-unit .entity-mage-special{
  width:140px !important;
  height:165px !important;
  left:-26px !important;
  top:-30px !important;
}
/* Cajado e mão frontal descem juntos; tamanho do cajado permanece controlado. */
.entity-visual.mage-visual.egypt-unit .mage-staff{
  width:68px;
  height:80px;
  left:32px;
  top:14px;
}
.entity-visual.mage-visual.egypt-unit .mage-hand{
  top:61px;
}
''','visual css')

# ---------------------------------------------------------
# 4) Per-mage ownership for Egypt summoned warriors
# ---------------------------------------------------------
rep("variant:'male',clan:'warriors',egyptSummoned:false,", "variant:'male',clan:'warriors',egyptSummoned:false,egyptSummonerId:null,", 'entity base summoner')
rep("variant:e.variant||'male',ownerId:e.ownerId??null,clan:normalizeClan(e.clan),egyptSummoned:!!e.egyptSummoned", "variant:e.variant||'male',ownerId:e.ownerId??null,clan:normalizeClan(e.clan),egyptSummoned:!!e.egyptSummoned,egyptSummonerId:e.egyptSummonerId??null", 'network summoner')
rep("function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null,clan='warriors',egyptSummoned=false){", "function spawnWarrior(x,y,team,color,controlled=false,variant='male',ownerId=null,clan='warriors',egyptSummoned=false,egyptSummonerId=null){", 'spawn warrior signature')
rep(" e.egyptSummoned=!!egyptSummoned;\n state.entities.push(e);", " e.egyptSummoned=!!egyptSummoned;\n e.egyptSummonerId=egyptSummonerId??null;\n state.entities.push(e);", 'spawn warrior summoner assignment')

old_helpers='''function countLivingEgyptSummons(team){
 let count=0;
 for(const t of state.entities){
   if(t.alive&&t.team===team&&t.type==='warrior'&&t.clan==='egypt'&&t.egyptSummoned)count++;
 }
 return count;
}
function hasPendingEgyptSummonSpecial(team,excludeId=null){
 for(const t of state.entities){
   if(!t.alive||t.id===excludeId||t.team!==team||t.type!=='mage'||t.clan!=='egypt')continue;
   if(t.pendingMageAttack?.kind==='special')return true;
 }
 return false;
}
'''
new_helpers='''function countLivingEgyptSummonsForMage(mageId){
 let count=0;
 for(const t of state.entities){
   if(t.alive&&t.type==='warrior'&&t.clan==='egypt'&&t.egyptSummoned&&t.egyptSummonerId===mageId)count++;
 }
 return count;
}
'''
rep(old_helpers,new_helpers,'per-mage summon helpers')
rep("   spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true);", "   spawnWarrior(x,y,e.team,e.color,false,variant,null,'egypt',true,e.id);", 'summoned warrior owner')

old_ai='''   if(e.clan==='egypt'){
     // Egito: vida baixa OU 5 normais completos tornam o especial devido.
     // Porém a invocação só acontece quando restar no máximo 1 guerreiro invocado vivo.
     const cycleDue=(Number(e.mageCycle)||0)>=5;
     const summonsAlive=countLivingEgyptSummons(e.team);
     if(e.specialCooldown<=0&&summonsAlive<=1&&!hasPendingEgyptSummonSpecial(e.team,e.id)&&(lowHealth||cycleDue)){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''
new_ai='''   if(e.clan==='egypt'){
     // Egito: 4 ataques normais -> o 5º ataque elegível é especial.
     // A trava é INDIVIDUAL: contam apenas guerreiros que ESTE mago invocou.
     // Se ainda houver 2 ou mais vivos, o especial nem entra em estado visual;
     // o mago segue atacando normalmente até restar no máximo 1 dos seus próprios invocados.
     const cycleDue=(Number(e.mageCycle)||0)>=4;
     const summonsAlive=countLivingEgyptSummonsForMage(e.id);
     if(e.specialCooldown<=0&&summonsAlive<=1&&cycleDue){
       if(startMageAttack(e,'special',target))return;
     }
   }else{'''
rep(old_ai,new_ai,'egypt mage AI cycle')

# ---------------------------------------------------------
# 5) One visual cycle per special GIF
# ---------------------------------------------------------
old_special='''   const powerDuration=egypt?EGYPT_MAGE_POWER_SPECIAL_DURATION:MAGE_POWER_SPECIAL_DURATION;
   const duration=Math.max(bodyDuration,powerDuration);
   e.specialCooldown=MAGE_SPECIAL_COOLDOWN;
   e.moving=false;e.pendingMageAttack={
     kind,targetId:null,originX:e.x,originY:e.y,startedAt:now,duration,
     damageAt:now+Math.min(1200,Math.max(650,duration*.40)),
     endAt:now+duration,impacted:false,hitIds:{}
   };'''
new_special='''   const powerDuration=egypt?EGYPT_MAGE_POWER_SPECIAL_DURATION:MAGE_POWER_SPECIAL_DURATION;
   const duration=Math.max(bodyDuration,powerDuration);
   e.specialCooldown=MAGE_SPECIAL_COOLDOWN;
   e.moving=false;e.pendingMageAttack={
     kind,targetId:null,originX:e.x,originY:e.y,startedAt:now,duration,bodyDuration,powerDuration,
     bodyEndAt:now+bodyDuration,powerEndAt:now+powerDuration,
     damageAt:now+Math.min(1200,Math.max(650,duration*.40)),
     endAt:now+duration,impacted:false,hitIds:{}
   };'''
rep(old_special,new_special,'special independent gif deadlines')

# Mage network serialization: carry per-layer deadlines.
old_ser='''       length:Number.isFinite(Number(p.length))?Number(p.length):245,
       duration:Number(p.duration)||(p.kind==='special'?MAGE_SPECIAL_DURATION:MAGE_NORMAL_DURATION),
       remainingMs:Math.max(0,Number(p.endAt)-now)
     };'''
new_ser='''       length:Number.isFinite(Number(p.length))?Number(p.length):245,
       duration:Number(p.duration)||(p.kind==='special'?MAGE_SPECIAL_DURATION:MAGE_NORMAL_DURATION),
       remainingMs:Math.max(0,Number(p.endAt)-now),
       bodyDuration:Number(p.bodyDuration)||0,
       powerDuration:Number(p.powerDuration)||0,
       bodyRemainingMs:p.bodyEndAt?Math.max(0,Number(p.bodyEndAt)-now):0,
       powerRemainingMs:p.powerEndAt?Math.max(0,Number(p.powerEndAt)-now):0
     };'''
rep(old_ser,new_ser,'mage network layer deadlines')

# Remote mage reconstruction: same serial cannot gain time on every snapshot.
old_remote='''     if(out.pendingMageAttack?.remainingMs!=null){
       const duration=out.pendingMageAttack.duration||(out.pendingMageAttack.kind==='special'?MAGE_SPECIAL_DURATION:MAGE_NORMAL_DURATION);
       out.pendingMageAttack={...out.pendingMageAttack,endAt:localNow+out.pendingMageAttack.remainingMs,duration};
     }
'''
new_remote='''     if(out.pendingMageAttack?.remainingMs!=null){
       const p=out.pendingMageAttack;
       const duration=p.duration||(p.kind==='special'?MAGE_SPECIAL_DURATION:MAGE_NORMAL_DURATION);
       const remaining=Math.max(0,Number(p.remainingMs)||0);
       const oldPending=old?.pendingMageAttack;
       const sameSerial=!!oldPending&&Number(old?.mageAttackSerial)===Number(out.mageAttackSerial)&&oldPending.kind===p.kind;
       if(remaining<=0){
         out.pendingMageAttack=null;
         out.mageAttackKind=null;
       }else if(sameSerial&&Number.isFinite(Number(oldPending.endAt))){
         const rebuilt={...p,duration,
           startedAt:Number(oldPending.startedAt)||localNow-Math.max(0,duration-remaining),
           endAt:Math.min(Number(oldPending.endAt),localNow+remaining)
         };
         if(p.kind==='special'){
           const bodyDuration=Number(p.bodyDuration)||Number(oldPending.bodyDuration)||(out.variant==='female'?EGYPT_MAGE_SPECIAL_FEMALE_DURATION:EGYPT_MAGE_SPECIAL_MALE_DURATION);
           const powerDuration=Number(p.powerDuration)||Number(oldPending.powerDuration)||EGYPT_MAGE_POWER_SPECIAL_DURATION;
           const bodyCandidate=localNow+Math.max(0,Number(p.bodyRemainingMs)||0);
           const powerCandidate=localNow+Math.max(0,Number(p.powerRemainingMs)||0);
           rebuilt.bodyDuration=bodyDuration;rebuilt.powerDuration=powerDuration;
           rebuilt.bodyEndAt=Math.min(Number(oldPending.bodyEndAt)||bodyCandidate,bodyCandidate);
           rebuilt.powerEndAt=Math.min(Number(oldPending.powerEndAt)||powerCandidate,powerCandidate);
         }
         out.pendingMageAttack=rebuilt;
       }else{
         const rebuilt={...p,duration,startedAt:localNow-Math.max(0,duration-remaining),endAt:localNow+remaining};
         if(p.kind==='special'){
           rebuilt.bodyDuration=Number(p.bodyDuration)||(out.clan==='egypt'?(out.variant==='female'?EGYPT_MAGE_SPECIAL_FEMALE_DURATION:EGYPT_MAGE_SPECIAL_MALE_DURATION):(out.variant==='female'?MAGE_SPECIAL_FEMALE_DURATION:MAGE_SPECIAL_MALE_DURATION));
           rebuilt.powerDuration=Number(p.powerDuration)||(out.clan==='egypt'?EGYPT_MAGE_POWER_SPECIAL_DURATION:MAGE_POWER_SPECIAL_DURATION);
           rebuilt.bodyEndAt=localNow+Math.max(0,Number(p.bodyRemainingMs)||0);
           rebuilt.powerEndAt=localNow+Math.max(0,Number(p.powerRemainingMs)||0);
         }
         out.pendingMageAttack=rebuilt;
       }
     }
     if(!out.pendingMageAttack)out.mageAttackKind=null;
'''
rep(old_remote,new_remote,'remote mage anti-stretch')

# Body special renderer: stop slightly before one full GIF cycle to prevent browser loop.
old_render='''   }else if(e.type==='mage'){
     const special=e.mageAttackKind==='special'&&e.pendingMageAttack?.kind==='special'&&e.pendingMageAttack.endAt>localNow;
     const normalAttack=e.mageAttackKind==='normal'&&e.pendingMageAttack?.kind==='normal';
     const desired=special?'special':visualMoving?'walk':'idle';
     setEntitySpriteState(el,desired);'''
new_render='''   }else if(e.type==='mage'){
     const magePending=e.pendingMageAttack;
     const specialPending=e.mageAttackKind==='special'&&magePending?.kind==='special'&&magePending.endAt>localNow;
     const bodyVisualEnd=specialPending?(Number(magePending.bodyEndAt)||Number(magePending.endAt))-45:0;
     const special=specialPending&&localNow<bodyVisualEnd;
     const normalAttack=e.mageAttackKind==='normal'&&magePending?.kind==='normal';
     const desired=special?'special':visualMoving?'walk':'idle';
     setEntitySpriteState(el,desired);'''
rep(old_render,new_render,'mage body one-cycle renderer')

# Power special: stop its own GIF after one cycle, independent of body/overall special state.
old_fx_start=''' for(const e of state.entities){
   const p=e.pendingMageAttack;if(!e.alive||!p)continue;
   // Poderes completamente fora da câmera não ganham DOM/GIF. Dano e estado seguem intactos.'''
new_fx_start=''' for(const e of state.entities){
   const p=e.pendingMageAttack;if(!e.alive||!p)continue;
   if(p.kind==='special'){
     const powerVisualEnd=(Number(p.powerEndAt)||Number(p.endAt)||0)-45;
     if(now>=powerVisualEnd){
       const old=magePowerNodes.get(e.id);
       if(old){releaseGifObjectUrl(old);old.remove();magePowerNodes.delete(e.id)}
       continue;
     }
   }
   // Poderes completamente fora da câmera não ganham DOM/GIF. Dano e estado seguem intactos.'''
rep(old_fx_start,new_fx_start,'mage power special cutoff')

old_fx_progress='''   }else{
     const duration=p.duration||MAGE_SPECIAL_DURATION;
     const progress=clamp(1-Math.max(0,p.endAt-now)/duration,0,1);
     // Cresce de forma contínua e um pouco mais que antes.'''
new_fx_progress='''   }else{
     const duration=Math.max(1,Number(p.powerDuration)||(e.clan==='egypt'?EGYPT_MAGE_POWER_SPECIAL_DURATION:MAGE_POWER_SPECIAL_DURATION));
     const powerEnd=Number(p.powerEndAt)||Number(p.endAt);
     const powerStart=powerEnd-duration;
     const progress=clamp((now-powerStart)/duration,0,1);
     // Cresce de forma contínua e um pouco mais que antes.'''
rep(old_fx_progress,new_fx_progress,'mage power progress own duration')

# Comments/guard marker for this revision.
rep('/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */','/* EGYPT SHOP + VISUAL TUNING 2026-09-13 */\n/* EGYPT MAGE INDIVIDUAL SUMMON CYCLE 2026-09-13 */','revision marker')

path.write_text(text,encoding='utf-8')
print('Egypt mage individual special + visual tuning patch applied')
