# pyright: reportMissingImports=false
"""Hard token budget and timeout safeguard for hybrid discovery delegates (ADR-0005).

Enforces:
- Hard token ceiling of 8,000 tokens total across all delegate invocations.
- Per-worker timeout safeguard of 30 seconds.
- Delegate ceiling of at most 3 targeted delegate workers.
- Graceful partial-failure salvage falling back to static analysis.
"""

from __future__ import annotations

import concurrent.futures
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

MAX_TOKEN_BUDGET: int = 8000
DELEGATE_TIMEOUT_SECONDS: float = 30.0
MAX_DELEGATES: int = 3


class TokenBudgetTracker:
    """Tracks token usage across delegate invocations and enforces hard budget ceilings."""

    def __init__(
        self,
        max_tokens: int = MAX_TOKEN_BUDGET,
        max_delegates: int = MAX_DELEGATES,
    ) -> None:
        self.max_tokens = max_tokens
        self.max_delegates = max_delegates
        self.total_tokens_used: int = 0
        self.delegate_count: int = 0

    def record_usage(self, tokens: int) -> None:
        """Records token consumption for a delegate invocation."""
        if tokens > 0:
            self.total_tokens_used += tokens
        self.delegate_count += 1

    def is_exhausted(self) -> bool:
        """Returns True if the total token consumption has reached or exceeded max budget."""
        return self.total_tokens_used >= self.max_tokens

    def tokens_remaining(self) -> int:
        """Returns the number of tokens remaining under the budget ceiling."""
        return max(0, self.max_tokens - self.total_tokens_used)

    @property
    def can_invoke(self) -> bool:
        """Returns True if budget has not been exhausted and delegate limit is not reached."""
        return not self.is_exhausted() and self.delegate_count < self.max_delegates


def run_delegate_with_budget(
    delegate_fn: Callable[..., Any],
    args: tuple[Any, ...] | list[Any] | Any = (),
    budget_tracker: TokenBudgetTracker | None = None,
    timeout: float = DELEGATE_TIMEOUT_SECONDS,
    kwargs: dict[str, Any] | None = None,
) -> Any:
    """Executes delegate_fn(*args) with a timeout and budget safeguard.

    - If token budget is exhausted: skips execution, logs warning, and returns None.
    - If timeout occurs: logs warning and returns None (partial-failure salvage).
    - If an exception occurs: logs warning and returns None.
    - On success: returns the result of delegate_fn.
    """
    if budget_tracker is not None:
        if budget_tracker.is_exhausted():
            logger.warning(
                "Token budget exhausted (%d/%d tokens used); skipping delegate %s",
                budget_tracker.total_tokens_used,
                budget_tracker.max_tokens,
                getattr(delegate_fn, "__name__", str(delegate_fn)),
            )
            return None
        if budget_tracker.delegate_count >= budget_tracker.max_delegates:
            logger.warning(
                "Max delegates limit reached (%d/%d); skipping delegate %s",
                budget_tracker.delegate_count,
                budget_tracker.max_delegates,
                getattr(delegate_fn, "__name__", str(delegate_fn)),
            )
            return None

    call_args = args if isinstance(args, (tuple, list)) else (args,)
    call_kwargs = kwargs or {}

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = executor.submit(delegate_fn, *call_args, **call_kwargs)
        result = future.result(timeout=timeout)
        executor.shutdown(wait=False)
        return result
    except concurrent.futures.TimeoutError:
        logger.warning(
            "Delegate %s timed out after %.1f seconds; salvaging with static analysis",
            getattr(delegate_fn, "__name__", str(delegate_fn)),
            timeout,
        )
        executor.shutdown(wait=False, cancel_futures=True)
        return None
    except Exception as exc:
        logger.warning(
            "Delegate %s failed with %s; salvaging with static analysis",
            getattr(delegate_fn, "__name__", str(delegate_fn)),
            exc,
        )
        executor.shutdown(wait=False, cancel_futures=True)
        return None


__all__ = [
    "DELEGATE_TIMEOUT_SECONDS",
    "MAX_DELEGATES",
    "MAX_TOKEN_BUDGET",
    "TokenBudgetTracker",
    "run_delegate_with_budget",
]
