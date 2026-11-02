# pyright: reportMissingImports=false
"""Unit tests for token budget tracker and timeout safeguards (ADR-0005)."""

from __future__ import annotations

import logging
import threading
from unittest.mock import MagicMock

import pytest

from understand_runs.budget import (
    DELEGATE_TIMEOUT_SECONDS,
    MAX_DELEGATES,
    MAX_TOKEN_BUDGET,
    TokenBudgetTracker,
    run_delegate_with_budget,
)


class TestBudgetConstants:
    """Tests architectural hard constraints from ADR-0005."""

    def test_hard_constraints_values(self):
        assert MAX_TOKEN_BUDGET == 8000
        assert DELEGATE_TIMEOUT_SECONDS == 30
        assert MAX_DELEGATES == 3


class TestTokenBudgetTracker:
    """Tests TokenBudgetTracker tracking, exhaustion, and remaining budget calculation."""

    def test_initial_state(self):
        tracker = TokenBudgetTracker()
        assert tracker.max_tokens == 8000
        assert tracker.max_delegates == 3
        assert tracker.total_tokens_used == 0
        assert tracker.delegate_count == 0
        assert tracker.tokens_remaining() == 8000
        assert not tracker.is_exhausted()
        assert tracker.can_invoke

    def test_record_usage_accumulates_and_decrements_remaining(self):
        tracker = TokenBudgetTracker()
        tracker.record_usage(2500)
        assert tracker.total_tokens_used == 2500
        assert tracker.delegate_count == 1
        assert tracker.tokens_remaining() == 5500
        assert not tracker.is_exhausted()
        assert tracker.can_invoke

        tracker.record_usage(3500)
        assert tracker.total_tokens_used == 6000
        assert tracker.delegate_count == 2
        assert tracker.tokens_remaining() == 2000
        assert not tracker.is_exhausted()
        assert tracker.can_invoke

    def test_is_exhausted_at_and_above_budget(self):
        tracker = TokenBudgetTracker()
        tracker.record_usage(8000)
        assert tracker.total_tokens_used == 8000
        assert tracker.tokens_remaining() == 0
        assert tracker.is_exhausted()

        # Additional usage keeps remaining at 0 and exhausted True
        tracker.record_usage(500)
        assert tracker.total_tokens_used == 8500
        assert tracker.tokens_remaining() == 0
        assert tracker.is_exhausted()

    def test_max_delegates_boundary(self):
        tracker = TokenBudgetTracker()
        tracker.record_usage(100)
        tracker.record_usage(100)
        assert tracker.can_invoke
        tracker.record_usage(100)
        assert tracker.delegate_count == 3
        assert not tracker.can_invoke

    def test_custom_parameters(self):
        tracker = TokenBudgetTracker(max_tokens=1000, max_delegates=2)
        assert tracker.tokens_remaining() == 1000
        tracker.record_usage(1000)
        assert tracker.is_exhausted()


class TestRunDelegateWithBudget:
    """Tests run_delegate_with_budget timeout, exception, and budget safeguards."""

    def test_successful_execution_returns_result(self):
        tracker = TokenBudgetTracker()

        def sample_delegate(x, y):
            tracker.record_usage(200)
            return x + y

        result = run_delegate_with_budget(sample_delegate, args=(10, 20), budget_tracker=tracker)
        assert result == 30
        assert tracker.total_tokens_used == 200
        assert tracker.delegate_count == 1

    def test_timeout_returns_none_and_logs_warning(self, caplog):
        tracker = TokenBudgetTracker()

        def slow_delegate():
            threading.Event().wait(0.2)
            return "never reached"

        with caplog.at_level(logging.WARNING):
            result = run_delegate_with_budget(
                slow_delegate,
                args=(),
                budget_tracker=tracker,
                timeout=0.05,
            )

        assert result is None
        assert any("timed out after" in record.message for record in caplog.records)

    def test_exception_returns_none_and_logs_warning(self, caplog):
        tracker = TokenBudgetTracker()

        def failing_delegate():
            raise RuntimeError("API connection failed")

        with caplog.at_level(logging.WARNING):
            result = run_delegate_with_budget(
                failing_delegate,
                args=(),
                budget_tracker=tracker,
            )

        assert result is None
        assert any("failed with" in record.message for record in caplog.records)

    def test_exhausted_budget_skips_execution(self, caplog):
        tracker = TokenBudgetTracker()
        tracker.record_usage(8000)
        assert tracker.is_exhausted()

        mock_delegate = MagicMock()
        with caplog.at_level(logging.WARNING):
            result = run_delegate_with_budget(
                mock_delegate,
                args=("arg1",),
                budget_tracker=tracker,
            )

        assert result is None
        mock_delegate.assert_not_called()
        assert any("Token budget exhausted" in record.message for record in caplog.records)

    def test_max_delegates_reached_skips_execution(self, caplog):
        tracker = TokenBudgetTracker()
        tracker.record_usage(100)
        tracker.record_usage(100)
        tracker.record_usage(100)
        assert tracker.delegate_count >= MAX_DELEGATES

        mock_delegate = MagicMock()
        with caplog.at_level(logging.WARNING):
            result = run_delegate_with_budget(
                mock_delegate,
                args=(),
                budget_tracker=tracker,
            )

        assert result is None
        mock_delegate.assert_not_called()
        assert any("Max delegates limit reached" in record.message for record in caplog.records)

    def test_single_argument_and_kwargs_support(self):
        tracker = TokenBudgetTracker()

        def delegate_with_kwargs(item, multiplier=2):
            return item * multiplier

        result = run_delegate_with_budget(
            delegate_with_kwargs,
            args=5,
            budget_tracker=tracker,
            kwargs={"multiplier": 3},
        )
        assert result == 15
