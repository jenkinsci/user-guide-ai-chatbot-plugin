from langchain_core.documents import Document
from qdrant_client.conversions.common_types import Record
from difflib import SequenceMatcher
from typing import List, Dict, Any


def qdrant_record_to_langchain_doc(records: list[Record]) -> list[Document]:
    """
    Converts a Qdrant record list in a Langchain Document list.
    """
    docs = []

    for r in records:
        payload = r.payload or {}

        page_content = payload.pop("page_content", "")

        metadata = {**payload["metadata"]}

        docs.append(Document(id=r.id, page_content=page_content, metadata=metadata))

    return docs


def remove_chunk_overlap(chunks: list[str]) -> str:
    """Join a chunk list removing the duplicated parts at the ends."""
    if not chunks:
        return ""

    reconstructed_text = chunks[0]

    for i in range(1, len(chunks)):
        next_chunk = chunks[i]

        max_overlap_search = min(len(reconstructed_text), len(next_chunk))

        match = SequenceMatcher(
            None,
            reconstructed_text[-max_overlap_search:],
            next_chunk[:max_overlap_search],
        ).find_longest_match(0, max_overlap_search, 0, max_overlap_search)

        if match.b == 0 and (match.a + match.size) == max_overlap_search:
            reconstructed_text += next_chunk[match.size :]
        else:
            reconstructed_text += next_chunk

    return reconstructed_text


def remove_chunk_context(chunks: list[Document]) -> list[Document]:
    """Remove context from each chunks (Contextual Retrieval)"""

    CONTEXT_CHUNK_SEPARATOR = "===CR==="

    for c in chunks:
        c.page_content = c.page_content.split(CONTEXT_CHUNK_SEPARATOR, 1)[-1]

    return chunks


def format_workspace_tree(workspaces: List[Dict[str, Any]]) -> str:
    """
    Formats the JSON workspace payload into a compact, token-efficient list of flat paths.
    This provides the LLM with the exact strings needed for the 'filePath' parameter,
    eliminating hallucinations and path reconstruction errors.

    Args:
        workspaces: The parsed JSON list returned by the Jenkins API.

    Returns:
        A formatted string easily digestible by the LLM.
    """
    if not workspaces or not isinstance(workspaces, list):
        return "No workspace data found."

    output_lines = []

    for ws in workspaces:
        ws_id = ws.get("workspaceId", "unknown-id")
        node_name = ws.get("node", "unknown-node")

        output_lines.append(f"=== Workspace ID: {ws_id} (Node: {node_name}) ===")

        tree_root = ws.get("tree", {})
        if not tree_root:
            output_lines.append("  [Empty workspace]\n")
            continue

        # Helper recursive function to extract flat relative paths
        def extract_paths(
            node_dict: Dict[str, Any], current_path: str = ""
        ) -> List[str]:
            paths = []
            children = node_dict.get("children", [])

            for child in children:
                child_name = child.get("name", "")
                child_type = child.get("type", "file")

                # Build the relative path (e.g., "src/main" + "/" + "App.java")
                new_path = (
                    f"{current_path}/{child_name}" if current_path else child_name
                )

                if child_type == "directory":
                    # Recursively extract paths from subdirectories
                    paths.extend(extract_paths(child, new_path))
                else:
                    # It's a file, add the exact path to the list
                    paths.append(new_path)

            return paths

        # Extract and sort paths alphabetically for better LLM readability
        file_paths = extract_paths(tree_root)
        if file_paths:
            for fp in sorted(file_paths):
                output_lines.append(f"- {fp}")
        else:
            output_lines.append("  [No files found]")

        output_lines.append("")

    return "\n".join(output_lines).strip()
