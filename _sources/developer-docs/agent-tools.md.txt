# Agent Tools

This document details the LangChain-based tools provided to the agent. These tools enable the agent to query external documentation, retrieve user-specific Jenkins contexts, inspect job configurations, and interact with the Jenkins workspace directly via the backend API.

The tools are dynamically generated and injected into the agent via the `get_tool_list` function, which accepts the current `chat_id`, the user's `context` (pre-fetched from PostgreSQL), and the `user_query`.

## Core Agent Tools

These tools are explicitly exposed to the Large Language Model (LLM) to perform actions and retrieve information.

### 1. Vector Database Search
- **Tool Name:** `fetch_from_vectordb(query: str)`
- **Objective:** Query the vector database (Qdrant) for official Jenkins documentation, plugin docs, and community Q&A (Reddit, Discourse).
- **Key Detail:** This tool is strictly for retrieving general Jenkins concepts and knowledge. It utilizes a hybrid retriever and applies a reranking step (if `ENABLE_RERANKING` is true) to optimize results. It also resolves code blocks dynamically to reconstruct complete examples from chunked vectors.

### 2. General Jenkins Context Retrieval
- **Tool Name:** `get_general_jenkins_context()`
- **Objective:** Retrieve global settings for the current user's Jenkins instance.
- **Key Detail:** Returns information parsed from the user's pre-loaded context, including the Jenkins version, master node hardware/status, active system messages, and the current UI screen the user is viewing.

### 3. Installed Plugins Check
- **Tool Name:** `get_installed_plugin_list()`
- **Objective:** Retrieve a complete JSON list of plugins currently active on the user's Jenkins instance.
- **Key Detail:** Used by the agent to verify dependencies before suggesting solutions (e.g., checking if the Kubernetes plugin is actually installed before providing a pod template).

### 4. Job Details Inspection
- **Tool Name:** `get_job_details()`
- **Objective:** Retrieve the configuration details of the specific Jenkins Job/Pipeline currently in scope.
- **Key Detail:** Allows the agent to inspect the pipeline definition, repository URLs, and the raw `config.xml`.

### 5. Build Execution and Log Search
- **Tool Name:** `get_build_details(log_search_query: str)`
- **Objective:** Retrieve the execution metadata of the current build (status, timestamp, duration) and perform a targeted semantic search within its console logs.
- **Key Detail:** The LLM passes a specific `log_search_query` (e.g., "npm ERR!", "timeout") to extract relevant log chunks from the vector database using the internal `get_build_logs` helper.

### 6. Workspace Tree Discovery
- **Tool Name:** `get_workspace_tree()`
- **Objective:** Fetch the complete directory tree of all workspaces associated with the current build via the Jenkins API.
- **Key Detail:** The agent is instructed to use this tool **first** when investigating files, as it provides the exact `workspace_id` and relative file paths necessary for reading specific file contents.

### 7. Workspace File Content Retriever 
- **Tool Name:** `get_workspace_file(file_path: str, workspace_id: str)`
- **Objective:** Read the raw string content of a specific file within a Jenkins workspace (e.g., a `Jenkinsfile`, `pom.xml`, or `package.json`).
- **Key Detail:** Enforces a strict system directive: the agent cannot guess paths or IDs and must rely on the output of `get_workspace_tree()` to call this tool successfully.

---

## Internal Helper Services

The module also includes several private helper functions that support the exposed tools above:

*   **`get_build_logs(chat_id, query)`:** Executes a filtered hybrid search against Qdrant to find specific error traces mapped to the current user's `chat_id`.
*   **`retrieve_chunk_context(chunk, retrieval_type, useful_cb)`:** A complex document parser that stitches together vector chunks, handles sliding window or parent-level context retrieval, removes overlaps, and reconstructs code blocks (`[[CODE_BLOCK_X]]`) from the database.
*   **`call_jenkins_api(endpoint, params)`:** An asynchronous HTTP client handling secure communication with the custom Jenkins backend plugin, generating short-lived JWT tokens for authentication.
*   **`fetch_context_from_db(chat_id, db_session)`:** Queries the PostgreSQL database (`ContextEntity`) to pre-load the user's Jenkins context into memory before the agent cycle begins, minimizing redundant database queries.