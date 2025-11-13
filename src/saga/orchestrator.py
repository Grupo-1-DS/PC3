import uuid

from .factory import StepFactory
from .mediator import Mediator


def run_demo(fail_assign=False):

    # Crear mediador
    mediator = Mediator()

    # Contexto vacío → el Mediator crea el saga_id real
    context = {}

    # Registrar steps en orden SAGA
    mediator.register(StepFactory.create("provision_user", name="alice"))
    mediator.register(StepFactory.create("create_quota"))
    mediator.register(
        StepFactory.create(
            "assign_permissions",
            permissions=["read", "write"],
            fail=fail_assign
        )
    )

    # Ejecutar steps → llenará el OUTBOX
    mediator.execute_all(context)

    return context


if __name__ == "__main__":
    ctx = run_demo()
    print("Saga ID:", ctx["_saga_id"])
