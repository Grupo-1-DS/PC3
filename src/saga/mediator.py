"""Mediator/Orchestrator que coordina la ejecución de Steps.

Provee ejecución secuencial con rollback en caso de fallo.
"""
from typing import Any, Dict
import logging


class Mediator:
    def __init__(self):
        self._steps = []
        self._logger = logging.getLogger(__name__)

    def register(self, step) -> None:
        self._steps.append(step)

    def execute_all(self, context: Dict[str, Any]) -> Dict[str, Any]:
        executed = []
        for step in self._steps:
            step_name = step.__class__.__name__
            try:
                self._logger.info("Executing step: %s", step_name)
                step.execute(context)
                executed.append(step)
                self._logger.info("Step succeeded: %s", step_name)
            except Exception as exc:
                self._logger.error("Step failed: %s -> %s", step_name, exc)

                for s in reversed(executed):
                    try:
                        name = s.__class__.__name__
                        self._logger.info("Rolling back step: %s", name)
                        s.rollback(context)
                        self._logger.info("Rollback succeeded: %s", name)
                    except Exception:

                        self._logger.exception(
                            "Rollback failed for step: %s",
                            s.__class__.__name__,
                        )
                raise
        return context
