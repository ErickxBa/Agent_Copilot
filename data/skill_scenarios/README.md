# Escenarios sinteticos para probar las skills

Estos archivos contienen datos ficticios para adjuntarlos al chat de Copilot
o para usarlos como material de una demostracion. No contienen datos reales y
no representan formatos oficiales de ningun banco.

## Escenarios

- `source_format_validation.json`: muestra valida y un caso invalido por
  campos faltantes para pedir una revision de esquema.
- `exception_evidence_analysis.json`: incluye una diferencia de monto y una
  contraparte ausente, pero declara que la cobertura de la fuente es
  incompleta. La skill debe evitar afirmar que existe una transaccion
  huerfana.
- `audit_reporting.json`: incluye hallazgos con referencias exactas a
  registros, evidencia observada y preguntas pendientes para una explicacion
  de analista.
- `reconciliation_engineering_scale.json`: muestra un pequeno lote sintetico
  con metadatos de medicion para discutir un benchmark. No demuestra
  procesamiento masivo.

## Prompts sugeridos

1. Adjunta `source_format_validation.json` y pregunta: "Compara el caso
   valido e invalido con el esquema actual y enumera los campos faltantes."
2. Adjunta `exception_evidence_analysis.json` y pregunta: "Clasifica cada
   hallazgo, cita los IDs y explica que evidencia falta antes de llamarlo
   huerfano."
3. Adjunta `audit_reporting.json` y pregunta: "Redacta una ficha de auditoria
   separando hechos, hipotesis y preguntas pendientes."
4. Adjunta `reconciliation_engineering_scale.json` y pregunta: "Propone una
   prueba offline de escala sin afirmar que este lote demuestra produccion."

Estos escenarios sirven para probar el comportamiento del agente. La
conciliacion ejecutable continua usando los tres fixtures de `data/` con
formato JSON y arreglo superior `records`.

El boton `Probar con Muestras` del dashboard usa el conjunto separado
`data/demo_samples/`. Ese conjunto esta conectado a un cliente offline
preautorizado para mostrar todas las tarjetas con datos sinteticos. La
excepcion y la transaccion posible huérfana son hallazgos de demostracion y
requieren revision humana; no representan una regla contable aprobada.
