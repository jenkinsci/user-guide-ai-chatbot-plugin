import os
from .formatting_utils import build_document
from ..tools.common import read_json_file, write_json_file
from .formatting_utils import extract_code_blocks
from bs4 import BeautifulSoup
from datetime import datetime 
from langchain_core.documents import Document
from ..models import DataSource

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "processed", "reddit_threads.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "documents", "reddit_threads")
DOCS_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "documents", "reddit_threads")
CODE_BLOCKS_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "documents", "code_blocks")

REDDIT_ID_TEMPLATE = "R_{}"
REDDIT_CB_ID_TEMPLATE = "CB_{}_N_{}"

PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"


def process_thread(thread: dict):
    """
    Process a single Reddit thread:
    - Extracts code blocks from question and answer
    - Converts content to plain text
    - Store everything in a LangChain Document

    Args:
        thread (dict)

    Returns:
        tuple[Document, list[Document]]: A Tuple containing a Document with a Reddit Q+A Pair and metadata 
                                        and a Document list containing docs codeblocks and their metadata.
    """
    post_id = str(thread.get("post_id"))
    reply_id = str(thread.get("reply_id"))
    title = thread.get("title", "Untitled")
    question_html = thread.get("question", "")
    answer_html = thread.get("answer", "")
    created_at = thread.get("created_at", "")
    upvotes = thread.get("upvotes", 0)
    
    question_soup = BeautifulSoup(question_html, "lxml")
    answer_soup = BeautifulSoup(answer_html, "lxml")
    
    code_blocks = []
    question_cb = extract_code_blocks(question_soup, ["pre"], PLACEHOLDER_TEMPLATE)
    answer_cb = extract_code_blocks(answer_soup, ["pre"], PLACEHOLDER_TEMPLATE, index_start=len(question_cb))
    code_blocks.extend(question_cb)
    code_blocks.extend(answer_cb)

    date = datetime.fromisoformat(created_at).strftime("%B %d, %Y")

    question = question_soup.get_text(separator="\n", strip=True)
    answer = answer_soup.get_text(separator="\n", strip=True)

    content = f"Title: {title}\nDate: {date}\nQuestion: {question}\nAnswer: {answer}"

    reply_id_clean = reply_id.strip()

    id = REDDIT_ID_TEMPLATE.format(reply_id_clean.upper().split("_")[1])
    return (
        build_document(
            content,
            {
                "data_source": DataSource.REDDIT_THREADS.value,
                "post_id": post_id,
                "reply_id": reply_id,
                "title": title,
                "upvotes": upvotes,
                "created_at": created_at,
            },
            id=id
        ),
        [
            build_document(
                cb, 
                {   
                    "data_source": DataSource.REDDIT_THREADS.value,
                    "post_id": post_id,
                    "reply_id": reply_id,
                    "title": title,
                    "upvotes": upvotes,
                    "created_at": created_at,
                    "cb_index": i,
                },
            id=REDDIT_CB_ID_TEMPLATE.format(id, i)
            )
            for i, cb in enumerate(code_blocks)
        ]
    )
 

def process_threads(threads: list[dict]):
    """
    Format each relevant Reddit Question + Answer pair in a Langchain Document with its specific metadata.

    Args:
        threads (list[dict])

    Returns:
        tuple[list[Document], list[Document]]: A tuple containing 2 list of Documents, one with Reddit Q+A Pairs and the other their codeblocks.
    """
    documents: list[Document] = []
    code_blocks: list[Document] = []

    for thread in threads:
        document, cbs = process_thread(thread)
        documents.append(document)

        code_blocks.extend(cbs)

    return documents, code_blocks


def start_reddit_formatter():
    """Start Reddit formatter."""
    data = read_json_file(INPUT_PATH)
    if not data:
        return

    documents, code_blocks = process_threads(data["posts"])

    for doc in documents: 
        write_json_file(f"{DOCS_OUTPUT_PATH}/{doc.id}.json", doc.model_dump())

    for cb in code_blocks: 
        write_json_file(f"{CODE_BLOCKS_OUTPUT_PATH}/{cb.id}.json", cb.model_dump())




if __name__ == "__main__":
    start_reddit_formatter()