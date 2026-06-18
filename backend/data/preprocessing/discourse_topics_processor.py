from ..tools.common import read_json_file, write_json_file
from pathlib import Path
import os


def process_topics(topics: list[dict]):
    """
    Process topics by keeping only useful question + answer pairs

    Args:
        topics: list[dict]

    Returns:
        list[dict]
    """

    topics_processed = []

    for topic in topics:
        # Keeping comments marked as solution
        if len(topic["solutions"]) > 0:
            for sol in topic["solutions"]:
                new_topic = {}
                new_topic["topic_id"] = topic["topic_id"]
                new_topic["answer_id"] = sol["id"]
                new_topic["title"] = topic["title"]
                new_topic["question"] = topic["posts"][0]["content"]
                new_topic["answer"] = sol["content"]
                new_topic["created_at"] = sol["created_at"]
                new_topic["url"] = sol["url"]
                new_topic["is_solution"] = True
                topics_processed.append(new_topic)
        else:
            # Keeping comments with more than 2 approval reactions
            approval_reaction_ids = ["heart"]
            for post in topic["posts"][1:]:
                approval_reaction_found = 0

                for r in post["reactions"]:
                    if r["id"] in approval_reaction_ids:
                        approval_reaction_found += r["count"]

                if approval_reaction_found >= 2:
                    new_topic = {}
                    new_topic["topic_id"] = topic["topic_id"]
                    new_topic["answer_id"] = post["id"]
                    new_topic["title"] = topic["title"]
                    new_topic["question"] = topic["posts"][0]["content"]
                    new_topic["answer"] = post["content"]
                    new_topic["created_at"] = post["created_at"]
                    new_topic["url"] = post["url"]
                    new_topic["is_solution"] = False
                    topics_processed.append(new_topic)

    return topics_processed


def discourse_topics_processor(output_dir: Path):
    """Start Discourse topics processor."""

    INPUT_FILE_PATH = output_dir / "raw" / "discourse_topics.json"
    OUTPUT_FILE_PATH = output_dir / "processed" / "discourse_topics.json"

    data = read_json_file(INPUT_FILE_PATH)
    topics_processed = process_topics(data["topics"])

    result = {"topics": topics_processed, "length": len(topics_processed)}

    saved = write_json_file(OUTPUT_FILE_PATH, result)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    discourse_topics_processor(OUTPUT_DIR)
