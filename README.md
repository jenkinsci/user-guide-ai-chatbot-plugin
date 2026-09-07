# AI Chatbot to Guide User Workflow

## Introduction

While Jenkins is the backbone of modern CI/CD, troubleshooting failed builds and complex configurations remains a time-consuming bottleneck. This plugin is a Diagnostic AI Chatbot which aims to drastically reduce this friction, minimizing debugging time and maximizing developer productivity. Powered by an advanced Retrieval-Augmented Generation (RAG) architecture, the agent leverages LangGraph and hybrid search to intelligently filter noisy build logs, cross-referencing them with official documentation and community discussions in order to deliver precise root-cause analysis and actionable fixes to the user. Architecturally, it utilizes a decoupled FastAPI backend, ensuring zero computational overhead on the Jenkins Controller. The system is highly flexible: it is designed with a privacy-first approach optimized for local open-source LLMs, while seamlessly supporting integration with third-party commercial APIs. This allows administrators to effortlessly toggle between absolute data privacy and frontier model performance based on their infrastructure needs.

> **Note**: The plugin was developed 🛠️ as part of a Google Summer of Code 2026 ☀️ project.

**Question**: Do you know why the build failed?

![Failed build troubleshooting](docs/_static/gif/BUILD_FAILED.gif)


**Question**: How can I install a new plugin?

![Installing new plugins](docs/_static/gif/NEW_PLUGIN.gif)


## Getting started

### User tutorial
Here you can find a tutorial on how to quickly install and configure the plugin.: [User Guide](https://jenkinsci.github.io/user-guide-ai-chatbot-plugin/user-guide/index.html)

### Contributor Docs
If you would like to contribute to the plugin, you can find the documentation here.: [Developer Docs](https://jenkinsci.github.io/user-guide-ai-chatbot-plugin/developer-docs/index.html)


## Contributing

Refer to our [contribution guidelines](https://github.com/jenkinsci/.github/blob/master/CONTRIBUTING.md)

## LICENSE

Licensed under MIT, see [LICENSE](LICENSE.md)

