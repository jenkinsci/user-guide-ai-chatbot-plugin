from ..tools.common import read_json_file, write_json_file
from pathlib import Path
import os


def process_threads(posts: list[dict]):
    """
    Process threads by keeping only useful question + answer pairs

    Args:
        topics: list[dict]

    Returns:
        list[dict]
    """

    # Each useful answer will be paired in the same document with his matching question
    conversations = []

    for post in posts:
        for comment in post["comments"][:3]:
            if comment["id"] == "unknown":
                continue
            new_conversation = {}

            # Keeping comments with more than 3 upvotes and a length greater than 20
            if comment["points"] >= 3 and len(comment["content"]) > 20:
                new_conversation["post_id"] = post["id"]
                new_conversation["reply_id"] = comment["id"]
                new_conversation["title"] = post["title"]
                new_conversation["question"] = post["content"]
                new_conversation["answer"] = comment["content"]
                new_conversation["created_at"] = comment["create_date"]
                new_conversation["upvotes"] = post["points"]

                conversations.append(new_conversation)

    return conversations


def reddit_threads_processor(output_dir: Path):
    """Start Reddit threads processor."""
    INPUT_FILE_PATH = output_dir / "raw" / "reddit_threads.json"
    OUTPUT_FILE_PATH = output_dir / "processed" / "reddit_threads.json"

    data = read_json_file(INPUT_FILE_PATH)

    filtered_data = process_threads(data["threads"])

    result = {"threads": filtered_data, "length": len(filtered_data)}

    saved = write_json_file(OUTPUT_FILE_PATH, result)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    reddit_threads_processor(OUTPUT_DIR)
