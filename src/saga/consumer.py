import json
import pika
import time
import logging
from pathlib import Path

from .factory import StepFactory, register_defaults
from .outbox.outbox import send_to_dlq

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("consumer")

# Registrar steps
register_defaults()


SAGA_STORE = Path(__file__).resolve().parent / "data" / "saga_state_store.json"


def _ensure_saga_state():
    SAGA_STORE.parent.mkdir(parents=True, exist_ok=True)
    if not SAGA_STORE.exists():
        SAGA_STORE.write_text(json.dumps({}))


def load_context(saga_id: str) -> dict:
    _ensure_saga_state()
    data = json.loads(SAGA_STORE.read_text())
    ctx = data.get(saga_id, {})
    ctx.setdefault("_saga_id", saga_id)
    return ctx


def save_context(saga_id: str, context: dict):
    _ensure_saga_state()
    data = json.loads(SAGA_STORE.read_text())
    data[saga_id] = context
    SAGA_STORE.write_text(json.dumps(data, indent=2))


def process_step(evt: dict):

    step_type = evt.get("type")
    saga_id = evt.get("context_saga")

    if not step_type:
        log.warning(f"Ignorando evento sin 'type': {evt}")
        return

    if saga_id is None:
        log.warning(
            f"Ignorando evento sin context_saga (mensaje viejo): {evt}")
        return

    context = load_context(saga_id)

    try:
        log.info(f"Ejecutando step desde cola: {step_type}")

        step = StepFactory.create(step_type)

        # 🚨🚨🚨 IMPORTANTE
        result = step.execute(context, from_consumer=True)

        save_context(saga_id, context)

    except Exception as e:
        retries = evt.get("retries", 0) + 1
        evt["retries"] = retries

        log.warning(f"Error ejecutando {step_type}, retry={retries} -> {e}")

        time.sleep(0.3 * (2 ** retries))

        if retries >= 3:
            log.error(f"Step {step_type} agotó retries → enviando a DLQ")
            send_to_dlq(evt)
        else:
            publish_retry(evt)


def publish_retry(evt):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue="saga_commands", durable=True)

    channel.basic_publish(
        exchange="",
        routing_key="saga_commands",
        body=json.dumps(evt),
    )
    connection.close()


def callback(ch, method, properties, body):
    evt = json.loads(body)
    process_step(evt)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost")
    )
    channel = connection.channel()

    channel.queue_declare(queue="saga_commands", durable=True)
    channel.queue_declare(queue="saga_dlq", durable=True)

    # Evita procesar 2 mensajes en paralelo (desordenaría el contexto)
    channel.basic_qos(prefetch_count=1)

    log.info("Consumer escuchando saga_commands...")

    channel.basic_consume(
        queue="saga_commands",
        on_message_callback=callback
    )

    channel.start_consuming()


if __name__ == "__main__":
    start_consumer()
