import os
from bs4 import BeautifulSoup
from .formatting_utils import (
    extract_code_blocks,
)
from .formatting_utils import (
    build_document,
)
from ..tools.common import read_json_file, write_json_file
from datetime import datetime
from langchain_core.documents import Document
from ..models import DataSource
from pathlib import Path


PLUGIN_DOCS_ID_TEMPLATE = "P_{}"
PLUGIN_DOCS_CB_ID_TEMPLATE = "CB_{}_N_{}"

PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"

def process_plugin(plugin_name: str, html, extra_content = {}, metadata = {}):
    """
    Process a single Jenkins plugin documentation HTML:
    - Extracts code blocks
    - Converts content to plain text
    - Store everything in a LangChain Document

    Args:
        plugin_name (str): Name of the Jenkins plugin (used as metadata title).
        html (str): Raw HTML content of the plugin documentation.
        extra_content (dict): Extra content to be inserted at the start of a specific Document page_content.
        metadata (dict): Metadata to be inserted in a specific Document.

    Returns:
        tuple[Document, list[Document]]: A Tuple containing a Document with plugin docs page 
                                        content and metadata and a Document list containing 
                                        docs codeblocks and their metadata.
    """
    soup = BeautifulSoup(html, "lxml")
    code_blocks = extract_code_blocks(soup, "pre", PLACEHOLDER_TEMPLATE)

    content = soup.get_text(separator="\n", strip=True)

    for k, v in extra_content.items():
        content = f"{k}: {v}\n" + content

    # Validate that the placeholders are not removed if code blocks were extracted
    if code_blocks and PLACEHOLDER_TEMPLATE.format(0) not in content:
        print(
            f"Extracted {len(code_blocks)} code blocks for {plugin_name} but no placeholders found in text. "
            "Possible issue with placeholder insertion.",
        )
 
    id = PLUGIN_DOCS_ID_TEMPLATE.format(plugin_name.upper())

    return (
        build_document(
            content,
            {
                "data_source": DataSource.PLUGIN_DOCS.value,
                "plugin_name": plugin_name,
                 **metadata
             },
            id=id
        ),
        [
            build_document(
                cb, 
                {   
                    "data_source": DataSource.PLUGIN_DOCS.value,
                    "plugin_name": plugin_name,
                    "cb_index": i,
                    **metadata,
                },
            id=PLUGIN_DOCS_CB_ID_TEMPLATE.format(id, i)
            )
            for i, cb in enumerate(code_blocks)
        ]
    )

def create_documents(plugin_docs):
    """
    Format each Plugin docs page in a Langchain Document with its specific metadata.

    Args:
        plugin_docs (dict): Mapping from plugin name to HTML content.

    Returns:
        tuple[list[Document], list[Document]]: A tuple containing 2 list of Documents, one with Plugin Docs and the other their codeblocks.
    """
    documents: list[Document] = []
    code_blocks: list[Document] = []

    for plugin_name, obj in plugin_docs.items():
        document, cbs = process_plugin(plugin_name, obj["content"],
                            extra_content={
                                "Jenkins version required": obj["jenkins_version_req"],
                                "Release date": datetime.fromisoformat(obj["release_date"]).strftime("%B %d, %Y"),
                                "Version": obj["version"],
                                "Plugin name": plugin_name,
                                },        
                            metadata={
                                "version": obj["version"],
                                })
        
        documents.append(document)
        code_blocks.extend(cbs)
        
    return documents, code_blocks    


def plugin_docs_formatter(output_dir: Path):
    """Start Plugin Docs formatter."""

    INPUT_FILE_PATH = output_dir / "processed" / "plugin_docs.json"
    DOCUMENTS_OUTPUT_DIR = output_dir / "documents" / "plugin_docs"
    CODE_BLOCKS_OUTPUT_DIR = output_dir / "documents" / "code_blocks"

    plugin_docs = read_json_file(INPUT_FILE_PATH)
    if not plugin_docs:
        return

    documents, code_blocks = create_documents(plugin_docs)

    for doc in documents: 
        write_json_file(f"{DOCUMENTS_OUTPUT_DIR}/{doc.id}.json", doc.model_dump())

    for cb in code_blocks: 
        write_json_file(f"{CODE_BLOCKS_OUTPUT_DIR}/{cb.id}.json", cb.model_dump())


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    plugin_docs_formatter(OUTPUT_DIR)