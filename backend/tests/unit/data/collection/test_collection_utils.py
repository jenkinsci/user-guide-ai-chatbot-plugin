import pytest
from data.collection.collection_utils import sleep, retry_until_success
from unittest.mock import patch


# Verify the sleep function logic
@patch("time.sleep")
def test_sleep_function(mock_time_sleep):
    test_seconds = 2.5
    sleep(test_seconds)
    mock_time_sleep.assert_called_once_with(test_seconds)


# Verify the decorator when the function succeeds immediately
def test_retry_success_first_attempt():

    @retry_until_success(sleep_time=0.1, max_attempts=3)
    def successful_function():
        return "Success Data"

    result = successful_function()

    assert result == "Success Data"


# Verify the decorator retries upon failure and eventually succeeds
@patch("time.sleep")
def test_retry_success_after_failures(mock_time_sleep):
    state = {"attempts_made": 0}

    @retry_until_success(sleep_time=0.5, max_attempts=3)
    def failing_then_succeeding_function():
        state["attempts_made"] += 1

        # Simulate a failure on the first two attempts
        if state["attempts_made"] < 3:
            raise ValueError("Simulated temporary error")

        return "Final Success"

    result = failing_then_succeeding_function()

    # Assert the final result is correct
    assert result == "Final Success"

    # Assert the function was actually called 3 times
    assert state["attempts_made"] == 3

    # Assert that our custom sleep logic (which calls time.sleep) was triggered 2 times
    assert mock_time_sleep.call_count == 2


# Verify the behavior when max_attempts is exceeded
@patch("time.sleep")
def test_retry_max_attempts_exceeded(mock_time_sleep):

    @retry_until_success(sleep_time=0.1, max_attempts=2)
    def always_failing_function():
        raise RuntimeError("Permanent error")

    result = always_failing_function()

    # Assert the return value is None
    assert result is None

    # Assert it tried exactly 2 times (so it slept 2 times)
    assert mock_time_sleep.call_count == 2
