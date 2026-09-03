# Preprocessing

In this phase, the raw data is filtered by extracting the main content, cleaning undesired HTML tags, and removing useless data.

**To run the preprocessing phase for all sources:**
```bash
python -m data.preprocessing.processors
```

## Jenkins Documentation

This script filters and extracts the main content from each raw Jenkins documentation page.

- **Input**: `output/raw/jenkins_docs.json`  
- **Output**: `output/processed/jenkins_docs.json`

It separates the documentation into:
- **Developer docs** (contains "developer" in the path)
- **Non-developer docs** 

Each page is cleaned by:
- Extracting only the main content container
- Removing the table of contents (`.toc`), `<script>`, `<img>`, and similar tags
- Removing navigation blocks
- Removing all HTML comments

**To run:**
```bash
python -m data.preprocessing.jenkins_docs_processor
```

## Jenkins Plugin Docs

This script processes the raw plugin documentation by cleaning the HTML and filtering out trivial entries.

The plugin documentation contains a wide range of formats and often includes boilerplate or short descriptions. This script ensures only meaningful documentation is kept by:

- Removing unwanted HTML tags (e.g., `<img>`, `<script>`, etc.)
- Stripping out all HTML comments
- Filtering out entries with fewer than 60 visible text characters

- **Input**: `output/raw/plugin_docs.json`
- **Output**: `output/processed/plugin_docs.json` (Cleaned plugin documentation)

**To run:**
```bash
python -m data.preprocessing.plugin_docs_processor
```

## Reddit Threads

This script filters the topics by keeping only the useful answers (those with more than 3 upvotes and a length greater than 20 characters). 
There may be more than one useful answer; each of them will be stored in an object containing the title, question, creation date, and other useful data. 

- **Input**: `output/raw/reddit_threads.json`
- **Output**: `output/processed/reddit_threads.json`

**To run:**
```bash
python -m data.preprocessing.reddit_threads
```

## Discourse Topics

This script filters the threads by keeping only the useful answers (comments marked as solutions and comments with more than 2 approval reactions). 
There may be more than one useful answer; each of them will be stored in an object containing the title, question, creation date, and other useful data. 

- **Input**: `output/raw/discourse_topics.json`
- **Output**: `output/processed/discourse_topics.json`

**To run:**
```bash
python -m data.preprocessing.discourse_topics
```