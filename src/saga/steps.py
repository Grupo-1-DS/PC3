from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import json
import time
import sqlite3
import uuid
import pika

def get_connection(db_type):
        return sqlite3.connect(f'db/{db_type}.db')

def rpc_call(event: dict, timeout: float = 5.0) -> dict:
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue

    corr_id = str(time.time())
    response = {'received': False, 'body': None}

    def on_response(ch, method, props, body):
        if props.correlation_id == corr_id:
            response['body'] = json.loads(body)
            response['received'] = True

    channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)

    channel.basic_publish(
        exchange='saga_exchange',
        routing_key='saga_commands',
        body=json.dumps(event),
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id,
            delivery_mode=2,
        ),
    )

    start = time.time()
    while not response['received'] and (time.time() - start) < timeout:
        connection.process_data_events(time_limit=0.1)

    connection.close()

    return response['body']

class Step(ABC):
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        pass

    @abstractmethod
    def rollback(self, *args, **kwargs) -> None:
        pass


class ProvisionUser(Step):

    def __init__(self, step_name="ProvisionUser", data=None, fail=False):
        self.name = step_name
        self.data = data or {}
        self.fail = fail

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("ProvisionUser falló")

        user_id = self.data["user"]["id"] or None
        user_name = self.data["user"]["name"]
        user_email = self.data["user"]["email"]

        conn = get_connection("users")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
                (user_id, user_name, user_email),
            )
            conn.commit()
                        
            result = rpc_call(
                {"type": "ProvisionUser", "data": {"id": user_id}})
            
            if(result.get('status') != 'ok'):
                raise RuntimeError(f"Error al procesar el registro en broker: {result}")

            print("     - Datos de usuario insertado en tabla users:", user_id, user_name, user_email)

        except Exception as e:
            raise RuntimeError(f"Fallo al registrar usuario: {e}")
        finally:
            conn.close()
            
    def rollback(self):
        conn = get_connection("users")
        cursor = conn.cursor()
        try:
            user_id = self.data["user"]["id"]
            cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()

            print(f"     - Rollback: Usuario eliminado con ID {user_id} de tabla users")
        except Exception as e:
            print(f"Fallo al hacer rollback de ProvisionUser: {e}")
        finally:
            conn.close()



class AssignPermissions(Step):

    def __init__(self, step_name="AssignPermissions", data=None, fail=False):
        self.name = step_name
        self.data = data or {}
        self.fail = fail

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("AssignPermissions falló")

        user_id = self.data["user"]["id"]
        user_name = self.data["user"]["name"]
        permissions = self.data["permissions"]

        conn = get_connection("permissions")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO permissions (user_id, permissions) VALUES (?, ?)",
                (user_id, json.dumps(permissions)),
            )

            conn.commit()

            result = rpc_call(
                {"type": "AssignPermissions", "data": {"id": user_id}})
            
            if(result.get('status') != 'ok'):
                raise RuntimeError(f"Error al procesar el registro en broker: {result}")

            print(f"     - Permisos asignados a user {user_name} en tabla permissions:", permissions)

        except Exception as e:
            raise RuntimeError(f"Fallo al asignar permisos: {e}")

        finally:
            conn.close()
        
        
    def rollback(self) -> None:
        conn = get_connection("permissions")
        cursor = conn.cursor()
        try:
            user_id = self.data["user"]["id"]
            cursor.execute("DELETE FROM permissions WHERE user_id=?", (user_id,))
            conn.commit()

            print(f"     - Rollback: Permisos eliminados para user {user_id} en tabla permissions")
        except Exception as e:
            print(f"Fallo al hacer rollback de AssignPermissions: {e}")
        finally:
            conn.close()


class CreateQuota(Step):

    def __init__(self, step_name="CreateQuota", data=None, fail=False):
        self.name = step_name
        self.data = data or {}
        self.fail = fail

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("CreateQuota fallló")

        quota_id = str(uuid.uuid4())
        user_id = self.data["user"]["id"]
        storage_gb = self.data["quota"]["storage_gb"]
        ops_per_month = self.data["quota"]["ops_per_month"]

        
        conn = get_connection("quotas")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO quotas (id, user_id, storage_gb, ops_per_month) VALUES (?, ?, ?, ?)",
                (quota_id, user_id, storage_gb, ops_per_month),
            )

            conn.commit()

            result = rpc_call(
                {"type": "CreateQuota",
                "data": {"id": user_id,}})

            if(result.get('status') != 'ok'):
                raise RuntimeError(f"Error al procesar la quota en el broker: {result}")
            
            print(f"     - Quota creada con ID {quota_id} para user {user_id} en tabla quotas")

        except Exception as e:
            raise RuntimeError(f"Fallo al crear quota: {e}")

    def rollback(self, context: Dict[str, Any]) -> None:
        conn = get_connection("quotas")
        cursor = conn.cursor()
        try:
            user_id = self.data["user"]["id"]
            cursor.execute("DELETE FROM quotas WHERE user_id=?", (user_id,))
            conn.commit()

            print(f"     - Rollback: Quota eliminada para user {user_id} en tabla quotas")
        except Exception as e:
            print(f"Fallo al hacer rollback de CreateQuota: {e}")
        finally:
            conn.close()
