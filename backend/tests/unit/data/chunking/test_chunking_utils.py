import pytest
from langchain_core.documents import Document
from data.chunking.chunking_utils import assign_code_blocks_to_chunks

PATTERN = r"\[CODE_BLOCK_(\d+)\]"
 
@pytest.fixture
def code_blocks():
    return [
        Document(page_content="print('hello')"),   
        Document(page_content="x = 42"),
        Document(page_content="def foo(): pass"),
    ]
 
 
@pytest.mark.parametrize("chunk_content, expected_code_contents, expected_chunk_count", [
    # 1. Single placeholder → one code block assigned
    (
        "Intro text [CODE_BLOCK_0] end.",
        [["print('hello')"]],
        1,
    ),
    # 2. Multiple placeholders in one chunk → multiple code blocks, sorted by index
    (
        "See [CODE_BLOCK_2] and [CODE_BLOCK_0] for details.",
        [["print('hello')", "def foo(): pass"]],
        1,
    ),
    # 3. No placeholders → code_blocks list is empty for that chunk
    (
        "Plain text with no placeholders.",
        [[]],
        1,
    ),
    # 4. Duplicate placeholder → assigned only once (set deduplication)
    (
        "Repeated [CODE_BLOCK_1]] and again [CODE_BLOCK_1].",
        [["x = 42"]],
        1,
    ),
    # 5. Out-of-range placeholder → skipped, chunk still produced with empty code_blocks
    (
        "Reference to [CODE_BLOCK_99] which does not exist.",
        [[]],
        1,
    ),
])
def test_assign_code_blocks_to_chunks(
    code_blocks, chunk_content, expected_code_contents, expected_chunk_count
):
    chunks = [Document(page_content=chunk_content)]
 
    result = assign_code_blocks_to_chunks(chunks, code_blocks, PATTERN)
 
    # Output length matches number of input chunks
    assert len(result) == expected_chunk_count
 
    for item, expected_codes in zip(result, expected_code_contents):
        # Each item has the required keys
        assert "chunk" in item
        assert "code_blocks" in item
 
        # The original chunk Document is preserved
        assert item["chunk"].page_content == chunk_content
 
        # Assigned code blocks match expected content, in order
        actual_contents = [cb.page_content for cb in item["code_blocks"]]
        assert actual_contents == expected_codes
 
 
def test_empty_chunks_list(code_blocks):
    """No chunks → returns empty list without errors."""
    result = assign_code_blocks_to_chunks([], code_blocks, PATTERN)
    assert result == []
 
 
def test_empty_code_blocks_list():
    """No code blocks available → every chunk gets an empty code_blocks list."""
    chunks = [Document(page_content="Text [CODE_BLOCK_0] here.")]
    result = assign_code_blocks_to_chunks(chunks, [], PATTERN)
    assert len(result) == 1
    assert result[0]["code_blocks"] == []
 
 
def test_multiple_chunks_independently_assigned(code_blocks):
    """Each chunk gets only its own referenced code blocks."""
    chunks = [
        Document(page_content="First chunk [CODE_BLOCK_0]."),
        Document(page_content="Second chunk [CODE_BLOCK_1] and [CODE_BLOCK_2]."),
    ]
    result = assign_code_blocks_to_chunks(chunks, code_blocks, PATTERN)
 
    assert len(result) == 2
    assert [cb.page_content for cb in result[0]["code_blocks"]] == ["print('hello')"]
    assert [cb.page_content for cb in result[1]["code_blocks"]] == ["x = 42", "def foo(): pass"]