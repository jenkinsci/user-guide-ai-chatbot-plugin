from data.preprocessing.jenkins_docs_processor import jenkins_docs_processor
from data.preprocessing.plugin_docs_processor import plugin_docs_processor
from data.preprocessing.discourse_topics_processor import discourse_topics_processor
from data.preprocessing.reddit_threads_processor import reddit_threads_processor
from ..models import DataSource
from pathlib import Path
import os


def start_processors(sources: list[DataSource], output_dir: Path):
    """ Start processors """

    processing_functions = {
        DataSource.JENKINS_DOCS: jenkins_docs_processor,
        DataSource.PLUGIN_DOCS: plugin_docs_processor,
        DataSource.DISCOURSE_TOPICS: discourse_topics_processor,
        DataSource.REDDIT_THREADS: reddit_threads_processor,
    }

    print("--------- START PREPROCESSING PHASE ---------")
    for source in sources: 
        func = processing_functions[source]
        if func:
            print(f"EXECUTING {source} PROCESSOR") 
            func(output_dir)
    print("--------- END PREPROCESSING PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")
    start_processors([DataSource.JENKINS_DOCS, DataSource.PLUGIN_DOCS, DataSource.DISCOURSE_TOPICS, DataSource.REDDIT_THREADS], OUTPUT_DIR)
 