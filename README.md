# AI Chatbot to Guide User Workflow

## Introduction

While Jenkins is the backbone of modern CI/CD, troubleshooting failed builds and complex configurations remains a time-consuming bottleneck. This plugin is a Diagnostic AI Chatbot which aims to drastically reduce this friction, minimizing debugging time and maximizing developer productivity. Powered by an advanced Retrieval-Augmented Generation (RAG) architecture, the agent leverages LangGraph and hybrid search to intelligently filter noisy build logs, cross-referencing them with official documentation and community discussions in order to deliver precise root-cause analysis and actionable fixes to the user. Architecturally, it utilizes a decoupled FastAPI backend, ensuring zero computational overhead on the Jenkins Controller. The system is highly flexible: it is designed with a privacy-first approach optimized for local open-source LLMs, while seamlessly supporting integration with third-party commercial APIs. This allows administrators to effortlessly toggle between absolute data privacy and frontier model performance based on their infrastructure needs.

> **Note**: The plugin is under development 🛠️ as part of a Google Summer of Code 2026 ☀️ project.

## Getting started

TODO Tell users how to configure your plugin here, include screenshots, pipeline examples and 
configuration-as-code examples.

## Issues

TODO Decide where you're going to host your issues, the default is Jenkins JIRA, but you can also enable GitHub issues,
If you use GitHub issues there's no need for this section; else add the following line:

Report issues and enhancements in the [Jenkins issue tracker](https://issues.jenkins.io/).

## Contributing

TODO review the default [CONTRIBUTING](https://github.com/jenkinsci/.github/blob/master/CONTRIBUTING.md) file and make sure it is appropriate for your plugin, if not then add your own one adapted from the base file

Refer to our [contribution guidelines](https://github.com/jenkinsci/.github/blob/master/CONTRIBUTING.md)

## LICENSE

Licensed under MIT, see [LICENSE](LICENSE.md)

