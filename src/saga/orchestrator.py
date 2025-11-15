from factory import StepFactory
from state import SagaState
from steps import Step
from metrics import saga_metrics
import time
import pika
import json
import random


class SagaOrchestrator():
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

        saga_metrics.record_saga_start()
        start_time = time.time()

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

                if not status:
                    max_retries = 5
                    base_delay = 1
                    max_delay = 60

                    for i in range(max_retries):

                        saga_metrics.record_retry()

                        # Backoff exponencial: base_delay * (2^i)
                        exponential_delay = base_delay * (2 ** i)

                        # Agregar jitter (aleatoriedad ±25%)
                        jitter = exponential_delay * \
                            0.25 * random.uniform(-1, 1)
                        wait_time = min(exponential_delay + jitter, max_delay)

                        print(f"🔄 Retry {i+1}/{max_retries} en {step.name}")

                        try:
                            response = step.execute()
                        except Exception as e:
                            print(f"❌ Fallo en retry {i+1}: {e}")
                            response = {"status": False}

                        status = response["status"]
                        if status:
                            print(f"✅ Éxito en retry {i+1}")
                            break

                        if i < max_retries - 1:
                            print(
                                f"⏱ Esperando {wait_time:.2f}s antes del siguiente retry...")
                            time.sleep(wait_time)

                    if not status:
                        print(
                            f"❌ Fallo definitivo en {step.name} tras retries")
                        self.send_to_dlq(step, response)
                        self.compensate()

                        execution_time = time.time() - start_time
                        saga_metrics.record_saga_failure(
                            step.name, execution_time)
                        self.state = SagaState.COMPENSATED
                        return

                self.completed.append(step)

            execution_time = time.time() - start_time
            saga_metrics.record_saga_success(execution_time)
            self.state = SagaState.SUCCEEDED
            print("✅ Saga completada")

        except Exception as e:
            print(f"❌ Error inesperado en saga: {e}")
            self.compensate()

            execution_time = time.time() - start_time
            saga_metrics.record_saga_failure("Exception", execution_time)
            self.state = SagaState.COMPENSATED

    def compensate(self):
        compensation_start = time.time()
        print("🔁 Iniciando compensación...")
        self.state = SagaState.COMPENSATING

        for step in reversed(self.completed):
            step.rollback()

        compensation_time = time.time() - compensation_start
        saga_metrics.record_compensation_time(compensation_time)

        print("✅ Compensación completada")

    def send_to_dlq(self, step, last_response):
        """Envía el paso fallido al DLQ para análisis posterior"""
        dlq_message = {
            'type': 'FailedStep',
            'step_name': step.name,
            'step_data': step.data,
            'last_response': last_response,
            'timestamp': time.time(),
            'retry_attempts': 5
        }

        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters('localhost'))
            channel = connection.channel()

            channel.basic_publish(
                exchange='saga_exchange',
                routing_key='saga_dlq',  # Usa el routing_key correcto
                body=json.dumps(dlq_message),
                properties=pika.BasicProperties(
                    delivery_mode=2)  # Mensaje persistente
            )

            connection.close()

            # Registrar mensaje enviado al DLQ
            saga_metrics.record_dlq()
            print(f" Paso fallido enviado a DLQ: {step.name}")
        except Exception as e:
            print(f" Error al enviar a DLQ: {e}")
