import pytest

from src.saga import orchestrator
from src.saga.factory import register_defaults, StepFactory
from src.saga.mediator import Mediator


def test_happy_path():
    ctx = orchestrator.run_demo(fail_assign=False)
    assert "user" in ctx
    assert ctx["user"]["name"] == "alice"
    assert "permissions" in ctx
    assert set(ctx["permissions"]) == {"read", "write"}
    # Comprobar que la cuota se creó en el flujo normal
    assert "quota" in ctx
    assert isinstance(ctx["quota"].get("values"), dict)


def test_assign_permissions_failure_triggers_rollback():
    # Al forzar fallo en AssignPermissions esperamos que el
    # usuario provisionado se elimine
    with pytest.raises(RuntimeError):
        orchestrator.run_demo(fail_assign=True)

    # Ejecutar manualmente para ver rollback:
    # crear context y pasos directamente

    register_defaults()
    med = Mediator()
    prov = StepFactory.create("provision_user", name="bob")
    med.register(prov)
    assign = StepFactory.create(
        "assign_permissions", permissions=["x"], fail=True)
    med.register(assign)

    ctx = {}
    with pytest.raises(RuntimeError):
        med.execute_all(ctx)

    # Después del rollback el usuario no debe existir
    assert "user" not in ctx
    # y la cuota tampoco
    assert "quota" not in ctx
