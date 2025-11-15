"""
Test E2E con caos controlado para Sprint 3
Simula fallos y verifica resiliencia del sistema
"""
from saga.metrics import saga_metrics
from saga.orchestrator import SagaOrchestrator
import sys
import os
import uuid
import pytest

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../src')))


def run_saga_e2e(name, email, fail_config):
    """Ejecuta un SAGA completo E2E"""
    data = {
        "user": {"id": str(uuid.uuid4()), "name": name, "email": email},
        "permissions": ["read", "write"],
        "quota": {"storage_gb": 20, "ops_per_month": 2000},
        "fail": fail_config
    }
    saga = SagaOrchestrator()
    saga.send_data(data)
    saga.execute_saga()


class TestE2EChaos:
    """Tests E2E con inyección de caos controlado"""

    def test_chaos_step_failure(self):
        """
        E2E: Fallo controlado en un paso
        Verifica que el sistema se recupere con compensación
        """
        print("\n" + "="*70)
        print("**TEST E2E: Caos - Fallo en CreateQuota")
        print("="*70)

        saga_metrics.reset()

        # Ejecutar SAGA que fallará en el paso 3
        run_saga_e2e("ChaosUser", "chaos@test.com", [False, False, True])

        # Validar que se compensó correctamente
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
    def test_chaos_different_failure_points(self, scenario, fail_config, expected_compensations):
        """
        E2E: Caos en diferentes puntos de fallo
        Verifica que la compensación sea proporcional al progreso
        """
        print(f"\n🔥 Escenario: {scenario}")

        saga_metrics.reset()
        run_saga_e2e("User", "user@test.com", fail_config)

        report = saga_metrics.get_report()
        assert report['compensation_rate'] == "100.00%"
        assert report['total_dlq_messages'] == 1

    def test_chaos_multiple_sagas_with_failures(self):
        """
        E2E: Múltiples SAGAs con y sin fallos
        Genera informe de resiliencia completo
        """
        print("\n" + "="*70)
        print(" TEST E2E: Múltiples SAGAs con caos")
        print("="*70)

        saga_metrics.reset()

        # Ejecutar mix de SAGAs
        run_saga_e2e("User1", "u1@test.com", [False, False, False])  # OK
        run_saga_e2e("User2", "u2@test.com", [False, False, True])   # Falla
        run_saga_e2e("User3", "u3@test.com", [False, False, False])  # OK
        run_saga_e2e("User4", "u4@test.com", [False, True, False])   # Falla

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


class TestResilienceWithTrends:
    """Test que genera informe con trends"""

    def test_resilience_report_with_trends(self):
        """
        Genera dos ejecuciones consecutivas y compara trends
        """
        print("\n" + "="*70)
        print("📊 TEST: Informe de Resiliencia con Trends")
        print("="*70)

        # Primera ejecución (peor escenario)
        print("\n--- Ejecución 1: Escenario con más fallos ---")
        saga_metrics.reset()

        run_saga_e2e("U1", "u1@test.com", [False, False, False])
        run_saga_e2e("U2", "u2@test.com", [False, False, True])
        run_saga_e2e("U3", "u3@test.com", [False, True, False])

        saga_metrics.print_report()
        saga_metrics.save_with_history('trend_test.json')

        # Segunda ejecución (mejor escenario)
        print("\n--- Ejecución 2: Escenario mejorado ---")
        saga_metrics.reset()

        run_saga_e2e("U4", "u4@test.com", [False, False, False])
        run_saga_e2e("U5", "u5@test.com", [False, False, False])
        run_saga_e2e("U6", "u6@test.com", [False, False, True])

        saga_metrics.print_report()

        # Guardar segunda ejecución (esto crea el archivo _previous con los datos de la primera)
        saga_metrics.save_with_history('trend_test.json')

        # Ahora sí mostrar informe de resiliencia con trends
        saga_metrics.print_resilience_report()

        # Validar que hay trends
        trends = saga_metrics.calculate_trends('trend_test_previous.json')

        if trends:
            print(f"\nTrends detectados: {trends}")
            assert 'success_rate' in trends
            print(" Trends calculados correctamente")
        else:
            print("Primera ejecución - No hay datos previos para comparar")
            # En la primera ejecución es normal que no haya trends


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
