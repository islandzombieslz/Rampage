from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

MARKER='WAR CAMERA COMPOSITOR 2026-09-09'
if MARKER in text:
    print('War camera compositor already applied.')
    raise SystemExit(0)


def replace_once(old,new,label):
    global text
    if old not in text:
        raise SystemExit(f'Trecho não encontrado: {label}')
    text=text.replace(old,new,1)

# =========================================================
# 1) SUBCAMADAS COMPOSTAS: PAN/ZOOM EM 2 TRANSFORMS, NÃO N SPRITES
# =========================================================
old_css="#entityLayer{position:absolute;inset:0;overflow:hidden;overflow:clip;pointer-events:none;z-index:2;contain:layout paint;transform:translateZ(0)}"
new_css=old_css+"\n#entityCameraLayer,#combatCameraLayer,#golemRockLayer{position:absolute;inset:0;pointer-events:none;transform-origin:0 0;backface-visibility:hidden;-webkit-backface-visibility:hidden}\n#entityCameraLayer,#combatCameraLayer{will-change:auto}"
replace_once(old_css,new_css,'CSS das subcamadas compostas')

old_html='''  <div id="entityLayer"></div>\n  <div id="combatFxLayer"></div>'''
new_html='''  <div id="entityLayer"><div id="entityCameraLayer"></div></div>\n  <div id="combatFxLayer"><div id="combatCameraLayer"></div><div id="golemRockLayer"></div></div>'''
replace_once(old_html,new_html,'subcamadas de câmera no HTML')

old_layers="""const entityLayer=$('#entityLayer');\nconst combatFxLayer=$('#combatFxLayer');"""
new_layers="""const entityLayer=$('#entityLayer');\nconst combatFxLayer=$('#combatFxLayer');\nconst entityCameraLayer=$('#entityCameraLayer');\nconst combatCameraLayer=$('#combatCameraLayer');\nconst golemRockLayer=$('#golemRockLayer');\n\n// WAR CAMERA COMPOSITOR 2026-09-09\n// Durante pan/zoom, a câmera move duas subcamadas compostas pela GPU.\n// As unidades continuam atualizando posição/IA normalmente, mas deixam de receber\n// left/top/scale novos só porque a câmera mudou. Isso evita picos de layout/paint.\nconst CAMERA_COMPOSITE_SETTLE_MS=180;\nconst CAMERA_COMPOSITE_REBASE_PX=260;\nconst CAMERA_COMPOSITE_MIN_RATIO=.78;\nconst CAMERA_COMPOSITE_MAX_RATIO=1.28;\nconst CAMERA_EFFECT_RETENTION_MS=650;\nconst cameraComposite={initialized:false,active:false,baseLeft:0,baseTop:0,baseZoom:1,lastLeft:0,lastTop:0,lastZoom:1,motionUntil:0};\nfunction applyCameraLayerTransform(transform,active){\n for(const layer of [entityCameraLayer,combatCameraLayer]){\n   if(!layer)continue;\n   if(layer._cameraTransform!==transform){layer._cameraTransform=transform;layer.style.transform=transform}\n   const will=active?'transform':'auto';\n   if(layer._cameraWillChange!==will){layer._cameraWillChange=will;layer.style.willChange=will}\n }\n}\nfunction resetCameraComposite(){\n const c=cameraComposite;\n c.initialized=false;c.active=false;c.motionUntil=0;\n applyCameraLayerTransform('translate3d(0,0,0)',false);\n}\nfunction prepareCameraComposite(left,top,zoom){\n if(state.mode!=='war'||!entityCameraLayer||!combatCameraLayer){\n   if(cameraComposite.initialized||cameraComposite.active)resetCameraComposite();\n   return {left,top,zoom};\n }\n const c=cameraComposite,now=performance.now();\n if(!c.initialized){\n   c.initialized=true;c.baseLeft=left;c.baseTop=top;c.baseZoom=zoom;\n   c.lastLeft=left;c.lastTop=top;c.lastZoom=zoom;\n }\n const moved=Math.abs(left-c.lastLeft)>.04||Math.abs(top-c.lastTop)>.04||Math.abs(zoom-c.lastZoom)>.00025;\n if(moved)c.motionUntil=now+CAMERA_COMPOSITE_SETTLE_MS;\n c.lastLeft=left;c.lastTop=top;c.lastZoom=zoom;\n const interaction=!!state.camera.intro||rightDragging||touches.size>0||Math.abs(state.camera.velX)>2||Math.abs(state.camera.velY)>2;\n let active=interaction||now<c.motionUntil;\n if(active){\n   let ratio=zoom/c.baseZoom;\n   let tx=(c.baseLeft-left)*zoom,ty=(c.baseTop-top)*zoom;\n   // Rebasa ocasionalmente para manter a escala composta pequena e nítida.\n   // Isso ocorre poucas vezes durante um gesto, em vez de reescrever N sprites a cada frame.\n   if(Math.max(Math.abs(tx),Math.abs(ty))>CAMERA_COMPOSITE_REBASE_PX||ratio<CAMERA_COMPOSITE_MIN_RATIO||ratio>CAMERA_COMPOSITE_MAX_RATIO){\n     c.baseLeft=left;c.baseTop=top;c.baseZoom=zoom;ratio=1;tx=0;ty=0;\n   }\n   c.active=true;\n   applyCameraLayerTransform(`translate3d(${tx}px,${ty}px,0) scale(${ratio})`,true);\n   return {left:c.baseLeft,top:c.baseTop,zoom:c.baseZoom};\n }\n if(c.active||c.baseLeft!==left||c.baseTop!==top||c.baseZoom!==zoom){\n   c.baseLeft=left;c.baseTop=top;c.baseZoom=zoom;c.active=false;\n   applyCameraLayerTransform('translate3d(0,0,0)',false);\n }\n return {left,top,zoom};\n}"""
replace_once(old_layers,new_layers,'referências e compositor da câmera')

# Nós do mundo entram nas subcamadas transformáveis.
replace_once(" entityLayer.appendChild(el);"," entityCameraLayer.appendChild(el);",'append de entidade')
replace_once("if(rock.parentElement!==combatFxLayer)combatFxLayer?.appendChild(rock);","if(rock.parentElement!==golemRockLayer)golemRockLayer?.appendChild(rock);",'layer das pedras do Golem')

# =========================================================
# 2) EFEITOS: POSIÇÃO USA A CÂMERA-BASE; CULLING USA A CÂMERA REAL
# =========================================================
replace_once("function syncMagePowerEffects(left,top,zoom,screenW,screenH){\n const layer=combatFxLayer,active=magePowerActiveIds;active.clear();const now=performance.now();",
"function syncMagePowerEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){\n const layer=combatCameraLayer,active=magePowerActiveIds;active.clear();const now=performance.now();",
'mago: assinatura/layer')
replace_once("const sx=((p.originX??e.x)-left)*zoom,sy=((p.originY??e.y)-top)*zoom,pr=radius*zoom;\n     effectVisible=sx+pr>=-40&&sx-pr<=screenW+40&&sy+pr>=-40&&sy-pr<=screenH+40;",
"const sx=((p.originX??e.x)-cullLeft)*cullZoom,sy=((p.originY??e.y)-cullTop)*cullZoom,pr=radius*cullZoom;\n     effectVisible=sx+pr>=-40&&sx-pr<=screenW+40&&sy+pr>=-40&&sy-pr<=screenH+40;",
'mago especial: culling real')
replace_once("const x1=(ox-left)*zoom,y1=(oy-top)*zoom,x2=(ox+Math.cos(angle)*length-left)*zoom,y2=(oy+Math.sin(angle)*length-top)*zoom;\n     effectVisible=Math.max(x1,x2)>=-120&&Math.min(x1,x2)<=screenW+120&&Math.max(y1,y2)>=-120&&Math.min(y1,y2)<=screenH+120;",
"const x1=(ox-cullLeft)*cullZoom,y1=(oy-cullTop)*cullZoom,x2=(ox+Math.cos(angle)*length-cullLeft)*cullZoom,y2=(oy+Math.sin(angle)*length-cullTop)*cullZoom;\n     effectVisible=Math.max(x1,x2)>=-120&&Math.min(x1,x2)<=screenW+120&&Math.max(y1,y2)>=-120&&Math.min(y1,y2)<=screenH+120;",
'mago normal: culling real')
replace_once("   if(!effectVisible){\n     const old=magePowerNodes.get(e.id);\n     if(old){releaseGifObjectUrl(old);old.remove();magePowerNodes.delete(e.id)}\n     continue;\n   }\n   active.add(e.id);",
"   if(!effectVisible){\n     const old=magePowerNodes.get(e.id);\n     if(old&&(cameraComposite.active||now-Number(old._lastEffectVisibleAt||0)<CAMERA_EFFECT_RETENTION_MS)){\n       active.add(e.id);old.style.visibility='hidden';continue;\n     }\n     if(old){releaseGifObjectUrl(old);old.remove();magePowerNodes.delete(e.id)}\n     continue;\n   }\n   active.add(e.id);",
'mago: retenção durante câmera')
replace_once("   let img=magePowerNodes.get(e.id);\n   if(!img){img=document.createElement('img');img.draggable=false;layer.appendChild(img);magePowerNodes.set(e.id,img);img.dataset.serial='-1'}",
"   let img=magePowerNodes.get(e.id);\n   if(!img){img=document.createElement('img');img.draggable=false;layer.appendChild(img);magePowerNodes.set(e.id,img);img.dataset.serial='-1'}\n   img._lastEffectVisibleAt=now;",
'mago: marca visibilidade')
replace_once("const desiredLayer=p.kind==='special'?entityLayer:layer;if(img.parentElement!==desiredLayer)desiredLayer.appendChild(img);",
"const desiredLayer=p.kind==='special'?entityCameraLayer:layer;if(img.parentElement!==desiredLayer)desiredLayer.appendChild(img);",
'mago: layer especial')

replace_once("function syncKingPowerEffects(left,top,zoom,screenW,screenH){\n const layer=entityLayer,active=kingPowerActiveIds;active.clear();const now=performance.now();",
"function syncKingPowerEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){\n const layer=entityCameraLayer,active=kingPowerActiveIds;active.clear();const now=performance.now();",
'rei: assinatura/layer')
replace_once("   const half=215*zoom;\n   const sx=(ox-left)*zoom,sy=(oy-top)*zoom;\n   const effectVisible=sx+half>=-40&&sx-half<=screenW+40&&sy+half>=-40&&sy-half<=screenH+40;",
"   const half=215*cullZoom;\n   const cullSx=(ox-cullLeft)*cullZoom,cullSy=(oy-cullTop)*cullZoom;\n   const effectVisible=cullSx+half>=-40&&cullSx-half<=screenW+40&&cullSy+half>=-40&&cullSy-half<=screenH+40;\n   const sx=(ox-left)*zoom,sy=(oy-top)*zoom;",
'rei: culling real')
replace_once("   if(!effectVisible){\n     const old=kingPowerNodes.get(e.id);\n     if(old){releaseGifObjectUrl(old);old.remove();kingPowerNodes.delete(e.id)}\n     continue;\n   }\n   active.add(e.id);",
"   if(!effectVisible){\n     const old=kingPowerNodes.get(e.id);\n     if(old&&(cameraComposite.active||now-Number(old._lastEffectVisibleAt||0)<CAMERA_EFFECT_RETENTION_MS)){\n       active.add(e.id);old.style.visibility='hidden';continue;\n     }\n     if(old){releaseGifObjectUrl(old);old.remove();kingPowerNodes.delete(e.id)}\n     continue;\n   }\n   active.add(e.id);",
'rei: retenção durante câmera')
replace_once("   const serial=String(p.serial||e.kingSpecialSerial||0);",
"   img._lastEffectVisibleAt=now;\n   const serial=String(p.serial||e.kingSpecialSerial||0);",
'rei: marca visibilidade')

replace_once("function syncDragonProjectileEffects(left,top,zoom,screenW,screenH){\n           const layer=combatFxLayer,active=dragonProjectileActiveIds;active.clear();",
"function syncDragonProjectileEffects(left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){\n           const layer=combatCameraLayer,active=dragonProjectileActiveIds;active.clear();const now=performance.now();",
'dragão: assinatura/layer')
replace_once("             const sx=(p.x-left)*zoom,sy=(p.y-top)*zoom,margin=90;if(sx<-margin||sx>screenW+margin||sy<-margin||sy>screenH+margin)continue;\n             active.add(p.id);let img=dragonProjectileNodes.get(p.id);",
"             const cullSx=(p.x-cullLeft)*cullZoom,cullSy=(p.y-cullTop)*cullZoom,margin=120;\n             if(cullSx<-margin||cullSx>screenW+margin||cullSy<-margin||cullSy>screenH+margin){\n               const old=dragonProjectileNodes.get(p.id);\n               if(old&&(cameraComposite.active||now-Number(old._lastEffectVisibleAt||0)<CAMERA_EFFECT_RETENTION_MS)){active.add(p.id);old.style.visibility='hidden'}\n               continue;\n             }\n             const sx=(p.x-left)*zoom,sy=(p.y-top)*zoom;\n             active.add(p.id);let img=dragonProjectileNodes.get(p.id);",
'dragão: culling e retenção')
replace_once("             if(!img){img=acquireDragonProjectileNode(layer);dragonProjectileNodes.set(p.id,img)}\n             const angle=",
"             if(!img){img=acquireDragonProjectileNode(layer);dragonProjectileNodes.set(p.id,img)}\n             img._lastEffectVisibleAt=now;\n             const angle=",
'dragão: marca visibilidade')

# =========================================================
# 3) ENTIDADES: COORDENADAS VISUAIS NA BASE, CULLING NA CÂMERA REAL
# =========================================================
replace_once("function syncEntityVisuals(visible,left,top,zoom,screenW,screenH){",
"function syncEntityVisuals(visible,left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom){",
'entidades: assinatura')
replace_once("   const sx=(e.x-left)*zoom,sy=(e.y-top)*zoom;\n\n   // Correção de \"sprites grudados nos cantos\":",
"   const sx=(e.x-left)*zoom,sy=(e.y-top)*zoom;\n   const cullSx=(e.x-cullLeft)*cullZoom,cullSy=(e.y-cullTop)*cullZoom;\n\n   // Correção de \"sprites grudados nos cantos\":",
'entidades: coordenadas de culling')
replace_once("   const entityPadX=e.type==='king'&&e.pendingKingSpecial?240*zoom:padX;\n   const entityPadY=e.type==='king'&&e.pendingKingSpecial?240*zoom:padY;\n   const onScreen=\n     sx>=-entityPadX && sx<=screenW+entityPadX &&\n     sy>=-entityPadY && sy<=screenH+entityPadY;",
"   const entityPadX=e.type==='king'&&e.pendingKingSpecial?240*cullZoom:150*cullZoom;\n   const entityPadY=e.type==='king'&&e.pendingKingSpecial?240*cullZoom:170*cullZoom;\n   const onScreen=\n     cullSx>=-entityPadX && cullSx<=screenW+entityPadX &&\n     cullSy>=-entityPadY && cullSy<=screenH+entityPadY;",
'entidades: culling real')

# As constantes padX/padY antigas deixam de ser necessárias no frame base.
text=text.replace(" // Tamanho visual aproximado máximo do guerreiro + espada.\n // Fazemos o culling em COORDENADAS DE TELA, não só no mundo.\n const padX=150*zoom;\n const padY=170*zoom;\n\n", " // Culling usa a câmera real; posicionamento usa a câmera-base do compositor.\n\n", 1)

# =========================================================
# 4) DRAW: CANVAS/BARREIRA NA CÂMERA REAL; DOM NAS SUBCAMADAS COMPOSTAS
# =========================================================
old_sync=""" syncWarArenaOverlay(left,top,zoom);\n syncEntityVisuals(visible,left,top,zoom,vw,vh);\n syncKingPowerEffects(left,top,zoom,vw,vh);\n syncMagePowerEffects(left,top,zoom,vw,vh);\n syncDragonProjectileEffects(left,top,zoom,vw,vh);"""
new_sync=""" syncWarArenaOverlay(left,top,zoom);\n const domCamera=prepareCameraComposite(left,top,zoom);\n syncEntityVisuals(visible,domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncKingPowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncMagePowerEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);\n syncDragonProjectileEffects(domCamera.left,domCamera.top,domCamera.zoom,vw,vh,left,top,zoom);"""
replace_once(old_sync,new_sync,'draw usando compositor')

# =========================================================
# 5) LIMPEZA PRESERVA OS WRAPPERS E RESETA A TRANSFORMAÇÃO
# =========================================================
replace_once(" entityLayer.innerHTML='';\n if(combatFxLayer)combatFxLayer.innerHTML='';",
" if(entityCameraLayer)entityCameraLayer.innerHTML='';\n if(combatCameraLayer)combatCameraLayer.innerHTML='';\n if(golemRockLayer)golemRockLayer.innerHTML='';\n resetCameraComposite();",
'limpeza preservando wrappers')

checks=[
 MARKER,
 'id="entityCameraLayer"',
 'id="combatCameraLayer"',
 'id="golemRockLayer"',
 'const CAMERA_COMPOSITE_SETTLE_MS=180;',
 'function prepareCameraComposite(left,top,zoom)',
 "applyCameraLayerTransform(`translate3d(${tx}px,${ty}px,0) scale(${ratio})`,true);",
 'entityCameraLayer.appendChild(el);',
 'golemRockLayer?.appendChild(rock);',
 'const layer=combatCameraLayer,active=magePowerActiveIds',
 "const desiredLayer=p.kind==='special'?entityCameraLayer:layer",
 'const layer=entityCameraLayer,active=kingPowerActiveIds',
 'const layer=combatCameraLayer,active=dragonProjectileActiveIds',
 'function syncEntityVisuals(visible,left,top,zoom,screenW,screenH,cullLeft=left,cullTop=top,cullZoom=zoom)',
 'const cullSx=(e.x-cullLeft)*cullZoom,cullSy=(e.y-cullTop)*cullZoom;',
 'const domCamera=prepareCameraComposite(left,top,zoom);',
 'CAMERA_EFFECT_RETENTION_MS=650',
 'resetCameraComposite();',
]
for marker in checks:
    if marker not in text:
        raise SystemExit(f'Validação do compositor falhou: {marker}')

for forbidden in [
    " entityLayer.appendChild(el);",
    "const layer=combatFxLayer,active=magePowerActiveIds",
    "const layer=entityLayer,active=kingPowerActiveIds",
    "const layer=combatFxLayer,active=dragonProjectileActiveIds",
    " entityLayer.innerHTML='';",
]:
    if forbidden in text:
        raise SystemExit(f'Comportamento antigo ainda presente: {forbidden}')

path.write_text(text,encoding='utf-8')
print('Compositor de câmera aplicado: pan/zoom deixam de reescrever cada sprite por frame.')
