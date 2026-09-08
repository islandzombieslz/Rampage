from pathlib import Path
import re

p=Path('index.html')
t=p.read_text(encoding='utf-8')
checks={
 'style_open': t.count('<style'),
 'style_close': t.count('</style>'),
 'warConfig_id': t.count('id="warConfig"'),
 'warConfig_css': t.count('#warConfig'),
 'compact_v2': t.count('WAR MENU COMPACT BUTTONS V2'),
 'old_war_specific': t.count('Mestre da Guerra: mantém todos os controles'),
 'old_price_text': t.count('Guerreiro 50 • Rei 300'),
 'round_reward_text': t.count('Rodada: vencedor +200'),
 'goals_text': t.count('Metas: 5 especiais +70'),
 'absolute_shared_config': t.count('#configScreen #pveConfig,\n#configScreen #warConfig{'),
}
for k,v in checks.items(): print(f'{k}={v}')
print('--- style block positions ---')
for m in re.finditer(r'<style[^>]*>',t): print('style at',m.start())
print('--- warConfig contexts ---')
for needle in ['Mestre da Guerra: mantém todos os controles','WAR MENU COMPACT BUTTONS V2','position:absolute !important;\n  left:21% !important;']:
    start=0
    while True:
        i=t.find(needle,start)
        if i<0: break
        print('\nNEEDLE',needle,'AT',i)
        print(t[max(0,i-250):min(len(t),i+900)])
        start=i+1
