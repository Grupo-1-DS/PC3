"""
Demo simple del SAGA Orchestrator

Este demo muestra dos casos básicos:
1. Un SAGA exitoso (todos los pasos se completan)
2. Un SAGA fallido (falla un paso, se ejecuta compensación)

Para tests más exhaustivos con métricas, ejecuta:
    pytest tests/unit/test_metrics.py -v -s
"""
from .orchestrator import SagaOrchestrator
from .metrics import saga_metrics
import uuid


def main():
    print("\n" + "="*70)
    print(" DEMO: SAGA Orchestrator con Compensación Automática")
    print("="*70)

    #  DEMO 1: SAGA EXITOSO
    print("\n" + "="*70)
    print(" CASO 1: Flujo Exitoso")
    print("="*70)
    print("Creando usuario 'Alice' con permisos y cuota...")

    data_success = {
        "user": {
            "id": str(uuid.uuid4()),
            "name": "Alice",
            "email": "alice@example.com"
        },
        "permissions": ["read", "write", "admin"],
        "quota": {
            "storage_gb": 100,
            "ops_per_month": 10000
        },
        "fail": [False, False, False]
    }

    saga = SagaOrchestrator()
    saga.send_data(data_success)
    saga.execute_saga()

    #  DEMO 2: SAGA CON FALLO Y COMPENSACIÓN
    print("\n" + "="*70)
    print(" CASO 2: Fallo con Compensación Automática")
    print("="*70)
    print("Intentando crear usuario 'Bob'...")
    print("(El paso CreateQuota fallará y se ejecutará rollback)")

    data_fail = {
        "user": {
            "id": str(uuid.uuid4()),
            "name": "Bob",
            "email": "bob@example.com"
        },
        "permissions": ["read"],
        "quota": {
            "storage_gb": 50,
            "ops_per_month": 5000
        },
        "fail": [False, False, True]
    }

    saga2 = SagaOrchestrator()
    saga2.send_data(data_fail)
    saga2.execute_saga()

    print("\n" + "="*70)
    print(" Resumen de Métricas del Demo")
    print("="*70)

    saga_metrics.print_report()
    saga_metrics.save_to_file('saga_metrics.json')


if __name__ == "__main__":
    main()
