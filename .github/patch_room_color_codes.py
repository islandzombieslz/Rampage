from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

replacements = [
    (
        '.code{font-size:26px;letter-spacing:5px;font-weight:900;color:var(--gold)}',
        '.code{font-size:26px;letter-spacing:2px;font-weight:900;color:var(--gold);overflow-wrap:anywhere}'
    ),
    (
        '<input id="roomCodeInput" maxlength="6" placeholder="ABC123" style="text-transform:uppercase;flex:1">',
        '<input id="roomCodeInput" maxlength="32" placeholder="AZUL-CORAL" autocapitalize="characters" spellcheck="false" style="text-transform:uppercase;flex:1">'
    ),
    (
        "function generateCode(){ return Math.random().toString(36).slice(2,8).toUpperCase(); }",
        """const ROOM_COLOR_NAMES=[
 'AZUL','VERDE','VERMELHO','AMARELO','LARANJA','ROXO','ROSA','PRETO','BRANCO','CINZA','MARROM','BEGE',
 'DOURADO','PRATA','CORAL','TURQUESA','VIOLETA','LILAS','MAGENTA','CIANO','BORDO','VINHO','SALMAO','CREME',
 'CARAMELO','MOSTARDA','ESMERALDA','SAFIRA','RUBI','AMBAR','JADE','OLIVA','MENTA','LIMA','INDIGO','ANIL',
 'COBRE','BRONZE','GRAFITE','PEROLA','AREIA','CHOCOLATE','CARMIM','ESCARLATE','FERRUGEM'
];
function normalizeRoomCode(value){
 const raw=String(value||'').trim().toUpperCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');
 // Compatibilidade: salas antigas de 6 caracteres continuam acessíveis enquanto existirem.
 if(/^[A-Z0-9]{6}$/.test(raw))return raw;
 return raw.replace(/\\s+/g,'-').replace(/[^A-Z-]/g,'').replace(/-+/g,'-').replace(/^-|-$/g,'');
}
function generateCode(){
 const n=ROOM_COLOR_NAMES.length;
 const ai=Math.floor(Math.random()*n);
 let bi=Math.floor(Math.random()*(n-1));
 if(bi>=ai)bi++;
 return ROOM_COLOR_NAMES[ai]+'-'+ROOM_COLOR_NAMES[bi];
}"""
    ),
    (
        "async createRoom(snapshot){const F=await this.waitFirebase(),user=await this.ensureAuth();let code=null;for(let i=0;i<8;i++){const c=generateCode(),s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));if(!s.exists()){code=c;break}}if(!code)throw Error('Falha ao gerar sala');",
        "async createRoom(snapshot){const F=await this.waitFirebase(),user=await this.ensureAuth();let code=null;for(let i=0;i<32;i++){const c=generateCode(),s=await F.get(F.ref(F.firebaseDb,`rooms/${c}`));if(!s.exists()){code=c;break}}if(!code)throw Error('Falha ao gerar sala');"
    ),
    (
        "async joinRoom(code){const F=await this.waitFirebase(),user=await this.ensureAuth();code=(code||'').trim().toUpperCase();",
        "async joinRoom(code){const F=await this.waitFirebase(),user=await this.ensureAuth();code=normalizeRoomCode(code);"
    ),
    (
        "const code=$('#roomCodeInput').value.trim().toUpperCase();\n  const res=await NetworkAdapter.joinRoom(code);",
        "const code=normalizeRoomCode($('#roomCodeInput').value);\n  const res=await NetworkAdapter.joinRoom(code);"
    ),
]

for old, new in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'Expected exactly one match, found {count}: {old[:90]}')
    text = text.replace(old, new, 1)

path.write_text(text, encoding='utf-8')
print('Color-name room code patch applied')
