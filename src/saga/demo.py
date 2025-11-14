from orchestrator import SagaOrchestrator

def main():
    data = {
        "user": {"id": 5, "name": "Pepe", "email": "pepe@example.com"},
        "permissions": ["read", "write"],
        "quota": {"storage_gb": 20, "ops_per_month": 2000}
    }

    saga = SagaOrchestrator()
    saga.send_data(data)
    saga.execute_saga()

if __name__ == "__main__":
    main()