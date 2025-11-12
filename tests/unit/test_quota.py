import pytest

from src.saga.factory import register_defaults, StepFactory
from src.saga.mediator import Mediator


def test_create_quota_happy_path():
    register_defaults()
    med = Mediator()

    # Provision user first
    med.register(StepFactory.create("provision_user", name="carla"))
    # Create quota
    med.register(StepFactory.create(
        "create_quota", quota_values={"storage_gb": 5}))

    ctx = {}
    med.execute_all(ctx)

    assert "user" in ctx
    assert "quota" in ctx
    assert ctx["quota"]["values"]["storage_gb"] == 5


def test_create_quota_idempotent_when_reexecuted():
    register_defaults()
    # Ejecutar CreateQuota dos veces sobre el mismo contexto
    prov = StepFactory.create("provision_user", name="dave")
    quota_step = StepFactory.create(
        "create_quota", quota_values={"storage_gb": 2}, quota_id="q-1"
    )

    ctx = {}
    prov.execute(ctx)

    # primera ejecución
    quota1 = quota_step.execute(ctx)
    # segunda ejecución (debe sobrescribir o ser inofensiva)
    quota2 = quota_step.execute(ctx)

    assert quota1["id"] == quota2["id"]
    assert ctx["quota"]["values"]["storage_gb"] == 2


def test_quota_removed_on_rollback_of_later_step():
    register_defaults()
    med = Mediator()
    med.register(StepFactory.create("provision_user", name="erin"))
    med.register(StepFactory.create(
        "create_quota", quota_values={"storage_gb": 3}))
    # Forzar fallo en AssignPermissions para provocar rollback
    med.register(StepFactory.create(
        "assign_permissions", permissions=["x"], fail=True))

    ctx = {}
    with pytest.raises(RuntimeError):
        med.execute_all(ctx)

    assert "quota" not in ctx
