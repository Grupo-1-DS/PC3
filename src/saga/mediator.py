from typing import Any, Dict
import logging

from .state import Saga
from .utils.ids import generate_saga_id
from .utils.retry import retry_with_backoff


class Mediator:
    def __init__(self):
        self._steps = []
        self._logger = logging.getLogger(__name__)

    def register(self, step) -> None:
        self._steps.append(step)

    @retry_with_backoff(max_retries=3, base_delay=0.3)
    def _execute_step(self, step, context):
        return step.execute(context)

    def execute_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        saga = Saga(generate_saga_id())
        context["_saga_id"] = saga.id

        self._logger.info(f"SAGA {saga.id} starting")
        saga.start()

        executed = []

        try:
            for step in self._steps:
                step_name = step.__class__.__name__
                self._logger.info(f"[{saga.id}] Step start: {step_name}")

                # Ejecuta el step real
                result = self._execute_step(step, context)

                # Lista para rollback
                executed.append(step)

            saga.succeed()
            return context

        except Exception as exc:
            saga.fail(str(exc))
            saga.start_compensation()

            self._logger.error(f"SAGA failed: {exc}")

            # rollback en orden inverso
            for s in reversed(executed):
                try:
                    s.rollback(context)
                except Exception:
                    self._logger.exception("Rollback failed!")

            saga.compensated()

            # No mandamos DLQ desde aquí porque
            # DLQ real pertenece al Worker/Consumer, no al Mediator.

            raise
