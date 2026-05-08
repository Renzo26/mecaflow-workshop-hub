# Diagrama de Classes — Mecaflow

> Abra o preview do Markdown no VS Code (`Ctrl+Shift+V`) para visualizar o diagrama renderizado.

---

## Modelos ORM (SQLAlchemy)

```mermaid
classDiagram
    direction TB

    class Workshop {
        +UUID id
        +str name
        +str cnpj
        +str phone
        +str email
        +datetime created_at
    }

    class User {
        +UUID id
        +UUID workshop_id
        +str name
        +str email
        +str password_hash
        +UserRole role
        +bool is_active
        +datetime created_at
    }

    class UserRole {
        <<enumeration>>
        ADMIN
        AGENT
    }

    class Client {
        +UUID id
        +UUID workshop_id
        +str nome
        +str telefone
        +str veiculo
        +str placa
        +str ultimo_atendimento
        +str resumo
        +datetime created_at
    }

    class Appointment {
        +UUID id
        +UUID workshop_id
        +str data
        +str hora
        +str titulo
        +str cliente
        +datetime created_at
    }

    class Conversation {
        +UUID id
        +str waha_chat_id
        +str lead_name
        +str lead_phone
        +str session
        +ConversationStatus status
        +str assigned_agent_id
        +str assigned_agent_name
        +int unread_count
        +str last_message
        +datetime last_message_at
        +datetime created_at
        +datetime updated_at
    }

    class ConversationStatus {
        <<enumeration>>
        BOT
        HUMAN
        UNASSIGNED
        RESOLVED
    }

    class Message {
        +UUID id
        +UUID conversation_id
        +str content
        +MessageType type
        +str sender_name
        +bool is_from_lead
        +str media_url
        +str waha_message_id
        +datetime created_at
    }

    class MessageType {
        <<enumeration>>
        TEXT
        IMAGE
        AUDIO
        DOCUMENT
    }

    class ConversationLabel {
        +UUID id
        +UUID conversation_id
        +str name
        +str color
    }

    class WorkshopLabel {
        +UUID id
        +UUID workshop_id
        +str nome
        +str cor
        +str descricao
        +datetime created_at
    }

    Workshop "1" --> "N" User : users
    Workshop "1" --> "N" Client : clients
    Workshop "1" --> "N" Appointment : appointments
    Workshop "1" --> "N" WorkshopLabel : labels
    User --> UserRole
    Conversation "1" --> "N" Message : messages
    Conversation "1" --> "N" ConversationLabel : labels
    Conversation --> ConversationStatus
    Message --> MessageType
```

---

## Schemas Pydantic (Entrada / Saída)

```mermaid
classDiagram
    direction LR

    class RegisterIn {
        +str workshop_name
        +str name
        +EmailStr email
        +str password
    }
    class LoginIn {
        +EmailStr email
        +str password
    }
    class RefreshIn {
        +str refresh_token
    }
    class TokenOut {
        +str access_token
        +str refresh_token
        +str token_type
        +UserOut user
        +WorkshopOut workshop
    }
    class UserOut {
        +UUID id
        +str name
        +str email
        +str role
        +UUID workshop_id
    }
    class WorkshopOut {
        +UUID id
        +str name
    }

    class ClientIn {
        +str nome
        +str telefone
        +str veiculo
        +str placa
        +str ultimo_atendimento
        +str resumo
    }
    class ClientOut {
        +UUID id
        +UUID workshop_id
        +datetime created_at
    }
    ClientOut --|> ClientIn

    class AppointmentIn {
        +str data
        +str hora
        +str titulo
        +str cliente
    }
    class AppointmentOut {
        +UUID id
        +UUID workshop_id
        +datetime created_at
    }
    AppointmentOut --|> AppointmentIn

    class ConversationSummary {
        +UUID id
        +str waha_chat_id
        +str lead_name
        +str lead_phone
        +str session
        +ConversationStatus status
        +str assigned_agent_id
        +str assigned_agent_name
        +int unread_count
        +str last_message
        +datetime last_message_at
        +datetime created_at
        +list~LabelOut~ labels
    }
    class ConversationDetail {
        +datetime updated_at
    }
    ConversationDetail --|> ConversationSummary

    class MessageOut {
        +UUID id
        +UUID conversation_id
        +str content
        +MessageType type
        +str sender_name
        +bool is_from_lead
        +str media_url
        +str waha_message_id
        +datetime created_at
    }
    class SendMessageIn {
        +str content
    }
    class MessagePage {
        +list~MessageOut~ items
        +int total
        +int page
        +int size
    }

    class LabelIn {
        +str name
        +str color
    }
    class LabelOut {
        +UUID id
        +str name
        +str color
    }

    class WorkshopLabelIn {
        +str nome
        +str cor
        +str descricao
    }
    class WorkshopLabelOut {
        +UUID id
        +UUID workshop_id
        +datetime created_at
    }
    WorkshopLabelOut --|> WorkshopLabelIn

    class WahaWebhookRequest {
        +str event
        +WahaMessagePayload payload
    }
    class WahaMessagePayload {
        +str id
        +str from_field
        +str to
        +str body
        +bool fromMe
        +bool hasMedia
        +str notifyName
        +WahaMediaPayload media
        +WahaInnerData inner_data
    }
    class WahaMediaPayload {
        +str url
        +str mimetype
    }
    class WahaInnerData {
        +str notifyName
    }
    WahaWebhookRequest --> WahaMessagePayload
    WahaMessagePayload --> WahaMediaPayload
    WahaMessagePayload --> WahaInnerData

    TokenOut --> UserOut
    TokenOut --> WorkshopOut
```

---

## Serviços (Lógica de Negócio)

```mermaid
classDiagram
    direction TB

    class AuthService {
        +register(db, workshop_name, name, email, password) tuple~User Workshop~
        +login(db, email, password) tuple~User Workshop~
        +refresh(db, refresh_token) tuple~User Workshop~
        +get_current_user(db, token) User
    }

    class ConversationService {
        +process_webhook(db, body) None
        +list_conversations(db, tab, agent_id) list~Conversation~
        +get_conversation(db, conv_id) Conversation
        +list_messages(db, conv_id, page, size) tuple~list~Message~ int~
        +send_message(db, conv, content, agent_name) Message
        +mark_as_read(db, conv) None
        +reopen(db, conv) Conversation
        +update_name(db, conv, lead_name) Conversation
        +resolve(db, conv) Conversation
        +assign(db, conv, agent_id, agent_name) Conversation
        +set_human(db, conv, redis_service) Conversation
        +set_bot(db, conv, redis_service) Conversation
        +add_label(db, conv, name, color) ConversationLabel
        +remove_label(db, conv_id, label_id) bool
    }

    class WahaService {
        -str _base_url
        -str _session
        -dict _headers
        +send_text(chat_id, text) str
    }

    class RedisService {
        -Redis _redis
        +set_human_block(waha_chat_id) None
        +del_human_block(waha_chat_id) None
    }

    class SSEBroadcaster {
        -set~Queue~ _queues
        +publish(event, data) None
        +subscribe() AsyncGenerator~str~
    }

    class ConflictError {
        <<exception>>
    }
    class AuthError {
        <<exception>>
    }
    class ValidationError {
        <<exception>>
    }

    ConversationService --> WahaService : envia mensagens
    ConversationService --> RedisService : bloqueia/libera bot
    ConversationService --> SSEBroadcaster : publica eventos
    AuthService --> ConflictError : lança
    AuthService --> AuthError : lança
```

---

## Routers FastAPI (API)

```mermaid
classDiagram
    direction LR

    class AuthRouter {
        <<router /auth>>
        +POST /register() TokenOut
        +POST /login() TokenOut
        +POST /refresh() TokenOut
        +GET /me() UserOut
    }

    class ConversationsRouter {
        <<router /conversations>>
        +GET /() list~ConversationSummary~
        +GET /{id}() ConversationDetail
        +GET /{id}/messages() MessagePage
        +POST /{id}/messages() MessageOut
        +PATCH /{id}/read() None
        +PATCH /{id}/reopen() ConversationDetail
        +PATCH /{id}/name() ConversationDetail
        +PATCH /{id}/resolve() ConversationDetail
        +PATCH /{id}/assign() ConversationDetail
        +PATCH /{id}/human() ConversationDetail
        +PATCH /{id}/bot() ConversationDetail
        +POST /{id}/labels() LabelOut
        +DELETE /{id}/labels/{lid}() None
    }

    class ClientsRouter {
        <<router /clients>>
        +GET /() list~ClientOut~
        +POST /() ClientOut
        +PUT /{id}() ClientOut
        +DELETE /{id}() None
    }

    class AppointmentsRouter {
        <<router /appointments>>
        +GET /() list~AppointmentOut~
        +POST /() AppointmentOut
        +PUT /{id}() AppointmentOut
        +DELETE /{id}() None
    }

    class LabelsRouter {
        <<router /labels>>
        +GET /() list~WorkshopLabelOut~
        +POST /() WorkshopLabelOut
        +PUT /{id}() WorkshopLabelOut
        +DELETE /{id}() None
    }

    class UsersRouter {
        <<router /users>>
        +GET /() list~UserOut~
        +POST /() UserOut
        +PUT /{id}() UserOut
        +DELETE /{id}() None
    }

    class WebhooksRouter {
        <<router /webhooks>>
        +POST /waha() None
    }

    class SSERouter {
        <<router /sse>>
        +GET /events() StreamingResponse
    }

    AuthRouter --> AuthService
    ConversationsRouter --> ConversationService
    ClientsRouter --> AuthService : JWT guard
    AppointmentsRouter --> AuthService : JWT guard
    LabelsRouter --> AuthService : JWT guard
    UsersRouter --> AuthService : JWT guard
    WebhooksRouter --> ConversationService
    SSERouter --> SSEBroadcaster
```

---

## Visão Geral das Camadas

```mermaid
graph TD
    subgraph API["Camada API (Routers)"]
        AR[AuthRouter]
        CR[ConversationsRouter]
        CLR[ClientsRouter]
        APR[AppointmentsRouter]
        LR[LabelsRouter]
        UR[UsersRouter]
        WR[WebhooksRouter]
        SR[SSERouter]
    end

    subgraph Services["Camada de Serviços"]
        AS[AuthService]
        CS[ConversationService]
        WS[WahaService]
        RS[RedisService]
        SS[SSEBroadcaster]
    end

    subgraph Models["Camada de Modelos"]
        W[Workshop]
        U[User]
        C[Client]
        A[Appointment]
        CONV[Conversation]
        MSG[Message]
        CL[ConversationLabel]
        WL[WorkshopLabel]
    end

    subgraph Infra["Infraestrutura"]
        DB[(PostgreSQL / Supabase)]
        RD[(Redis)]
        WH[WAHA WhatsApp]
    end

    AR --> AS
    CR --> CS
    CLR --> AS
    APR --> AS
    LR --> AS
    UR --> AS
    WR --> CS
    SR --> SS

    AS --> U
    AS --> W
    CS --> CONV
    CS --> MSG
    CS --> CL
    CS --> WS
    CS --> RS
    CS --> SS

    WS --> WH
    RS --> RD
    W & U & C & A & CONV & MSG & CL & WL --> DB
```
