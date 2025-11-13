import uuid


def generate_saga_id() -> str:
    return str(uuid.uuid4())
