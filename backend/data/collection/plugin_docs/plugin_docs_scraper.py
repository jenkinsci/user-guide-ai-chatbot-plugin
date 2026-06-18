from .plugin_names_scraper import plugin_names_scraper
import os
from bs4 import BeautifulSoup
import requests
from ..collection_utils import retry_until_success
from pathlib import Path
from typing import Optional
from ...tools.common import write_json_file, read_json_file
from .plugin_docs_utils import get_jenkins_version_req_and_release_date, get_version


@retry_until_success(3.0, 3)
def fetch_plugin_details(plugin_name: str) -> Optional[dict[str, str]]:
    """
    Extract plugin details including docs content, version and jenkins version required.
    If exceptions occur, retry execution up to 3 times.
    Wait 3.0 seconds after the exception occurs.

    Args:
        plugin_name (str): The name of the plugin.

    Returns:
        plugin_details (dict)
    """

    url = f"https://plugins.jenkins.io/{plugin_name}/"

    plugin_details = {}
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")
    content_div = soup.find("div", class_="content")

    if content_div:
        plugin_details["content"] = str(content_div)

    sidebar = soup.find("div", class_="col-md-3 sidebar")
    if sidebar:
        plugin_details["version"] = get_version(sidebar)
        plugin_details["jenkins_version_req"], plugin_details["release_date"] = (
            get_jenkins_version_req_and_release_date(sidebar)
        )

    return plugin_details


def collect_plugin_docs(plugin_names) -> dict[str, str]:
    """
    Iterates through all plugin names and collects their details.

    Args:
        plugin_names (List[str]): List of plugin names to fetch.

    Returns:
        dict: A dictionary mapping plugin names to their details.
    """
    result = {}

    for idx, plugin_name in enumerate(plugin_names):
        print(f"[{idx+1}/{len(plugin_names)}] Fetching {plugin_name} docs...")
        data = fetch_plugin_details(plugin_name)

        if data:
            result[plugin_name] = data

    return result


def plugin_docs_scraper(output_dir: Path):
    """
    Start the Plugin docs scraper.
    """
    PLUGIN_NAMES_LIST_FILE_PATH = output_dir / "raw" / "plugin_names.json"
    OUTPUT_FILE_PATH = output_dir / "raw" / "plugin_docs.json"

    # Fetch plugin names list and stores it
    plugin_names_scraper(output_dir)

    plugin_names_list = []

    # Get plugin names list content
    plugin_names_list = read_json_file(PLUGIN_NAMES_LIST_FILE_PATH)

    plugin_docs = collect_plugin_docs(plugin_names_list)

    print(f"Total plugins docs found: {len(plugin_docs)}")

    # Store in a json file
    write_json_file(OUTPUT_FILE_PATH, plugin_docs, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "..", "output")

    plugin_docs_scraper(OUTPUT_DIR)
