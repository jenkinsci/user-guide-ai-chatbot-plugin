from langchain_core.tools import tool, BaseTool
from .hybrid_retriever import hybrid_retriever
import json
from sqlalchemy.future import select
from models import ContextEntity
from sqlalchemy.ext.asyncio import AsyncSession
from ..reranker import get_reranked_documents
from manage_env import get_env
from langchain_core.documents import Document
from qdrant_client import models
from vectordb.qdrant import get_with_metadata
import aiohttp
from typing import Optional, Dict, Any, Union, Literal
from ..utils import (
    qdrant_record_to_langchain_doc,
    remove_chunk_context,
    remove_chunk_overlap,
    format_workspace_tree,
)
import re
from manage_env import get_env
from routers.auth import create_access_token
import asyncio

ENABLE_RERANKING = get_env("ENABLE_RERANKING").lower() == "true"
CODE_BLOCK_PLACEHOLDER_PATTERN = r"\[\[CODE_BLOCK_(\d+)\]\]"


async def get_build_logs(
    chat_id: int,
    query: str,
) -> str:
    """
    Search between Jenkins build logs. Use this to tool find errors, stack traces, or specific execution steps inside the logs of
    the build.

    Args:
        query: Search input representing the error or log section to find.
        chat_id: The ID of the current chat.
    """

    try:
        payload_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.chat_id", match=models.MatchValue(value=chat_id)
                ),
            ]
        )

        documents = await hybrid_retriever(
            query=query, payload_filter=payload_filter, k=3
        )

        if not documents:
            return "No relevant logs found for the given query."

        formatted_logs = []
        for index, doc in enumerate(documents):
            content = getattr(doc, "page_content", str(doc))
            formatted_logs.append(f"--- LOG CHUNK {index + 1} ---\n{content}")

        return "\n\n".join(formatted_logs)

    except Exception as e:
        print(f"Error retrieving logs for chat {chat_id}: {str(e)}")
        return f"Error retrieving logs: {str(e)}"


async def fetch_context_from_db(chat_id: int, db_session: AsyncSession) -> dict:
    """
    Helper function to retrieve the context entity from PostgreSQL.
    Returns the context as a dictionary or an empty dict if not found.
    """
    stmt = select(ContextEntity).where(ContextEntity.chat_id == chat_id)
    result = await db_session.execute(stmt)
    context = result.scalars().first()

    if context:
        return {
            "current_screen": context.current_screen,
            "root_url": context.root_url,
            "jenkins_version": context.jenkins_version,
            "system_message": context.system_message,
            "agent_stats": context.agent_stats,
            "master_node": context.master_node,
            "active_plugins": context.active_plugins,
            "job_details": context.job_details,
            "build_details": context.build_details,
            "build_log_stored": context.build_log_stored,
        }
    return {}


async def retrieve_chunk_context(
    chunk: Document,
    retrieval_type: Literal["window", "parent"],
    useful_cb: tuple[str, int] | None,
) -> tuple[str, list[str]]:
    parent_id = chunk.metadata["parent_id"]
    chunk_index = chunk.metadata["chunk_index"]
    total_chunks = chunk.metadata["total_chunks"]
    data_source = chunk.metadata["data_source"]

    payload_filter: models.Filter | None = None

    # 1. Setup the filter based on the retrieval type
    if retrieval_type == "window":
        window_range = 3
        min_range = max(0, chunk_index - window_range)
        max_range = min(total_chunks - 1, chunk_index + window_range)

        payload_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.parent_id", match=models.MatchValue(value=parent_id)
                ),
                models.FieldCondition(
                    key="metadata.chunk_index",
                    range=models.Range(gte=min_range, lte=max_range),
                ),
            ]
        )

    elif retrieval_type == "parent":
        payload_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.parent_id", match=models.MatchValue(value=parent_id)
                )
            ]
        )

    # 2. Fetch the text chunks
    records, _ = get_with_metadata(payload_filter=payload_filter)
    chunks = qdrant_record_to_langchain_doc(records)

    # Sort documents sequentially by chunk_index
    chunks = sorted(chunks, key=lambda x: x.metadata["chunk_index"])

    # Remove context applied for Contextual Retrieval
    chunks = remove_chunk_context(chunks)

    # Merge all text chunks into a single string and remove overlaps
    merged_text = ""
    if data_source == "jenkins_docs" or data_source == "plugin_docs":
        merged_text = remove_chunk_overlap([c.page_content for c in chunks])
    else:
        merged_text = "\n".join([c.page_content for c in chunks])

    # 3. Aggregate all code block IDs to perform a single DB query
    all_cb_ids: set[str] = set()
    for c in chunks:
        all_cb_ids.update(c.metadata.get("cb_ids", []))

    cb_index_to_text: dict[str, str] = {}

    # Only query if there are codeblocks to fetch
    if all_cb_ids:
        useful_cb_parent_id, useful_cb_chunk_index = (
            useful_cb if useful_cb else (None, None)
        )

        should_conditions: list[models.Condition] = []
        default_cb_ids = list(all_cb_ids)

        # Handle the specific useful code block separately to avoid range overlap
        if (
            useful_cb_parent_id is not None
            and useful_cb_chunk_index is not None
            and useful_cb_parent_id in all_cb_ids
        ):
            # Remove it from the default IDs so it gets unique rules
            default_cb_ids.remove(useful_cb_parent_id)

            # Ensure the lower bound doesn't go below 0
            min_cb_range = max(0, useful_cb_chunk_index - 2)
            max_cb_range = useful_cb_chunk_index + 2

            should_conditions.append(
                models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.parent_id",
                            match=models.MatchValue(value=useful_cb_parent_id),
                        ),
                        models.FieldCondition(
                            key="metadata.chunk_index",
                            range=models.Range(gte=min_cb_range, lte=max_cb_range),
                        ),
                    ]
                )
            )

        # Add the condition for the remaining standard code blocks
        if default_cb_ids:
            should_conditions.append(
                models.Filter(
                    must=[
                        models.FieldCondition(
                            key="metadata.parent_id",
                            match=models.MatchAny(any=default_cb_ids),
                        ),
                        models.FieldCondition(
                            key="metadata.chunk_index", range=models.Range(gte=0, lte=4)
                        ),
                    ]
                )
            )

        cb_payload_filter = models.Filter(should=should_conditions)
        cb_records, _ = get_with_metadata(payload_filter=cb_payload_filter, limit=100)
        cb_docs = qdrant_record_to_langchain_doc(cb_records)

        # 4. Group and process the fetched code block chunks
        codeblocks_groups: dict[str, list[Document]] = {}
        for cb_doc in cb_docs:
            cb_parent_id = cb_doc.metadata["parent_id"]
            if cb_parent_id not in codeblocks_groups:
                codeblocks_groups[cb_parent_id] = []
            codeblocks_groups[cb_parent_id].append(cb_doc)

        for cb_parent_id, cb_chunks in codeblocks_groups.items():
            ordered_cb_chunks = sorted(
                cb_chunks, key=lambda x: x.metadata["chunk_index"]
            )
            cb_full_text = "\n".join(
                [chunk.page_content for chunk in ordered_cb_chunks]
            )

            cb_index = str(ordered_cb_chunks[0].metadata.get("cb_index"))
            cb_index_to_text[cb_index] = cb_full_text

    # 5. Replace placeholders in the merged text with the actual code
    def replace_placeholder(match: re.Match) -> str:
        extracted_index = match.group(1)
        return cb_index_to_text.get(extracted_index, match.group(0))  # type: ignore

    final_text_with_code = re.sub(
        CODE_BLOCK_PLACEHOLDER_PATTERN, replace_placeholder, merged_text
    )

    return final_text_with_code, list(cb_index_to_text.values())


async def call_jenkins_api(
    endpoint: str, params: Optional[Dict[str, Any]] = None
) -> Union[dict, list]:
    """
    Makes an asynchronous HTTP call to the Jenkins plugin using JWT authentication.

    Args:
        chat_id: The ID of the current chat.
        endpoint: The API path (e.g., '/job/my-job/1/chatbot/workspaceTree').
        params: Optional query parameters to append to the URL.

    Returns:
        A dictionary or list containing the JSON response from Jenkins.
    """
    jenkins_url = get_env("JENKINS_URL")

    if not jenkins_url:
        print("JENKINS_URL environment variable is missing!")
        return {
            "status": "error",
            "message": "Jenkins server configuration is missing on the backend.",
        }

    base_url = jenkins_url.rstrip("/")
    endpoint_path = endpoint.lstrip("/")
    full_url = f"{base_url}/{endpoint_path}"

    safe_params = {}
    if params:
        for key, value in params.items():
            safe_params[key] = str(value)

    try:
        # Generate the JWT token
        jwt_token = create_access_token()
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            print(f"Calling Jenkins API: {full_url} with params: {safe_params}")

            async with session.get(full_url, params=safe_params) as response:
                response.raise_for_status()
                return await response.json()

    except ValueError as e:
        print(str(e))
        return {
            "status": "error",
            "message": "Backend configuration error (JWT Secret missing).",
        }

    except aiohttp.ClientResponseError as e:
        print(f"HTTP Error {e.status} calling Jenkins: {e.message}")
        return {
            "status": "error",
            "message": f"Error from Jenkins (HTTP {e.status}): {e.message}",
        }

    except Exception as e:
        print(f"Unexpected error in call_jenkins_api: {str(e)}")
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


def get_tool_list(chat_id: int, context: dict, user_query: str) -> list[BaseTool]:
    """
    Returns a dynamic list of tools based on the available context.
    Avoids redundant database queries by using the pre-fetched context.
    """

    @tool
    async def fetch_from_vectordb(query: str) -> str:
        """
        Query the vector database for official documentation and community Q&A.
        Use this tool ONLY for Jenkins concepts.
        Do NOT use this tool to search for specific build logs, information regarding the job details, or user local context.

        Args:
            query: The search input (e.g., "How to write a declarative pipeline", "Docker plugin setup").
        """
        k = 50 if ENABLE_RERANKING else 3

        sources = ["jenkins_docs", "plugin_docs", "reddit_threads", "discourse_topics"]
        cb_payload_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="metadata.data_source", match=models.MatchAny(any=sources)
                )
            ]
        )

        documents = await hybrid_retriever(
            query=query, payload_filter=cb_payload_filter, k=k
        )

        # Rerank results
        ordered_documents = documents
        if ENABLE_RERANKING:
            try:
                ordered_documents: list[Document] = [
                    data["document"]
                    for data in get_reranked_documents(user_query, documents)
                ]
            except Exception as e:
                ordered_documents = documents

        output = "These documents might be useful to answer user question:\n"
        cb_useful = None

        for i, v in enumerate(ordered_documents[:3]):
            # Apply extended retrieval
            related_id = v.metadata.get("related_id")
            if related_id:
                # If is a codeblock, check which is the related chunk and pass as if that
                # one was fetched from the hybrid retriever
                payload_filter = models.Filter(
                    must=[models.HasIdCondition(has_id=[related_id])]
                )

                records, _ = get_with_metadata(payload_filter=payload_filter, limit=1)
                docs = qdrant_record_to_langchain_doc(records)
                if len(docs) == 0:
                    continue
                else:
                    cb_useful = (v.metadata["parent_id"], v.metadata["chunk_index"])
                    v = docs[0]

            data_source = v.metadata.get("data_source")
            retrieval_type = (
                "parent"
                if data_source == "discourse_topics" or data_source == "reddit_threads"
                else "window"
            )
            final_text, _ = await retrieve_chunk_context(
                v, retrieval_type, useful_cb=cb_useful
            )

            output += f"DOCUMENT {i}:\n{final_text}\n"

        return output

    @tool
    async def get_general_jenkins_context() -> str:
        """
        Retrieve global settings for the current user's Jenkins instance.
        Use this tool to find out the Jenkins version, the master configuration,
        system messages, and the current screen the user is viewing.
        """
        if not context:
            return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

        general_info = {
            "current_screen": context.get("current_screen", "Unknown"),
            "root_url": context.get("root_url", "Unknown"),
            "jenkins_version": context.get("jenkins_version", "Unknown"),
            "system_message": context.get("system_message", "Unknown"),
            "agent_stats": context.get("agent_stats", "Unknown"),
            "master_node": context.get("master_node", {}),
        }
        return json.dumps(general_info, indent=2)

    @tool
    async def get_installed_plugin_list() -> str:
        """
        Retrieve the complete list of plugins currently installed on the user's Jenkins instance.
        Use this tool to verify if a specific plugin is available or to check plugin versions
        before suggesting a solution that requires them.
        """

        if not context.get("active_plugins"):
            return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

        return json.dumps(context["active_plugins"], indent=2)

    @tool
    async def get_job_details() -> str:
        """
        Retrieve the configuration details of the specific Jenkins Job/Pipeline the user is currently looking at.
        Use this tool to inspect the pipeline definition, repository URLs, and config.xml.
        Do NOT use this tool to find execution logs (use get_build_details instead).
        """
        if not context.get("job_details"):
            return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

        return json.dumps(context["job_details"], indent=2)

    @tool
    async def get_build_details(log_search_query: str) -> str:
        """
        Retrieve the execution details of the current Jenkins build (status, timestamp, duration) the user is currently looking at
        AND search its console logs for specific errors or keywords.
        build_id it's not needed.

        Args:
            log_search_query: A specific keyword or error type to search within the build logs
                                (e.g., "Error", "Exception", "NullPointer", "npm ERR!", "timeout").
                                If you need to search for errors you can pass "error".

        HINT: e.g., {"log_search_query": "error"}. STRICTLY DO NOT USE `build_id`
        """
        if not context.get("build_details"):
            return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

        logs = await get_build_logs(chat_id, log_search_query)

        result = {"build_details": context["build_details"], "build_logs": logs}
        return json.dumps(result, indent=2)

    @tool
    async def get_workspace_tree() -> str:
        """
        Retrieves the directory tree of ALL workspaces associated with the current build.
        Use this to explore available files before reading their content.

        HINT: Call this FIRST to discover files.
        """
        try:
            if not context or not context.get("build_details"):
                return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

            job_name = context["job_details"]["full_name"]
            build_number = context["build_details"]["number"]

            response = await call_jenkins_api(
                endpoint="/chatbot-api/workspaceTree",
                params={"jobName": job_name, "buildNumber": build_number},
            )

            if isinstance(response, dict) and response.get("status") == "error":
                return f"API Error: {response.get('message')}"

            formatted_tree = format_workspace_tree(response)  # type: ignore
            return formatted_tree

        except Exception as e:
            print(f"Failed to fetch workspace tree: {e}")
            return f"Error retrieving workspace tree: {str(e)}"

    @tool
    async def get_workspace_file(file_path: str, workspace_id: str) -> str:
        """
        Reads the content of a specific file within a Jenkins workspace.
        You MUST call get_workspace_tree() tool first to obtain the correct 'workspace_id' and exact 'file_path'.

        Args:
            file_path: The relative path of the file (e.g., 'src/main/java/App.java' or 'pom.xml')
            workspace_id: The workspace ID provided by get_workspace_tree() (e.g., 'ws-default' or 'ws-pipeline-1')

        HINT: NEVER call this before get_workspace_tree.
        """

        try:
            if not context or not context.get("build_details"):
                return "[MISSING_CONTEXT]: tell the user to try to upload the context and try again."

            job_name = context["job_details"]["full_name"]
            build_number = context["build_details"]["number"]

            response = await call_jenkins_api(
                endpoint="/chatbot-api/workspaceFile",
                params={
                    "jobName": job_name,
                    "buildNumber": build_number,
                    "workspaceId": workspace_id,
                    "filePath": file_path,
                },
            )

            if response.get("status") == "success":
                return response.get("content", "")
            else:
                error_msg = response.get("message", "Unknown API Error")
                return (
                    f"Error reading file: {error_msg}. "
                    "SYSTEM DIRECTIVE: You probably guessed an invalid 'workspace_id' or 'file_path'. "
                    "You are FORBIDDEN from guessing. YOU MUST CALL 'get_workspace_tree' NOW to find the exact IDs and paths."
                )

        except Exception as e:
            print(f"Failed to read file {file_path}: {e}")
            return f"Error reading file: {str(e)}"

    return [
        fetch_from_vectordb,
        get_general_jenkins_context,
        get_installed_plugin_list,
        get_job_details,
        get_build_details,
        get_workspace_tree,
        get_workspace_file,
    ]
