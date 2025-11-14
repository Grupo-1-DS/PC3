import pika
import json

EXCHANGE_NAME = "saga_exchange"
COMMAND_QUEUE_NAME = "saga_commands"
DLQ_QUEUE_NAME = "saga_dlq"

def callback(ch, method, properties, body):
    try:
        evt = json.loads(body)
    except:
        evt = body.decode()
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"Mensaje procesado: {evt}")

def connect_to_message_broker():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost")
    )
    return connection

def start_listening():

    conn = connect_to_message_broker()
    
    channel = conn.channel()
    channel.queue_declare(queue=COMMAND_QUEUE_NAME, durable=True)
    channel.queue_declare(queue=DLQ_QUEUE_NAME, durable=True)
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="direct", durable=True)

    channel.queue_bind(exchange=EXCHANGE_NAME, queue=COMMAND_QUEUE_NAME, routing_key=COMMAND_QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=DLQ_QUEUE_NAME, routing_key=DLQ_QUEUE_NAME)

    channel.basic_qos(prefetch_count=1)

    print(f"Escuchando mensajes en cola '{COMMAND_QUEUE_NAME}'...")

    channel.basic_consume(
        queue=COMMAND_QUEUE_NAME,
        on_message_callback=callback
    )

    channel.start_consuming()


if __name__ == "__main__":
    start_listening()
