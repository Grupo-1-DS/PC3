import pytest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from saga.orchestrator import SagaOrchestrator


@pytest.fixture
def saga_orchestrator_instance():
    return SagaOrchestrator()