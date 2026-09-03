# Jenkins Context

Here are listed and documented all the Jenkins Controller endpoints.

## Starting the Controller
```bash
mvn clean hpi:run
```

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/chatbot-api/*` | ANY | Proxy method which forwards req to the FastApi Backend |
| `/chatbot-api/workspaceTree/` | GET | Get the various workspace trees |
| `/chatbot-api/workspaceFile/` | GET | Get the content of a workspace file |


### `ANY /chatbot-api/*`

Proxy method which forwards requests to the FastAPI Backend. Automatically generates and attaches a JWT token for authorization. If the path matches `/context/`, it intercepts the request to inject the Jenkins context payload before forwarding.

**Request body:**
*Depends on the proxied FastApi endpoint.*

**Response:**
*Returns the response from the FastApi Backend (supports both standard JSON responses and Server-Sent Events streams).*

---

### `GET /chatbot-api/workspaceTree?jobName={jobName}&buildNumber={buildNumber}`

Retrieves the tree of all workspaces for a specific build. Automatically filters out heavy folders like `.git`, `node_modules`, and `target` to save tokens.

**Query Parameters:**
*   `jobName` (string): The full name of the Jenkins job.
*   `buildNumber` (int): The build number.

**Response:**
```json
[
    {
        "workspaceId": "str",
        "node": "str",
        "path": "str",
        "tree": {
            "name": "str",
            "type": "directory | file",
            "size": "int (if file)",
            "children": "Array (recursive, if directory)"
        }
    }
]
```
*(Note: "path" is included for Pipeline jobs, while classic projects will use a default "ws-default" workspaceId).*

---

### `GET /chatbot-api/workspaceFile?jobName={jobName}&buildNumber={buildNumber}&workspaceId={workspaceId}&filePath={filePath}`

Reads the content of a specific file within a specific workspace. Truncates files larger than ~50KB to avoid overloading the LLM context window. Includes security checks to prevent path traversal.

**Query Parameters:**
*   `jobName` (string): The full name of the Jenkins job.
*   `buildNumber` (int): The build number.
*   `workspaceId` (string): The specific workspace ID retrieved from the `workspaceTree` endpoint.
*   `filePath` (string): The relative path to the target file.

**Response (Success):**
```json
{
    "status": "success",
    "content": "str"
}
```

**Response (Error):**
```json
{
    "status": "error",
    "message": "str"
}
```