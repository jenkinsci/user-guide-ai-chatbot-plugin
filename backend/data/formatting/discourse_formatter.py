import os
from .formatting_utils import build_document
from ..tools.common import read_json_file, write_json_file
from .formatting_utils import extract_code_blocks
from langchain_core.documents import Document
from bs4 import BeautifulSoup
from datetime import datetime 
from ..models import DataSource

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "processed", "discourse_topics.json")
DOCS_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "documents", "discourse_topics")
CODE_BLOCKS_OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "documents", "code_blocks")

PLACEHOLDER_TEMPLATE = "[[CODE_BLOCK_{}]]"

DISCOURSE_ID_TEMPLATE = "D_{}"
DISCOURSE_CB_ID_TEMPLATE = "CB_{}_N_{}"


def process_topic(topic: dict):
    """
    Process a single Discourse topic:
    - Extracts code blocks from question and answer
    - Converts content to plain text
    - Store everything in a LangChain Document

    Args:
        topic (dict)

    Returns:
        tuple[Document, list[Document]]: A Tuple containing a Document with a Discourse Q+A Pair and metadata 
                                        and a Document list containing docs codeblocks and their metadata.
    """
    topic_id = str(topic.get("topic_id"))
    answer_id = str(topic.get("answer_id"))
    title = topic.get("title", "Untitled")
    question_html = topic.get("question", "")
    answer_html = topic.get("answer", "")
    created_at = topic.get("created_at", "")
    url = topic.get("url", "")
    is_solution = topic.get("is_solution", False)
    
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

    id = DISCOURSE_ID_TEMPLATE.format(answer_id)

    return (
        build_document(
            content,
            {
                "data_source": DataSource.DISCOURSE_TOPICS.value,
                "topic_id": topic_id,
                "answer_id": answer_id,
                "title": title,
                "url": url,
                "is_solution": is_solution,
                "created_at": created_at,
            },
            id=id
        ),
        [
            build_document(
                cb, 
                {   
                    "data_source": DataSource.DISCOURSE_TOPICS.value,
                    "topic_id": topic_id,
                    "answer_id": answer_id,
                    "title": title,
                    "url": url,
                    "is_solution": is_solution,
                    "created_at": created_at,
                    "cb_index": i,
                },
            id=DISCOURSE_CB_ID_TEMPLATE.format(id, i)
            )
            for i, cb in enumerate(code_blocks)
        ]
    )
 

def process_topics(topics: list[dict]):
    """
    Format each relevant Discourse Question + Answer pair in a Langchain Document with its specific metadata.

    Args:
        topics (list[dict])

    Returns:
        tuple[list[Document], list[Document]]: A tuple containing 2 list of Documents, one with Discourse Q+A Pairs and the other their codeblocks.
    """
    documents: list[Document] = []
    code_blocks: list[Document] = []

    for topic in topics:
        document, cbs = process_topic(topic)
        documents.append(document)

        code_blocks.extend(cbs)

    return documents, code_blocks


def start_discourse_formatter():
    """Start Discourse formatter."""
    data = read_json_file(INPUT_PATH)
    if not data:
        return

    documents, code_blocks = process_topics(data["topics"])

    for doc in documents: 
        write_json_file(f"{DOCS_OUTPUT_PATH}/{doc.id}.json", doc.model_dump())

    for cb in code_blocks: 
        write_json_file(f"{CODE_BLOCKS_OUTPUT_PATH}/{cb.id}.json", cb.model_dump())



if __name__ == "__main__":
    start_discourse_formatter()