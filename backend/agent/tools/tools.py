from langchain_core.tools import tool, BaseTool
from .hybrid_retriever import hybrid_retriever
import json
from sqlalchemy.future import select
from models import ContextEntity
from sqlalchemy.ext.asyncio import AsyncSession


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
        documents = await hybrid_retriever(
            query=query, metadata={"chat_id": chat_id}, k=3
        )

        if not documents:
            return "No relevant logs found for the given query."

        formatted_logs = []
        for index, doc in enumerate(documents):
            content = getattr(doc, "page_content", str(doc))
            formatted_logs.append(f"--- LOG CHUNK {index + 1} ---\n{content}")

        print(formatted_logs)

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


def get_tool_list(chat_id: int, context: dict) -> list[BaseTool]:
    """
    Returns a dynamic list of tools based on the available context.
    Avoids redundant database queries by using the pre-fetched context.
    """
    available_tools = []

    @tool
    async def fetch_from_vectordb(query: str, data_source: str) -> str:
        """
        Query the vector database for official documentation and community Q&A.
        Use this tool ONLY for general knowledge, syntax, or global Jenkins concepts.
        Do NOT use this tool to search for user-specific logs, job details, or local context.

        Args:
            query: The search input (e.g., "How to write a declarative pipeline", "Docker plugin setup").
            data_source: You MUST choose exactly one of these strings based on the query context:
                - "jenkins_docs" (For core Jenkins features and architecture)
                - "plugin_docs" (For specific plugin configurations and syntax)
                - "reddit_threads" (For community opinions and common troubleshooting)
                - "discourse_topics" (For deep-dive technical discussions)
        """
        results = await hybrid_retriever(
            query=query, metadata={"data_source": data_source}, k=3
        )
        output = "These documents might be useful to answer user question:\n"
        for i, v in enumerate(results):
            output += f"DOCUMENT {i}:\n{v.page_content}\n"

        return output

    available_tools.append(fetch_from_vectordb)

    if not context:
        return available_tools

    @tool
    async def get_general_jenkins_context() -> str:
        """
        Retrieve global settings for the current Jenkins instance.
        Use this tool to find out the Jenkins version, the master configuration,
        system messages, and the current screen the user is viewing.
        """
        general_info = {
            "current_screen": context.get("current_screen", "Unknown"),
            "root_url": context.get("root_url", "Unknown"),
            "jenkins_version": context.get("jenkins_version", "Unknown"),
            "system_message": context.get("system_message", "Unknown"),
            "agent_stats": context.get("agent_stats", "Unknown"),
            "master_node": context.get("master_node", {}),
        }
        return json.dumps(general_info, indent=2)

    available_tools.append(get_general_jenkins_context)

    if context.get("active_plugins"):

        @tool
        async def get_installed_plugin_list() -> str:
            """
            Retrieve the complete list of plugins currently installed on the user's Jenkins instance.
            Use this tool to verify if a specific plugin is available or to check plugin versions
            before suggesting a solution that requires them.
            """
            return json.dumps(context["active_plugins"], indent=2)

        available_tools.append(get_installed_plugin_list)

    if context.get("job_details"):

        @tool
        async def get_job_details() -> str:
            """
            Retrieve the configuration details of the specific Jenkins Job/Pipeline the user is currently looking at.
            Use this tool to inspect the pipeline definition, repository URLs, and config.xml.
            Do NOT use this tool to find execution logs (use get_build_details instead).
            """
            return json.dumps(context["job_details"], indent=2)

        available_tools.append(get_job_details)

    if context.get("build_details"):

        @tool
        async def get_build_details(log_search_query: str) -> str:
            """
            Retrieve the execution details of the current Jenkins build (status, timestamp, duration)
            AND search its console logs for specific errors or keywords.

            Args:
                log_search_query: A specific keyword or error type to search within the build logs
                                  (e.g., "Exception", "NullPointer", "npm ERR!", "timeout").
                                  If you need to search for errors you can pass "error".
            """
            logs = await get_build_logs(chat_id, log_search_query)

            result = {"build_details": context["build_details"], "build_logs": logs}
            return json.dumps(result, indent=2)

        available_tools.append(get_build_details)

    return available_tools
