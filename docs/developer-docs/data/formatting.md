# Formatting

The formatting phase takes the processed data as input and stores it in LangChain Documents, extracts code blocks, and stores them in separate Documents.
Each Document is stored in a separate JSON file in a source-specific subfolder.
Depending on the source, specific metadata is stored in the document.

**To run the formatting phase for all sources:**
```bash
python -m data.formatting.formatters
```

## Jenkins Documentation

**Metadata:**
```json
{
    "data_source": "jenkins_docs",
    "title": "Activity View",
    "path": "doc/book/blueocean/activity/",
    "type": "non_developer",
    "version": "2.568"  
}
```

- **Input**: `output/processed/jenkins_docs.json`
- **Output**: `output/documents/jenkins_docs/J_{path_uppercase}` (example -> `/J_DOC-BOOK-BLUEOCEAN-ACTIVITY`)

**To run:**
```bash
python -m data.formatting.jenkins_docs_formatter
```

## Jenkins Plugin Docs

**Metadata:**
```json
{
    "data_source": "plugin_docs",
    "plugin_name": "semantic-versioning-plugin",
    "version": "1.15"
}
```

- **Input**: `output/processed/plugin_docs.json`
- **Output**: `output/documents/plugin_docs/P_{plugin_name_uppercase}` (example -> `/P_SEMANTIC-VERSIONING-PLUGIN`)

**To run:**
```bash
python -m data.formatting.plugin_docs_formatter
```

## Discourse Topics

**Metadata:**
```json
{
    "data_source": "discourse_topics",
    "topic_id": "454",
    "answer_id": "1342",
    "title": "Wrong characters after I restored my jenkins_home",
    "url": "/t/wrong-characters-after-i-restored-my-jenkins-home/454/4",
    "is_solution": true,
    "created_at": "2021-10-01T15:29:38.716Z"
}
```

- **Input**: `output/processed/discourse_topics.json`
- **Output**: `output/documents/discourse_topics/D_{topic_id}` (example -> `/D_454`)

**To run:**
```bash
python -m data.formatting.discourse_topics_formatter
```

## Reddit Threads

**Metadata:**
```json
{
    "data_source": "reddit_threads",
    "post_id": "t3_w4hlgn",
    "reply_id": "t1_ih2obq6",
    "title": "Jenkinsfile multiline powershell",
    "upvotes": 5,
    "created_at": "2022-07-21T17:07:26+00:00"
}
```

- **Input**: `output/processed/reddit_threads.json`
- **Output**: `output/documents/reddit_threads/R_{post_id}` (example -> `/R_W4HLGN`)

**To run:**
```bash
python -m data.formatting.reddit_threads_formatter
```

## Codeblocks

Each code block document contains metadata from the source it was extracted from, as well as a `cb_index`, which represents the index of the code block. In the example below, it is the first code block in the document.

**Metadata:**
```json
{
    // ...
    "cb_index": 0
}
```