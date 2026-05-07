# MecaFlow — Contexto Completo do Módulo de Conversas

> Este documento é a fonte de verdade sobre credenciais, URLs, fluxos e arquitetura de integração do módulo de conversas. Destina-se a modelos de linguagem que darão continuidade ao desenvolvimento.

---

## 1. Serviços Envolvidos

O módulo de conversas conecta quatro serviços externos:

| Serviço     | Papel                                                                 |
|-------------|-----------------------------------------------------------------------|
| **WAHA**    | Provedor WhatsApp HTTP API (auto-hospedado). Recebe/envia mensagens.  |
| **n8n**     | Motor de automações. Roda o CloudyBot (resposta automática).          |
| **EasyPanel** | Plataforma de hospedagem onde WAHA, n8n e o backend vivem.          |
| **Neon**    | PostgreSQL gerenciado (cloud). Banco de dados do backend.             |

---

## 2. URLs de Produção

| Recurso                    | URL                                                                |
|----------------------------|--------------------------------------------------------------------|
| Backend API (prod)         | `https://portfloio-meca-flow-api.e4xqua.easypanel.host/api`       |
| Frontend (prod)            | `https://portfloio-meca-flow.e4xqua.easypanel.host`               |
| WAHA API                   | `https://cloudy-waha.e4xqua.easypanel.host`                       |
| n8n Webhook (CloudyBot)    | `https://n8n.cloudysolutions.fun/webhook/Recebemensagem`           |
| Backend local (dev)        | `http://localhost:8080/api`                                        |
| Frontend local (dev)       | `http://localhost:4200`                                            |

---

## 3. Credenciais e Configurações

### 3.1 WAHA

| Parâmetro    | Valor                              |
|--------------|------------------------------------|
| URL base     | `https://cloudy-waha.e4xqua.easypanel.host` |
| API Key      | `DH2zDGOz7KusN1UItxTI4LZxVeIVig9g` |
| Header       | `X-Api-Key: DH2zDGOz7KusN1UItxTI4LZxVeIVig9g` |
| Session name | `Cloudy`                           |

### 3.2 PostgreSQL (Neon)

| Parâmetro    | Valor                                                                                                |
|--------------|------------------------------------------------------------------------------------------------------|
| Host         | `ep-small-sun-aia1wbw6-pooler.c-4.us-east-1.aws.neon.tech`                                         |
| Database     | `neondb`                                                                                             |
| Username     | `neondb_owner`                                                                                       |
| Password     | `npg_Abdu0NUXRK6E`                                                                                  |
| JDBC URL     | `jdbc:postgresql://ep-small-sun-aia1wbw6-pooler.c-4.us-east-1.aws.neon.tech/neondb?user=neondb_owner&password=npg_Abdu0NUXRK6E&sslmode=require&channelBinding=require` |

### 3.3 Redis (compartilhado com n8n no EasyPanel)

| Parâmetro | Valor                                                                 |
|-----------|-----------------------------------------------------------------------|
| URL       | `redis://default:c875c4dcf056a7f60c08@cloudy_evolution-api-redis:6379` |
| Uso       | Chave de bloqueio do bot (controle humano/bot)                        |

### 3.4 JWT (backend)

| Parâmetro             | Valor                                                                  |
|-----------------------|------------------------------------------------------------------------|
| Secret                | `mecaflow-tcc-secret-key-must-be-at-least-256-bits-long-for-hs256`    |
| Access token TTL      | `28800000` ms (8 horas)                                                |
| Refresh token TTL     | `604800000` ms (7 dias)                                                |

---

## 4. Arquitetura de Comunicação

### 4.1 Recebimento de mensagens (WAHA → backend → frontend)

```
WhatsApp
   │
   ▼
WAHA recebe mensagem
   │
   ├──► POST https://n8n.cloudysolutions.fun/webhook/Recebemensagem
   │         (CloudyBot avalia e responde automaticamente se bot ativo)
   │
   └──► POST https://portfloio-meca-flow-api.e4xqua.easypanel.host/api/webhooks/waha
             │
             ▼
        WebhookController → WebhookService
             │ - Deduplicação por wahaMessageId
             │ - Cria/busca Conversation por wahaChatId
             │ - Salva Message
             │ - Dispara AutomationService
             │ - Publica via SSE
             ▼
        Frontend (SSE listener)
             │ - evento "message" → atualiza lista de mensagens
             └─ evento "conversation" → atualiza painel de conversas
```

### 4.2 Envio de mensagens (agente → WhatsApp)

```
Agente digita e envia no frontend
   │
   ▼
POST /api/conversations/{id}/messages  { "content": "texto" }
   │
   ▼
ConversationService.sendMessage()
   │
   ▼
WahaApiService.sendText(chatId, text)
   │
   ▼
POST https://cloudy-waha.e4xqua.easypanel.host/api/sendText
     { "session": "Cloudy", "chatId": "5511...@c.us", "text": "..." }
```

### 4.3 Controle bot / humano (via Redis)

O CloudyBot (n8n) verifica no Redis se há uma chave de bloqueio antes de responder. O backend escreve/apaga essa chave.

| Ação no frontend              | Operação Redis                                          |
|-------------------------------|---------------------------------------------------------|
| Agente clica "Assumir"        | `SET CloudSolutions_{wahaChatId}_block true` (sem TTL) |
| Agente clica "Liberar bot"    | `DEL CloudSolutions_{wahaChatId}_block`                 |

Enquanto a chave existir, o n8n ignora a conversa e não responde.

---

## 5. Endpoints do Backend (módulo conversas)

### Webhook WAHA

```
POST /api/webhooks/waha
```

Payload esperado (envelope WAHA):
```json
{
  "payload": {
    "from": "5511999999999@c.us",
    "to": "...",
    "body": "texto",
    "fromMe": false,
    "id": "waha-message-id-unico",
    "hasMedia": false,
    "media": {
      "url": "https://...",
      "mimetype": "audio/ogg"
    },
    "_data": {
      "notifyName": "Nome do Contato"
    }
  }
}
```

### Conversas

```
GET    /api/conversations                        Lista conversas (filtro: ?tab=ALL|MINE|UNASSIGNED|RESOLVED)
GET    /api/conversations/{id}                   Detalhe da conversa
GET    /api/conversations/{id}/messages          Mensagens paginadas (?page=0&size=50)
POST   /api/conversations/{id}/messages          Enviar mensagem { "content": "texto" }
PATCH  /api/conversations/{id}/resolve           Marcar como resolvida
PATCH  /api/conversations/{id}/assign            Atribuir { "agentId": "...", "agentName": "..." }
PATCH  /api/conversations/{id}/human             Agente assume (bloqueia bot no Redis)
PATCH  /api/conversations/{id}/bot               Libera bot (apaga chave Redis)
POST   /api/conversations/{id}/labels            Adicionar label
DELETE /api/conversations/{id}/labels/{labelId}  Remover label
```

### SSE (realtime)

```
GET /api/sse/events
```

Eventos emitidos:
- `message` — nova mensagem recebida
- `conversation` — conversa atualizada (status, agente, etc.)

O frontend usa `EventSource` nativo. **Não é WebSocket nem Socket.io** — é SSE (Server-Sent Events).

---

## 6. Modelo de Dados

### Conversation

| Campo            | Tipo    | Descrição                                              |
|------------------|---------|--------------------------------------------------------|
| `wahaChatId`     | String  | ID do chat WAHA (`{phone}@c.us`)                       |
| `leadName`       | String  | Nome do contato                                        |
| `leadPhone`      | String  | Número de telefone                                     |
| `session`        | String  | Sempre `"Cloudy"`                                      |
| `status`         | Enum    | `BOT` \| `HUMAN` \| `UNASSIGNED` \| `RESOLVED`         |
| `assignedAgentId`| String  | ID do agente responsável                               |
| `unreadCount`    | Integer | Mensagens não lidas                                    |
| `lastMessage`    | String  | Último texto recebido/enviado                          |
| `lastMessageAt`  | DateTime| Timestamp da última mensagem                           |

### Message

| Campo          | Tipo    | Descrição                                          |
|----------------|---------|----------------------------------------------------|
| `content`      | String  | Texto da mensagem                                  |
| `type`         | Enum    | `TEXT` \| `IMAGE` \| `AUDIO` \| `DOCUMENT`         |
| `senderName`   | String  | Quem enviou                                        |
| `isFromLead`   | Boolean | `true` = cliente, `false` = bot/agente             |
| `mediaUrl`     | String  | URL da mídia (se aplicável)                        |
| `wahaMessageId`| String  | ID único do WAHA (usado para deduplicação)         |

---

## 7. Configurações de CORS

Origens permitidas no backend:

- `http://localhost:4200` (dev)
- `http://localhost:5173` (dev alternativo)
- `https://portfloio-meca-flow.e4xqua.easypanel.host` (produção)

---

## 8. Variáveis de Ambiente (application.properties)

```properties
# Banco de dados
spring.datasource.url=jdbc:postgresql://ep-small-sun-aia1wbw6-pooler.c-4.us-east-1.aws.neon.tech/neondb?user=neondb_owner&password=npg_Abdu0NUXRK6E&sslmode=require&channelBinding=require
spring.datasource.username=neondb_owner
spring.datasource.password=npg_Abdu0NUXRK6E

# WAHA (fallback para valores hardcoded se env não definida)
waha.base-url=${WAHA_BASE_URL:https://cloudy-waha.e4xqua.easypanel.host}
waha.api-key=${WAHA_API_KEY:DH2zDGOz7KusN1UItxTI4LZxVeIVig9g}
waha.session=${WAHA_SESSION:Cloudy}

# JWT
jwt.secret=mecaflow-tcc-secret-key-must-be-at-least-256-bits-long-for-hs256
jwt.access-token-expiration=28800000
jwt.refresh-token-expiration=604800000
```

---

## 9. Observações Importantes para o Desenvolvedor

1. **Webhook sem autenticação:** o endpoint `POST /api/webhooks/waha` não valida origem. Qualquer cliente pode postar nele.

2. **SSE, não WebSocket:** o frontend usa `EventSource` (SSE), não Socket.io. O arquivo `websocket.service.ts` existe mas o backend não implementa Socket.io.

3. **Redis compartilhado com n8n:** a chave `CloudSolutions_{wahaChatId}_block` é lida pelo n8n. Mudanças no padrão da chave precisam ser sincronizadas com o workflow do n8n.

4. **Deduplicação de mensagens:** feita pelo campo `wahaMessageId` na tabela `message`. O WAHA pode disparar o webhook `message` e `message.any` para a mesma mensagem — sem esse controle haveria duplicatas.

5. **Formato do chatId:** WAHA envia mensagens com `@s.whatsapp.net` para grupos e `@c.us` para individuais. O backend normaliza tudo para `@c.us`.

6. **Sessão fixa:** o nome da sessão WAHA é sempre `"Cloudy"`. Caso a sessão seja recriada no painel WAHA, todos os webhooks param de funcionar até a sessão ser reconectada.
