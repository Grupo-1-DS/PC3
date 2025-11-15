import json
import time
import sqlite3
import pika

DB_PATH = "./db/users.db"

def send_to_rabbit(event: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    channel.queue_declare(queue='saga_commands', durable=True)

    channel.basic_publish(
        exchange='saga_exchange',
        routing_key='saga_commands',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2  
        )
    )

    connection.close()


def start_processing_outbox():
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, step, payload FROM outbox WHERE processed=0 ORDER BY id LIMIT 2"
        )
        rows = cursor.fetchall()

        if not rows:
            return

        for row in rows:
            id, step, payload = row
            try:
                payload = json.loads(payload)
            except Exception:
                payload = payload

            event = {"id": id, "step": step, "payload": payload}

            try:
                send_to_rabbit(event)
                cursor.execute("UPDATE outbox SET processed=1 WHERE id=?", (id,))
            except Exception as e:
                print(f"No se pudo enviar el evento con id={id} a rabbitmq: {e}")

        conn.commit()

    except Exception as e:
        print(f"Error al procesar el Outbox: {e}")

    finally:
        if conn:
            conn.close()
    

if __name__ == "__main__":
    print("Procesando registros del Outbox...")
    while True:
        start_processing_outbox()
        time.sleep(2)
