# Backend

Here are listed and documented all the FastApi backend server endpoints.

## Starting the server
```bash
cd backend/
python run.py install
python run.py dev
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chats/` | POST | Creates a new chat session |
| `/chats/` | GET | Retrieves the paginated chat sessions |
| `/chats/{chat_id}` | GET | Retrieves conversation history |
| `/chats/{chat_id}/title` | PUT | Updates the title of a specific chat |
| `/chats/{chat_id}` | DELETE | Deletes a chat session |
| `/messages/send` | POST | Sends a message to the chatbot |
| `/messages/{qa_pair_id}/retry` | POST | Regenerates the answer for a specific message |
| `/messages/{qa_pair_id}/edit` | PUT | Edits a specific question |
| `/context/{chat_id}/` | POST | Uploads Jenkins context |
| `/context/{chat_id}/last-upload` | GET | Gets last context upload date |


### `POST /chats/`

Create a new chat session

**Request body:**
```json
{
    "title": "string"
}
```

**Response:**
```json
{
    "id": "int",
    "user_id": "str",
    "title": "str",
    "created_at": "str (datetime)",
    "updated_at": "str (datetime)"
}
```

---

### `GET /chats?limit=10&offset=0`

Retrieve the chat history

**Request body:**
```json
{}
```

**Response:**
```json
{
    "items": "ChatResponse[]",
    "total_items": "int",
    "limit": "int",
    "offset": "int"
}
```

---

### `GET /chats/{chat_id}?limit=10&offset=0`

Retrieves conversation history

**Request body:**
```json
{}
```

**Response:**
```json
{
    "items": "QAPairResponse[]",
    "total_items": "int",
    "limit": "int",
    "offset": "int"
}
```

---

### `PUT /chats/{chat_id}/title`

Updates the title of a specific chat

**Request body:**
```json
{
    "new_title": "str"
}
```

**Response:**
```json
{
    "id": "int",
    "user_id": "str",
    "title": "str",
    "created_at": "str (datetime)",
    "updated_at": "str (datetime)"
}
```

---

### `DELETE /chats/{chat_id}`

Deletes a chat session

**Request body:**
```json
{}
```

**Response:**
```json
{
    "message": "str"
}
```

---

### `POST /messages/send`
Sends a message to the chatbot. Returns a Server-Sent Events (SSE) stream for typing simulation.

**Request body:**
```json
{
    "chat_id": "int",
    "content": "str"
}
```

**Response:**
```text
Event Stream (text/event-stream)
data: {"event": "started", "qa_pair_id": "int"}
data: {"event": "chunk", "content": "str"}
...
data: {"event": "done"}
```

---

### `POST /messages/{qa_pair_id}/retry`
Regenerates the answer for a specific message. Truncates the chat history from this point onward and returns a new Server-Sent Events (SSE) stream.

**Request body:**
```json
{}
```

**Response:**
```text
Event Stream (text/event-stream)
data: {"event": "started", "qa_pair_id": "int"}
data: {"event": "chunk", "content": "str"}
...
data: {"event": "done"}
```

---

### `PUT /messages/{qa_pair_id}/edit`
Edits a specific question. Truncates the chat history from this point onward, generates a new question, and returns a Server-Sent Events (SSE) stream.

**Request body:**
```json
{
    "new_content": "str"
}
```

**Response:**
```text
Event Stream (text/event-stream)
data: {"event": "started", "qa_pair_id": "int"}
data: {"event": "chunk", "content": "str"}
...
data: {"event": "done"}
```

---

### `POST /context/{chat_id}`
Uploads Jenkins context for a specific chat, stores the logs, and updates vector embeddings.

**Request body:**
```json
{
    "jenkinsContext": {
        "currentScreen": "str",
        "jenkinsVersion": "str",
        "rootUrl": "str",
        "systemMessage": "str",
        "activePlugins": {
            "plugin_name": "version_str"
        },
        "masterNode": {
            "executors": "int",
            "isOnline": "bool",
            "systemInfo": {}
        },
        "agentStats": {
            "onlineAgents": "int",
            "offlineAgents": "int"
        },
        "jobDetails": {},
        "buildDetails": {}
    }
}
```

**Response:**
```json
{
    "success": "bool",
    "received_data": "JenkinsContext (object)"
}
```

---

### `GET /context/{chat_id}/last-upload`
Gets the date and time of the last context upload for a specific chat.

**Request body:**
```json
{}
```

**Response:**
```json
{
    "last_upload_at": "str (datetime) | null"
}
```