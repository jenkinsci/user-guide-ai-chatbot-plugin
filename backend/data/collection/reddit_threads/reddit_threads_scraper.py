import requests
from bs4 import BeautifulSoup
import time
from typing import List, Optional, Set
from .models import ThreadPreview, Author, Comment, ThreadDetails, Section
from .reddit_threads_utils import (
    get_subreddit_page_url,
    export_threads_to_json,
    extract_integer,
    parse_reddit_datetime,
    print_thread_details,
)
from ..collection_utils import retry_until_success, sleep
import os
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def scrape_subreddit_threads(
    target_subreddit: str, section: Section, n_pages: int = 3
) -> Optional[List[ThreadPreview]]:
    """
    Scrape the threads title and id contained in a specific subreddit section.

    Args:
        target_subreddit (str): Subreddit name.
        section (Section): Section to scrape.
        n_pages (int): number of pages to scrape.

    Returns:
        Optional[List[ThreadPreview]]
    """

    custom_headers = HEADERS

    current_url = get_subreddit_page_url(target_subreddit, section)

    threads = []
    page_counter = 0

    while page_counter < n_pages and current_url:
        page_counter += 1
        print(
            f"\n--- Scraping Page {page_counter} | Section: {section.value} | N. Threads scraped: {len(threads)} | URL: {current_url} ---"
        )

        try:
            # Execute the HTTP GET request
            html_response = requests.get(current_url, headers=custom_headers)
            html_response.raise_for_status()

            # Parse the raw HTML content
            parsed_soup = BeautifulSoup(html_response.text, "html.parser")

            # Find all structural containers for threads
            thread_elements = parsed_soup.find_all("div", class_="thing")

            # Extract specific data from each container
            for single_thread in thread_elements:
                thread_title_element = single_thread.find("a", class_="title")
                thread_id = str(single_thread["id"].split("_", 1)[1])

                if thread_title_element:
                    extracted_title = thread_title_element.text

                    threads.append(ThreadPreview(thread_id, extracted_title))
                    print(f"Id: {thread_id}, Title: {extracted_title}")

            # --- PAGINATION LOGIC ---
            # Look for the span containing the 'Next' button
            next_button_span = parsed_soup.find("span", class_="next-button")

            if next_button_span:
                # Find the anchor tag and extract the href attribute
                next_link_element = next_button_span.find("a")
                if next_link_element and "href" in next_link_element.attrs:
                    current_url = str(next_link_element["href"])
                else:
                    print("\nReached the last page or next link not found.")
                    current_url = None
            else:
                print("\nNo 'next-button' span found. Stopping pagination.")
                current_url = None

            # Pause execution to respect server load
            if current_url:
                sleep(4)

        except requests.exceptions.RequestException as network_error:
            print(f"A network error occurred: {network_error}")
            break

    return threads


@retry_until_success(60.0, 3)
def scrape_thread_details(thread_id: str) -> Optional[ThreadDetails]:
    """
    Scrape the details of specific thread.
    If exceptions occur, retry execution up to 3 times.
    Wait 3.0 seconds after the exception occurs.

    Args:
        thread_id (str)

    Returns:
        Optional[ThreadDetails]
    """

    # old.reddit automatically redirects /comments/{id} to the full URL
    target_url = f"https://old.reddit.com/comments/{thread_id.split("_")[1]}/"

    headers = HEADERS

    try:
        response = requests.get(target_url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # --- EXTRACT MAIN THREAD DATA ---

        # The main thread container is the first 'div.thing' inside 'div#siteTable'
        site_table = soup.find("div", id="siteTable")
        if not site_table:
            print("Could not find the main thread container.")
            return None

        main_post_node = site_table.find("div", class_="thing")

        if not main_post_node:
            return None

        # Subreddit name
        subreddit_element = soup.select_one("span.redditname > a")
        subreddit_name = subreddit_element.text if subreddit_element else "Unknown"

        # Title
        title_element = main_post_node.find("a", class_="title")
        thread_title = title_element.text if title_element else "Unknown Title"

        # Content (Self-text)
        body_element = main_post_node.find("div", class_="usertext-body")
        content = str(body_element) if body_element else ""

        # Author and Subreddit
        author_element = main_post_node.find("a", class_="author")
        post_author_name = author_element.text if author_element else "[deleted]"

        # Points (Score)
        score_element = main_post_node.find("div", class_="score unvoted")
        thread_points = extract_integer(score_element.text if score_element else "0")

        # Create Date
        time_element = main_post_node.find("time")
        create_date = parse_reddit_datetime(time_element)

        # Comments Quantity
        comments_link = soup.find("a", class_="bylink comments")
        thread_comments_qty = extract_integer(
            comments_link.text if comments_link else "0"
        )

        # --- EXTRACT COMMENTS ---
        extracted_comments = []
        comment_area = soup.find("div", class_="commentarea")

        if comment_area:
            # Find all individual comments in the thread
            comment_nodes = comment_area.find_all("div", class_="comment")

            for comment_node in comment_nodes:

                # Avoid extracting 'more comments' placeholder links
                if "morechildren" in comment_node.get("class", []):  # type: ignore
                    print("SKIP: ", thread_id)
                    continue

                # ID
                comment_id = comment_node.get("data-fullname", "unknown")

                # Author
                c_author_tag = comment_node.find("a", class_="author")
                c_author_name = c_author_tag.text if c_author_tag else "[deleted]"

                # Content
                c_body_el = str(comment_node.find("div", class_="usertext-body"))
                c_content = str(c_body_el) if c_body_el else ""

                # Points
                c_score_tag = comment_node.find("span", class_="score unvoted")
                # Sometimes scores are hidden on new comments
                c_score_text = (
                    c_score_tag.text
                    if c_score_tag and "score hidden" not in c_score_tag.text
                    else "0"
                )
                c_points = extract_integer(c_score_text)

                # Date
                c_time_tag = comment_node.find("time")
                c_date = parse_reddit_datetime(c_time_tag)

                # Parent ID Logic (To know which comment this replies to)
                parent_node = comment_node.find_parent("div", class_="comment")
                if parent_node:
                    c_parent_id = parent_node.get("data-fullname")
                else:
                    # If there's no parent comment, it's a top-level reply to the main post
                    c_parent_id = thread_id

                # Append to list
                extracted_comments.append(
                    Comment(
                        id=str(comment_id),
                        author=Author(username=c_author_name),
                        content=c_content,
                        points=c_points,
                        create_date=c_date,
                        parent_id=str(c_parent_id),
                    )
                )

        return ThreadDetails(
            id=thread_id,
            title=thread_title,
            content=content,
            author=Author(username=post_author_name),
            subreddit=subreddit_name,
            comments=extracted_comments,
            comments_qty=thread_comments_qty,
            points=thread_points,
            create_date=create_date,
        )

    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch post: {e}")
        raise Exception("Too many request")


def scrape_all_subreddit_sections(subreddit: str) -> Set[str]:
    """
    Scrape all subreddit sections and returns a list of unique threads ids

    Args:
        subreddit (str): Subreddit name

    Returns:
        Set[str]: A set containing all the ids of the found threads
    """

    all_threads = {
        Section.Hot: [],
        Section.New: [],
        Section.Rising: [],
        Section.Controversial: [],
        Section.Top: [],
    }

    total_threads = 0
    uniques_id = set()

    max_pages = 1000
    threads_per_page = 25

    for k in all_threads.keys():
        try:
            list: List[ThreadPreview] | None = scrape_subreddit_threads(
                subreddit, k, int(max_pages / threads_per_page)
            )
            if list:
                all_threads[k] = list
                total_threads += len(list)
                uniques_id.update([x.id for x in list])
        except Exception:
            pass

    for k, v in all_threads.items():
        print(f"{k}: {len(v)} THREADS")

    print(f"Total: {total_threads} THREADS")
    print(f"Unique: {len(uniques_id)} THREADS")

    return uniques_id


def scrape_all_threads_details(thread_ids: Set[str]) -> List[ThreadDetails]:
    """
    Scrape all thread details with ids contained in the input list

    Args:
        thread_ids (Set[str]): List containing thread ids

    Returns:
        List[ThreadDetails]
    """
    threads = []

    for id in thread_ids:
        print(
            f"\n--- Scraping Threads details | N. Thread scraped: {len(threads)} | Id: {id} ---"
        )

        thread_details = scrape_thread_details(thread_id=id)

        if thread_details:
            threads.append(thread_details)
            print_thread_details(thread_details)

        sleep_time = 5
        time.sleep(sleep_time)
        print(f"Waiting for {sleep_time} seconds...")

    return threads


def reddit_threads_scraper(output_dir: Path):
    """
    Start the Reddit scraper.
    """
    OUTPUT_FILE_PATH = output_dir / "raw" / "reddit_threads.json"

    SUBREDDIT_NAME = "jenkinsci"

    unique_thread_ids = scrape_all_subreddit_sections(SUBREDDIT_NAME)
    thread_list = scrape_all_threads_details(unique_thread_ids)

    export_threads_to_json(thread_list, OUTPUT_FILE_PATH)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "..", "output")

    reddit_threads_scraper(OUTPUT_DIR)
