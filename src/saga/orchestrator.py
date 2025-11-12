"""Orquestador de ejemplo que usa Factory y Mediator.

Provee la función `run_demo(fail_assign=False)` que construye una
secuencia de steps usando la `StepFactory` y la ejecuta con el
`Mediator`.
"""

try:
    from .factory import StepFactory, register_defaults
    from .mediator import Mediator
except Exception:
    from src.saga.factory import StepFactory, register_defaults
    from src.saga.mediator import Mediator


def run_demo(fail_assign: bool = False):
    """Crea y ejecuta la secuencia: provision -> quota -> assign.

    Si `fail_assign=True` se fuerza el fallo en AssignPermissions para
    probar la compensación (rollback).
    """
    register_defaults()
    mediator = Mediator()

    provision = StepFactory.create("provision_user", name="alice")
    mediator.register(provision)

    quota = StepFactory.create(
        "create_quota",
        quota_values={"storage_gb": 10},
        fail=False,
    )
    mediator.register(quota)

    assign = StepFactory.create(
        "assign_permissions",
        permissions=["read", "write"],
        fail=fail_assign,
    )
    mediator.register(assign)

    context = {}
    mediator.execute_all(context)
    return context
