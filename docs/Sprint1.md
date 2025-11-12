## Documentación: Steps implementados y patrones usados

Se crearon 3 steps para implementar la saga y demostrar ejecución
y compensación (rollback) sobre un backend simulado (JSON):

- Step 1: ProvisionUser
 	- Qué hace: crea/provisiona un usuario en memoria y lo persiste en
  el store JSON.
 	- Por qué se implementó: simular el primer paso de aprovisionamiento
  de un recurso dependiente (usuario) y generar efectos secundarios
  que deben revertirse si un paso posterior falla.
 	- Entradas (parámetros): `name` (str), `user_id` (str opcional),
  `fail` (bool, para forzar fallo en pruebas).
 	- Salida/efecto: añade `context['user'] = {id, name}` y escribe en
  `src/saga/data/saga_store.json` bajo `users[user_id]`.
 	- Rollback: elimina `context['user']` y borra la entrada del store
  `users[user_id]`.

- Step 2: AssignPermissions
 	- Qué hace: asigna una lista de permisos a un usuario ya creado y
  persiste esa asignación en el store JSON.
 	- Por qué se implementó: representar un paso dependiente que requiere
  que `ProvisionUser` ya haya creado el usuario; sirve para probar la
  coherencia y la compensación cuando falla.
 	- Entradas: `permissions` (list[str], por defecto `['read']`),
  `fail` (bool) para simulación de errores.
 	- Precondición: `context['user']` debe existir; si no, lanza error.
 	- Salida/efecto: añade `context['permissions']` y guarda en el store
  JSON bajo `permissions[user_id]`.
 	- Rollback: elimina `context['permissions']` y borra
  `permissions[user_id]` del store.

- Step 3: CreateQuota
 	- Qué hace: crea/adjunta una cuota al usuario actual y la persiste en
  el store JSON.
 	- Por qué se implementó: simular la creación de un recurso asociado
  (cuota) y validar que también puede revertirse.
 	- Entradas: `quota_values` (dict; por defecto `{'storage_gb':10,...}`),
  `quota_id` (str opcional), `fail` (bool para pruebas).
 	- Precondición: `context['user']` debe existir.
 	- Salida/efecto: añade `context['quota']` y escribe en
  `quotas[quota_id]` del store JSON.
 	- Rollback: elimina `context['quota']` y borra la cuota del store.

Cada Step implementa la interfaz `execute(context)` y
`rollback(context)`. La persistencia usa `src/saga/data/saga_store.json`
como mock backend (lectura/escritura JSON), mediante helpers internos
`_read_store()` / `_write_store()`.

### Patrones implementados

1) Factory
 - Implementación: `src/saga/factory.py` con `StepFactory`.
 - Métodos relevantes:
  - `StepFactory.register(name, step_cls)`: registra una clase de Step
   bajo una clave textual.
  - `StepFactory.create(step_type, *args, **kwargs)`: instancia la
   clase registrada pasando parámetros. Lanza `ValueError` si no
   existe el tipo.
  - `register_defaults()`: función que registra los pasos por defecto
   (`provision_user`, `assign_permissions`, `create_quota`).
 - Por qué: desacopla la creación de objetos Step del orquestador;
  permite construir flujos a partir de nombres y parámetros sin
  depender de clases concretas.

2) Mediator (Orchestrator)
 - Implementación: `src/saga/mediator.py` con la clase `Mediator`.
 - Métodos relevantes:
  - `Mediator.register(step)`: añade una instancia de Step a la
   secuencia de ejecución.
  - `Mediator.execute_all(context)`: ejecuta todos los steps en
   orden. Mantiene una lista `executed` de pasos completados; si un
   step falla, itera `executed` en orden inverso y llama
   `rollback(context)` en cada uno, registrando errores de
   rollback pero sin perdernos el rollback completo. Finalmente
   vuelve a lanzar la excepción original.
 - Por qué: centraliza la coordinación del flujo y garantiza la
  compensación (rollback) en caso de fallo en cualquier paso.

### Ejemplos de uso / comandos (PowerShell)

1) Ejecutar el demo (happy path) usando el orquestador:

```powershell
py -3 -c "from src.saga.orchestrator import run_demo; print(run_demo(False))"
```

2) Ejecutar el script verbose que fuerza fallo en `AssignPermissions`
  (muestra rollback):

```powershell
py -3 scripts\check_rollback_verbose.py
```

3) Ejecutar la suite de tests (pytest):

```powershell
py -3 -m pytest -q
```

- Los Steps persistentes escriben en `src/saga/data/saga_store.json`.
- En los tests se parchea `steps.STORE_PATH` a un `tmp_path` para evitar
 tocar el store real y poder verificar efectos de execute/rollback.

---
