import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from saga.orchestrator import SagaOrchestrator
from saga.metrics import saga_metrics


@pytest.fixture
def saga_orchestrator_instance():
    return SagaOrchestrator()

@pytest.fixture
def fresh_metrics():
    saga_metrics.reset()
    yield saga_metrics