import os
from urllib.parse import urljoin, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from ...tools.common import write_json_file
from .jenkins_docs_utils import (
    extract_page_content_container,
    is_valid_url,
    normalize_url,
)
from pathlib import Path

BASE_URL = "https://www.jenkins.io/doc/"
visited_urls = set()


def create_session_with_retries() -> requests.Session:
    """Create a requests session with automatic retry on rate limits.

    Uses exponential backoff and respects Retry-After header from server.
    This is an optimistic approach - we don't slow down unless the server
    tells us to.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


# Key: url ; Value: content of that page
data = {}
non_canonic_content_urls = set()


def get_current_jenkins_docs_version(session: requests.Session):
    """
    Retrieve and extract the last jenkins docs version and its pubblication date
    """
    response = session.get("https://www.jenkins.io/changelog/", timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    title_section = soup.find_all(class_="app-releases__item__title")[0]
    date_el = soup.find_all(class_="app-releases__item__date")[0]

    jenkins_ver = None
    pub_date = None

    if date_el:
        pub_date = date_el.text.strip()

    if title_section:
        title_el = title_section.find_all("a")[0]
        if title_el:
            jenkins_ver = str(title_el.text).strip()

    return jenkins_ver, pub_date


def crawl(start_url):
    """Iteratively crawl documentation pages using stack-based DFS.

    Uses an explicit stack instead of recursion to avoid RecursionError
    on deep documentation structures.

    Args:
        start_url: The URL to begin crawling from.
    """
    session = create_session_with_retries()

    jenkins_ver, pub_date = get_current_jenkins_docs_version(session)

    data["docs_version"] = jenkins_ver
    data["pubblication_date"] = pub_date
    data["pages"] = {}

    # Get all the urls in the left nav bar
    stack = [start_url]

    while stack:
        url = stack.pop()

        # Normalize URL before checking visited
        url = normalize_url(url)

        # Fast skip for already visited or invalid URLs
        if url in visited_urls or not is_valid_url(url, BASE_URL):
            continue

        print(f"Visiting: {url}")

        try:
            visited_urls.add(url)

            response = session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

            content = extract_page_content_container(soup)
            if content:
                data["pages"][url] = content
            else:
                non_canonic_content_urls.add(url)

            # Find all links in the page
            links = soup.find_all("a", href=True)

            # Push links in reverse order to maintain original DFS traversal order
            # Stack is LIFO, so reversed() ensures first link gets processed first
            for link in reversed(links):
                href = link["href"]
                full_url = urljoin(url, str(href))
                # Normalize before pushing to prevent duplicate stack entries
                full_url = normalize_url(full_url)
                if is_valid_url(full_url, BASE_URL) and full_url not in visited_urls:
                    stack.append(full_url)

        except requests.RequestException as e:
            # Skip this URL, continue with remaining stack
            print(f"Error accessing {url}: {e}")
            continue


def jenkins_docs_scraper(output_dir: Path):
    """
    Start the Jenkins docs scraper.
    """

    OUTPUT_FILE_PATH = output_dir / "raw" / "jenkins_docs.json"

    print("JENKINS DOCS SCRAPER")
    crawl(BASE_URL)
    print(f"Total pages found: {len(visited_urls)}")
    print(f"Total pages with content: {len(data)}")
    print(f"Non canonic content page structure links: {non_canonic_content_urls}")
    print("Crawling ended")

    print("Saving results in json")
    write_json_file(OUTPUT_FILE_PATH, data, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "..", "output")

    jenkins_docs_scraper(OUTPUT_DIR)
