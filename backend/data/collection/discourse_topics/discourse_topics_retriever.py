import requests
from typing import Dict, List, Optional
from .discourse_topics_utils import build_discourse_endpoint, build_topic_tree, export_topics_to_json, print_topic_preview
from .models import TopicCollection, TopicDetails, SearchFilters, SolutionPost
import time
from ..collection_utils import retry_until_success
import os


DISCOURSE_URL = "https://community.jenkins.io"


@retry_until_success(3.0, 3)
def fetch_topic_previews(
    page: int,
    base_url: str, 
    search_filters: SearchFilters
) -> List[Dict]:
    """
        Fetch a list of 30 topic summaries

        Args:
            page (int): Number of the page to retrieve.
            base_url (str): Discourse base url.
            search_filters (SearchFilters): Query's search filters.
        
        Returns:
            List[Dict]: A list containing 30 topic summary dicts
    """

    # Generate the dynamic endpoint
    endpoint = build_discourse_endpoint(
        base_url=base_url,
        search_filters=search_filters
    )
    
    print(f"[*] Hitting endpoint: {endpoint}")
    
    headers = {
        "Accept": "application/json"
    }
    
    params = {
        "page": page
        }

    try:
        # Send the request
        response = requests.get(endpoint, headers=headers, params=params)
        
        # Raise HTTP error if occurs
        response.raise_for_status()
        
        data = response.json()
        topic_preview_list = data.get("topic_list", {}).get("topics", [])

        return topic_preview_list
        
    except requests.exceptions.RequestException as e:
        # If HTTP error occurs log it and raise again exception 
        # in order to trigger the retry
        print(f"[!] Error fetching topics: {e}")
        raise Exception()


def fetch_topic_collection(
    base_url: str, 
    search_filters: SearchFilters
) -> TopicCollection:
    """
        Fetch an entire topic collection

        Args:
            base_url (str): Discourse base url.
            search_filters (SearchFilters): Query's search filters.
        
        Returns:
            TopicCollection: A Collection containing all the TopicSummary objs retrieved
    """

    topic_collection = TopicCollection()
    current_page = 0
    n_topics = 0

    while True: 
        try:
            # Fetch 30 elements
            fetched_topics = fetch_topic_previews(
                current_page, 
                base_url, 
                search_filters
                )
            
            if fetched_topics:
                n_topics += len(fetched_topics)
                print(f"[*] Fetched {n_topics} topics")

                # Add each element to the collection
                for raw_topic in fetched_topics:
                    print(raw_topic.get("title", "no title"))
                    topic_collection.add_topic(raw_topic)

                current_page += 1
                
            else:  
                print(f"[+] Reached the end. No more topics on page {current_page}.")
                break

        except requests.exceptions.RequestException as e:
            print(f"[!] Error fetching page {current_page}: {e}")
            print("Retrying in 10s")
            time.sleep(10)

    return topic_collection


@retry_until_success(3.0, 3)
def fetch_topic_details(
    base_url: str, 
    topic_id: int, 
) -> Optional[TopicDetails]:
    """
        Fetch the details of a specific topic

        Args:
            base_url (str): Discourse base url.
            topic_id (int)
        
        Returns:
            Optional[TopicDetail]: Details of a specific topic
    """
    
    # Endpoint to get the actual posts inside a specific topic
    endpoint = f"{base_url.rstrip('/')}/t/{topic_id}.json"
    
    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()
        
        response_data = response.json()
        post_stream = response_data.get("post_stream", {})
        posts = post_stream.get("posts", [])

        solutions_list = response_data.get("accepted_answers", [])

        solutions = []
        for sol in solutions_list: 
            sol = SolutionPost.from_dict(solutions_list[0])
            solutions.append(sol)

        # Build the topic's tree
        hierarchical_posts = build_topic_tree(posts)
        
        topic = TopicDetails(
            topic_id=response_data.get("id"),
            title=response_data.get("title"),
            posts=hierarchical_posts,
            solutions=solutions
        )

        return topic

    except requests.exceptions.RequestException as e:
        # If HTTP error occurs log it and raise again exception 
        # in order to trigger the retry
        print(f"[!] Error fetching topics: {e}")
        raise Exception()
        

def start_discourse_topics_retriever():
    """
        Start Discourse extractor.
    """
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "..", "output", "raw", "discourse_topics.json")

    filters_list = [SearchFilters("using-jenkins", "support", "")]
    all_topics_collections: List[TopicCollection] = []
    n_topics_found = 0

    # Get topic collection containing topics ids
    for filters in filters_list: 
        print(f"[*] Fetching topics for {filters.category_slug}/{filters.subcategory_slug} tagged with '{filters.tag_slug}'...")
        topics_collection = fetch_topic_collection(
            base_url=DISCOURSE_URL,
            search_filters=filters
        )
        n_topics_found += len(topics_collection.topics)
        all_topics_collections.append(topics_collection)

    
    if n_topics_found:
        print(f"[+] Found {n_topics_found} topics. Fetching topics details...\n")
    else: 
        print("[-] No topics found.")
        return
    
    topics_detail_list: List[TopicDetails] = []
    n_topics_fetched = 0
    
    # Get topic details
    for collection in all_topics_collections:
        for topic in collection.topics:
            topic_id = topic.id
            if not topic_id: continue
            topic_title = topic.title
            
            print(f"--- [{n_topics_fetched}/{n_topics_found}] Topic: {topic_title} (ID: {topic_id}) ---")
            
            # Fetch the topic details
            topic_details = fetch_topic_details(
                base_url=DISCOURSE_URL,
                topic_id=topic_id,
            )
                
            if topic_details:
                topics_detail_list.append(topic_details)
                print_topic_preview(topic_details)

            n_topics_fetched += 1
            time.sleep(0.2)

    export_topics_to_json(topics_detail_list, OUTPUT_PATH)


if __name__ == "__main__":
    start_discourse_topics_retriever()