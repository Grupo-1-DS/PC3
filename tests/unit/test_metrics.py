from saga.metrics import saga_metrics
from saga.orchestrator import SagaOrchestrator
import sys
import os
import uuid
import pytest


sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../../src')))


@pytest.fixture
def fresh_metrics():
    saga_metrics.reset()
    yield saga_metrics


def run_saga(name, email, fail_config):
    data = {
        "user": {"id": str(uuid.uuid4()), "name": name, "email": email},
        "permissions": ["read", "write"],
        "quota": {"storage_gb": 20, "ops_per_month": 2000},
        "fail": fail_config
    }
    saga = SagaOrchestrator()
    saga.send_data(data)
    saga.execute_saga()


class TestSagaMetrics:

    def test_successful_saga(self, fresh_metrics):
        run_saga("Alice", "alice@test.com", [False, False, False])

        report = fresh_metrics.get_report()
        assert report['total_sagas'] == 1
        assert report['success_rate'] == "100.00%"
        assert report['compensation_rate'] == "0.00%"
        assert report['total_dlq_messages'] == 0

    @pytest.mark.parametrize("fail_config,expected_step", [
        ([False, False, True], "CreateQuota"),
        ([False, True, False], "AssignPermissions"),
    ])
    def test_failed_sagas(self, fresh_metrics, fail_config, expected_step):
        run_saga("User", "user@test.com", fail_config)

        report = fresh_metrics.get_report()
        assert report['success_rate'] == "0.00%"
        assert report['compensation_rate'] == "100.00%"
        assert report['total_dlq_messages'] == 1
        assert expected_step in report['step_failures']

    def test_metrics_tracking(self, fresh_metrics):
        run_saga("Bob", "bob@test.com", [False, False, True])

        report = fresh_metrics.get_report()
        assert report['avg_execution_time'] != "0.00s"
        assert report['avg_compensation_time'] != "0.00s"
        assert float(report['avg_retries_per_saga']) > 0


class TestMetricsIntegration:
    def test_full_metrics_report(self, fresh_metrics):
        print("\n" + "="*70)
        print("📊 GENERANDO REPORTE COMPLETO DE MÉTRICAS")
        print("="*70)

        # 3 exitosos
        run_saga("Alice", "alice@test.com", [False, False, False])
        run_saga("Charlie", "charlie@test.com", [False, False, False])
        run_saga("Eve", "eve@test.com", [False, False, False])

        # 2 fallidos
        run_saga("Bob", "bob@test.com", [False, False, True])
        run_saga("Diana", "diana@test.com", [False, True, False])

        # Imprimir reporte
        fresh_metrics.print_report()
        fresh_metrics.save_to_file('test_saga_metrics.json')

        # Validaciones
        report = fresh_metrics.get_report()
        assert report['total_sagas'] == 5
        assert report['success_rate'] == "60.00%"
        assert report['compensation_rate'] == "40.00%"
        assert report['total_dlq_messages'] == 2

        print("\nTest completado")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
