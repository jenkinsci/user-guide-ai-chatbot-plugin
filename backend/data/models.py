from enum import Enum

class DataSource(Enum):
    JENKINS_DOCS = "jenkins_docs"
    PLUGIN_DOCS = "plugin_docs"
    DISCOURSE_TOPICS = "discourse_topics"
    REDDIT_THREADS = "reddit_threads"

class DataPhase(Enum):
    COLLECTION = "collection"
    PREPROCESSING = "preprocessing"
    FORMATTING = "formatting"
    EMBEDDING = "embedding"