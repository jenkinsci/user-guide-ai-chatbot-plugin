from data.preprocessing.jenkins_docs_processor import start_jenkins_docs_processor
from data.preprocessing.plugin_docs_processor import start_plugin_docs_processor
from data.preprocessing.discourse_topics_processor import start_discourse_topics_processor
from data.preprocessing.reddit_threads_processor import start_reddit_threads_processor
from ..models import DataSource


def start_processors(sources: list[DataSource]):
    """ Start processors """

    processing_functions = {
        DataSource.JENKINS_DOCS: start_jenkins_docs_processor,
        DataSource.PLUGIN_DOCS: start_plugin_docs_processor,
        DataSource.DISCOURSE_TOPICS: start_discourse_topics_processor,
        DataSource.REDDIT_THREADS: start_reddit_threads_processor,
    }

    print("--------- START PREPROCESSING PHASE ---------")
    for source in sources: 
        func = processing_functions[source]
        if func:
            print(f"EXECUTING {source} PROCESSOR") 
            func()
    print("--------- END PREPROCESSING PHASE ---------")


if __name__ == "__main__":
    start_processors([DataSource.JENKINS_DOCS, DataSource.PLUGIN_DOCS, DataSource.DISCOURSE_TOPICS, DataSource.REDDIT_THREADS])
 