import json
import pika
from pathlib import Path

# -------------------------------
# Archivos locales del sistema
# -------------------------------
BASE = Path(__file__).resolve().parent / "saga"

OUTBOX = BASE / "outbox" / "outbox_store.json"
DLQ_STORE = BASE / "outbox" / "dlq_store.json"
SAGA_STATE = BASE / "data" / "saga_state_store.json"

# -------------------------------
# Función para limpiar archivos
# -------------------------------


def clean_file(path: Path, empty_data):
    if path.exists():
        path.write_text(json.dumps(empty_data, indent=2))
        print(f"[OK] Limpio → {path.name}")
    else:
        print(f"[SKIP] No existe → {path.name}")

# -------------------------------
# Función para purgar colas RabbitMQ
# -------------------------------


def purge_rabbit_queue(queue_name):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters("localhost"))
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_purge(queue=queue_name)
        connection.close()
        print(f"[OK] Cola purgada → {queue_name}")
    except Exception as e:
        print(f"[ERROR] No se pudo purgar {queue_name}: {e}")

# -------------------------------
# Ejecución principal
# -------------------------------


def reset_all():
    print(" RESET COMPLETO DEL SISTEMA SAGA ")

    # Purga de colas RabbitMQ
    purge_rabbit_queue("saga_commands")
    purge_rabbit_queue("saga_dlq")

    # Limpieza de archivos persistentes
    clean_file(OUTBOX, {"events": []})
    clean_file(DLQ_STORE, {"events": []})
    clean_file(SAGA_STATE, {})

    print("\nSistema completamente reseteado.")
    print("Puedes ejecutar nuevamente:")
    print(" → python -m src.saga.orchestrator (si quieres lanzar saga)")
    print(" → python -m src.saga.worker")
    print(" → python -m src.saga.consumer")


if __name__ == "__main__":
    reset_all()
