from .plugin_names_scraper import start_plugin_names_scraper
import os
from bs4 import BeautifulSoup
import requests
from ..collection_utils import retry_until_success
from pathlib import Path
from typing import Optional
from ...tools.common import write_json_file, read_json_file

def get_version(sidebar) -> str | None:
    """
        Extract current plugin version.
    """
    rd_el = sidebar.find("h5")

    if rd_el: 
        return str(rd_el.text).split(" ")[1]
    
    return None


def get_jenkins_version_req_and_release_date(sidebar) -> tuple[str | None, str | None]:
    """
        Extract current jenkins version required and its release date.
    """
    div_list = sidebar.find_all("div")
    
    time_el = div_list[0].find("time")
    datetime = None
    if time_el:
        datetime = str(time_el.get("datetime")) 

    jenkins_ver_el = div_list[1]
    jenkins_version_req = None
    if jenkins_ver_el: 
        jenkins_version_req = str(jenkins_ver_el.text).split(" ")[2]

    return jenkins_version_req, datetime


@retry_until_success(3.0, 3)
def fetch_plugin_details(plugin_name: str) -> Optional[dict[str, str]]:
    """
    Extract plugin details including docs content, version and jenkins version required.

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

    sidebar = soup.find('div', class_='col-md-3 sidebar')
    if sidebar:          
        plugin_details["version"] = get_version(sidebar)
        plugin_details["jenkins_version_req"], plugin_details["release_date"]  = get_jenkins_version_req_and_release_date(sidebar)


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


def start_plugin_docs_scraper():
    """
    Start the Plugin docs scraper.
    """
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PLUGIN_NAMES_LIST_PATH = os.path.join(SCRIPT_DIR, "..", "..", "output", "raw", "plugin_names.json")
    OUTPUT_PATH = Path(os.path.join(SCRIPT_DIR, "..", "..", "output", "raw", "plugin_docs.json"))

    # Fetch plugin names list and stores it
    start_plugin_names_scraper()

    plugin_names_list = []

    # Get plugin names list content
    plugin_names_list = read_json_file(PLUGIN_NAMES_LIST_PATH)

    plugin_docs = collect_plugin_docs(plugin_names_list)

    print(f"Total plugins docs found: {len(plugin_docs)}")

    # Store in a json file 
    write_json_file(OUTPUT_PATH, 
                plugin_docs, 
                indent=4,                     
                ensure_ascii=False)


if __name__ == "__main__":
    start_plugin_docs_scraper()