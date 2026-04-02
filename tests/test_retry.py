"""Tests for retry logic."""
from src.retry import retry_with_backoff


def test_retry_succeeds_first_try():
    call_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def always_works():
        nonlocal call_count
        call_count += 1
        return "ok"

    assert always_works() == "ok"
    assert call_count == 1


def test_retry_succeeds_after_failures():
    call_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01)
    def fails_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("network error")
        return "ok"

    assert fails_twice() == "ok"
    assert call_count == 3


def test_retry_exhausted_raises():
    @retry_with_backoff(max_retries=2, base_delay=0.01)
    def always_fails():
        raise ValueError("bad")

    try:
        always_fails()
        assert False, "Should have raised"
    except ValueError as e:
        assert "bad" in str(e)


def test_retry_only_catches_specified_exceptions():
    @retry_with_backoff(max_retries=3, base_delay=0.01, exceptions=(ConnectionError,))
    def raises_type_error():
        raise TypeError("wrong type")

    try:
        raises_type_error()
        assert False, "Should have raised"
    except TypeError:
        pass  # Should not retry TypeError, should raise immediately
