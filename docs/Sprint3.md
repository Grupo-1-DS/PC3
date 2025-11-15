# Sprint 3 - E2E con caos y trends

## Lo que se hizo

### 1. Sistema de trends

Ahora las métricas comparan con la ejecución anterior y muestran si mejoraron o empeoraron:

```
 Trends (comparado con ejecución anterior):
   📈 success_rate: mejora
   📈 retries: mejora
```

### 2. Informe de resiliencia

Reporte específico con métricas de recuperación:

- Tasa de recuperación (% de fallos que se compensaron bien)
- MTTR (Mean Time To Recovery)
- Mensajes en DLQ
- Reintentos promedio

### 3. Tests E2E con caos controlado

Nuevos tests que simulan:

- Fallos en diferentes pasos
- Múltiples SAGAs con mix de éxitos/fallos
- Comparación de trends entre ejecuciones

## Cómo ejecutar

### Ver informe de resiliencia con trends

```bash
# Ejecutar tests E2E con caos
pytest tests/e2e/test_e2e_chaos.py -v -s
```

Al final muestra:

```
  INFORME DE RESILIENCIA
Total de fallos:              2
Tasa de recuperación:         100.00%
MTTR (tiempo recuperación):   0.15s
Mensajes en DLQ:              2
Reintentos promedio:          5.00

 Trends (comparado con ejecución anterior):
   📈 success_rate: mejora
   📉 retries: empeora
```

### Generar trends manualmente

```bash
# Primera ejecución
cd src
python -m saga

# Segunda ejecución (trends automáticos)
python -m saga
```

El demo ahora guarda historial automáticamente y muestra trends si existe ejecución previa.

## Archivos nuevos

- `tests/e2e/test_e2e_chaos.py` - Tests E2E con caos
- Métodos nuevos en `metrics.py`:
  - `calculate_trends()` - Compara con ejecución anterior
  - `get_resilience_report()` - Genera informe de resiliencia
  - `print_resilience_report()` - Muestra informe con trends
  - `save_with_history()` - Guarda preservando historial

## Tipos de caos probados

1. **Fallo en paso 1** - Sin compensación (falla antes de hacer nada)
2. **Fallo en paso 2** - Compensa 1 paso
3. **Fallo en paso 3** - Compensa 2 pasos

## Métricas de resiliencia

- **Tasa de recuperación**: % de SAGAs fallidos que se compensaron exitosamente
- **MTTR**: Tiempo promedio que toma hacer rollback
- **Trends**: Compara con ejecución anterior (mejora/empeora/igual)

## Ejemplo de output

```bash
$ pytest tests/e2e/test_e2e_chaos.py::TestResilienceWithTrends -v -s

--- Ejecución 1: Escenario con más fallos ---
Tasa de éxito: 33.33%

--- Ejecución 2: Escenario mejorado ---
Tasa de éxito: 66.67%

  INFORME DE RESILIENCIA
Total de fallos:              1
Tasa de recuperación:         100.00%

 Trends:
   📈 success_rate: mejora    (de 33.33% a 66.67%)
   📈 retries: mejora
```

## Comandos útiles

```bash
# Tests E2E con caos
pytest tests/e2e/test_e2e_chaos.py -v -s

# Solo test de trends
pytest tests/e2e/test_e2e_chaos.py::TestResilienceWithTrends -v -s

# Limpiar archivos de historial
rm *_previous.json
```
