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
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue

    corr_id = str(time.time())
    response = {'received': False, 'body': None}

    def on_response(ch, method, props, body):
        if props.correlation_id == corr_id:
            response['body'] = json.loads(body)
            response['received'] = True

    channel.basic_consume(queue=callback_queue,
                          on_message_callback=on_response, auto_ack=True)

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
    def __init__(self, step_name="ProvisionUser", data=None):
        self.name = step_name
        self.data = data or {}

    def execute(self) -> None:
        fail = self.data.get("fail")[0]

        if fail:
            raise RuntimeError("ProvisionUser falló")

        user_id = self.data["user"]["id"]
        user_name = self.data["user"]["name"]
        user_email = self.data["user"]["email"]

        # Enviar al message broker
        result = rpc_call({
            "type": "ProvisionUser",
            "data": {
                "id": user_id,
                "name": user_name,
                "email": user_email,
            }
        })
        if result.get('status') != 'ok':
            raise RuntimeError(
                f"Error al procesar el registro en broker: {result}")
        # Guardar el id real generado por el broker para rollback
        self.data["db_id"] = result.get("id", user_id)
        print("     - Solicitud de creación de usuario enviada al broker:",
              user_id, user_name, user_email, "(db_id:", self.data["db_id"], ")")

    def rollback(self) -> None:
        db_id = self.data.get("db_id")
        if db_id is None:
            print("     - Rollback: No se tiene db_id para eliminar usuario")
            return
        result = rpc_call({
            "type": "CompositeProvisionUser",
            "data": {"db_id": db_id}
        })
        if result and result.get("status") == "ok":
            print(f"     - Rollback exitoso usuario: {db_id}")
        else:
            print(f"     - Fallo rollback usuario: {db_id} -> {result}")


class AssignPermissions(Step):
    def __init__(self, step_name="AssignPermissions", data=None):
        self.name = step_name
        self.data = data or {}

    def execute(self) -> None:
        fail = self.data.get("fail")[1]
        if fail:
            raise RuntimeError("AssignPermissions falló")

        user_id = self.data["user"]["id"]
        permissions = self.data["permissions"]

        # Enviar al message broker
        result = rpc_call({
            "type": "AssignPermissions",
            "data": {
                "id": user_id,
                "permissions": permissions,
            }
        })
        if result.get('status') != 'ok':
            raise RuntimeError(
                f"Error al procesar el registro en broker: {result}")
        self.data["db_id"] = result.get("id")
        print(
            f"     - Solicitud de asignación de permisos enviada al broker: {user_id}, {permissions} (db_id: {self.data['db_id']})")

    def rollback(self) -> None:
        db_id = self.data.get("db_id")
        if db_id is None:
            print("     - Rollback: No se tiene db_id para eliminar permisos")
            return
        result = rpc_call({
            "type": "CompositeAssignPermissions",
            "data": {"db_id": db_id}
        })
        if result and result.get("status") == "ok":
            print(f"     - Rollback exitoso permisos: {db_id}")
        else:
            print(f"     - Fallo rollback permisos: {db_id} -> {result}")


class CreateQuota(Step):
    def __init__(self, step_name="CreateQuota", data=None):
        self.name = step_name
        self.data = data or {}

    def execute(self) -> None:
        fail = self.data.get("fail")[2]

        if fail:
            raise RuntimeError("CreateQuota fallló")

        quota_id = self.data["quota"].get("quota_id", str(uuid.uuid4()))
        user_id = self.data["user"]["id"]
        storage_gb = self.data["quota"]["storage_gb"]
        ops_per_month = self.data["quota"]["ops_per_month"]

        # Enviar al message broker
        result = rpc_call({
            "type": "CreateQuota",
            "data": {
                "id": user_id,
                "quota_id": quota_id,
                "storage_gb": storage_gb,
                "ops_per_month": ops_per_month,
            }
        })
        if result.get('status') != 'ok':
            raise RuntimeError(
                f"Error al procesar la quota en el broker: {result}")
        self.data["db_id"] = result.get("id")
        print(
            f"     - Solicitud de creación de quota enviada al broker: {quota_id}, {user_id}, {storage_gb}, {ops_per_month} (db_id: {self.data['db_id']})")

    def rollback(self) -> None:
        db_id = self.data.get("db_id")
        if db_id is None:
            print("     - Rollback: No se tiene db_id para eliminar quota")
            return
        result = rpc_call({
            "type": "CompositeCreateQuota",
            "data": {"db_id": db_id}
        })
        if result and result.get("status") == "ok":
            print(f"     - Rollback exitoso quota: {db_id}")
        else:
            print(f"     - Fallo rollback quota: {db_id} -> {result}")
