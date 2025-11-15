# Sprint 2 - Métricas y reintentos mejorados

## Lo que se hizo

### 1. Sistema de métricas (metrics.py)

Ahora el sistema registra automáticamente:

- Cuántos SAGAs se ejecutaron
- Cuántos tuvieron éxito/fallaron
- Tiempos de ejecución
- Cantidad de reintentos
- Qué pasos fallan más

Genera un archivo `saga_metrics.json` con toda la info.

### 2. Dead Letter Queue (DLQ)

Cuando un paso falla después de intentarlo 5 veces, el mensaje se va a una cola especial (DLQ) para revisarlo después.

### 3. Backoff exponencial

Antes esperábamos siempre 2 segundos entre reintentos. Ahora:

- Retry 1: 1s
- Retry 2: 2s
- Retry 3: 4s
- Retry 4: 8s
- Retry 5: 16s

Esto evita bombardear el sistema cuando hay problemas.

### 4. Tests automatizados

Creamos tests con `pytest.mark.parametrize` que validan:

- SAGAs exitosos
- SAGAs con fallos en diferentes pasos
- Que las métricas se registren bien

## Cómo ejecutar

### Ver las métricas con tests

```bash
# Ejecutar tests (genera métricas de 5 SAGAs)
pytest tests/unit/test_metrics.py -v -s
```

Al final muestra un reporte como este:

```
Total SAGAs ejecutados:       5
Tasa de éxito:                60.00%
Tasa de compensación:         40.00%
Tiempo promedio ejecución:    12.45s
Reintentos promedio:          4.00
Mensajes en DLQ:              2

Pasos que más fallan:
   - CreateQuota: 1 veces
   - AssignPermissions: 1 veces
```

### Ver el demo en acción

Terminal 1 - Broker:

```bash
cd src
python -m saga.message_broker
```

Terminal 2 - Demo:

```bash
cd src
python -m saga
```

El demo ejecuta 2 SAGAs (1 exitoso, 1 con fallo) y al final muestra el reporte de métricas.

## Archivos nuevos

- `src/saga/metrics.py` - Maneja todo el tracking
- `tests/unit/test_metrics.py` - Tests con parametrize
- `src/saga/__main__.py` - Para ejecutar con `python -m saga`

## Diferencias con Sprint 1

Antes:

- Reintentos con espera fija (2s)
- Sin métricas
- Sin DLQ
- Tests básicos

Ahora:

- Backoff exponencial inteligente
- Métricas completas y automáticas
- DLQ para mensajes fallidos
- Tests con parametrize

## Comandos útiles

```bash
# Ejecutar tests
pytest tests/unit/test_metrics.py -v -s

# Ejecutar demo
cd src && python -m saga

# Ver métricas guardadas
cat saga_metrics.json
```
