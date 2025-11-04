import time

class SagaOrchestrator:
    def __init__(self):
        self.state = "PENDIENTE"
        self.steps = [
            "FIRST STEP",
            "SECOND STEP"
        ]
        self.compensations = []

    def execute(self):
        print("Inciando orquestador SAGA...")
        self.state = "EN PROCESO"
        try:
            for step in self.steps:
                print(f"Ejecutando pas: {step.name}")
                step.execute()
                self.compensations.append(step)
            self.state = "COMPLETADO"
            print("✓ SAGA completada con exito")
        except Exception as e:
            print(f"Fallo encontrado: {e}")
            self.compensate()
            self.state = "COMPENSADO"

    def compensate(self):
        print("Inciando compensación...")
        self.state = "COMPENSANDO"
        for step in reversed(self.compensations):
            step.compensate()
        print("✓ Compensación completada")