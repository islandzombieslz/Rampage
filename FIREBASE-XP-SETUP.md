# Rampage — permissões do XP no Firebase Realtime Database

O progresso é salvo em `profiles/<UID>` por meio de transações. **Não substitua as regras existentes** do Realtime Database: preserve as regras de `rooms` e os demais nós. Adicione apenas o bloco abaixo dentro de `rules` no console do projeto `rampage-69334`.

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

Entre em **Firebase Console → Build → Realtime Database → Rules**, incorpore esse bloco ao objeto `rules` que já existe e publique. Não cole apenas o fragmento como documento completo: isso apagaria regras essenciais da sala.

A conta precisa ter autorização de **leitura e escrita no próprio perfil**: transações de Realtime Database exigem ambas. Não coloque `.read: true` / `.write: true` na raiz.

O cliente registra toda recompensa não sincronizada no armazenamento local por UID antes de gravar no Firebase. Enquanto a gravação não puder ser confirmada, o menu informa “XP neste dispositivo • sincronização pendente”. Ao permitir as regras e recarregar na mesma conta/navegador, o jogo tenta transferir o valor sem premiar o mesmo ID de partida duas vezes. A cópia local não substitui o Firebase para recuperação em outro aparelho.

**Limite de segurança:** regras que permitem ao próprio cliente gravar XP não impedem um cliente modificado de inventar recompensas. Antes de criar rankings públicos ou prêmios reais, a concessão de XP deve migrar para uma função confiável no servidor, validando o resultado da partida.
