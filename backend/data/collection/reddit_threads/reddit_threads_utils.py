from dataclasses import asdict
from datetime import datetime
from typing import List
from .models import ThreadDetails, Section
from typing import List, Optional
import re
from ...tools.common import datetime_serializer, write_json_file

def print_thread_details(post: ThreadDetails):
    """
    Print Thread details

    Args: 
        post (PostDetails)
    """
    print("\n--- POST ---")
    print(f"Title: {post.title}")
    print(f"Author: {post.author.username}")
    print(f"Subreddit: {post.subreddit}")
    print(f"Post Date: {post.create_date}")
    print(f"Post Points: {post.points}")
    print(f"Total comments text stated: {post.comments_qty}")
    print(f"Actually extracted comments: {len(post.comments)}")
    print("\n--- Comments ---")
    for c in post.comments:
        print(f"- {c.author.username} ({c.points} pts): {c.content[:60]}... [Replies to: {c.parent_id}]")


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


def export_threads_to_json(thread_list: List[ThreadDetails], file_path: str):
    """
    Takes a list of PostDetails dataclasses, nests the comments hierarchically,
    and saves them to a formatted JSON file.

    Args: 
        thread_list (List[PostDetails])
        file_path (str)
    """

    thread_as_dicts = [asdict(post) for post in thread_list]
    
    # Process each post to build the comment tree
    for post_data in thread_as_dicts:
        flat_comments_list = post_data.get('comments', [])
        
        # Initialize a 'replies' list for every comment and build a lookup map
        comment_lookup_map = {}
        for single_comment in flat_comments_list:
            single_comment['replies'] = []
            comment_lookup_map[single_comment['id']] = single_comment
            
        hierarchical_comments_tree = []
        
        # Iterate again to place each comment inside its parent's 'replies' list
        for single_comment in flat_comments_list:
            parent_id = single_comment.get('parent_id')
            
            # If the parent_id starts with 't1_', it's a reply to another comment
            if parent_id and str(parent_id).startswith('t1_'):
                parent_comment_node = comment_lookup_map.get(parent_id)
                
                if parent_comment_node:
                    # Attach this comment to its parent's replies
                    parent_comment_node['replies'].append(single_comment)
                else:
                    # Fallback: if the parent comment is missing from our scrape we append it to the root
                    hierarchical_comments_tree.append(single_comment)
            else:
                # It's a top-level comment (parent_id starts with 't3_' or is None)
                hierarchical_comments_tree.append(single_comment)
                
        # Replace the flat list with the newly structured tree
        post_data['comments'] = hierarchical_comments_tree

    # Wrap everything in the final structure
    posts_length = len(thread_as_dicts)

    final_output_dict = {
        "posts": thread_as_dicts,
        "length": posts_length
    }    
    
    completed = write_json_file(file_path, final_output_dict, indent=4, ensure_ascii=False, default=datetime_serializer)

    if completed: 
        print(f"Successfully saved {posts_length} posts with nested comments to '{file_path}'.")
 

def extract_integer(text: str) -> int:
    """Extracts the first integer found in a string (e.g., '14 points' -> 14)."""
    if not text:
        return 0
    
    clean_text = text.replace(',', '')
    
    match = re.search(r'[+-]?\d+', clean_text)
    
    return int(match.group()) if match else 0


def parse_reddit_datetime(time_element) -> Optional[datetime]:
    """Parses Reddit's ISO datetime attribute."""
    if time_element and time_element.has_attr('datetime'):
        try:
            return datetime.fromisoformat(time_element['datetime'])
        except ValueError:
            return None
    return None