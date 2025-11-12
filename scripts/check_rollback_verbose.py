"""Script de comprobación: ejecuta la saga con `AssignPermissions` fallando.

Ejecuta la secuencia y muestra el contexto final para verificar rollback.
"""
from src.saga.mediator import Mediator
from src.saga.factory import register_defaults, StepFactory
import logging
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto está en sys.path para que 'src' sea importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    """Ejecuta un Mediator con AssignPermissions fallando para probar rollback."""
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s: %(message)s")

    register_defaults()
    med = Mediator()
    med.register(StepFactory.create("provision_user", name="bob"))
    med.register(
        StepFactory.create("assign_permissions", permissions=["x"], fail=True)
    )

    ctx = {}
    try:
        med.execute_all(ctx)
    except Exception as e:
        print("Exception:", e)

    print("Context after run:", ctx)


if __name__ == "__main__":
    main()
