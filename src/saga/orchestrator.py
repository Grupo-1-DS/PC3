from factory import StepFactory
from state import SagaState
from steps import Step
import time


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

    def send_data(self, raw_data):
        step1 = StepFactory.create("provision_user", data=raw_data)
        step2 = StepFactory.create("assign_permissions", data=raw_data)
        step3 = StepFactory.create("create_quota", data=raw_data)
        self.steps = [step1, step2, step3]

    def execute_saga(self):
        print("☸️ Iniciando Saga Orchestrator...")
        self.state = SagaState.RUNNING

        try:
            for step in self.steps:
                print(f"➡️ Ejecutando paso: {step.name}")

                try:
                    response = step.execute()
                except Exception as e:
                    print(f"❌ Error en {step.name}: {e}")
                    response = {"status": False}

                status = response["status"]

                # ---------- RETRIES ----------
                if not status:
                    for i in range(5):
                        print(f"🔄 Retry {i+1} en {step.name}")

                        try:
                            response = (step.execute())
                        except Exception as e:
                            print(
                                f"❌ Fallo en retry {i+1} de {step.name}: {e}")
                            response = {"status": False}

                        status = response["status"]
                        if status:
                            break

                        time.sleep(2)

                    if not status:
                        print(
                            f"❌ Fallo definitivo en {step.name} tras retries")
                        self.compensate()
                        return

                self.completed.append(step)
            print("✅ Saga completada")
        except Exception as e:
            print(f"❌ Error inesperado en saga: {e}")
            self.compensate()

    def compensate(self):
        print("🔁 Iniciando compensación...")
        self.state = SagaState.COMPENSATING
        for step in reversed(self.completed):
            step.rollback()
        print("✅ Compensación completada")
