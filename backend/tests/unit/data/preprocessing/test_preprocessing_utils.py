import pytest
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from data.preprocessing.preprocessing_utils import (
    split_doc_types,
    extract_page_content_container,
    get_visible_text_length,
    remove_container_by_class,
    remove_html_comments,
    remove_edge_navigation_blocks,
    remove_tags,
    strip_html_body_wrappers,
)


def test_split_doc_types(capsys):
    # Setup test data with different URL patterns
    test_data = {
        "https://www.jenkins.io/doc/book/getting-started/": "<html>Getting started</html>",
        "https://www.jenkins.io/doc/book/installing/": "<html>Installing</html>",
        "https://www.jenkins.io/doc/developer/extensions/pipeline-input-notification/": "<html>Pipeline Input notifications</html>",
        "https://www.jenkins.io/doc/developer/extensions/pipeline-maven/": "<html>Pipeline Maven</html>",
    }

    # Execute the function
    dev_urls, non_dev_urls = split_doc_types(test_data)

    # Verify standard output print
    captured = capsys.readouterr()
    assert "There are 4 pages" in captured.out

    # Verify developer lists
    assert len(dev_urls) == 2
    assert "https://www.jenkins.io/doc/developer/extensions/pipeline-maven/" in dev_urls
    assert (
        "https://www.jenkins.io/doc/developer/extensions/pipeline-input-notification/"
        in dev_urls
    )

    # Verify non-developer lists
    assert len(non_dev_urls) == 2
    assert "https://www.jenkins.io/doc/book/getting-started/" in non_dev_urls
    assert "https://www.jenkins.io/doc/book/installing/" in non_dev_urls


def test_extract_page_content_container():
    # Setup HTML with multiple divs
    html_content = """
    <html>
        <body>
            <div class="sidebar">Sidebar Content</div>
            <div class="target-container"><h3>Main Target</h3></div>
            <div class="footer">Footer Content</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Execute extraction for existing class
    result = extract_page_content_container(soup, "target-container")
    assert "target-container" in result
    assert "<h3>Main Target</h3>" in result
    assert "Sidebar Content" not in result

    # Execute extraction for non-existing class
    empty_result = extract_page_content_container(soup, "non-existent-class")
    assert empty_result == ""


def test_remove_container_by_class():
    html_content = (
        '<div><div class="keep-me">Safe</div><div class="remove-me">Deleted</div></div>'
    )

    # Execute the function
    result = remove_container_by_class(html_content, "remove-me")

    # Assert correct extraction
    assert "Safe" in result
    assert "remove-me" not in result
    assert "Deleted" not in result


def test_remove_tags():
    # HTML with mixed tags
    html_content = """
    <div>
        <p>Text to keep</p>
        <script>alert("Malicious code")</script>
        <img src="image.png" alt="An image" />
        <style>.css { color: red; }</style>
    </div>
    """

    # Test default tags removal
    result_default = remove_tags(html_content)
    assert "Text to keep" in result_default
    assert "script" not in result_default
    assert "Malicious code" not in result_default
    assert "img" not in result_default
    assert "style" not in result_default

    # Test custom tags removal
    custom_html = "<div><h1>Title</h1><p>Paragraph</p></div>"
    result_custom = remove_tags(custom_html, tags_to_remove=["h1"])
    assert "Title" not in result_custom
    assert "Paragraph" in result_custom
    assert "<h1>" not in result_custom


@pytest.mark.parametrize(
    "html_input, text_to_keep, text_to_remove",
    [
        # 1. Single comment between two paragraphs
        ("<p>Hello</p><!-- secret --><p>World</p>", "World", "secret"),
        # 2. Multiple comments — only visible text survives
        ("<!-- one --><div>Content</div><!-- two -->", "Content", "one"),
        # 3. Comment containing inner HTML markup
        ("<p>Visible</p><!-- <b>hidden bold</b> -->", "Visible", "hidden bold"),
        # 4. Multiline comment
        (
            "<p>Top</p><!--\n  line one\n  line two\n--><p>Bottom</p>",
            "Bottom",
            "line one",
        ),
        # 5. No comments at all — content must be fully preserved
        ("<article><p>Just text</p></article>", "Just text", None),
    ],
)
def test_remove_html_comments(
    html_input: str, text_to_keep: str, text_to_remove: str | None
):
    # Execute the function
    result = remove_html_comments(html_input)

    # Assert that the valid, non-comment content is preserved
    assert text_to_keep in result

    # Assert that HTML comment delimiters are completely gone
    assert "<!--" not in result
    assert "-->" not in result

    # Assert that the specific hidden text was successfully removed (if applicable)
    if text_to_remove:
        assert text_to_remove not in result


@pytest.mark.parametrize(
    "html_input, expected_length",
    [
        # Case 1: Standard HTML with text and spaces
        ("<html><body><h1>Hello</h1>  <p>World</p> </body></html>", 11),
        # Case 2: Text with excessive whitespaces and newlines
        ("<div>  Lots of \n spaces  </div>", 16),
        # Case 3: Empty HTML tags with no text
        ("<div><span></span></div>", 0),
        # Case 4: Completely empty string
        ("", 0),
        # Case 5: Plain text without any HTML tags
        ("Just plain text", 15),
    ],
)
def test_get_visible_text_length(html_input: str, expected_length: int):
    # Execute the function
    result = get_visible_text_length(html_input)

    # Assert the calculated length matches expectations
    assert result == expected_length


@pytest.mark.parametrize(
    "html_input, expected_output_contains, expected_output_excludes",
    [
        # Case 1: Full HTML document with head and body
        (
            "<html><head><title>Test</title></head><body><h2>Body Content</h2><p>More</p></body></html>",
            "<h2>Body Content</h2>",
            ["<html>", "<head>", "<title>", "<body>"],
        ),
        # Case 2: Just the body tag
        (
            "<body><div>Inner Fragment</div></body>",
            "<div>Inner Fragment</div>",
            ["<body>", "<html>"],
        ),
        # Case 3: Raw fragment without any body/html tags (lxml adds them, the function should remove them)
        (
            "<p>Just a raw fragment</p>",
            "<p>Just a raw fragment</p>",
            ["<body>", "<html>"],
        ),
        # Case 4: Empty body
        ("<html><body></body></html>", "", ["<body>", "<html>"]),
    ],
)
def test_strip_html_body_wrappers(
    html_input: str, expected_output_contains: str, expected_output_excludes: list[str]
):
    # Execute the function
    result = strip_html_body_wrappers(html_input)

    # Clean up line breaks for easier assertion if present
    clean_result = result.replace("\n", "")

    # Assert the target content is present
    if expected_output_contains:
        assert expected_output_contains in clean_result

    # Assert all wrapper tags are missing
    for tag in expected_output_excludes:
        assert tag not in clean_result
