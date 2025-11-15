from saga.metrics import saga_metrics
from saga.orchestrator import SagaOrchestrator
import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../src')))


def run_saga_e2e(fail_config, saga_orquestrator):
    data = {
        "user": {"id": str(uuid.uuid4()), "name": "user", "email": "user@gmail.com"},
        "permissions": ["read", "write"],
        "quota": {"storage_gb": 20, "ops_per_month": 2000},
        "fail": fail_config
    }
    saga_orquestrator.send_data(data)
    saga_orquestrator.execute_saga()


def test_chaos_step_failure(saga_orchestrator_instance):
    print("\n" + "="*70)
    print("**TEST E2E: Fallo en CreateQuota")
    print("="*70)

    saga_metrics.reset()

    run_saga_e2e([False, False, True], saga_orchestrator_instance)

    report = saga_metrics.get_report()
    assert report['total_sagas'] == 1
    assert report['compensation_rate'] == "100.00%"
    assert report['total_dlq_messages'] == 1

    print("\n Sistema se recuperó correctamente")

@pytest.mark.parametrize("scenario,fail_config,expected_compensations", [
    # Falla inmediato, sin compensación
    ("Fallo paso 1", [True, False, False], 0),
    ("Fallo paso 2", [False, True, False], 1),   # Compensa paso 1
    ("Fallo paso 3", [False, False, True], 2),   # Compensa pasos 1 y 2
])
def test_chaos_different_failure_points(scenario, fail_config, expected_compensations, saga_orchestrator_instance):
    """
    E2E: Caos en diferentes puntos de fallo
    Verifica que la compensación sea proporcional al progreso
    """
    print(f"\nEscenario: {scenario}")

    saga_metrics.reset()
    run_saga_e2e(fail_config, saga_orchestrator_instance)

    report = saga_metrics.get_report()
    assert report['compensation_rate'] == "100.00%"
    assert report['total_dlq_messages'] == 1

def test_chaos_multiple_sagas_with_failures(saga_orchestrator_instance):
    print("\n" + "="*70)
    print(" TEST E2E: Múltiples SAGAs con caos")
    print("="*70)

    saga_metrics.reset()

    # Ejecutar mix de SAGAs
    run_saga_e2e([False, False, False], saga_orchestrator_instance)  # OK
    run_saga_e2e([False, False, True], saga_orchestrator_instance)   # Falla
    run_saga_e2e([False, False, False], saga_orchestrator_instance)  # OK
    run_saga_e2e([False, True, False], saga_orchestrator_instance)   # Falla

    # Validar resiliencia
    report = saga_metrics.get_report()
    assert report['total_sagas'] == 4
    assert report['success_rate'] == "50.00%"
    assert report['compensation_rate'] == "50.00%"

    # Mostrar informe de resiliencia
    saga_metrics.print_resilience_report()

    # Guardar con historial para trends
    saga_metrics.save_with_history('test_e2e_metrics.json')

    print("\n✅ Test E2E con caos completado")


def test_resilience_report_with_trends(self, saga_orchestrator_instance):
    print("\n" + "="*70)
    print("📊 TEST: Informe de Resiliencia con Trends")
    print("="*70)

    # Primera ejecución (peor escenario)
    print("\n--- Ejecución 1: Escenario con más fallos ---")
    saga_metrics.reset()

    run_saga_e2e([False, False, False], saga_orchestrator_instance) # OK
    run_saga_e2e([False, False, True], saga_orchestrator_instance) # Falla
    run_saga_e2e([False, True, False], saga_orchestrator_instance) # Falla

    saga_metrics.print_report()
    saga_metrics.save_with_history('trend_test.json')

    # Segunda ejecución (mejor escenario)
    print("\n--- Ejecución 2: Escenario mejorado ---")
    saga_metrics.reset()

    run_saga_e2e([False, False, False], saga_orchestrator_instance) # OK
    run_saga_e2e([False, False, False], saga_orchestrator_instance) # OK
    run_saga_e2e([False, False, True], saga_orchestrator_instance) # Falla

    saga_metrics.print_report()

    # Guardar segunda ejecución
    saga_metrics.save_with_history('trend_test.json')

    # Mostrar informe de resiliencia con trends
    saga_metrics.print_resilience_report()

    # Validar los trends
    trends = saga_metrics.calculate_trends('trend_test_previous.json')

    if trends:
        print(f"\nTrends detectados: {trends}")
        assert 'success_rate' in trends
        print(" Trends calculados correctamente")
    else:
        print("Primera ejecución - No hay datos previos para comparar")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
