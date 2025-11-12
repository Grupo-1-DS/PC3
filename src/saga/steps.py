"""Steps para la saga: definición base y pasos concretos.

Ahora los steps persisten en un pequeño 'mock backend' basado en JSON
ubicado en `src/saga/data/saga_store.json`. Cada execute escribe el
cambio y cada rollback lo revierte en ese archivo además de actualizar
el `context` en memoria.
"""
from typing import Any, Dict, Optional
import json
import logging
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
STORE_PATH = Path(__file__).resolve().parent / "data" / "saga_store.json"


def _ensure_store() -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not STORE_PATH.exists():
        initial = {"users": {}, "quotas": {}, "permissions": {}}
        STORE_PATH.write_text(json.dumps(initial))


def _read_store() -> Dict[str, Dict[str, Any]]:
    _ensure_store()
    try:
        return json.loads(STORE_PATH.read_text())
    except Exception:
        return {"users": {}, "quotas": {}, "permissions": {}}


def _write_store(data: Dict[str, Dict[str, Any]]) -> None:
    _ensure_store()
    STORE_PATH.write_text(json.dumps(data, indent=2))


class Step:
    """Clase base para un Step en la saga."""

    def execute(self, context: Dict[str, Any]) -> Any:
        raise NotImplementedError()

    def rollback(self, context: Dict[str, Any]) -> None:
        return None


class ProvisionUser(Step):
    """Step que 'provisiona' un usuario y lo persiste en el store JSON.

    kwargs aceptados: name, user_id, fail
    """

    def __init__(
        self,
        name: str = "user",
        user_id: Optional[str] = None,
        fail: bool = False,
    ):
        self.name = name
        self.user_id = user_id or f"{name}-id"
        self.fail = fail
        self._logger = logging.getLogger(__name__)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if self.fail:
            self._logger.error("ProvisionUser failed for %s", self.name)
            raise RuntimeError("ProvisionUser failed")

        user = {"id": self.user_id, "name": self.name}
        # Guardar en context en memoria
        context["user"] = user

        # Persistir en el store JSON
        store = _read_store()
        store.setdefault("users", {})[self.user_id] = user
        _write_store(store)

        self._logger.info("Provisioned user: %s (%s)", self.name, self.user_id)
        return user

    def rollback(self, context: Dict[str, Any]) -> None:
        # Eliminar del context y del store
        context.pop("user", None)
        store = _read_store()
        if store.get("users") and self.user_id in store["users"]:
            del store["users"][self.user_id]
            _write_store(store)
        self._logger.info("Rolled back ProvisionUser: %s", self.name)


class AssignPermissions(Step):
    """Step que asigna permisos a un usuario y lo persiste en el store."""

    def __init__(self, permissions=None, fail: bool = False):
        self.permissions = permissions or ["read"]
        self.fail = fail
        self._logger = logging.getLogger(__name__)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if self.fail:
            self._logger.error("AssignPermissions simulated failure")
            raise RuntimeError("AssignPermissions failed")

        user = context.get("user")
        if not user:
            raise RuntimeError("No user in context to assign perms")

        # Actualizar context
        context["permissions"] = list(self.permissions)

        # Persistir en store
        store = _read_store()
        perms = list(self.permissions)
        store.setdefault("permissions", {})[user["id"]] = perms
        _write_store(store)

        self._logger.info(
            "Assigned permissions %s to user %s",
            self.permissions,
            user.get("name"),
        )
        return {"user": user, "permissions": context["permissions"]}

    def rollback(self, context: Dict[str, Any]) -> None:
        # Eliminar permisos del context y del store
        user = context.get("user")
        context.pop("permissions", None)
        if user:
            store = _read_store()
            if (
                store.get("permissions")
                and user.get("id") in store["permissions"]
            ):
                del store["permissions"][user.get("id")]
                _write_store(store)
            self._logger.info("Rolled back AssignPermissions")


class CreateQuota(Step):
    """Step que crea/asigna una cuota al usuario y lo persiste en el store."""

    def __init__(
        self,
        quota_values=None,
        fail: bool = False,
        quota_id: Optional[str] = None,
    ):
        default_vals = {"storage_gb": 10, "ops_per_month": 1000}
        self.quota_values = quota_values or default_vals
        self.fail = fail
        self.quota_id = quota_id or "quota-1"
        self._logger = logging.getLogger(__name__)

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if self.fail:
            self._logger.error("CreateQuota simulated failure")
            raise RuntimeError("CreateQuota failed")

        user = context.get("user")
        if not user:
            raise RuntimeError("No user in context to attach quota")

        quota = {
            "id": self.quota_id,
            "user_id": user.get("id"),
            "values": dict(self.quota_values),
        }
        context["quota"] = quota

        # Persistir
        store = _read_store()
        store.setdefault("quotas", {})[self.quota_id] = quota
        _write_store(store)

        self._logger.info("QuotaCreated: %s", quota)
        return quota

    def rollback(self, context: Dict[str, Any]) -> None:
        # Eliminar cuota del context y del store
        quota = context.pop("quota", None)
        store = _read_store()
        if (
            quota
            and store.get("quotas")
            and quota.get("id") in store["quotas"]
        ):
            del store["quotas"][quota.get("id")]
            _write_store(store)
        self._logger.info("Rolled back CreateQuota: %s", self.quota_id)
