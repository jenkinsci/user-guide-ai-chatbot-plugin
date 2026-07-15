from langchain_core.tools import tool
from .hybrid_retriever import hybrid_retriever
from data.models import DataSource
from functools import partial
import json
from sqlalchemy.future import select
from models import ContextEntity
from database import get_database_session
from sqlalchemy.ext.asyncio import AsyncSession


def get_tool_list(chat_id: int, db_session: AsyncSession):
    return [fetch_from_vectordb]


@tool 
def fetch_from_vectordb(query: str, data_source: str) -> str:
    """
    Uses an Hybrid retriever to fetch from a vector db.

    It takes a query and also the specified data source you want to search in
    between jenkins_docs, plugin_docs, discourse_topics and reddit_threads.

    Args:
        query: Search input.
        data_source: str
    """

    results = hybrid_retriever(query=query, metadata={"data_source": data_source}, k = 3)

    OUTPUT = ""

    for i, v in enumerate(results):
        OUTPUT += f"""DOCUMENT {i}:\n{v.page_content}\n"""

    return OUTPUT

async def _fetch_context_from_db(chat_id: int, db_session: AsyncSession) -> dict:
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
            "jenkins_version": context.jenkins_version,
            "master_node": context.master_node,
            "active_plugins": context.active_plugins,
            "job_details": context.job_details,
            "build_details": context.build_details
        }
    return {}


@tool 
async def get_general_jenkins_context(query: str, chat_id: int, db_session: AsyncSession) -> str:
    """
    Includes name of the current screen where the context has been uploaded, 
    the current Jenkins version and info regarding the master node.
    
    Args:
        query: Search input.
        chat_id: The ID of the current chat.
    """
    context = await _fetch_context_from_db(chat_id, db_session)
    
    if not context:
        return "No Jenkins context found for this chat."

    general_info = {
        "current_screen": context.get("current_screen", "Unknown"),
        "jenkins_version": context.get("jenkins_version", "Unknown"),
        "master_node": context.get("master_node", {})
    }
    
    return json.dumps(general_info, indent=2)


@tool 
async def get_installed_plugin_list(query: str, chat_id: int, db_session: AsyncSession) -> str:
    """
    Get the list of the installed plugins with their version.
    
    Args:
        query: Search input.
        chat_id: The ID of the current chat.
    """
    context = await _fetch_context_from_db(chat_id, db_session)
    
    if not context or not context.get("active_plugins"):
        return "No plugin list found in the current context."

    return json.dumps(context["active_plugins"], indent=2)


@tool 
async def get_job_details(query: str, chat_id: int, db_session: AsyncSession) -> str:
    """
    Get details regarding the Jenkins job, including the pipeline and workspace tree.
    
    Args:
        query: Search input.
        chat_id: The ID of the current chat.
    """
    context = await _fetch_context_from_db(chat_id, db_session)
    
    if not context or not context.get("job_details"):
        return "No job details available. The context might have been uploaded from a general dashboard."

    return json.dumps(context["job_details"], indent=2)


@tool 
async def get_build_details(query: str, chat_id: int, db_session: AsyncSession) -> str:
    """
    Get details regarding the Jenkins build (e.g., status, duration, timestamp).
    
    Args:
        query: Search input.
        chat_id: The ID of the current chat.
    """
    context = await _fetch_context_from_db(chat_id, db_session)
    
    if not context or not context.get("build_details"):
        return "No build details available. The context does not point to a specific build execution."

    return json.dumps(context["build_details"], indent=2)


@tool 
async def get_build_logs(query: str, chat_id: int) -> str:
    """
    Search between Jenkins build logs. Use this to find errors, stack traces, or specific execution steps.
    
    Args:
        query: Search input representing the error or log section to find.
        chat_id: The ID of the current chat.
    """
    try:
        documents = hybrid_retriever(
            query=query, 
            metadata={"chat_id": chat_id}, 
            k=3
        )
        
        if not documents:
            return "No relevant logs found for the given query."
            
        formatted_logs = []
        for index, doc in enumerate(documents):
            content = getattr(doc, 'page_content', str(doc))
            formatted_logs.append(f"--- LOG CHUNK {index + 1} ---\n{content}")
            
        return "\n\n".join(formatted_logs)
        
    except Exception as e:
        print(f"Error retrieving logs for chat {chat_id}: {str(e)}")
        return f"Error retrieving logs: {str(e)}"