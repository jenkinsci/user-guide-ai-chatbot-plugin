# Configuration

## Hybrid retriever

The hybrid retriever is used for retrieving docs, discussions and build logs.

Before to using, it's required to collect, vectorize and store the data in the vector db (qdrant). 

There are 4 different types of sources: 
- Official Jenkins Documentation (jenkins_docs)
- Jenkins Plugin Documentations (plugin_docs)
- "r/jenkinsci" Reddit Threads (reddit_threads)
- Official Discourse Topics (discourse_topics)

To start the process of population of the vector db you must run the following command listing the sources you are interested in. 

```bash
python -m data.manager --sources jenkins_docs plugin_docs
```

You can also pick the embedding model and sparse model that you prefer the two default
are the suggested ones.

```bash
####### HYBRID RETRIEVER #######
# Search for one here: https://huggingface.co/models?library=sentence-transformers
HUGGING_FACE_EMBEDDING_NAME="all-MiniLM-L6-v2"
EMBEDDING_SIZE="384"

# Search for one here: https://qdrant.github.io/fastembed/examples/Supported_Models/#supported-text-embedding-models
FAST_EMBED_SPARSE_MODEL_NAME="Qdrant/bm25"

```

## Contextual Retrieval 

The contextual retrieval is a technique used to improve the retrieval accuracy by appending a 
small context summary before each chunk stored in the vectordb.

Read more:
- https://www.datacamp.com/tutorial/contextual-retrieval-anthropic?dc_referrer=https%3A%2F%2Fwww.google.com%2F
- https://platform.claude.com/cookbook/capabilities-contextual-embeddings-guide

WARNING: This function can give some benefits, but it will surely increment setup costs and time.

```bash
######## CONTEXTUAL RETRIEVAL ########
ENABLE_CONTEXTUAL_RETRIEVAL="True"
CONTEXTUAL_LLM_PROVIDER="ollama"
CONTEXTUAL_LLM_MODEL_NAME = "llama3.1:8b"
CONTEXTUAL_LLM_BASE_URL = "http://192.168.178.149:11434/"
CONTEXTUAL_LLM_API_KEY = ""
CONTEXTUAL_LLM_TEMPERATURE = "0"
```

## Observability 

It is possible to configure observability by setting the following env vars, both
LangSmith and LangFuse are supported.

```bash
########### LANGFUSE ############
LANGFUSE_TRACING="true"
LANGFUSE_PUBLIC_KEY="your-public-key"
LANGFUSE_SECRET_KEY="your-secret-key"
LANGFUSE_HOST="https://cloud.langfuse.com"

########### LANGSMITH ############
LANGSMITH_TRACING="true"
LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
LANGSMITH_API_KEY="your-secret-key"
LANGSMITH_PROJECT="AI Chatbot Jenkins"
```

## Agent 

The Agent is powered by two different LLMs.

The Router LLM picks the tools and decide the next action. 
The Final LLM reads the context and info retrieved and create the final response to the user.

If you prefer you can set the same values for both.

The supported providers are: "openai", "groq", "ollama", "anthropic".

ROUTER_LLM_API_KEY (if the provider doesn't require it) and ROUTER_LLM_TEMPERATURE are optional.

```bash
########### AGENT ############
ROUTER_LLM_PROVIDER="groq"
ROUTER_LLM_MODEL_NAME = "llama-3.3-70b-versatile"
ROUTER_LLM_BASE_URL = "https://api.groq.com/openai/v1/"
ROUTER_LLM_API_KEY = "your-secret-key"
ROUTER_LLM_TEMPERATURE = "0"

FINAL_LLM_PROVIDER="groq"
FINAL_LLM_MODEL_NAME = "llama-3.3-70b-versatile"
FINAL_LLM_BASE_URL = "https://api.groq.com/openai/v1/"
FINAL_LLM_API_KEY = "your-secret-key"
FINAL_LLM_TEMPERATURE = "0.2"

LANGGRAPH_RECURSION_LIMIT = "10"
```

## Postgresql 

The DB is used to store both the history chat and the LangGraph states.

```bash
########### POSTGRESQL ############
POSTGRES_USER="admin_user"
POSTGRES_PASSWORD="your-secret-key"
POSTGRES_DB="production_db"
# Format: postgresql+asyncpg://user:password@host:port/dbname
POSTGRES_URL="postgresql+asyncpg://admin_user:your-secret-key@localhost:5432/production_db"
```

## Qdrant

The VectorDB stores docs, threads and also failed build logs.

```bash
############ QDRANT #############
QDRANT_HOST="localhost"
QDRANT_PORT="6333"
QDRANT_SSL="false"
QDRANT_COLLECTION_NAME="production_docs"
QDRANT_SECRET_KEY="your-secret-key"
```

## Reranker

The reranker model is used to rerank the results retrieved by the hybrid retriever.
This highly improve results accuracy.

```bash
########### RERANKING ############
ENABLE_RERANKING="true"
RERANKER_PROVIDER="infinity"
RERANKER_BASE_URL="http://192.168.178.149:7997/"
RERANKER_MODEL_NAME="baai/bge-reranker-v2-m3"
RERANKER_API_KEY="your-secret-key"
```
