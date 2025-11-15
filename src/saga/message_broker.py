import pika
import json
import sqlite3
import random
import os

EXCHANGE_NAME = "saga_exchange"
COMMAND_QUEUE_NAME = "saga_commands"
DLQ_QUEUE_NAME = "saga_dlq"
TEST_FAILS = os.getenv("FAILS", "false").lower() == "true"
NUMBER_RANDOM = os.getenv("RANDOM", "false").lower() == "true"

def get_connection(db_type):
    return sqlite3.connect(f'db/{db_type}.db')


# HANDLERS PARA ELIMINAR RECURSOS
def handler_composite_provision_user(data):
    db_id = data.get("db_id")
    if db_id is None:
        print("     - Rollback: No se tiene db_id para eliminar usuario")
        return
    conn = get_connection("users")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id=?", (db_id,))
        conn.commit()
        print(
            f"     - Rollback: Usuario eliminado con ID {db_id} de tabla users")
    except Exception as e:
        print(f"Fallo al hacer rollback de ProvisionUser: {e}")
    finally:
        conn.close()
    return {'status': 'ok', 'detail': f'Usuario {db_id} eliminado'}


def handler_composite_assign_permissions(data):
    perm_id = data.get("db_id")
    if perm_id is None:
        print("     - Rollback: No se tiene db_id para eliminar permisos")
        return
    conn = get_connection("permissions")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM permissions WHERE id=?", (perm_id,))
        conn.commit()
        print(
            f"     - Rollback: Permisos eliminados con ID {perm_id} de tabla permissions")
    except Exception as e:
        print(f"Fallo al hacer rollback de AssignPermissions: {e}")
    finally:
        conn.close()
    return {'status': 'ok', 'detail': 'Permisos eliminados'}


def handler_composite_create_quota(data):
    quota_row_id = data.get("db_id")
    if quota_row_id is None:
        print("     - Rollback: No se tiene db_id para eliminar quota")
        return
    conn = get_connection("quotas")
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM quotas WHERE id=?", (quota_row_id,))
        conn.commit()
        print(
            f"     - Rollback: Quota eliminada con ID {quota_row_id} de tabla quotas")
    except Exception as e:
        print(f"Fallo al hacer rollback de CreateQuota: {e}")
    finally:
        conn.close()
    return {'status': 'ok', 'detail': 'Quotas eliminadas'}


# HANDLERS PARA CREAR RECURSOS

def handle_provision_user(data: dict) -> dict:
    user_id = data.get('id')
    user_name = data.get('name')
    user_email = data.get('email')
    fail = data.get('fail')
    num = random.randint(12, 16) if NUMBER_RANDOM else None

    if (TEST_FAILS):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    if (fail and not NUMBER_RANDOM):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    if (fail and num is not None and num < 14):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    try:
        conn = get_connection("users")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (id, name, email) VALUES ( ?,?, ?)",
            (user_id, user_name, user_email),
        )
        conn.commit()
    except Exception as e:
        return {'status': 'error', 'detail': f'Fallo al registrar usuario: {e}'}
    finally:
        conn.close()
    return {'status': 'ok', 'id': user_id, 'detail': f'Usuario {user_id} provisionado'}


def handle_assign_permissions(data: dict) -> dict:
    user_id = data.get('id')
    permissions = data.get('permissions')
    fail = data.get('fail')
    num = random.randint(12, 16) if NUMBER_RANDOM else None

    if (TEST_FAILS):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    if (fail and not NUMBER_RANDOM):
        return {'status': 'error', 'detail': f'Fallo al asignar permisos(default)'}

    if (fail and num is not None and num < 14):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    try:
        conn = get_connection("permissions")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO permissions (user_id, permissions) VALUES (?, ?)",
            (user_id, json.dumps(permissions)),
        )
        conn.commit()
        perm_id = cursor.lastrowid
        print(
            f"     - Permisos asignados a user {user_id} en tabla permissions: {permissions} (perm_id={perm_id})")
    except Exception as e:
        return {'status': 'error', 'detail': f'Fallo al asignar permisos: {e}'}
    finally:
        conn.close()
    return {'status': 'ok', 'id': perm_id, 'detail': f'Permisos asignados a {user_id}'}


def handle_create_quota(data: dict) -> dict:
    user_id = data.get('id')
    quota_id = data.get('quota_id')
    storage_gb = data.get('storage_gb')
    ops_per_month = data.get('ops_per_month')
    fail = data.get('fail')
    num = random.randint(12, 16) if NUMBER_RANDOM else None

    if (TEST_FAILS):
        return {'status': 'error', 'detail': f'Fallo al crear cuota(default)'}

    if (fail and not NUMBER_RANDOM):
        return {'status': 'error', 'detail': f'Fallo al crear cuota(default)'}

    if (fail and num is not None and num < 14):
        return {'status': 'error', 'detail': f'Fallo al registrar usuario(default)'}

    try:
        conn = get_connection("quotas")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO quotas (user_id, storage_gb, ops_per_month) VALUES ( ?, ?, ?)",
            (user_id, storage_gb, ops_per_month),
        )
        conn.commit()
        quota_row_id = cursor.lastrowid
        print(
            f"     - Quota creada con ID {quota_id} para user {user_id} en tabla quotas (row_id={quota_row_id})")
    except Exception as e:
        return {'status': 'error', 'detail': f'Fallo al crear quota: {e}'}
    finally:
        conn.close()
    return {'status': 'ok', 'id': quota_row_id, 'detail': f'Quota {quota_id} creada para {user_id}'}


HANDLERS = {
    'ProvisionUser': handle_provision_user,
    'AssignPermissions': handle_assign_permissions,
    'CreateQuota': handle_create_quota,
    'CompositeAssignPermissions': handler_composite_assign_permissions,
    'CompositeProvisionUser': handler_composite_provision_user,
    'CompositeCreateQuota': handler_composite_create_quota
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
            resp_payload = {'status': 'error',
                            'detail': f'Tipo de operación desconocido: {evt_type}'}
    except Exception as e:
        resp_payload = {'status': 'error', 'detail': str(e)}

    try:
        if properties.reply_to:
            ch.basic_publish(
                exchange='',
                routing_key=properties.reply_to,
                body=json.dumps(resp_payload),
                properties=pika.BasicProperties(
                    correlation_id=properties.correlation_id),
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
    channel.exchange_declare(exchange=EXCHANGE_NAME,
                             exchange_type="direct", durable=True)

    channel.queue_bind(exchange=EXCHANGE_NAME,
                       queue=COMMAND_QUEUE_NAME, routing_key=COMMAND_QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME,
                       queue=DLQ_QUEUE_NAME, routing_key=DLQ_QUEUE_NAME)

    channel.basic_qos(prefetch_count=1)

    print(f"Escuchando mensajes en cola '{COMMAND_QUEUE_NAME}'...")

    channel.basic_consume(
        queue=COMMAND_QUEUE_NAME,
        on_message_callback=callback
    )

    channel.start_consuming()


if __name__ == "__main__":
    start_listening()
