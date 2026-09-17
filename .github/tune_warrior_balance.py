from pathlib import Path

p = Path('index.html')
t = p.read_text(encoding='utf-8')


def replace_once(old, new, label):
    global t
    if new in t:
        return
    count = t.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected 1 old anchor, found {count}')
    t = t.replace(old, new, 1)


# Guerreiro normal e Guerreiro do Egito compartilham o mesmo custo-base.
replace_once(
    "const WAR_UNIT_COSTS=Object.freeze({warrior:50,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550});",
    "const WAR_UNIT_COSTS=Object.freeze({warrior:65,brownWarrior:450,king:400,golem:550,mage:550,dragon:450,naja:550});",
    'Warrior cost',
)

# Atualiza metadados acessiveis/titles da loja para refletirem o novo preco.
replace_once(
    'aria-label="Comprar Guerreiro por 50 gemas" title="Guerreiro — 50 gemas"',
    'aria-label="Comprar Guerreiro por 65 gemas" title="Guerreiro — 65 gemas"',
    'Normal warrior shop price text',
)
replace_once(
    'aria-label="Comprar Guerreiro do Egito por 50 gemas" title="Guerreiro do Egito — 50 gemas"',
    'aria-label="Comprar Guerreiro do Egito por 65 gemas" title="Guerreiro do Egito — 65 gemas"',
    'Egypt warrior shop price text',
)

# Ambos usam a mesma rotina de ataque. Aumentar o cooldown reduz levemente a cadencia.
replace_once(
    " // Guerreiros atacam um pouco mais devagar que na versão anterior.\n e.attackCooldown=.38;\n e.attackAnim=.30;",
    " // Guerreiros normais e do Egito atacam em cadencia um pouco mais lenta.\n e.attackCooldown=.50;\n e.attackAnim=.30;",
    'Warrior attack cadence',
)

p.write_text(t, encoding='utf-8')

required = [
    'warrior:65',
    'Comprar Guerreiro por 65 gemas',
    'Comprar Guerreiro do Egito por 65 gemas',
    'e.attackCooldown=.50;',
]
missing = [x for x in required if x not in t]
if missing:
    raise SystemExit('Missing warrior balance tuning: ' + repr(missing))

print('Warrior price and attack cadence tuning applied.')
