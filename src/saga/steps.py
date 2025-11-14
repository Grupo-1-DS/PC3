from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import json
import sqlite3
import pika

def get_connection(db_type):
        return sqlite3.connect(f'db/{db_type}.db')

def send_to_rabbit(event: dict):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters("localhost")
    )
    channel = connection.channel()
    channel.queue_declare(queue="saga_commands", durable=True)

    channel.basic_publish(
        exchange="saga_exchange",
        routing_key="saga_commands",
        body=json.dumps(event),
        properties=pika.BasicProperties(
            delivery_mode=2
        ),
    )
    connection.close()

class Step(ABC):
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        pass
    @abstractmethod
    def rollback(self, context: Dict[str, Any]) -> None:
        pass


class ProvisionUser(Step):

    def __init__(self, step_name="ProvisionUser", data=None, fail=False):
        self.name = step_name
        self.data = data or {}
        self.fail = fail

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("ProvisionUser failed")
        
        try:
            user_id = self.data.get("id")
            user_name = self.data.get("name")
            user_email = self.data.get("email")
        
            conn = get_connection("users")
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, name, email) VALUES (?, ?, ?)",
                (user_id, user_name, user_email),
            )

            event = {
                "type": "AssignPermissions",
                "data": {
                    "id": user_id,
                },
            }

            send_to_rabbit(event)

            conn.commit()
            conn.close()
        except Exception as e:
            pass
    
    def rollback(self):
        print("Rollback ProvisionUser")



class AssignPermissions(Step):

    def __init__(self,step_name="AssignPermissions", permissions=None, fail=False):
        self.name = step_name
        self.permissions = permissions or ["read"]
        self.fail = fail

    def execute(self) -> None:
        if self.fail:
            raise RuntimeError("AssignPermissions failed")
        
        try:
            conn = get_connection("permissions")
            cursor = conn.cursor()
            
            permissions = self.permissions 
            cursor.execute(
                "INSERT INTO permissions (user_id, permissions) VALUES (?, ?)",
                (user_id, json.dumps(self.permissions)),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            pass

    def rollback(self) -> None:
        print("Rollback AssignPermissions")


class CreateQuota(Step):

    def __init__(self, step_name="CreateQuota", quota_values=None, fail=False):
        self.name = step_name
        default = {"storage_gb": 10, "ops_per_month": 1000}
        self.quota_values = quota_values or default
        self.fail = fail

    def execute(self, context: Dict[str, Any], from_consumer=False) -> Dict[str, Any]:
        if self.fail:
            raise RuntimeError("CreateQuota failed")

        user = context.get("user")
        if not user:
            raise RuntimeError("No user in context to attach quota")

        quota = {
            "id": self.quota_id,
            "user_id": user["id"],
            "values": dict(self.quota_values),
        }

        context["quota"] = quota

        return quota
    
    def rollback(self, context: Dict[str, Any]) -> None:
        print("Rollback CreateQuota")
