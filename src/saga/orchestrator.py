from factory import StepFactory
from state import SagaState
from steps import Step

class Saga:
    def __init__(self, saga_id: str):
        self.id = saga_id
        self.state = SagaState.PENDING

    def start(self):
        self.state = SagaState.RUNNING

    def succeed(self):
        self.state = SagaState.SUCCEEDED

    def fail(self, error: str):
        self.state = SagaState.FAILED
        self.error = error

    def start_compensation(self):
        self.state = SagaState.COMPENSATING

    def compensated(self):
        self.state = SagaState.COMPENSATED


class SagaOrchestrator(Saga):
    def __init__(self):
        self.state = SagaState.PENDING
        self.steps = []
        self.completed = []

    def send_data(self, provision_data, permissions_data, quota_data):
        step1 = StepFactory.create("provision_user", data=provision_data)
        step2 = StepFactory.create("assign_permissions", permissions=permissions_data)
        step3 = StepFactory.create("create_quota", quota_values=quota_data)
        self.steps = [step1, step2, step3]

    def execute_saga(self):
        print("☸️ Iniciando Saga Orchestrator...")
        self.state = SagaState.RUNNING
        try:
            for step in self.steps:
                print(f"➡️ Ejecutando paso: {step.name}")
                step.execute()
                self.completed.append(step)
            self.state = SagaState.SUCCEEDED
            print("✅ Saga completada exitosamente")
        except Exception as e:
            print(f"❌ Fallo en {step.name}: {e}")
            self.compensate()
            self.state = SagaState.COMPENSATED

    def compensate(self):
        print("🔁 Iniciando compensación...")
        self.state = SagaState.COMPENSATING
        print(self.completed)
        for step in reversed(self.completed):
            step.rollback()
        print("✅ Compensación completada")
