from .reddit_threads.reddit_threads_scraper import reddit_threads_scraper
from .discourse_topics.discourse_topics_retriever import discourse_topics_retriever
from .jenkins_docs.jenkins_docs_scraper import jenkins_docs_scraper
from .plugin_docs.plugin_docs_scraper import plugin_docs_scraper
from ..models import DataSource
from pathlib import Path
import os


def start_collectors(sources: list[DataSource], output_dir: Path):
    """Start collectors"""

    collector_functions = {
        DataSource.JENKINS_DOCS: jenkins_docs_scraper,
        DataSource.PLUGIN_DOCS: plugin_docs_scraper,
        DataSource.DISCOURSE_TOPICS: discourse_topics_retriever,
        DataSource.REDDIT_THREADS: reddit_threads_scraper,
    }

    print("--------- START COLLECTION PHASE ---------")
    for source in sources:
        func = collector_functions[source]
        if func:
            print(f"EXECUTING {source} COLLECTOR")
            func(output_dir)
    print("--------- END COLLECTION PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")
    start_collectors(
        [
            DataSource.JENKINS_DOCS,
            DataSource.PLUGIN_DOCS,
            DataSource.DISCOURSE_TOPICS,
            DataSource.REDDIT_THREADS,
        ],
        OUTPUT_DIR,
    )
