import os
import requests
from bs4 import BeautifulSoup
from typing import List
from ...tools.common import write_json_file
from pathlib import Path

def fetch_plugin_names() -> List[str]:
    """
    Fetches a list of available plugin artifact names (.hpi) from the Jenkins update site.
    
    Returns:
        list[str]: List of raw plugin file names (e.g., 'git.hpi', 'docker-slaves.hpi').
    """

    list_url = "https://updates.jenkins.io/experimental/latest/"

    print("Fetching plugin names list")
    response = requests.get(list_url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, "html.parser")

    plugin_list = []
    ul = soup.find("ul", class_="artifact-list")
    if ul:
        for li in ul.find_all("li"):
            a_tag = li.find("a")
            if a_tag and "href" in a_tag.attrs:
                href = a_tag["href"]
                plugin_name = str(href).strip("/").strip()
                if plugin_name:
                    plugin_list.append(plugin_name)

    print(f"Found {len(plugin_list)} plugins.")
    return plugin_list



def plugin_names_scraper(output_dir: Path):
    OUTPUT_FILE_PATH = output_dir / "raw" / "plugin_names.json"

    plugins = fetch_plugin_names()

    plugin_names = [plugin_name.split(".")[0] for plugin_name in plugins]

    write_json_file(OUTPUT_FILE_PATH, plugin_names, indent=2, ensure_ascii=False)
    print(f"Saved plugin list to {OUTPUT_FILE_PATH}")



if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "..", "output")

    plugin_names_scraper(OUTPUT_DIR)