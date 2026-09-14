from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

old="""     if(e.clan==='egypt'){
       // Especial do Egito: substitui o dano em área pela invocação de 5 guerreiros egípcios.
       spawnEgyptMageWarriors(e,p);
     }else{
       forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
         if(!t.alive||t===e||t.team===e.team)return;
         const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
         if(p.hitIds[t.id])return;p.hitIds[t.id]=true;
         applyCombatHit(t,e,MAGE_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10});
       });
     }

     // A cura de 30 do Mago original é preservada; a diferença egípcia substitui somente o dano pela invocação.
     forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,ally=>{
       if(!ally.alive||ally.team!==e.team)return;
       const dx=ally.x-ox,dy=ally.y-oy;if(dx*dx+dy*dy>r2)return;
       const before=Number(ally.hp)||0;
       ally.hp=Math.min(Number(ally.maxHp)||before,before+MAGE_SPECIAL_HEAL);
       if(ally.hp>before)ally.regenSerial=(ally.regenSerial||0)+1;
     });
"""

new="""     if(e.clan==='egypt'){
       // Especial do Egito é 100% invocação: o GIF é apenas visual.
       // Não causa dano, não cura o próprio Mago e não cura aliados.
       spawnEgyptMageWarriors(e,p);
     }else{
       // Mago Guerreiro mantém o especial original: dano em área + cura de aliados.
       forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,t=>{
         if(!t.alive||t===e||t.team===e.team)return;
         const dx=t.x-ox,dy=t.y-oy;if(dx*dx+dy*dy>r2)return;
         if(p.hitIds[t.id])return;p.hitIds[t.id]=true;
         applyCombatHit(t,e,MAGE_SPECIAL_DAMAGE,{knockForce:260,knockTime:.18,tilt:10});
       });
       forEachWarSpatialCandidate(ox-r,oy-r,ox+r,oy+r,ally=>{
         if(!ally.alive||ally.team!==e.team)return;
         const dx=ally.x-ox,dy=ally.y-oy;if(dx*dx+dy*dy>r2)return;
         const before=Number(ally.hp)||0;
         ally.hp=Math.min(Number(ally.maxHp)||before,before+MAGE_SPECIAL_HEAL);
         if(ally.hp>before)ally.regenSerial=(ally.regenSerial||0)+1;
       });
     }
"""

if new in text:
    print('Patch already applied')
elif old in text:
    text=text.replace(old,new,1)
    path.write_text(text,encoding='utf-8')
    print('Applied Egypt mage pure summon special patch')
else:
    raise SystemExit('Expected Mage special impact block not found')
