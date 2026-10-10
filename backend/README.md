# Backend

## Running end-to-end tests

The end-to-end test exercises the complete data pipeline using mock collection
data. It does not require Jenkins, PostgreSQL, Qdrant, or LLM credentials.

From the repository root, create the local configuration file and install the
development dependencies. `uv sync` creates or reuses the project-local
`.venv`, so no separate virtual-environment command is needed:

```bash
cd backend
cp .env.example .env
uv sync --extra dev
```

Run the end-to-end test suite:

```bash
uv run pytest tests/e2e
```

Pytest writes its JUnit report to `test_reports/pytest_results.xml`.
