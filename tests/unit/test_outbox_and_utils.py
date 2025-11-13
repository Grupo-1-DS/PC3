import json
import uuid
import pytest

from src.saga.outbox import outbox as outbox
from src.saga.utils import ids, retry


def test_record_and_process_outbox_success(tmp_path, monkeypatch):
    out_path = tmp_path / "outbox.json"
    dlq_path = tmp_path / "dlq.json"
    # Patch module paths
    monkeypatch.setattr(outbox, "OUTBOX_PATH", out_path)
    monkeypatch.setattr(outbox, "DLQ_PATH", dlq_path)

    # Record two events
    outbox.record_outbox({"step": "A", "value": 1})
    outbox.record_outbox({"step": "B", "value": 2})

    # worker_function marks processed (no exception)
    def worker(evt):
        # simple assertion to ensure event passed
        assert "step" in evt

    outbox.process_outbox(worker)

    data = json.loads(out_path.read_text())
    assert all(evt["status"] == "processed" for evt in data["events"])

    # DLQ should be empty
    dlq = json.loads(dlq_path.read_text())
    assert dlq.get("events") == []


def test_process_outbox_failure_sends_to_dlq(tmp_path, monkeypatch):
    out_path = tmp_path / "outbox2.json"
    dlq_path = tmp_path / "dlq2.json"
    monkeypatch.setattr(outbox, "OUTBOX_PATH", out_path)
    monkeypatch.setattr(outbox, "DLQ_PATH", dlq_path)

    outbox.record_outbox({"step": "X", "value": 10})

    # worker will raise
    def worker_fail(evt):
        raise RuntimeError("boom")

    outbox.process_outbox(worker_fail)

    data = json.loads(out_path.read_text())
    assert data["events"][0]["status"] == "failed"

    dlq = json.loads(dlq_path.read_text())
    assert len(dlq.get("events", [])) == 1


def test_generate_saga_id_is_uuid():
    val = ids.generate_saga_id()
    # parse with uuid to ensure format
    parsed = uuid.UUID(val)
    assert str(parsed) == val


def test_retry_decorator_success_after_retries():
    calls = {"n": 0}

    @retry.retry_with_backoff(max_retries=3, base_delay=0)
    def flaky(x):
        calls["n"] += 1
        if calls["n"] < 3:
            raise ValueError("try again")
        return x * 2

    assert flaky(3) == 6
    assert calls["n"] == 3


def test_retry_decorator_exhausts_retries():
    @retry.retry_with_backoff(max_retries=2, base_delay=0)
    def always_fail():
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        always_fail()
