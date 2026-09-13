# Testing Guide

This document describes the different test suites available for the project and how to run them.

## End-to-End Tests (Cypress)
These tests verify the overall functionality of the application.

To run the E2E tests, go to the project's root folder and run:

```bash
# Run the complete E2E test suite using Docker
docker compose -f docker-compose.e2e.yml up --abort-on-container-exit --exit-code-from e2e_runner
```

## Data Pipeline Test
This suite checks the data pipeline, including:
- Collection
- Preprocessing
- Formatting
- Chunking
- Embedding

To run these tests, navigate to the **`backend`** folder and run `pytest`:

```bash
# Change to the backend directory and run the tests
cd backend
pytest tests
```

## Evaluation Tests
These tests evaluate the performance and operation of the agent and Hybrid Retriever.

For more information on the logic and metrics, please refer to the dedicated document:
👉 [evaluation.md](./evaluation.md)