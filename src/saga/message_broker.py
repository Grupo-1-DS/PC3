import pika
import json

def callback(ch, method, properties, body):
    evt = json.loads(body)
    #process_step(evt)
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
    channel.queue_declare(queue="saga_commands", durable=True)
    channel.queue_declare(queue="saga_dlq", durable=True)
    channel.exchange_declare(exchange="saga_exchange", exchange_type="direct", durable=True)

    channel.queue_bind(exchange="saga_exchange", queue="saga_commands", routing_key="saga_command")
    channel.queue_bind(exchange="saga_exchange", queue="saga_dlq", routing_key="saga_dlq")

    channel.basic_qos(prefetch_count=1)

    print("Message Broker escuchando saga_commands...")

    channel.basic_consume(
        queue="saga_commands",
        on_message_callback=callback
    )

    channel.start_consuming()


if __name__ == "__main__":
    start_listening()
