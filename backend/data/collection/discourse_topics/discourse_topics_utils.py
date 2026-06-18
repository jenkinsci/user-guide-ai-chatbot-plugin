from typing import List, Dict, Any
from .models import Post, TopicDetails, SearchFilters
from ...tools.common import write_json_file
from pathlib import Path


def print_topic_preview(topic_details: TopicDetails):
    first_post = topic_details.posts[0]
    raw_content = first_post.content

    # Print a preview of the content
    snippet = raw_content[:150].replace("\n", " ")
    print(f"    Content: {snippet}...\n")


def build_discourse_endpoint(base_url: str, search_filters: SearchFilters) -> str:
    """
    Builds the correct Discourse API endpoint based on the provided filters.

    Args:
        base_url (str): Discourse base url.
        category_slug (Optional[str])
        subcategory_slug (Optional[str])
        tag_slug (Optional[str])

    Returns:
        str: Specific Discourse endpoint path

    """
    base = base_url.rstrip("/")

    category_slug = search_filters.category_slug
    subcategory_slug = search_filters.subcategory_slug
    tag_slug = search_filters.tag_slug

    # Filtering with a Tag
    if tag_slug:
        if category_slug and subcategory_slug:
            return f"{base}/tags/c/{category_slug}/{subcategory_slug}/{tag_slug}.json"
        elif category_slug:
            return f"{base}/tags/c/{category_slug}/{tag_slug}.json"
        else:
            return f"{base}/tag/{tag_slug}.json"

    # Filtering by Category (without Tag)
    if category_slug:
        if subcategory_slug:
            return f"{base}/c/{category_slug}/{subcategory_slug}.json"
        else:
            return f"{base}/c/{category_slug}.json"

    # No filters applied, fetch global latest topics
    return f"{base}/latest.json"


def build_topic_tree(raw_posts_data: List[Dict[str, Any]]) -> List[Post]:
    """
    Converts a flat list of Discourse API posts into a hierarchical tree based
    on the 'reply_to_post_number' field.

    Args:
        raw_posts_data (List[Dict[str, Any]]): Posts list

    Returns:
        List[Post]: Topic with its hierarchical tree format
    """
    # 1. Convert all raw dictionaries into Post objects
    # We store them in a dictionary keyed by 'post_number' for O(1) fast lookups
    post_map: Dict[int, Post] = {}

    for post_dict in raw_posts_data:
        post_obj = Post.from_dict(post_dict)
        post_map[post_obj.post_number] = post_obj

    root_posts: List[Post] = []

    # Build the relationships
    for post_number, post in post_map.items():
        # post_number 1 is always the original topic starter
        parent_number = post.reply_to_post_number

        if parent_number and parent_number in post_map:
            # If it's a reply to a specific post, append it to that parent's replies list
            parent_post = post_map[parent_number]
            parent_post.replies.append(post)
        else:
            # If it has no parent (or parent is missing), it's a root-level post
            root_posts.append(post)

    # Return only the top-level posts; the rest are accessible via the 'replies' lists
    return root_posts


def export_topics_to_json(topic_list: List[TopicDetails], file_path: Path | str):
    """
    Store list of TopicDetail objs in a json file

    Args:
        topic_list (List[TopicDetail]): TopicDetail objs to store
        file_path (str): Path where to store the objs
    """

    topic_length = len(topic_list)

    final_output_dict = {
        "topics": [topic.model_dump() for topic in topic_list],
        "length": topic_length,
    }

    try:
        write_json_file(file_path, final_output_dict, indent=4, ensure_ascii=False)
        print(
            f"Successfully saved {topic_length} posts with nested comments to '{file_path}'."
        )

    except IOError as file_error:
        print(f"An error occurred while saving the file: {file_error}")


if __name__ == "__main__":
    topics_detail = [
        TopicDetails(
            topic_id=0,
            title="Jonh",
            posts=[
                Post(
                    id=1,
                    post_number=3,
                    username="Mario",
                    content="ciao a tutti!",
                    created_at="2026-05-14T11:20:33.214Z",
                    is_solution=False,
                    replies=[],
                    reply_to_post_number=None,
                    reactions=[],
                    url="",
                )
            ],
        )
    ]
    export_topics_to_json(topics_detail, "data/raw/dump.json")
