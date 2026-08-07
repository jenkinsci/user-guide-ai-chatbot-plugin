import re
from langchain_core.documents import Document
from typing import Any, List


def assign_code_blocks_to_chunks(
    chunks: list[Document],
    code_blocks_dict: dict[int, Document],
    placeholder_pattern: str,
) -> List[dict[str, Any]]:
    """
    Assigns relevant code blocks to each chunk based on placeholder references.

    Args:
        chunks: List of text chunks (strings).
        code_blocks_dict: Dictionary mapping code block index to its Document.
        placeholder_pattern: Regex pattern to find placeholder indices.

    Returns:
        A list of dicts with 'chunk' and corresponding 'code_blocks'.
    """
    processed_chunks = []

    for chunk in chunks:
        matches = re.findall(placeholder_pattern, chunk.page_content)
        indices = set()

        for match in matches:
            try:
                idx = int(match)
                if idx in code_blocks_dict:
                    indices.add(idx)
                else:
                    print(
                        f"Code block index {idx} not found in parsed files. Skipping."
                    )
            except ValueError:
                print(f"Malformed placeholder index: '{match}'. Skipping.")

        chunk_code_blocks = [code_blocks_dict[i] for i in sorted(indices)]

        processed_chunks.append({"chunk": chunk, "code_blocks": chunk_code_blocks})

    return processed_chunks
