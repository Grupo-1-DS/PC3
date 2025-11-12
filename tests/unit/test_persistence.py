import json
from src.saga import steps
from src.saga.mediator import Mediator


def test_execute_writes_store(tmp_path):
    # Usar un store temporal para no tocar el real
    tmp_store = tmp_path / "saga_store.json"
    steps.STORE_PATH = tmp_store

    med = Mediator()
    # Registrar ProvisionUser y CreateQuota para un camino feliz
    med.register(
        steps.ProvisionUser(name="bob", user_id="bob-id")
    )
    med.register(
        steps.CreateQuota(quota_id="q-bob", quota_values={"storage_gb": 5})
    )

    ctx = {}
    med.execute_all(ctx)

    # El contexto debe contener user y quota
    assert ctx.get("user") and ctx.get("quota")

    data = json.loads(tmp_store.read_text())
    assert "bob-id" in data.get("users", {})
    assert "q-bob" in data.get("quotas", {})


def test_rollback_clears_store_on_failure(tmp_path):
    # Parchar el store a un temporal
    tmp_store = tmp_path / "saga_store.json"
    steps.STORE_PATH = tmp_store

    med = Mediator()
    # ProvisionUser se ejecutará; AssignPermissions fallará y se hará rollback
    med.register(steps.ProvisionUser(name="eve", user_id="eve-id"))
    med.register(
        steps.AssignPermissions(permissions=["admin"], fail=True)
    )

    ctx = {}
    try:
        med.execute_all(ctx)
    except Exception:
        # tras rollback, el store no debe contener la entrada creada
        data = json.loads(tmp_store.read_text())
        assert data.get("users", {}) == {}
        assert data.get("permissions", {}) == {}
        return

    # Si no hubo excepción, la prueba falla
    assert False, "Expected failure from AssignPermissions did not occur"
