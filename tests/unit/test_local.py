from src.saga.orchestrator import run_demo

print("===== SAGA EXITOSA =====")
print(run_demo(fail_assign=False))

print("===== SAGA FALLANDO (rollback) =====")
try:
    run_demo(fail_assign=True)
except Exception as e:
    print("Falló correctamente:", e)
