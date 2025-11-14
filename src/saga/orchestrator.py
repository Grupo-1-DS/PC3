from saga.mediator import StepMediator
from saga.factory import StepFactory

class SagaOrchestrator:
    def __init__(self):
        self.state = "PENDING"
        self.mediator = StepMediator()
        self.steps = [
            StepFactory.create_step("provision_user"),
            StepFactory.create_step("assign_permissions")
        ]
        self.completed = []

    def execute(self):
        print("🔄 Iniciando Saga Orchestrator...")
        self.state = "RUNNING"
        try:
            for step in self.steps:
                print(f"➡️ Ejecutando paso: {step.name}")
                self.mediator.execute(step)
                self.completed.append(step)
            self.state = "SUCCEEDED"
            print("✅ Saga completada exitosamente")
        except Exception as e:
            print(f"❌ Fallo en {step.name}: {e}")
            self._compensate()
            self.state = "COMPENSATED"

    def _compensate(self):
        print("♻️ Iniciando compensación...")
        self.state = "COMPENSATING"
        for step in reversed(self.completed):
            step.compensate()
        print("🔁 Compensación completada")
