from pathlib import Path
p=Path('index.html')
t=p.read_text(encoding='utf-8')
old='''        <div class="small">Guerreiro 75 • Dragão 350 • Golem 350 • Mago 550 gemas.</div>\n        <div class="small">O vencedor de cada rodada recebe +200 gemas extras na rodada seguinte.</div>'''
new='''        <div class="small">Guerreiro 50 • Rei 300 • Dragão 450 • Golem 550 • Mago 550 gemas.</div>\n        <div class="small">Rodada: vencedor +200 • perdedores +100 • empate +100 para todos.</div>\n        <div class="small">Metas: 5 especiais +70 • 3 ataques à distância +40 gemas.</div>'''
if t.count(old)!=1:
    raise SystemExit(f'expected exactly one old economy info block, found {t.count(old)}')
p.write_text(t.replace(old,new,1),encoding='utf-8')
print('economy info updated')
