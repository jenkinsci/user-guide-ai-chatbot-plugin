from langchain_core.documents import Document
from bs4.element import NavigableString


def build_document(content, metadata, id):
    """Create a standardized document."""
    return Document(page_content=content, metadata=metadata, id=id)


def extract_title(soup):
    """
    Extracts the title from a BeautifulSoup-parsed HTML document.

    Priority:
    1. <h1> element if present
    2. <title> tag as fallback
    3. Returns "Untitled" if neither is found

    Args:
        soup (BeautifulSoup): Parsed HTML document.

    Returns:
        str: The extracted title string.
    """
    h1 = soup.find("h1")
    if h1 and h1.get_text(strip=True):
        return h1.get_text(strip=True)
    if soup.title:
        return soup.title.get_text(strip=True)
    return "Untitled"


def extract_code_blocks(soup, tag, placeholder_template: str, index_start=0):
    """
    Extracts all code blocks of a specified HTML tag (e.g., <pre>, <code>),
    replaces them with numbered placeholders, and returns the list of raw code strings.

    Args:
        soup (BeautifulSoup): Parsed HTML content.
        tag (str): HTML tag to search for (e.g., "pre", "code").

    Returns:
        list[str]: A list of code block strings, in the order they were found.
    """
    code_blocks = []
    for i, code_block in enumerate(soup.find_all(tag), index_start):
        placeholder = placeholder_template.format(i)
        code_blocks.append(code_block.get_text(strip=True))
        code_block.replace_with(NavigableString(placeholder))
    return code_blocks
