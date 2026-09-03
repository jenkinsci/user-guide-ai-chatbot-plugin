import pytest
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRecallMetric
from deepeval import assert_test
from agent.tools.tools import get_tool_list
from eval.utils import JUDGE_MODEL
from eval.test_cases import CONTEXT_RECALL_TEST_CASES


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", CONTEXT_RECALL_TEST_CASES)
async def test_real_vectordb_context_recall(test_case: dict, request):
    """
    Evaluates the real Hybrid Retriever and Reranker (Context Recall).
    It calls the actual Qdrant DB and checks if the retrieved chunks
    contain the facts required by the expected_output.
    """
    query = test_case["query"]
    expected_truth = test_case["expected_output"]

    print(f"\n[Testing Query]: {query}")

    # Initialize the REAL tools (No mocks here)
    real_tools = get_tool_list(chat_id=999, context={}, user_query=query)

    # Extract the fetch_from_vectordb tool
    vectordb_tool = real_tools[0]
    assert vectordb_tool.name == "fetch_from_vectordb", "Tool index mismatch!"

    # Execute the tool
    raw_retrieved_text = await vectordb_tool.ainvoke({"query": query})

    # Format the output for DeepEval
    # DeepEval expects a list of strings for retrieval_context
    retrieval_context = [raw_retrieved_text]

    print(f"[Real Retrieved Context Preview]: {raw_retrieved_text[:200]}...")

    # Build the DeepEval Test Case
    # actual_output is not evaluated by ContextualRecallMetric, so we provide a placeholder.
    test_case_obj = LLMTestCase(
        input=query,
        actual_output="Placeholder output - ignored by Context Recall.",
        expected_output=expected_truth,
        retrieval_context=retrieval_context,
    )

    # Execute the evaluation
    # Threshold 0.8 means at least 80% of the facts in expected_output
    # must be found in the retrieved context.
    context_recall_metric = ContextualRecallMetric(
        threshold=0.8, model=JUDGE_MODEL, include_reason=True
    )

    try:
        await context_recall_metric.a_measure(test_case_obj)

        assert_test(test_case_obj, [context_recall_metric])
    except AssertionError as e:
        print(f"\n[Recall Failed] Reason: {context_recall_metric.reason}")
        raise e
    finally:
        final_score = (
            context_recall_metric.score
            if context_recall_metric.score is not None
            else 0.0
        )
        request.config.eval_scores["context_recall"].append(final_score)
