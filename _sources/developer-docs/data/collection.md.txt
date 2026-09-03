# Collection

For Jenkins documentation, plugin documentation, and Reddit threads, we use a scraping approach, while for Discourse topics, we use the official API.

If you only need to set up the plugin, we suggest running the data pipeline by executing: 
```bash
python -m data.manager --sources jenkins_docs plugin_docs
```
> **Note**: Make sure you're in the backend directory before running this or any script.

## Jenkins Documentation

The scraper iteratively crawls documentation pages using stack-based DFS from https://www.jenkins.io/doc/.
This means that when the scraper retrieves a documentation page, it checks if there are any URLs inside the content. If there are, they are added to a stack and will be the next routes to be scraped. The documentation version's publication date is also retrieved.

- **Input**: No input required
- **Output**: The result is split into 'developer' docs and 'non_developer' docs, and saved in `data/output/raw/jenkins_docs.json`.

To run: 
```bash
python -m data.collection.jenkins_docs
```

## Jenkins Plugin Docs

The scraper first fetches the list of currently existing Jenkins plugins from https://updates.jenkins.io/experimental/latest/, and then retrieves the main page (https://plugins.jenkins.io/{plugin_name}/) for each one. 

- **Input**: No input required
- **Output**: The list of plugin names is saved in `data/output/raw/plugin_names.json`, and the documentation is saved in `data/output/raw/plugin_docs.json`.

To run: 
```bash
python -m data.collection.plugin_docs
```

## Reddit Threads

This scraper is the slowest, as the Reddit website has strict rate limits. 
It scrapes the IDs of the top 1000 threads for each section of https://old.reddit.com/r/jenkinsci.
The sections are Hot, New, Rising, Controversial, and Top.
Finally, it fetches the content of every thread, rebuilding the exact original comment tree for each one. 

- **Input**: No input required  
- **Output**: The output is saved in `data/output/raw/reddit_threads.json` and contains a list with all the thread details.

To run: 
```bash
python -m data.collection.reddit_threads
```

## Discourse Topics

Discourse topics are retrieved using the official API of https://community.jenkins.io/, which doesn't require any authentication. 
It fetches the topic IDs for all the topics in the `using-jenkins > support` category (`support` being the subcategory).
Finally, it fetches the content of every topic, rebuilding the exact original tree for each one. 

- **Input**: No input required
- **Output**: The output is saved in `data/output/raw/discourse_topics.json` and contains a list with all the topic details.

To run: 
```bash
python -m data.collection.discourse_topics
```