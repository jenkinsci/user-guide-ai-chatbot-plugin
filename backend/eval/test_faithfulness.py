import pytest
from unittest.mock import patch
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric
from deepeval import assert_test
from eval.utils import execute_test_agent, create_mock_tools, JUDGE_MODEL
from eval.test_cases import FAITHFULNESS_TEST_CASES


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", FAITHFULNESS_TEST_CASES)
@patch("agent.agent.get_tool_list")
async def test_faithfulness(mock_get_tool_list, test_case: dict, request):
    """
    Evaluates Faithfulness (Groundedness) across multiple scenarios.
    Checks if the agent's output is fully deducible from the tool responses,
    penalizing hallucinations.
    """
    # Initialize mock tools with the specific data for this iteration
    dummy_data = test_case["dummy_context"]
    mock_get_tool_list.return_value = create_mock_tools(dummy_data)

    user_prompt = test_case["question"]
    print(f"\n[Testing Prompt]: {user_prompt}")

    # Execute the agent and capture both output and tool context
    actual_output, retrieval_context = await execute_test_agent(user_prompt)
    print(f"[Agent Output]: {actual_output}")
    print(f"[Retrieval Context]: {retrieval_context}")

    # Define the DeepEval Test Case
    test_case_obj = LLMTestCase(
        input=user_prompt,
        actual_output=actual_output,
        retrieval_context=retrieval_context,  # type: ignore
    )

    # Assert with the metric
    # Threshold is set high to be strict against hallucinations
    faithfulness_metric = FaithfulnessMetric(threshold=0.8, model=JUDGE_MODEL)

    try:
        await faithfulness_metric.a_measure(test_case_obj)

        assert_test(test_case_obj, [faithfulness_metric])

    finally:
        final_score = (
            faithfulness_metric.score if faithfulness_metric.score is not None else 0.0
        )
        request.config.eval_scores["faithfulness"].append(final_score)
