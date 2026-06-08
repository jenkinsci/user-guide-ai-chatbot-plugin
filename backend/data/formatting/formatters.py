from .jenkins_docs_formatter import start_jenkins_docs_formatter
from .plugin_docs_formatter import start_plugin_docs_formatter
from .discourse_topics_formatter import start_discourse_formatter
from .reddit_threads_formatter import start_reddit_formatter 
from ..models import DataSource


def start_formatters(sources: list[DataSource]):
    """ Start formatters """

    formatter_functions = {
        DataSource.JENKINS_DOCS: start_jenkins_docs_formatter,
        DataSource.PLUGIN_DOCS: start_plugin_docs_formatter,
        DataSource.DISCOURSE_TOPICS: start_discourse_formatter,
        DataSource.REDDIT_THREADS: start_reddit_formatter,
    }

    print("--------- START FORMATTING PHASE ---------")
    for source in sources: 
        func = formatter_functions[source]
        if func:
            print(f"EXECUTING {source} FORMATTER") 
            func()
    print("--------- END FORMATTING PHASE ---------")


if __name__ == "__main__":
    start_formatters([DataSource.JENKINS_DOCS, DataSource.PLUGIN_DOCS, DataSource.DISCOURSE_TOPICS, DataSource.REDDIT_THREADS])
 

 