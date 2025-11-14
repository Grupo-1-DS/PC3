import pika

def send_message(message: str):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()

    channel.queue_declare(queue='saga_commands', durable=True)

    channel.basic_publish(
        exchange='saga_exchange',
        routing_key='saga_commands',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2  
        )
    )

    print(f" [x] Mensaje enviado: {message}")
    connection.close()


if __name__ == "__main__":
    send_message("Hola, este es un mensaje para saga_commands")
