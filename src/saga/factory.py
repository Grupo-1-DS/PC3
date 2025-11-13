"""Factory para crear instancias de Steps por nombre.

Permite registrar clases de Step y crear instancias con kwargs.
"""
from typing import Dict, Type
from .steps import Step
from . import steps


class StepFactory:
    _registry: Dict[str, Type[Step]] = {}

    @classmethod
    def register(cls, name: str, step_cls: Type[Step]) -> None:
        cls._registry[name] = step_cls

    @classmethod
    def create(cls, step_type: str, *args, **kwargs) -> Step:
        step_cls = cls._registry.get(step_type)
        if not step_cls:
            raise ValueError(f"Unknown step type: {step_type}")
        return step_cls(*args, **kwargs)


def register_defaults() -> None:
    StepFactory.register("provision_user", steps.ProvisionUser)
    StepFactory.register("assign_permissions", steps.AssignPermissions)
    StepFactory.register("create_quota", steps.CreateQuota)
