from orchestrator import SagaOrchestrator

def main():
    saga = SagaOrchestrator()
    saga.send_data(
        provision_data={"id": 1, "name": "Alice", "email": "alice@example.com"},
        permissions_data=["read", "write"], # Necesita el id del ususario
        quota_data={"storage_gb": 20, "ops_per_month": 2000} # Necesita el id del usuario
    )
    saga.execute_saga()

if __name__ == "__main__":
    main()