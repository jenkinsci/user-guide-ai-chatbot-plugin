# Evaluation

The Jenkins agent evaluation system is built using the **DeepEval** framework combined with **pytest**. The suite is designed to test the agent against four key pillars, using parameterized test cases (defined in `test_cases.py`) that simulate real-world problem-solving scenarios and logic traps.

## 1. Answer Relevancy
- **File:** `test_answer_relevancy.py`
- **Goal:** Ensure answers are direct, relevant, and limited to the DevOps/Jenkins context.
- **Metrics:** `AnswerRelevancyMetric`
- **Key Detail:** If the user asks questions out of context (e.g., recipes), the agent should refuse to answer. This polite refusal is evaluated as the correct response and receives a full score (1.0).

## 2. Context Recall
- **File:** `test_context_recall.py`
- **Goal:** Evaluate the *Hybrid Retriever* and *Reranker* system by querying the real Vector DB (Qdrant).
- **Metrics:** `ContextualRecallMetric`
- **Key Detail:** Unlike other tests that use mocked data, this test verifies that the text chunks retrieved from the vector database actually contain the necessary facts (`expected_output`) to correctly answer the user's query.

## 3. Faithfulness (Groundedness)
- **File:** `test_faithfulness.py`
- **Goal:** Prevent hallucinations. The output must be entirely deducible from the responses provided by the tools.
- **Metrics:** `FidelityMetric` 
- **Key Detail:** The test cases belong to specific "Hallucination Traps." For example, the agent is tested to see if it invents the existence of a missing file or assumes that a plugin is installed just because it is popular (e.g., Kubernetes plugins), forcing it to rely only on the logs/data received.

## 4. Latency and Costs
- **File:** `test_performance.py`
- **Goal:** Ensure that end-to-end (E2E) operations meet budget and time constraints.
- **Metrics:** Custom classes `AgentLatencyMetric` and `AgentCostMetric`.
- **Key detail:** The test tracks execution time in seconds and calculates actual costs by counting input and output tokens (multiplied by the prices defined in the environment). It fails if the latency exceeds the `max_latency` or if the cost exceeds the `max_cost` defined for that specific scenario.