import os
from bs4 import BeautifulSoup
from .formatting_utils import (
    build_document,
)
from .formatting_utils import (
    extract_code_blocks,
    extract_title,
)
from ..tools.common import read_json_file, write_json_file
from langchain_core.documents import Document
from ..models import DataSource
from pathlib import Path

PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"

JENKINS_DOCS_ID_TEMPLATE = "J_{}"
JENKINS_DOCS_CB_ID_TEMPLATE = "CB_{}_N_{}"


def process_page(path: str, html: str, metadata: dict):
    """
    Processes a single Jenkins documentation page:
    - Parses the HTML
    - Extracts title and code blocks
    - Converts content to plain text
    - Store everything in a LangChain Document

    Args:
        url (str): Source URL of the documentation page.
        html (str): Raw HTML content of the page.
        metadata (dict): Metadata to be inserted in a specific Document.

    Returns:
        tuple[Document, list[Document]]: A Tuple containing a Document with jenkins docs page
                                        content and metadata and a Document list containing
                                        docs codeblocks and their metadata.
    """
    soup = BeautifulSoup(html, "lxml")
    title = extract_title(soup)
    code_blocks = extract_code_blocks(soup, "pre", PLACEHOLDER_TEMPLATE)

    content = soup.get_text(separator="\n", strip=True)
    # Validate that the placeholders are not removed if code blocks were extracted
    if code_blocks and PLACEHOLDER_TEMPLATE.format(0) not in content:
        print(
            f"Extracted {len(code_blocks)} code blocks for {path} but no placeholders found in text. "
            "Possible issue with placeholder insertion.",
        )

    edited_path = path[:-1] if path[-1] == "/" else path
    edited_path = edited_path.replace("/", "-").upper()

    id = JENKINS_DOCS_ID_TEMPLATE.format(edited_path)

    return (
        build_document(
            content,
            {
                "data_source": DataSource.JENKINS_DOCS.value,
                "title": title,
                "path": path,
                **metadata,
            },
            id=id,
        ),
        [
            build_document(
                cb,
                {
                    "data_source": DataSource.JENKINS_DOCS.value,
                    "title": title,
                    "path": path,
                    "cb_index": i,
                    **metadata,
                },
                id=JENKINS_DOCS_CB_ID_TEMPLATE.format(id, i),
            )
            for i, cb in enumerate(code_blocks)
        ],
    )


def create_documents(data):
    """
    Format each Jenkins docs page in a Langchain Document with its specific metadata.

    Args:
        docs (dict): A dictionary mapping URLs to raw HTML strings.

    Returns:
        tuple[list[Document], list[Document]]: A tuple containing 2 list of Documents, one with Jenkins Docs and the other its codeblocks.
    """

    doc_types: dict = data["pages"]

    documents: list[Document] = []
    code_blocks: list[Document] = []

    for doc_type, doc_pages in doc_types.items():

        for url, html in doc_pages.items():
            document, cbs = process_page(
                url, html, {"type": doc_type, "version": data["docs_version"]}
            )

            documents.append(document)
            code_blocks.extend(cbs)

    return documents, code_blocks


def jenkins_docs_formatter(output_dir: Path):
    """Start Jenkins Docs formatter."""
    INPUT_FILE_PATH = output_dir / "processed" / "jenkins_docs.json"
    DOCUMENTS_OUTPUT_DIR = output_dir / "documents" / "jenkins_docs"
    CODE_BLOCKS_OUTPUT_DIR = output_dir / "documents" / "code_blocks"

    data = read_json_file(INPUT_FILE_PATH)
    if not data:
        return

    documents, code_blocks = create_documents(data)

    for doc in documents:
        write_json_file(f"{DOCUMENTS_OUTPUT_DIR}/{doc.id}.json", doc.model_dump())

    for cb in code_blocks:
        write_json_file(f"{CODE_BLOCKS_OUTPUT_DIR}/{cb.id}.json", cb.model_dump())


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    jenkins_docs_formatter(OUTPUT_DIR)
