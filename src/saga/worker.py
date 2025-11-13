import json
import time
import pika
import logging
from pathlib import Path

from .outbox.outbox import OUTBOX_PATH, _ensure

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("worker")
logging.getLogger("pika").setLevel(logging.WARNING)


def send_to_rabbit(event: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue="saga_commands", durable=True)

    channel.basic_publish(
        exchange="",
        routing_key="saga_commands",
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2
        ),
    )

    connection.close()


def process_outbox():
    _ensure()

    data = json.loads(OUTBOX_PATH.read_text())
    events = data.get("events", [])

    new_events = []

    for evt in events:

        if evt.get("status") == "pending" and evt.get("type") and evt.get("context_saga"):

            try:
                send_to_rabbit(evt)
                evt["status"] = "sent"
                log.info(f"Evento enviado a RabbitMQ: {evt.get('step')}")

            except Exception:
                evt["retries"] = evt.get("retries", 0) + 1
                log.warning(f"Error enviando, retry {evt['retries']}")

                if evt["retries"] >= 3:
                    evt["status"] = "failed"
                    log.error(f"Marcado como FAILED: {evt.get('step')}")
                else:
                    time.sleep(0.3 * (2 ** evt["retries"]))

        else:

            pass

        new_events.append(evt)

    OUTBOX_PATH.write_text(json.dumps({"events": new_events}, indent=2))


if __name__ == "__main__":
    log.info("Worker iniciado. Escaneando OUTBOX cada 1s...")
    while True:
        process_outbox()
        time.sleep(1)
