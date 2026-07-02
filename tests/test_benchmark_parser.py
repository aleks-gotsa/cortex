"""benchmark SSE reducer — locks the error-event fix: a stream that ends
after an `error` event must never count as success."""

import json

from benchmarks.runner import _new_stream_state, _reduce_sse_event


def _success(state: dict) -> bool:
    # The exact expression _run_single_query applies after the stream ends
    # (including its total_time backfill for error-free streams).
    if state["total_time"] is None and state["error"] is None:
        state["total_time"] = 99.0
    return state["error"] is None and state["total_time"] is not None


def test_error_event_yields_failure_with_captured_payload():
    state = _new_stream_state()
    _reduce_sse_event("planning", json.dumps({"sub_questions": []}), 1.0, state)
    _reduce_sse_event("error", json.dumps({"error": "invalid x-api-key"}), 2.0, state)
    assert state["error"] == "invalid x-api-key"
    assert _success(state) is False


def test_error_event_with_empty_payload_still_fails():
    state = _new_stream_state()
    _reduce_sse_event("error", "", 1.0, state)
    assert state["error"] == "SSE error event received"
    assert _success(state) is False


def test_complete_event_yields_success_with_cost_and_id():
    state = _new_stream_state()
    _reduce_sse_event("planning", "{}", 0.5, state)
    _reduce_sse_event("complete", json.dumps({"cost_usd": 0.12, "research_id": "r1"}), 3.0, state)
    assert state["cost_usd"] == 0.12
    assert state["research_id"] == "r1"
    assert state["total_time"] == 3.0
    assert _success(state) is True


def test_stream_without_complete_backfills_total_time_and_succeeds():
    # Pre-fix behavior preserved for error-free streams that just end.
    state = _new_stream_state()
    _reduce_sse_event("planning", "{}", 0.5, state)
    assert _success(state) is True


def test_ttff_and_stage_times_recorded_and_malformed_json_tolerated():
    state = _new_stream_state()
    _reduce_sse_event("planning", "{not json", 0.25, state)
    _reduce_sse_event("gathering", "{}", 1.5, state)
    assert state["ttff"] == 0.25
    assert state["stage_times"] == {"planning": 0.25, "gathering": 1.5}
