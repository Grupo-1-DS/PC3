# Sprint 1 - Orquestador SAGA con compensación

 **Objetivo:** Implementar un orquestador SAGA básico con al menos 2 pasos que soporten compensación automática.
  
## ¿Qué logramos?

Desarrollamos un orquestador SAGA que gestiona flujos de trabajo distribuidos con capacidad de deshacer cambios cuando algo sale mal. El caso de uso implementado es el aprovisionamiento de usuarios con tres pasos:

1. **Provisionar usuario** - Crea el usuario en la BD
2. **Asignar permisos** - Da permisos al usuario
3. **Crear cuota** - Asigna límites de almacenamiento y operaciones

Si cualquier paso falla, el sistema revierte todos los pasos anteriores automáticamente.

## Componentes desarrollados

### Orquestador (orchestrator.py)

El componente principal que coordina la ejecución de pasos. Tiene lógica de:

+ Estados de saga (PENDING, RUNNING, SUCCEEDED, FAILED, COMPENSATING, COMPENSATED)
+ Ejecución secuencial de pasos
+ Mecanismo de compensación al detectar fallas
+ Reintentos básicos (hasta 5 intentos con sleep de 2s)

### Pasos (steps.py)

Cada paso implementa dos métodos principales:

+ `execute()`: realiza la operación principal
+ `rollback()`: deshace la operación si algo falla después

Los tres pasos creados:

+ ProvisionUser
+ AssignPermissions
+ CreateQuota

Todos se comunican con el broker de mensajes usando RPC.

### Estados (state.py)

Un enum sencillo con los estados posibles del SAGA. Nos ayuda a trackear en qué punto está cada flujo.

### Message Broker (message_broker.py)

Worker que escucha comandos en RabbitMQ y ejecuta operaciones en las bases de datos SQLite (users.db, permissions.db, quotas.db). También maneja las operaciones de rollback.

### Factory (factory.py)

Patrón factory para crear instancias de los pasos según el tipo solicitado.

## Cómo funciona el flujo

1. El orquestador recibe datos del usuario
2. Crea los tres pasos usando el factory
3. Ejecuta cada paso en orden
4. Si un paso falla:
   + Intenta hasta 5 veces
   + Si sigue fallando, inicia compensación
   + Llama al rollback() de cada paso completado en orden inverso
5. Si todo sale bien, marca el SAGA como SUCCEEDED
