import pytest
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from data.formatting.formatting_utils import build_document, extract_title, extract_code_blocks 


def test_build_document_creates_correct_instance():
    # Define input data
    test_content = "This is a test document."
    test_metadata = {"source": "web", "author": "John Doe"}
    test_id = "doc_001"
    
    # Execute function
    result = build_document(test_content, test_metadata, test_id)
    
    # Assert the returned object is of the correct type
    assert isinstance(result, Document)
    
    # Assert all properties match the inputs
    assert result.page_content == test_content
    assert result.metadata == test_metadata
    assert result.id == test_id


# --- Tests for extract_title ---

def test_extract_title_prioritizes_h1():
    # HTML with both h1 and title tags
    html = "<html><head><title>Page Title</title></head><body><h1>Main Heading</h1></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    
    result = extract_title(soup)
    
    # Assert that h1 text is returned, ignoring the title tag
    assert result == "Main Heading"

def test_extract_title_falls_back_to_title_if_h1_empty():
    # HTML where h1 exists but has no text
    html = "<html><head><title>Valid Title</title></head><body><h1>   </h1></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    
    result = extract_title(soup)
    
    assert result == "Valid Title"

def test_extract_title_falls_back_to_title_if_no_h1():
    # HTML with only a title tag
    html = "<html><head><title>Only Title Here</title></head><body><p>Some text</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    
    result = extract_title(soup)
    
    assert result == "Only Title Here"

def test_extract_title_returns_untitled_when_no_tags_found():
    # HTML with neither h1 nor title
    html = "<html><body><p>Just some paragraph text</p></body></html>"
    soup = BeautifulSoup(html, "html.parser")
    
    result = extract_title(soup)
    
    assert result == "Untitled"


# --- Tests for extract_code_blocks ---

def test_extract_code_blocks_returns_correct_list():
    html = """
    <div>
        <p>First code:</p>
        <pre>print("Hello World")</pre>
        <p>Second code:</p>
        <pre>return True</pre>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    template = "[[CODE_BLOCK_{}]]"
    
    # Execute function
    extracted_blocks = extract_code_blocks(soup, "pre", template)
    
    # Assert the list contains the exact text from the pre tags
    assert len(extracted_blocks) == 2
    assert extracted_blocks[0] == 'print("Hello World")'
    assert extracted_blocks[1] == 'return True'

def test_extract_code_blocks_modifies_soup_with_placeholders():
    html = "<body><pre>x = 1</pre><span>middle</span><pre>y = 2</pre></body>"
    soup = BeautifulSoup(html, "html.parser")
    template = "---CODE_{}---"
    
    # Execute function
    extract_code_blocks(soup, "pre", template)
    
    # Convert soup back to string to verify the replacement
    modified_html = str(soup)
    
    # Assert placeholders replaced the original tags
    assert "---CODE_0---" in modified_html
    assert "---CODE_1---" in modified_html
    
    # Assert the original code is no longer in the HTML structure
    assert "x = 1" not in modified_html
    assert "y = 2" not in modified_html
    assert "<pre>" not in modified_html

def test_extract_code_blocks_with_custom_index_start():
    html = "<pre>Code A</pre><pre>Code B</pre>"
    soup = BeautifulSoup(html, "html.parser")
    template = "BLOCK_ID_{}"
    
    # Start indexing at 10 instead of 0
    extract_code_blocks(soup, "pre", template, index_start=10)
    
    modified_html = str(soup)
    assert "BLOCK_ID_10" in modified_html
    assert "BLOCK_ID_11" in modified_html