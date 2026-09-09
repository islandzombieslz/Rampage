from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')

# Códigos oficiais atuais.
old_codes="const ROOM_CODES=['REI','PLEBEU','CONDE'];"
room_codes="const ROOM_CODES=['REI','PLEBEU','CONDE','VINHO','FURIA','PAZ','DRAGON'];"
if room_codes not in text:
    if old_codes not in text:
        raise SystemExit('Lista de códigos de sala não encontrada')
    text=text.replace(old_codes,room_codes,1)

# A criação deve testar cada código uma vez em ordem aleatória.
old_pick="let code=null;for(let i=0;i<32;i++){const c=generateCode(),s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));if(!s.exists()){code=c;break}}"
new_pick="let code=null;const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);for(const c of roomCandidates){const s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));if(!s.exists()){code=c;break}}"
if new_pick not in text and 'const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);' not in text:
    if old_pick not in text:
        raise SystemExit('Seleção de código da sala não encontrada')
    text=text.replace(old_pick,new_pick,1)

# Gemas: 3000 continua sendo apenas o teto configurável antes da partida.
old_round='p.gems=clamp(state.gems+(p.bonusGems||0),0,3000);'
new_round='p.gems=Math.max(0,state.gems+(p.bonusGems||0));'
if new_round not in text:
    if old_round not in text: raise SystemExit('Regra de gemas por rodada não encontrada')
    text=text.replace(old_round,new_round,1)
config_cap="if(b.dataset.target==='gems') state.gems=clamp(state.gems+dir*100,300,3000);"
if config_cap not in text: raise SystemExit('Teto configurável de 3000 gemas foi alterado')

# Barras atuais, já reduzidas pela rodada seguinte de balanceamento.
base_bars='position:absolute;left:15px;top:-3px;width:48px;height:12px;'
base_bg='.hp-bg,.shield-bg{position:absolute;left:0;width:48px'
king_bars='.entity-visual.king-visual .entity-bars{left:36px;top:-4px;width:66px}'
king_bg='.entity-visual.king-visual .shield-bg{width:66px}'
for required in [base_bars,base_bg,king_bars,king_bg]:
    if required not in text: raise SystemExit('Barras atuais não encontradas: '+required)

required=[
    room_codes,
    'return ROOM_CODES[Math.floor(Math.random()*ROOM_CODES.length)];',
    'const roomCandidates=[...ROOM_CODES].sort(()=>Math.random()-.5);',
    config_cap,new_round,
    base_bars,base_bg,king_bars,king_bg,
    'ROOM LIFECYCLE 2026-09-09',
    'const ROOM_INACTIVITY_MS=10*60*1000;',
    "const WAR_UNIT_COSTS=Object.freeze({warrior:50,king:400,golem:550,mage:550,dragon:450});",
    'e.hp=e.maxHp=280;','e.shield=e.maxShield=280;','e.damage=35;',
    'e.hp=e.maxHp=150;','e.shield=e.maxShield=100;',
]
missing=[m for m in required if m not in text]
if missing: raise SystemExit('Validação final falhou: '+repr(missing))

forbidden=[
    'const ROOM_COLOR_NAMES=[',
    "const ROOM_CODES=['REI','PLEBEU','CONDE'];",
    'p.gems=clamp(state.gems+(p.bonusGems||0),0,3000);',
]
present=[m for m in forbidden if m in text]
if present: raise SystemExit('Comportamento antigo ainda presente: '+repr(present))

path.write_text(text,encoding='utf-8')
print('Room/gems patch aligned with 7 codes, lifecycle cleanup and current compact bars.')
