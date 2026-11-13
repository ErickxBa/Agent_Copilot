# Agentes y base de conocimiento

Este repositorio contiene dos flujos de agente distintos. Comparten archivos
de contexto, pero no son el mismo agente ni se ejecutan juntos.

## 1. Agente de desarrollo en VS Code

El agente **Conciliacion y auditoria contable** se selecciona manualmente en
Copilot Chat, en el selector **Agents**. No lo inicia `src/orchestrator.py`.
Usa el modelo y la autenticacion que tenga configurados Copilot en VS Code;
`OPENAI_API_KEY`, Ollama y la configuracion `.env` de la aplicacion no controlan
ese chat.

Su contexto de proyecto se compone de:

1. [`.github/copilot-instructions.md`](../.github/copilot-instructions.md):
   instrucciones generales de Copilot para este repositorio.
2. [`.github/agents/conciliacion-auditoria.agent.md`](../.github/agents/conciliacion-auditoria.agent.md):
   rol y comportamiento del agente personalizado.
3. [`.github/skills/reconciliation-engineering/SKILL.md`](../.github/skills/reconciliation-engineering/SKILL.md):
   skill de VS Code descubierta en `.github/skills/` y cargada bajo demanda
   cuando es pertinente. El agente la instruye a cargar para tareas financieras.
   Hay skills especializadas para [validar formatos de fuente](../.github/skills/source-format-validation/SKILL.md),
   [analizar excepciones con evidencia](../.github/skills/exception-evidence-analysis/SKILL.md)
   y [mejorar reportes con trazabilidad](../.github/skills/audit-reporting/SKILL.md);
   tampoco añaden reglas financieras ni soporte de formatos por sí solas.
4. [`CONTEXT.md`](../CONTEXT.md), codigo, pruebas, fixtures y documentos que el
   agente consulte al trabajar.

La skill enlaza las reglas runtime para que el agente de desarrollo las pueda
consultar, pero eso no las convierte en skills de Copilot. Al pedirle al agente
que lea archivos del workspace, su contenido puede formar parte del contexto
enviado al servicio de Copilot conforme a la configuracion y politicas de esa
cuenta. La proteccion `ALLOW_REMOTE_ENDPOINT` de la aplicacion no gobierna el
chat de Copilot.

## 2. Auditor de excepciones de la aplicacion

Este flujo es el programa Python ejecutado manualmente:

```bash
python src/orchestrator.py
```

Secuencia actual:

1. Lee `.env` y carga tres reportes desde `data/` (o desde
   `RECONCILIATION_DATA_DIR`): banco, pasarela y libro mayor. Acepta nombres
   `.json` o `.txt`, pero el contenido de ambos debe ser JSON válido; prefiere
   `.json` si existen las dos extensiones.
2. Valida identificadores, importes, monedas y marcas de tiempo, y construye
   DataFrames en memoria.
3. Ejecuta las reglas deterministas implementadas en
   [`src/orchestrator.py`](../src/orchestrator.py): screening AML ilustrativo,
   cruce banco-libro mayor y cruce de liquidaciones banco-pasarela.
4. Si quedan excepciones no resueltas y no aisladas, envia esas excepciones al
   endpoint OpenAI-compatible configurado, en lotes acotados. Por defecto el
   endpoint es Ollama local en `localhost`; un endpoint remoto se rechaza salvo
   que `ALLOW_REMOTE_ENDPOINT=true` lo habilite explicitamente.
5. Valida el JSON del modelo y sus referencias contra los registros de origen,
   combina sus excepciones con los resultados deterministas y guarda un reporte
   JSON en `output/` (o en `AUDIT_OUTPUT_DIR`).

Si no quedan excepciones que necesiten interpretacion, no se requiere llamar al
modelo. El modelo no calcula conciliaciones deterministas ni reglas AML. Para
cada solicitud al endpoint se construye contexto textual leyendo estos
documentos:

- [`agent_config/system_prompt.md`](../agent_config/system_prompt.md): rol del
  auditor runtime y contrato de salida JSON.
- [`agent_config/skills/reconciliation_analysis.md`](../agent_config/skills/reconciliation_analysis.md):
  esquema de entrada, límites de evidencia por lote y guía de análisis de
  excepciones.
- [`agent_config/skills/fuzzy_matching.md`](../agent_config/skills/fuzzy_matching.md):
  referencia de comisiones y liquidaciones.
- [`agent_config/skills/aml_fraud_detection.md`](../agent_config/skills/aml_fraud_detection.md):
  explicacion de las alertas AML calculadas por la aplicacion.
- [`docs/compliance_aml_rules.md`](compliance_aml_rules.md): reglas AML
  ilustrativas usadas por el codigo y documentacion.

`src/orchestrator.py` concatena estos textos en memoria como mensaje de sistema;
no hay base de datos vectorial, busqueda RAG, entrenamiento ni una base de
conocimiento institucional conectada. Los reportes fuente se envian como
mensaje separado solo cuando hay excepciones. El envio a un endpoint remoto
puede sacar esos registros de la maquina; no se deben usar datos financieros
reales sin aprobacion y controles adecuados. Ollama local tampoco garantiza por
si solo que no haya persistencia en logs.

## 3. Interfaz local para probar el agente personalizado

Para probar desde el navegador el agente de desarrollo sin confundirlo con el
auditor de excepciones, ejecuta desde la raiz:

```bash
streamlit run src/copilot_app.py
```

La interfaz se muestra como **Agent Concilation**; los nombres internos del
repositorio y del contexto de Copilot siguen siendo `Agent_Banca`.

La interfaz usa `src/copilot_backend.py` y el SDK oficial `github-copilot-sdk`.
Comprueba la autenticacion de Copilot CLI sin recibir tokens del navegador,
crea/lista/reanuda sesiones persistidas por el SDK, y carga el agente y skills
del workspace. En la API FastAPI, las operaciones síncronas de chat se ejecutan
en un thread pool para no bloquear el event loop mientras el backend espera al
SDK asíncrono. El modelo es el configurado por Copilot CLI; no es el modelo
`OPENAI_MODEL` de la aplicacion ni implica que `llama3.1` se use en este chat.
La respuesta de cada turno se obtiene del evento final devuelto por el SDK.
Si el SDK divide la respuesta en partes, se reconstruye usando solo eventos con
el mismo identificador de mensaje; no se reutiliza una respuesta anterior si el
turno actual no produjo contenido visible.

La lista permitida de herramientas es de solo lectura (`view`, `grep` y
`glob`); no se ofrecen shell ni herramientas de edicion. La interfaz presenta
un aviso y requiere confirmacion antes de habilitar el chat. Aun asi, los
mensajes y el contenido del repositorio que lea el agente pueden procesarse por
Copilot bajo las politicas de la cuenta del usuario. Usa datos sinteticos. La
proteccion `ALLOW_REMOTE_ENDPOINT` solo aplica al flujo OpenAI-compatible del
auditor runtime, no a esta integracion.
El servidor Streamlit se configura para escuchar solo en `127.0.0.1`.
La apariencia del workspace se centraliza en `src/assets/global.css`, y la
skill `ui-ux-design-system` documenta cómo mantener los tokens y patrones
accesibles de la interfaz. Los colores base de `.streamlit/config.toml` deben
mantenerse alineados.

Esta herramienta sirve para probar el agente de desarrollo. No ejecuta la
conciliacion financiera, no consume automáticamente los fixtures ni constituye
una interfaz de revision de reportes para analistas.

La aplicación ofrece dos cargas separadas:

- **Explicar archivo:** adjunta un `.txt` o `.json` de hasta 1 MiB desde el
  icono de clip integrado en el compositor del chat. El archivo y la pregunta
  se envían en el mismo turno; si solo se adjunta, se solicita una explicación
  general. El contenido se valida y el backend lo trata como dato no confiable.
- **Conciliar reportes:** carga un archivo para cada fuente sintética (banco,
  pasarela y libro mayor), también `.txt` o `.json`, de hasta 1 MiB cada uno.
  Los tres archivos deben contener JSON con un arreglo superior `records` y
  cumplir el esquema actual validado por `src/orchestrator.py`. La UI muestra
  cuántas fuentes faltan y solo habilita la acción con tres archivos y la
  confirmación de privacidad. Si una fuente cambia después de conciliar, el
  resultado anterior se descarta para evitar mostrar un reporte desactualizado.
  Los archivos se escriben temporalmente. La UI presenta un PDF explicativo
  con el significado de cada sección, los conteos y las referencias observadas;
  el JSON detallado sigue disponible en una sección avanzada. Las explicaciones
  del PDF son texto fijo de la aplicación, no una evaluación generada por el
  modelo. Excepciones, alertas AML ilustrativas y posibles huérfanas siguen
  requiriendo revisión humana. Las excepciones no resueltas pueden enviarse al
  endpoint del orquestador, sujeto a `ALLOW_REMOTE_ENDPOINT`.

El espacio de trabajo organiza el acceso y las cuatro skills del asistente en
`Fuentes`, el diálogo en el panel central y el objetivo/límites en `Studio`.
Desde `Fuentes` se pueden activar o desactivar las skills de conciliación,
formatos, evidencia de excepciones y reportes. La skill de UI/UX se conserva
para desarrollo, pero se deshabilita en sesiones de chat de la aplicación. Los
controles se traducen a `disabled_skills` del Copilot SDK para nuevas sesiones
y turnos. Esto controla la disponibilidad de las skills, pero no constituye
evidencia de que se hayan utilizado en una respuesta. La conciliación conserva
su vista aparte; sus métricas se acompañan de secciones expandibles con
registros de origen, estados, motivos y detalles para revisión.

El agente personalizado recibe instrucciones para limitarse al proyecto
Agent_Banca y tratar los archivos como datos, no como instrucciones. Esta
restricción es una guía para el modelo, no un filtro determinista que garantice
que el modelo jamás responda fuera de tema.

## Fuentes de verdad y limites

- El **codigo y las pruebas** determinan el comportamiento ejecutable actual.
- `CONTEXT.md` resume ese comportamiento y sus limitaciones; no implementa
  reglas por si mismo.
- Los fixtures en `data/` son sinteticos. No definen formatos oficiales de
  bancos, pasarelas, libros mayores o bancos centrales.
- Las instrucciones AML son ejemplos del PoC, no politica regulatoria
  aprobada.
- El objetivo del producto incluye extractos del banco central, pero todavia
  no se especifican institucion, formato externo, reglas contables aprobadas,
  volumen objetivo, controles productivos ni criterios completos de aceptacion.
- No existe interfaz para revisar reportes de conciliacion ni gestion de casos
  implementada. El reporte JSON requiere revision posterior; la interfaz
  Streamlit solo permite probar el agente de desarrollo.

No se deben confundir los prompts runtime de `agent_config/` con la
configuracion de Copilot en `.github/`, ni describir el PoC como sistema de
produccion o de procesamiento masivo.

## Probar con archivos `.txt`

`data/txt_samples/` contiene tres ejemplos sintéticos con extension `.txt` y
contenido JSON. Para ejecutarlos desde la raiz del repositorio:

```bash
RECONCILIATION_DATA_DIR=data/txt_samples python src/orchestrator.py
```

Ese conjunto de ejemplo tiene todas sus transacciones conciliadas mediante las
reglas deterministas actuales; por eso guarda un reporte sin requerir Ollama ni
otro endpoint de modelo. Estos archivos no son texto libre, CSV ni formatos
oficiales de una institución.
