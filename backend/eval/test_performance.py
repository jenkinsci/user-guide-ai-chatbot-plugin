import time
import pytest
from langchain_core.messages import HumanMessage, AIMessage

from deepeval.test_case import LLMTestCase
from deepeval.metrics import BaseMetric
from deepeval import assert_test

from eval.test_cases import PERFORMANCE_TEST_CASES
from agent.agent import Agent
from langgraph.checkpoint.memory import MemorySaver
from manage_env import get_env

PRICE_PER_1M_INPUT_TOKENS = float(get_env("PRICE_PER_1M_INPUT_TOKENS") or 0)
PRICE_PER_1M_OUTPUT_TOKENS = float(get_env("PRICE_PER_1M_OUTPUT_TOKENS") or 0)


class AgentLatencyMetric(BaseMetric):
    def __init__(self, threshold: float = 15.0, measured_latency: float = 0.0):
        self.threshold = threshold
        self.measured_latency = measured_latency
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        self.score = self.measured_latency
        self.success = self.measured_latency <= self.threshold

        if self.success:
            self.reason = f"Execution time ({self.measured_latency:.2f}s) is under the {self.threshold}s limit."
        else:
            self.reason = f"Execution time ({self.measured_latency:.2f}s) exceeded the {self.threshold}s limit."

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """
        Asynchronous evaluation method required by DeepEval.
        Since we do not perform I/O operations here, we just call the sync method.
        """
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Agent Latency Metric"


class AgentCostMetric(BaseMetric):
    def __init__(self, threshold: float = 0.01, measured_cost: float = 0.0):
        self.threshold = threshold
        self.measured_cost = measured_cost
        self.score = 0.0
        self.reason = ""
        self.success = False

    def measure(self, test_case: LLMTestCase) -> float:
        self.score = self.measured_cost
        self.success = self.measured_cost <= self.threshold

        if self.success:
            self.reason = f"Cost (${self.measured_cost:.5f}) is under the ${self.threshold} limit."
        else:
            self.reason = f"Cost (${self.measured_cost:.5f}) exceeded the ${self.threshold} limit."

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        """
        Asynchronous evaluation method required by DeepEval.
        """
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Agent Cost Metric"


DUMMY_CONTEXT = {
    "current_screen": "Job Configuration",
    "root_url": "http://jenkins.internal.company.com:8080/",
    "jenkins_version": "2.440.3",
    "system_message": "Production deployments are locked until Monday.",
    "agent_stats": {
        "online_agents": 12,
        "offline_agents": 2,
        "busy_executors": 4,
        "idle_executors": 8,
    },
    "master_node": {
        "executors": 2,
        "is_online": True,
        "system_info": {
            "os_name": "Linux",
            "os_arch": "amd64",
            "java_version": "17.0.10",
            "free_memory_mb": 2048,
            "total_memory_mb": 8192,
        },
    },
    "active_plugins": {
        "git": "5.2.1",
        "workflow-job": "1385.vb_58b_86cef6a_c",
        "kubernetes": "4150.v2a_5b_2959828d",
        "credentials-binding": "642.v996e38b_2408b_",
    },
    "job_details": {
        "full_name": "backend-api-pipeline",
        "job_type": "WorkflowJob",
        "is_buildable": True,
        "is_pipeline": True,
        "url": "http://jenkins.internal.company.com:8080/job/backend-api-pipeline/",
        "config_xml": "<?xml version='1.1' encoding='UTF-8'?><flow-definition>...</flow-definition>",
    },
    "build_details": {
        "number": 104,
        "result": "FAILURE",
        "duration": 124500,
        "timestamp": 1723407032000,
        "causes": ["Started by user admin"],
    },
    "build_log_stored": True,
}


@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", PERFORMANCE_TEST_CASES)
async def test_agent_performance_and_cost(test_case: dict, request):
    """
    Executes an End-to-End performance test ensuring the agent stays within
    acceptable latency and budget limits for various task complexities.
    """
    user_query = test_case["query"]
    allowed_latency = test_case["max_latency"]
    allowed_cost = test_case["max_cost"]

    print(f"\n[E2E Performance Test]: {user_query}")

    test_chat_id = 999
    test_checkpointer = MemorySaver()

    agent_instance = Agent(
        chat_id=test_chat_id,
        prompt=user_query,
        context=DUMMY_CONTEXT,
        checkpointer=test_checkpointer,
    )

    app = agent_instance.create_state_graph()
    input_state = {"messages": [HumanMessage(content=user_query)]}
    execution_config = {"configurable": {"thread_id": str(test_chat_id)}}

    start_time = time.time()
    final_state = await app.ainvoke(input_state, config=execution_config)
    execution_time = time.time() - start_time

    total_input_tokens = 0
    total_output_tokens = 0
    actual_output = ""

    for msg in final_state["messages"]:
        if isinstance(msg, AIMessage):
            # Extract final response string
            if not msg.tool_calls:
                actual_output = str(msg.content)

            # Extract tokens if the provider passed them back
            if hasattr(msg, "usage_metadata") and msg.usage_metadata is not None:
                total_input_tokens += msg.usage_metadata.get("input_tokens", 0)
                total_output_tokens += msg.usage_metadata.get("output_tokens", 0)

            # Fallback for some providers that store it in response_metadata
            elif "token_usage" in msg.response_metadata:
                usage = msg.response_metadata["token_usage"]
                total_input_tokens += usage.get("prompt_tokens", 0)
                total_output_tokens += usage.get("completion_tokens", 0)

    total_tokens = total_input_tokens + total_output_tokens

    # Calculate manual cost
    input_cost = (total_input_tokens / 1_000_000) * PRICE_PER_1M_INPUT_TOKENS
    output_cost = (total_output_tokens / 1_000_000) * PRICE_PER_1M_OUTPUT_TOKENS
    total_cost = input_cost + output_cost

    print(f"\n[Performance Stats]")
    print(f"Latency: {execution_time:.2f} seconds")
    print(
        f"Tokens Used: {total_tokens} (IN: {total_input_tokens}, OUT: {total_output_tokens})"
    )
    print(f"Cost: ${total_cost:.6f}")

    # Build the LLMTestCase
    test_case_obj = LLMTestCase(input=user_query, actual_output=actual_output)

    # Initialize dynamic metrics based on the specific test case thresholds
    latency_metric = AgentLatencyMetric(
        threshold=allowed_latency, measured_latency=execution_time
    )
    cost_metric = AgentCostMetric(threshold=allowed_cost, measured_cost=total_cost)

    try:
        await latency_metric.a_measure(test_case_obj)
        await cost_metric.a_measure(test_case_obj)

        assert_test(test_case_obj, [latency_metric, cost_metric])
    finally:
        latency_final_score = (
            latency_metric.score if latency_metric.score is not None else 0.0
        )
        request.config.eval_scores["latency"].append(latency_final_score)

        cost_final_score = cost_metric.score if cost_metric.score is not None else 0.0
        request.config.eval_scores["cost_per_query"].append(cost_final_score)
