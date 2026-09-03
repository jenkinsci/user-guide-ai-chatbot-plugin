import os
import json
from datetime import datetime
import asyncio
from manage_env import get_env
import pytest


EVAL_THROTTLE_SECONDS = get_env("EVAL_THROTTLE_SECONDS")

@pytest.fixture(autouse=True)
async def api_rate_limit_throttle():
    """
    Automatically introduces a delay after every test execution 
    to prevent hitting API Requests limits.
    """
    yield 
    
    throttle_seconds = float(EVAL_THROTTLE_SECONDS) 
    print(f"\n[Throttle] Waiting {throttle_seconds}s to respect API rate limits...")
    await asyncio.sleep(throttle_seconds)


def pytest_configure(config):
    """
    Initializes a global dictionary attached to the Pytest config object.
    This guarantees a single instance in memory across all test files.
    """
    config.eval_scores = {
        "answer_relevancy": [],
        "faithfulness": [],
        "context_recall": [],
        "latency": [],
        "cost": [],
    }


def pytest_sessionfinish(session, exitstatus):
    """
    Calculates the averages, stores all individual scores, 
    and saves them as a JSON file.
    """
    report = {}

    # Retrieve the global dictionary from the session config
    scores_dict = session.config.eval_scores

    for metric_name, scores in scores_dict.items():
        if scores:
            average = sum(scores) / len(scores)
            # Grouping average and the full array under the metric name
            report[metric_name] = {
                "average": round(average, 5),
                "all_scores": scores
            }
        else:
            report[metric_name] = {
                "average": None,
                "all_scores": []
            }

    report_dir = "test_reports"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(report_dir, f"eval_{timestamp}.json")

    with open(report_path, "w") as json_file:
        json.dump(report, json_file, indent=4)

    print(f"\n\n[SUCCESS] Evaluation summary saved to {report_path}")