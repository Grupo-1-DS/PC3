"""Factory para crear instancias de Steps por nombre.

Permite registrar clases de Step y crear instancias con kwargs.
"""
from typing import Dict, Type
from .steps import Step


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
    from . import steps as _steps
    StepFactory.register("provision_user", _steps.ProvisionUser)
    StepFactory.register("assign_permissions", _steps.AssignPermissions)
    StepFactory.register("create_quota", _steps.CreateQuota)


try:
    register_defaults()
except Exception:
    pass
