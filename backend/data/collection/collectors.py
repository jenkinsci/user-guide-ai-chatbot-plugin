from .reddit_threads.reddit_scraper import start_reddit_threads_scraper
from .discourse_topics.discourse_retriever import start_discourse_topics_retriever
from .jenkins_docs.jenkins_docs_scraper import start_jenkins_docs_scraper
from .plugin_docs.plugin_docs_scraper import start_plugin_docs_scraper
from ..models import DataSource


def start_collectors(sources: list[DataSource]):
    """ Start collectors """

    collector_functions = {
        DataSource.JENKINS_DOCS: start_jenkins_docs_scraper,
        DataSource.PLUGIN_DOCS: start_plugin_docs_scraper,
        DataSource.DISCOURSE_TOPICS: start_discourse_topics_retriever,
        DataSource.REDDIT_THREADS: start_reddit_threads_scraper,
    }

    print("--------- START COLLECTION PHASE ---------")
    for source in sources: 
        func = collector_functions[source]
        if func:
            print(f"EXECUTING {source} COLLECTOR") 
            func()
    print("--------- END COLLECTION PHASE ---------")


if __name__ == "__main__":
    start_collectors([DataSource.JENKINS_DOCS, DataSource.PLUGIN_DOCS, DataSource.DISCOURSE_TOPICS, DataSource.REDDIT_THREADS])