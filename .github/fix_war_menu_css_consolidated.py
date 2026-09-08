from pathlib import Path

p=Path('index.html')
t=p.read_text(encoding='utf-8')

CANON='WAR CONFIG CANONICAL OVERRIDE — 2026-09-08'
if CANON in t:
    print('canonical override already present; no changes')
    raise SystemExit(0)

# 1) Remove the first war-only corrective block that was added earlier.
old_start='/* Mestre da Guerra: mantém todos os controles dentro da área útil do sprite. */'
old_end='.config{padding:16px;background:#0d1117;border:1px solid var(--line);border-radius:15px}'
if old_start in t:
    a=t.index(old_start)
    b=t.index(old_end,a)
    t=t[:a]+t[b:]
else:
    print('older war-specific block already absent')

# 2) Remove the V2 block that was appended at the end of the only style block.
v2='/* WAR MENU COMPACT BUTTONS V2 — somente Mestre da Guerra */'
if v2 in t:
    a=t.index(v2)
    b=t.index('</style>',a)
    t=t[:a]+t[b:]
else:
    print('V2 block already absent')

# 3) One final, canonical war-only override. It explicitly overrides the older
# shared absolute layout instead of stacking several competing war patches.
css=r'''

/* WAR CONFIG CANONICAL OVERRIDE — 2026-09-08
   Única regra corretiva específica do menu Mestre da Guerra. */
#configScreen.war-config #warConfig{
  position:absolute !important;
  left:26% !important;
  right:26% !important;
  top:31.5% !important;
  bottom:25% !important;
  width:auto !important;
  min-width:0 !important;
  max-width:none !important;
  margin:0 !important;
  padding:0 !important;
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  grid-template-rows:auto auto !important;
  gap:5px 8px !important;
  align-content:center !important;
  align-items:center !important;
}
#configScreen.war-config #warConfig .config{
  width:100% !important;
  min-width:0 !important;
  padding:1px 2px !important;
  margin:0 !important;
}
#configScreen.war-config #warConfig .label{
  font-size:10px !important;
  line-height:1.05 !important;
  margin:0 0 2px !important;
}
#configScreen.war-config #warConfig .option-group{
  gap:4px !important;
}
#configScreen.war-config #warConfig .option-group button{
  width:100% !important;
  min-width:0 !important;
  max-width:100% !important;
  height:22px !important;
  min-height:22px !important;
  padding:0 3px !important;
  margin:0 !important;
  font-size:8.5px !important;
  line-height:1 !important;
  border-radius:6px !important;
}
#configScreen.war-config #warConfig .counter{
  display:grid !important;
  grid-template-columns:22px 34px 22px !important;
  gap:4px !important;
  justify-content:center !important;
  align-items:center !important;
  width:86px !important;
  max-width:86px !important;
  margin:0 auto !important;
}
#configScreen.war-config #warConfig .counter button{
  width:22px !important;
  min-width:22px !important;
  max-width:22px !important;
  height:22px !important;
  min-height:22px !important;
  padding:0 !important;
  margin:0 !important;
  font-size:11px !important;
  line-height:1 !important;
  border-radius:6px !important;
}
#configScreen.war-config #warConfig .counter b{
  width:34px !important;
  min-width:34px !important;
  max-width:34px !important;
  font-size:12px !important;
  line-height:1 !important;
  text-align:center !important;
}
#configScreen.war-config>.card>.divider{
  display:none !important;
}
#configScreen.war-config>.card>.row:last-child{
  position:absolute !important;
  left:27% !important;
  right:27% !important;
  bottom:16.5% !important;
  width:auto !important;
  min-width:0 !important;
  margin:0 !important;
  padding:0 !important;
  display:grid !important;
  grid-template-columns:repeat(2,minmax(0,1fr)) !important;
  gap:8px !important;
}
#configScreen.war-config>.card>.row:last-child button{
  width:100% !important;
  min-width:0 !important;
  max-width:100% !important;
  height:28px !important;
  min-height:28px !important;
  padding:1px 4px !important;
  margin:0 !important;
  font-size:9px !important;
  line-height:1 !important;
  border-radius:7px !important;
  white-space:nowrap !important;
}
@media (pointer:coarse), (max-height:700px), (max-width:800px){
  #configScreen.war-config #warConfig{
    left:27% !important;
    right:27% !important;
    top:31% !important;
    bottom:25.5% !important;
    gap:3px 6px !important;
  }
  #configScreen.war-config #warConfig .label{font-size:9px !important}
  #configScreen.war-config #warConfig .option-group button{
    height:20px !important;
    min-height:20px !important;
    font-size:8px !important;
    padding:0 2px !important;
  }
  #configScreen.war-config #warConfig .counter{
    grid-template-columns:20px 31px 20px !important;
    width:79px !important;
    max-width:79px !important;
    gap:4px !important;
  }
  #configScreen.war-config #warConfig .counter button{
    width:20px !important;
    min-width:20px !important;
    max-width:20px !important;
    height:20px !important;
    min-height:20px !important;
    font-size:10px !important;
  }
  #configScreen.war-config #warConfig .counter b{
    width:31px !important;
    min-width:31px !important;
    max-width:31px !important;
    font-size:11px !important;
  }
  #configScreen.war-config>.card>.row:last-child{
    left:28% !important;
    right:28% !important;
    bottom:16.8% !important;
    gap:6px !important;
  }
  #configScreen.war-config>.card>.row:last-child button{
    height:25px !important;
    min-height:25px !important;
    font-size:8.5px !important;
  }
}
'''
close='</style>'
if t.count(close)!=1:
    raise SystemExit(f'expected one </style>, found {t.count(close)}')
t=t.replace(close,css+'\n'+close,1)

p.write_text(t,encoding='utf-8')
print('consolidated war menu CSS written')
