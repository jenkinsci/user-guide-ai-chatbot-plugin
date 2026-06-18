from dataclasses import asdict
from datetime import datetime
from typing import List
from .models import ThreadDetails, Section
from typing import List, Optional, Any
import re
from ...tools.common import datetime_serializer, write_json_file
from pathlib import Path


def print_thread_details(thread: ThreadDetails):
    """
    Print Thread details

    Args:
        thread (ThreadDetails)
    """
    print("\n--- THREAD ---")
    print(f"Title: {thread.title}")
    print(f"Author: {thread.author.username}")
    print(f"Subreddit: {thread.subreddit}")
    print(f"Thread Create Date: {thread.create_date}")
    print(f"Thread Points: {thread.points}")
    print(f"Total comments text stated: {thread.comments_qty}")
    print(f"Actually extracted comments: {len(thread.comments)}")
    print("\n--- Comments ---")
    for c in thread.comments:
        print(
            f"- {c.author.username} ({c.points} pts): {c.content[:60]}... [Replies to: {c.parent_id}]"
        )


def get_subreddit_page_url(subreddit: str, section: Section = Section.Hot) -> str:
    """
    Compose the subreddit page url
    """
    if section == Section.Hot:
        return f"https://old.reddit.com/r/{subreddit}"
    else:
        return f"https://old.reddit.com/r/{subreddit}/{section.value}/"


def get_thread_page_url(subreddit: str, id: str):
    """
    Compose a thread page url
    """
    return f"https://old.reddit.com/r/{subreddit}/comments/{id}/"


def extract_integer(text: str) -> int:
    """Extracts the first integer found in a string (e.g., '14 points' -> 14)."""
    if not text:
        return 0

    clean_text = text.replace(",", "")

    match = re.search(r"[+-]?\d+", clean_text)

    return int(match.group()) if match else 0


def parse_reddit_datetime(time_element) -> Optional[datetime]:
    """Parses Reddit's ISO datetime attribute."""
    if time_element and time_element.has_attr("datetime"):
        try:
            return datetime.fromisoformat(time_element["datetime"])
        except ValueError:
            return None
    return None


def build_thread_tree(thread: ThreadDetails):
    thread_dict = asdict(thread)

    flat_comments_list = thread_dict.get("comments", [])

    # Initialize a 'replies' list for every comment and build a lookup map
    comment_lookup_map = {}
    for single_comment in flat_comments_list:
        single_comment["replies"] = []
        comment_lookup_map[single_comment["id"]] = single_comment

    hierarchical_comments_tree = []

    # Iterate again to place each comment inside its parent's 'replies' list
    for single_comment in flat_comments_list:
        parent_id = single_comment.get("parent_id")

        # If the parent_id starts with 't1_', it's a reply to another comment
        if parent_id and str(parent_id).startswith("t1_"):
            parent_comment_node = comment_lookup_map.get(parent_id)

            if parent_comment_node:
                # Attach this comment to its parent's replies
                parent_comment_node["replies"].append(single_comment)
            else:
                # Fallback: if the parent comment is missing from our scrape we append it to the root
                hierarchical_comments_tree.append(single_comment)
        else:
            # It's a top-level comment (parent_id starts with 't3_' or is None)
            hierarchical_comments_tree.append(single_comment)

    # Replace the flat list with the newly structured tree
    thread_dict["comments"] = hierarchical_comments_tree

    return thread_dict


def build_thread_trees(thread_list: List[ThreadDetails]) -> dict[str, Any]:
    """
    Nests the threads comments hierarchically,
    and saves them to a formatted JSON file.

    Args:
        thread_list (List[ThreadDetails])
    """
    processed_threads = []

    # Process each thread to build the comment tree
    for thread in thread_list:
        p_thread = build_thread_tree(thread)
        processed_threads.append(p_thread)

    return {"threads": processed_threads, "length": len(processed_threads)}


def export_threads_to_json(thread_list: List[ThreadDetails], file_path: Path | str):
    """
    Takes a list of ThreadDetails dataclasses, nests the comments hierarchically,
    and saves them to a formatted JSON file.

    Args:
        thread_list (List[ThreadDetails])
        file_path (str)
    """

    result = build_thread_trees(thread_list)
    completed = write_json_file(
        file_path, result, indent=4, ensure_ascii=False, default=datetime_serializer
    )

    if completed:
        print(
            f"Successfully saved {result["length"]} threads with nested comments to '{file_path}'."
        )
