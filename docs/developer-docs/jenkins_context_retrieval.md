# Jenkins Context Retrieval

## `getCurrentContext` Method Documentation
The `getCurrentContext` method is a core utility within the `ChatbotApiAction` class. It generates a cascading JSON payload that encapsulates the current state and context of the Jenkins environment, based on the page the user is currently viewing (inferred from the HTTP `Referer` header).

## Method Signature
```java
private JSONObject getCurrentContext(StaplerRequest2 request)
```

## Parameters
*   **`request`** (`StaplerRequest2`): The incoming HTTP request from the user's browser, which includes headers such as the `Referer` used to deduce the current UI path.

## Returns
*   **`JSONObject`**: A structured JSON object containing the context payload. This object is populated progressively depending on the depth of the user's current view (e.g., Global Dashboard -> Job -> Specific Build).

## Logic and Data Flow

1.  **Base Initialization**: 
    *   Initializes the root `JSONObject`.
    *   Attempts to extract the current UI path using `getUIPath(request)`.
    *   Uses `GlobalAiDecorator` to map the path to a recognizable `currentScreen` name.
2.  **Level 1: Dashboard Context**: 
    *   Unconditionally calls `addDashboardContext(rootNode)` to append core system data, active plugins, controller (Master Node) hardware/memory stats, and agent online/offline status.
3.  **Level 2: Job Context**:
    *   Parses the `Referer` URL to check if the user is currently navigating a specific job (`/job/`).
    *   Extracts the job name and verifies if the user has the required `Item.READ` permissions for that specific job.
    *   If valid, calls `addJobContext(rootNode, targetJob)` to append job-specific metadata (e.g., job type, health score, upstream/downstream dependencies, and configuration XML).
4.  **Level 3: Build Context**:
    *   If a specific build number is successfully parsed from the URL, it retrieves the corresponding `Run` object.
    *   Calls `addBuildContext(rootNode, targetRun)` to append execution-specific details (e.g., status, duration, test results, parameters, execution node, SCM changes, and console log tails).
5.  **Error Handling**:
    *   If any parsing or retrieval step fails, it catches the exception and appends a `contextParsingError` field to the root JSON object, ensuring the context generation does not crash the proxy request.

## Resulting JSON Structure (Conceptual)
Depending on how deep the user is navigating, the resulting payload will look similar to this:

```json
{
  "currentScreen": "Build Job Pipeline2",
  "jenkinsVersion": "2.528.3",
  "rootUrl": "http://localhost:8080/jenkins/",
  "activePlugins": {
    "user-guide-ai-chatbot": "999999-SNAPSHOT (private-b32bb79d-Claudio)",
    "antisamy-markup-formatter": "173.v680e3a_b_69ff3",
    "asm-api": "9.10.1-216.va_9256d3b_844b_",
    // ...
  },
  "masterNode": {
    "executors": 2,
    "isOnline": true,
    "systemInfo": {
      "osName": "Windows 11",
      "osArch": "amd64",
      "osVersion": "10.0",
      "javaVersion": "21.0.10",
      "availableProcessors": 22,
      "freeMemoryMB": 316,
      "totalMemoryMB": 512,
      "maxMemoryMB": 1024
    }
  },
  "agentStats": {
    "onlineAgents": 0,
    "offlineAgents": 0
  },
  "jobDetails": {
    "fullName": "Pipeline2",
    "jobType": "WorkflowJob",
    "url": "http://localhost:8080/jenkins/job/Pipeline2/",
    "isBuildable": true,
    "inQueue": false,
    "healthScore": 50,
    "configXml": "<?xml version='1.1' encoding='UTF-8'?>\n<flow-definition plugin=\"workflow-job@1571.1580.v18e46842c125\">\n  <actions>\n    <org.jenkinsci.plugins
    ...more",
    "isPipeline": true
  },
  "buildDetails": {
    "number": 2,
    "result": "SUCCESS",
    "duration": 2074,
    "timestamp": 1785667366331,
    "causes": [
      "Started by user anonymous"
    ],
    "consoleLogTail": "Started by user unknown or anonymous\n[Pipeline] Start of Pipeline\n[Pipeline] node\nRunning on Jenkins in...more",
    "previousBuild": {
      "number": 1,
      "result": "FAILURE"
    }
  },
  "contextParsingError": null
}
```
