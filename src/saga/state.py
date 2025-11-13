from enum import Enum, auto


class SagaState(Enum):
    PENDING = auto()
    RUNNING = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    COMPENSATING = auto()
    COMPENSATED = auto()


class Saga:
    def __init__(self, saga_id: str):
        self.id = saga_id
        self.state = SagaState.PENDING
        self.error: str | None = None

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
