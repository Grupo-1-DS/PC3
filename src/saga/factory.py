from typing import Dict, Type
from .steps import Step, ProvisionUser, AssignPermissions, CreateQuota

class StepFactory:
    @classmethod
    def create(cls, step_type: str, *args, **kwargs) -> Step:
        step_types = {
            "provision_user": ProvisionUser,
            "assign_permissions": AssignPermissions,
            "create_quota": CreateQuota,
        }
        step = step_types.get(step_type)
        if not step:
            raise ValueError(f"Tipo de paso desconocido: {step_type}")
        return step(*args, **kwargs)
