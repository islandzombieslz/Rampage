from pathlib import Path

path=Path('index.html')
text=path.read_text(encoding='utf-8')
marker='</style>'
if marker not in text:
    raise SystemExit('style closing tag not found')
css=r'''

/* WAR MENU COMPACT BUTTONS V2 — somente Mestre da Guerra */
#configScreen.war-config #warConfig{
  width:84% !important;
  margin-left:auto !important;
  margin-right:auto !important;
  gap:4px 7px !important;
}
#configScreen.war-config #warConfig .option-group button{
  width:82% !important;
  min-width:0 !important;
  max-width:82% !important;
  height:24px !important;
  min-height:24px !important;
  padding:1px 4px !important;
  font-size:9.5px !important;
  line-height:1 !important;
  border-radius:7px !important;
  justify-self:center !important;
}
#configScreen.war-config #warConfig .counter{
  display:grid !important;
  grid-template-columns:24px 36px 24px !important;
  justify-content:center !important;
  align-items:center !important;
  width:auto !important;
  max-width:100% !important;
  gap:5px !important;
  margin-left:auto !important;
  margin-right:auto !important;
}
#configScreen.war-config #warConfig .counter button{
  width:24px !important;
  min-width:24px !important;
  max-width:24px !important;
  height:24px !important;
  min-height:24px !important;
  padding:0 !important;
  font-size:12px !important;
  line-height:1 !important;
  border-radius:7px !important;
}
#configScreen.war-config #warConfig .counter b{
  width:36px !important;
  min-width:36px !important;
  max-width:36px !important;
  font-size:13px !important;
  line-height:1 !important;
  text-align:center !important;
}
#configScreen.war-config>.card>.row:last-child{
  width:82% !important;
  margin-left:auto !important;
  margin-right:auto !important;
  gap:10px !important;
}
#configScreen.war-config>.card>.row:last-child button{
  width:82% !important;
  min-width:0 !important;
  max-width:82% !important;
  height:30px !important;
  min-height:30px !important;
  padding:2px 5px !important;
  font-size:10px !important;
  line-height:1 !important;
  border-radius:8px !important;
  justify-self:center !important;
}
@media (pointer:coarse), (max-height:700px), (max-width:800px){
  #configScreen.war-config #warConfig{width:80% !important;gap:3px 5px !important}
  #configScreen.war-config #warConfig .option-group button{
    width:78% !important;max-width:78% !important;height:21px !important;min-height:21px !important;font-size:8.5px !important;padding:0 3px !important
  }
  #configScreen.war-config #warConfig .counter{grid-template-columns:21px 32px 21px !important;gap:4px !important}
  #configScreen.war-config #warConfig .counter button{
    width:21px !important;min-width:21px !important;max-width:21px !important;height:21px !important;min-height:21px !important;font-size:11px !important
  }
  #configScreen.war-config #warConfig .counter b{
    width:32px !important;min-width:32px !important;max-width:32px !important;font-size:12px !important
  }
  #configScreen.war-config>.card>.row:last-child{width:78% !important;gap:8px !important}
  #configScreen.war-config>.card>.row:last-child button{
    width:78% !important;max-width:78% !important;height:26px !important;min-height:26px !important;font-size:9px !important;padding:1px 4px !important
  }
}
'''
if 'WAR MENU COMPACT BUTTONS V2' in text:
    raise SystemExit('compact button patch already present')
text=text.replace(marker,css+'\n'+marker,1)
path.write_text(text,encoding='utf-8')
print('war menu buttons compacted')
