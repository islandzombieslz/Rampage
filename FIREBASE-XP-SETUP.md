# Rampage — XP exclusivamente na conta Firebase

**Projeto:** `rampage-69334`, Realtime Database `rampage-69334-default-rtdb`. O código do jogo foi ajustado para usar exclusivamente `profiles/<UID>/totalXp` como saldo de XP. Nenhum saldo local é usado como nível, e o jogo só exibe XP após confirmar a leitura **e a escrita** no perfil. O HUD aparece desde o primeiro menu; durante a partida fica oculto.

## Etapa obrigatória no Firebase Console

[Abrir as regras do Realtime Database](https://console.firebase.google.com/project/rampage-69334/database/rampage-69334-default-rtdb/rules)

O jogo está hospedado no GitHub Pages; **alterar `index.html` não altera automaticamente as permissões do Firebase**. O projeto precisa autorizar a conta autenticada a ler e escrever apenas o seu perfil. No console, preserve todas as regras já existentes, especialmente `rooms`, e adicione o seguinte bloco como irmão de `rooms` dentro do objeto `"rules"`:

```json
"profiles": {
  "$uid": {
    ".read": "auth != null && auth.uid === $uid",
    ".write": "auth != null && auth.uid === $uid && newData.exists() && newData.child('totalXp').isNumber() && (!data.exists() || newData.child('totalXp').val() >= data.child('totalXp').val())",
    "totalXp": {
      ".validate": "newData.isNumber() && newData.val() >= 0"
    },
    "awards": {
      "$matchId": {
        ".validate": "newData.hasChildren(['xp', 'mode', 'at']) && newData.child('xp').isNumber() && newData.child('xp').val() >= 50 && newData.child('xp').val() <= 400 && newData.child('mode').isString() && newData.child('at').isNumber()"
      }
    }
  }
}
```

Este bloco é um **trecho**, não um arquivo completo de regras. Não substitua o objeto inteiro por ele: isso quebraria as salas online. Publique as regras no console e recarregue o jogo.

O Firebase Realtime Database exige **permissões de leitura e escrita** para transações; o jogo agora testa ambas antes de liberar uma partida com XP. Uma conta recém-criada recebe `totalXp: 0` no próprio Firebase. Uma recompensa só é somada e anunciada após confirmação da transação. Cada ID de partida permanece registrado em `awards`, evitando premiações duplicadas.

Enquanto o perfil não estiver acessível, o jogo não inventa nível nem apresenta XP local: informa o erro e impede iniciar uma partida que não teria XP persistido. Somente recibos antigos **pendentes da versão anterior** podem ser migrados uma única vez para o Firebase depois de confirmada a conexão; nunca são contabilizados na barra antes de serem salvos na conta.

**Importante sobre segurança:** permitir que o cliente escreva no próprio perfil garante isolamento por UID, mas não impede que um cliente modificado apresente um resultado falso. Para XP antifraude, rankings ou recompensas de valor, a concessão deve ser validada por um backend confiável (por exemplo, Cloud Functions) com regras de escrita do XP restritas ao servidor. Sem acesso administrativo ao projeto, estas regras não podem ser publicadas pelo repositório.
