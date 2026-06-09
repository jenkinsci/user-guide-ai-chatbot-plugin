from .jenkins_docs_formatter import jenkins_docs_formatter
from .plugin_docs_formatter import plugin_docs_formatter
from .discourse_topics_formatter import discourse_formatter
from .reddit_threads_formatter import reddit_formatter 
from ..models import DataSource
from pathlib import Path
import os

def start_formatters(sources: list[DataSource], output_dir: Path):
    """ Start formatters """

    formatter_functions = {
        DataSource.JENKINS_DOCS: jenkins_docs_formatter,
        DataSource.PLUGIN_DOCS: plugin_docs_formatter,
        DataSource.DISCOURSE_TOPICS: discourse_formatter,
        DataSource.REDDIT_THREADS: reddit_formatter,
    }

    print("--------- START FORMATTING PHASE ---------")
    for source in sources: 
        func = formatter_functions[source]
        if func:
            print(f"EXECUTING {source} FORMATTER") 
            func(output_dir)
    print("--------- END FORMATTING PHASE ---------")


if __name__ == "__main__":
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = Path(SCRIPT_DIR, "..", "output")

    start_formatters([DataSource.JENKINS_DOCS, DataSource.PLUGIN_DOCS, DataSource.DISCOURSE_TOPICS, DataSource.REDDIT_THREADS], OUTPUT_DIR)
 

 