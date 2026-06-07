import os
from bs4 import BeautifulSoup
from .preprocessing_utils import (
    remove_tags,
    remove_html_comments,
    get_visible_text_length,
    strip_html_body_wrappers
)
from data.tools.common import read_json_file, write_json_file


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "raw", "plugin_docs.json")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "..", "output", "processed", "plugin_docs.json")

MIN_VISIBLE_TEXT_LENGTH = 60

def process_plugin_docs(plugin_docs):
    """Clean and filter plugin HTML docs based on content length.

    Args:
        plugin_docs (dict): Raw plugin documentation keyed by plugin name.

    Returns:
        dict: Filtered documentation content.
    """
    processed_plugin_docs = {}

    for plugin_name, data in plugin_docs.items():
        html_content = data["content"]
        soup = BeautifulSoup(html_content, "lxml")
        html_content = str(soup)
 
        cleaned_html = remove_tags(html_content)

        content_without_comments = remove_html_comments(cleaned_html)
        content_without_wrappers = strip_html_body_wrappers(content_without_comments)

        text_length = get_visible_text_length(content_without_wrappers)
        if text_length > MIN_VISIBLE_TEXT_LENGTH:
            processed_plugin_docs[plugin_name] = {
                "version": data["version"],
                "release_date": data["release_date"],
                "jenkins_version_req": data["jenkins_version_req"],
                "content": content_without_wrappers
                }
        else:
            print(
                f"Skipping plugin '{plugin_name}' - visible text length: {text_length} <= {MIN_VISIBLE_TEXT_LENGTH}",
            )

    print(
      f"Processed {len(processed_plugin_docs)} out of {len(plugin_docs)} plugins.",     
    )

    return processed_plugin_docs

def start_plugin_docs_processor():
    """Start Plugin docs processor."""
    plugin_data = {}

    plugin_data = read_json_file(INPUT_PATH)

    print(f"Handling {len(plugin_data)} plugin docs.")

    processed_plugin_docs = process_plugin_docs(plugin_data)

    saved = write_json_file(OUTPUT_PATH, processed_plugin_docs)

    if saved:
        print(f"Saved processed plugins to {OUTPUT_PATH}.")
    

if __name__ == "__main__":
    start_plugin_docs_processor()