import pika
import json

EXCHANGE_NAME = "saga_exchange"
COMMAND_QUEUE_NAME = "saga_commands"
DLQ_QUEUE_NAME = "saga_dlq"

def handle_provision_user(data: dict) -> dict:
    user_id = data.get('id')
    return {'status': 'ok', 'detail': f'Ususario {user_id} provisionado'}


def handle_assign_permissions(data: dict) -> dict:
    user_id = data.get('id')
    return {'status': 'ok', 'detail': f'Permisos asignados a {user_id}'}


def handle_create_quota(data: dict) -> dict:
    user_id = data.get('id')
    quota_id = data.get('quota_id')
    return {'status': 'ok', 'detail': f'Quota {quota_id} creada para {user_id}'}


HANDLERS = {
    'ProvisionUser': handle_provision_user,
    'AssignPermissions': handle_assign_permissions,
    'CreateQuota': handle_create_quota,
}


def callback(ch, method, properties, body):
    try:
        evt = json.loads(body)
    except Exception:
        try:
            evt = body.decode()
        except Exception:
            evt = body

    resp_payload = {'status': 'error', 'detail': 'no handler'}
    try:
        evt_type = evt.get('type')
        data = evt.get('data', {})
        handler = HANDLERS.get(evt_type)

        if handler:
            resp_payload = handler(data)
        else:
            resp_payload = {'status': 'error', 'detail': f'Tipo de operación desconocido: {evt_type}'}
    except Exception as e:
        resp_payload = {'status': 'error', 'detail': str(e)}

    try:
        if properties.reply_to:
            ch.basic_publish(
                exchange='',
                routing_key=properties.reply_to,
                body=json.dumps(resp_payload),
                properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            )
    except Exception as e:
        print(f"Fallo al enviar la repuesta: {e}")

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"Mensaje procesado: {evt} -> Respuesta: {resp_payload}")

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
