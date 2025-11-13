import json
from pathlib import Path
import logging
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]
OUTBOX_PATH = Path(__file__).resolve().parent / "outbox_store.json"
DLQ_PATH = Path(__file__).resolve().parent / "dlq_store.json"


def _ensure():
    OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not OUTBOX_PATH.exists():
        OUTBOX_PATH.write_text(json.dumps({"events": []}, indent=2))
    if not DLQ_PATH.exists():
        DLQ_PATH.write_text(json.dumps({"events": []}, indent=2))


def record_outbox(event: Dict[str, Any]) -> None:
    _ensure()
    data = json.loads(OUTBOX_PATH.read_text())
    data["events"].append({**event, "status": "pending"})
    OUTBOX_PATH.write_text(json.dumps(data, indent=2))


def process_outbox(worker_function) -> None:
    """Simula un worker que procesa mensajes."""

    log = logging.getLogger("outbox")
    _ensure()
    data = json.loads(OUTBOX_PATH.read_text())
    new_events = []

    for evt in data["events"]:
        if evt["status"] != "pending":
            new_events.append(evt)
            continue

        try:
            worker_function(evt)
            evt["status"] = "processed"
        except Exception:
            evt["status"] = "failed"
            send_to_dlq(evt)

        new_events.append(evt)

    OUTBOX_PATH.write_text(json.dumps({"events": new_events}, indent=2))


def send_to_dlq(event: Dict[str, Any]):
    _ensure()
    data = json.loads(DLQ_PATH.read_text())
    data["events"].append(event)
    DLQ_PATH.write_text(json.dumps(data, indent=2))
