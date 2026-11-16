# Registro de decisiones

Se actualiza durante todo el proyecto. Cuando una decisión cambia, se agrega una fila nueva
indicando la entrega en que cambió y el motivo; las filas anteriores se conservan.

| Fecha | Decisión | Alternativa elegida | Alternativas consideradas | Motivo | Entrega |
|---|---|---|---|---|---|
| 2026-11-15 | Objetivo | Predecir los pasos del día siguiente por usuario | Recomendar recetas según actividad; comparar calorías consumidas y gastadas | Variable observable en los datos; apoya una decisión concreta (recordatorio matinal) | E1 |
| 2026-11-15 | Modelo operacional | Relacional, con la vinculación separada del reloj | Vinculación como atributo del reloj | Permite el historial de cambios de reloj (15 usuarios) y la regla de un reloj activo | E1 |
| 2026-11-15 | Mediciones | Serie temporal fuera de la base OLTP | Tabla relacional en la base de la app | 15,5 M de filas en 61 días; se leen por reloj y rango de tiempo | E1 |
| 2026-11-15 | Modelo analítico | Esquema en estrella con dos hechos (actividad diaria y comida) | Una sola tabla de hechos | Evita mezclar las granularidades usuario-día y comida | E1 |
| 2026-11-15 | Datos crudos | Archivos originales en almacenamiento de objetos | Cargar directo a tablas | Trazabilidad y reprocesamiento | E1 |
| 2026-11-15 | Datos limpios | Parquet particionado por fecha local de medición | CSV; partición por fecha de recepción | Compresión, lectura columnar y poda por fecha | E1 |
| 2026-11-15 | Arquitectura | Lakehouse | Data Warehouse; Data Lake sin capas | Separa las capas cruda, limpia y analítica a bajo costo | E1 |
| 2026-11-15 | Escala | Procesamiento local (DuckDB/pandas) | Spark | 115 MB comprimidos; no hay evidencia que justifique distribuir | E1 |
| 2026-11-15 | Deduplicación | Clave (device_id, ts_medicion) | Fila completa | 300.015 duplicados llegan con otra hora de recepción | E1 |
| 2026-11-15 | Temporalidad | UTC, más fecha local según la vinculación | Solo UTC | Asignar los pasos al día correcto del usuario | E1 |
| 2026-11-15 | Validación ML | Corte por ts_recepcion y separación temporal 42/9/9 días | Separación aleatoria | Evita la fuga por lecturas que llegan tarde | E1 |
| 2026-11-16 | Días sin lecturas | Calendario continuo por usuario; objetivos sin cobertura mínima excluidos del entrenamiento | Rellenar con cero pasos; usar LEAD sobre las filas con datos | Un día sin reloj no equivale a 0 pasos; las ventanas deben ser de 7 días calendario | E1 |
