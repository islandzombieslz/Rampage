from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')
MARK='BROWN WARRIOR TUNING 2026-09-12'
if MARK in t:
    print('Brown Warrior tuning already applied.')
    raise SystemExit(0)

def rep(old,new,label):
    global t
    n=t.count(old)
    if n!=1:
        raise SystemExit(f'{label}: expected exactly 1 match, found {n}')
    t=t.replace(old,new,1)

rep(
    'const BROWN_SPECIAL_DAMAGE=15;',
    '/* BROWN WARRIOR TUNING 2026-09-12 */\nconst BROWN_SPECIAL_DAMAGE=25;',
    'special damage'
)

rep(
    ' BROWN_SPECIAL_DURATION=Math.max(BROWN_SPECIAL_BODY_DURATION,BROWN_POWER_DURATION);',
    ' BROWN_SPECIAL_DURATION=BROWN_POWER_DURATION;',
    'special single-cycle duration'
)

rep(
    'setTimeout(()=>{brownAttackAssetsReady=true},3500);',
    'setTimeout(()=>{brownAttackAssetsReady=true},12000);',
    'brown preload fallback'
)

rep(
    """ const progress=clamp((at-Number(p.startedAt||at))/duration,0,1);
 const travelProgress=1-Math.pow(1-progress,2.35);""",
    """ const progress=clamp((at-Number(p.startedAt||at))/duration,0,1);
 // O poder percorre a trajetória mais rápido e chega ao destino antes do GIF acabar.
 const moveProgress=clamp(progress/.65,0,1);
 const travelProgress=1-Math.pow(1-moveProgress,2.65);""",
    'special travel speed'
)

rep(
    "img.style.transform=`translate(-50%,-50%) rotate(${angle}rad)`;",
    """// Mantém o poder visualmente em pé quando a direção aponta para a esquerda.
   const flipX=Math.cos(angle)<0;
   const visualAngle=flipX?angle+Math.PI:angle;
   img.style.transform=`translate(-50%,-50%) rotate(${visualAngle}rad) scaleX(${flipX?-1:1})`;""",
    'special upright orientation'
)

rep(
    "const typeScale=e.type==='golem'?1.34:e.type==='brownWarrior'?1.04:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;",
    "const typeScale=e.type==='golem'?1.34:e.type==='brownWarrior'?1.10:e.type==='mage'?0.96:e.type==='dragon'?1.16:e.type==='king'?0.96:1;",
    'brown visual scale'
)

p.write_text(t,encoding='utf-8')
print('Brown Warrior tuning applied.')
