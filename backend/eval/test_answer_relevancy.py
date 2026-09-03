import pytest
from unittest.mock import patch
from deepeval.metrics import AnswerRelevancyMetric
from deepeval import assert_test
from eval.test_cases import ANSWER_RELEVANCY_TEST_CASES
from eval.utils import execute_test_agent, create_mock_tools, JUDGE_MODEL
from deepeval.test_case import LLMTestCase


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", ANSWER_RELEVANCY_TEST_CASES)
@patch("agent.agent.get_tool_list")
async def test_answer_relevancy(mock_get_tool_list, test_case: dict, request):
    """
    Evaluates Answer Relevancy across multiple scenarios.
    All tools are passed to the agent, but only the targeted ones return useful dummy data.
    """
    dummy_data = test_case["dummy_context"]
    mock_get_tool_list.return_value = create_mock_tools(dummy_data)

    user_prompt = test_case["question"]
    print(f"\n[Testing Prompt]: {user_prompt}")

    # Execute the agent
    actual_output, _ = await execute_test_agent(user_prompt)
    print(f"[Agent Output]: {actual_output}")

    # Define the DeepEval Test Case (No retrieval_context needed for Relevancy)
    test_case_obj = LLMTestCase(
        input=user_prompt,
        actual_output=actual_output,
    )

    # Assert with the metric
    relevancy_metric = AnswerRelevancyMetric(threshold=0.7, model=JUDGE_MODEL)

    try:
        await relevancy_metric.a_measure(test_case_obj)

        assert_test(test_case_obj, [relevancy_metric])
    finally:
        final_score = (
            relevancy_metric.score if relevancy_metric.score is not None else 0.0
        )
        request.config.eval_scores["answer_relevancy"].append(final_score)
