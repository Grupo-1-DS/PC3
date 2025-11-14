from typing import Any, Dict
from abc import ABC
from steps import Step


class Mediator(ABC):
    def __init__(self):
        self.registered_steps = []
    def register_step(self, step: Step) -> None:
        self.registered_steps.append(step)