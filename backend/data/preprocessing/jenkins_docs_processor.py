import os
from bs4 import BeautifulSoup
from .preprocessing_utils import (
    remove_container_by_class,
    remove_tags,
    extract_page_content_container,
    remove_html_comments,
    remove_edge_navigation_blocks,
    strip_html_body_wrappers,
    split_doc_types,
)
from ..tools.common import read_json_file, write_json_file, convert_date_str_in_iso
from pathlib import Path


def filter_content(urls: list[str], data, is_developer_content):
    """
    Filters HTML content for a list of URLs by extracting the main section
    and cleaning out unwanted elements like TOC, scripts, images, nav blocks, and comments.

    Parameters:
    - urls (list): List of URLs to filter.
    - data (dict): Dictionary of raw HTML content keyed by URL.
    - is_developer_content (bool): Whether the content is from developer docs.

    Returns:
    - dict: Filtered HTML content keyed by URL.
    """
    config = get_config(is_developer_content)
    filtered_contents = {}

    for url in urls:
        if url not in data:
            print(f"URL not found in data: {url}")
            continue
        content = data[url]
        soup = BeautifulSoup(content, "lxml")

        content_extracted = extract_page_content_container(
            soup, config["class_to_extract"]
        )
        if content_extracted == "":
            print(
                f"NO {config["class_to_extract"]} FOUND IN A {"" if is_developer_content else "NON "}DEVELOPER PAGE! Skipping page: %{url}"
            )
            continue

        # Remove eventually toc (table of content)
        content_without_toc = remove_container_by_class(content_extracted, "toc")

        # Remove eventually img or script tags
        content_filtered_by_tags = remove_tags(content_without_toc)

        # Remove eventually navigation blocks (for docs under /developer this is not necessary)
        content_without_navigation_blocks = (
            content_filtered_by_tags
            if is_developer_content
            else remove_edge_navigation_blocks(content_filtered_by_tags)
        )

        content_without_comments = remove_html_comments(
            content_without_navigation_blocks
        )

        path_without_https = url.split("//")[1]
        path_without_domain = path_without_https.split("/", 1)[1]

        filtered_contents[path_without_domain] = strip_html_body_wrappers(
            content_without_comments
        )

    return filtered_contents


def get_config(is_developer_content):
    """
    Returns configuration options depending on doc type. Introduced to maintain in the future
    a unique filter_content function, without hardcoding parameters whether it is a developer
    content or not.

    Parameters:
    - is_developer_content (bool): Whether the content is from developer docs.

    Returns:
    - dict: Configuration dict with class name to extract.
    """
    if is_developer_content:
        return {"class_to_extract": "col-8"}

    return {"class_to_extract": "col-lg-9"}


def jenkins_docs_processor(output_dir: Path):
    """Start Jenkins Docs processor."""

    INPUT_FILE_PATH = output_dir / "raw" / "jenkins_docs.json"
    OUTPUT_FILE_PATH = output_dir / "processed" / "jenkins_docs.json"

    data = read_json_file(INPUT_FILE_PATH)

    developer_urls, non_developer_urls = split_doc_types(data["pages"])

    print("Processing Developer contents")
    developer_content_filtered = filter_content(developer_urls, data["pages"], True)
    print("Processing  Non Developer contents")
    non_developer_content_filtered = filter_content(
        non_developer_urls, data["pages"], False
    )

    output = {}
    output["docs_version"] = data["docs_version"]
    output["pubblication_date"] = convert_date_str_in_iso(data["pubblication_date"])
    output["pages"] = {}
    output["pages"]["developer"] = developer_content_filtered
    output["pages"]["non_developer"] = non_developer_content_filtered

    write_json_file(OUTPUT_FILE_PATH, output, indent=4)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    jenkins_docs_processor(OUTPUT_DIR)
