# Instrucciones de Copilot para Agent_Banca

## Contexto obligatorio

- Lee `CONTEXT.md` antes de proponer o implementar cambios de comportamiento.
- Para tareas de conciliacion y auditoria, usa el agente
  `.github/agents/conciliacion-auditoria.agent.md` cuando este disponible.
- Para implementar o revisar el flujo financiero, consulta y aplica la skill
  `reconciliation-engineering` de `.github/skills/`. Las skills se descubren
  desde esa ubicacion y se cargan bajo demanda; el agente debe invocarla en
  tareas pertinentes, no asumir que sus instrucciones ya estan en contexto.
- Para tareas específicas de formatos de entrada, evidencia de excepciones o
  reportes, carga respectivamente `source-format-validation`,
  `exception-evidence-analysis` o `audit-reporting` desde `.github/skills/`.
  Son guías de ingeniería: no habilitan formatos ni agregan reglas financieras
  por sí mismas.
- Para cambios de UI/UX, consulta la skill `ui-ux-design-system` de
  `.github/skills/` y centraliza los estilos del app Streamlit en
  `src/assets/global.css`.
- Distingue las instrucciones de desarrollo de Copilot de
  `agent_config/system_prompt.md`: este ultimo es el contrato del modelo en
  tiempo de ejecucion, no una especificacion para modificar el codigo.
- Consulta las referencias enlazadas por la skill, especialmente
  `CONTEXT.md`, la implementacion, las pruebas y las reglas de
  `agent_config/skills/`. Los documentos bajo `agent_config/` son contexto del
  modelo de auditoria en ejecucion; no son skills de Copilot ni se ejecutan
  automaticamente como agente de desarrollo.
- El objetivo de producto es cruzar reportes de pasarelas, libro mayor y
  extractos del banco central, identificar diferencias y huerfanos verificables
  y producir reportes para analistas. Es un objetivo, no una capacidad que el
  PoC ya haya demostrado. No afirmes cumplimiento o soporte sin implementacion
  y validacion.

## Reglas de trabajo

- Inspecciona la implementacion, las pruebas y la documentacion relacionada
  antes de editar. Conserva los cambios existentes y no elimines ni reemplaces
  archivos del proyecto para simplificar una implementacion.
- No inventes formatos de reportes, identificadores, reglas contables,
  tolerancias, conversiones de moneda, calendarios, ventanas de liquidacion ni
  requisitos regulatorios. Si la decision afecta resultados, formula preguntas
  concretas al usuario antes de codificarla.
- Mantén la aritmetica financiera, las reglas de conciliacion y los controles
  de integridad deterministas. Usa el modelo solo donde el flujo actual lo
  permita y valida cada salida antes de utilizarla.
- Distingue coincidencias probadas, discrepancias, candidatos y transacciones
  huerfanas. La ausencia en un archivo o lote parcial no demuestra por si sola
  que una transaccion sea huerfana.
- Presenta reportes con referencias a registros de origen y evidencia
  verificable; no conviertas una hipotesis del modelo en un hecho contable.
- Trata las reglas AML actuales como fixtures ilustrativos, no como politica
  regulatoria aprobada. Conserva la revision humana y no automatices pagos,
  asientos, bloqueos de cuentas ni presentaciones regulatorias.
- Usa datos sinteticos. Respeta las protecciones existentes contra envio remoto
  de informacion financiera; no habilites endpoints remotos por defecto ni
  incluyas secretos o datos reales en codigo, logs, prompts o pruebas.
- Sigue los patrones y dependencias ya presentes. Haz cambios acotados, agrega
  pruebas para el comportamiento nuevo y actualiza la documentacion afectada.
- Mantén CI y validaciones offline; no hagas llamadas a modelos externos ni
  requieras credenciales para las pruebas.
- Verifica que las personalizaciones de agente sigan los formatos de VS Code:
  agentes en `.github/agents/*.agent.md`, skills de workspace en
  `.github/skills/<nombre>/SKILL.md`, e instrucciones generales en
  `.github/copilot-instructions.md`. Mantén cada conocimiento en su capa y
  valida enlaces, carga de contexto y escenarios de uso.

## Criterio de terminado

Resume lo que cambio, las reglas o supuestos que aplicaste, las pruebas
ejecutadas y los requisitos que quedan pendientes. No afirmes soporte para
formatos de extractos del banco central, procesamiento masivo ni uso en
produccion hasta que exista implementacion y validacion representativa.