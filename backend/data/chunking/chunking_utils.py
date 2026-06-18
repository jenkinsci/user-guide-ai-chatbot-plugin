import re
from langchain_core.documents import Document


def assign_code_blocks_to_chunks(
    chunks: list[Document], code_blocks: list[Document], placeholder_pattern
):
    """
    Assigns relevant code blocks to each chunk based on placeholder references.

    Args:
        chunks: List of text chunks (strings).
        code_blocks: List of all extracted code blocks.
        placeholder_pattern: Regex pattern to find placeholder indices

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
                if idx < len(code_blocks):
                    indices.add(idx)
                else:
                    print(
                        f"Placeholder index {idx} out of range (max index {len(code_blocks) - 1}). Skipping.",
                    )
            except ValueError:
                print(
                    f"Malformed placeholder index: '{match}'. Skipping.",
                )

        chunk_code_blocks = [code_blocks[i] for i in sorted(indices)]

        processed_chunks.append({"chunk": chunk, "code_blocks": chunk_code_blocks})

    return processed_chunks
