"""
Steps para la saga: definición base y pasos concretos.

Arreglado para evitar bucles infinitos:
- Los steps solo escriben en Outbox cuando los ejecuta el ORCHESTRATOR.
- Cuando los ejecuta el CONSUMER, no escriben en Outbox.
"""

from typing import Any, Dict, Optional
from abc import ABC, abstractmethod
import json
import logging
from pathlib import Path


class Step(ABC):
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Any:
        pass
    @abstractmethod
    def rollback(self, context: Dict[str, Any]) -> None:
        pass


class ProvisionUser(Step):

    def __init__(self, step_name="ProvisionUser", fail=False):
        self.name = step_name
        self.fail = fail

    def execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.fail:
            raise RuntimeError("ProvisionUser failed")



        user = {"id": self.user_id, "name": self.name}


class AssignPermissions(Step):

    def __init__(self, permissions=None, fail=False):
        self.permissions = permissions or ["read"]
        self.fail = fail
        self._logger = logging.getLogger(__name__)

    def execute(self, context: Dict[str, Any], from_consumer=False) -> Dict[str, Any]:
        if self.fail:
            raise RuntimeError("AssignPermissions failed")

        user = context.get("user")
        if not user:
            raise RuntimeError("No user in context to assign perms")

        context["permissions"] = list(self.permissions)

        # Persistir
        store = _read_store()
        store["permissions"][user["id"]] = list(self.permissions)
        _write_store(store)

        # SOLO ORCHESTRATOR CREA OUTBOX
        if not from_consumer:
            record_outbox({
                "step": "AssignPermissions",
                "type": "assign_permissions",
                "user_id": user["id"],
                "permissions": list(self.permissions),
                "context_saga": context.get("_saga_id"),
            })

        self._logger.info(
            "Assigned permissions %s to user %s",
            self.permissions,
            user.get("name"),
        )
        return {"user": user, "permissions": context["permissions"]}


class CreateQuota(Step):

    def __init__(self, quota_values=None, fail=False, quota_id=None):
        default = {"storage_gb": 10, "ops_per_month": 1000}
        self.quota_values = quota_values or default
        self.fail = fail
        self.quota_id = quota_id or "quota-1"
        self._logger = logging.getLogger(__name__)

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

        # Persistir
        store = _read_store()
        store["quotas"][self.quota_id] = quota
        _write_store(store)

        # SOLO ORCHESTRATOR CREA OUTBOX
        if not from_consumer:
            record_outbox({
                "step": "CreateQuota",
                "type": "create_quota",
                "quota_id": self.quota_id,
                "user_id": user["id"],
                "values": dict(self.quota_values),
                "context_saga": context.get("_saga_id"),
            })

        self._logger.info("QuotaCreated: %s", quota)
        return quota
