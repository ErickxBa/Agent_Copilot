---
name: reconciliation-engineering
description: Use when implementing, debugging, reviewing, or documenting this repository's bank, payment-gateway, ledger, AML-screening, reconciliation, exception-reporting, or scale-validation workflows.
---

# Reconciliation engineering for Agent_Banca

Use this skill for engineering work on the financial-reconciliation
application. It provides project context and a safe workflow; it does not
replace repository-wide Copilot instructions or the runtime model prompt.

## Read the source of truth

Before changing behavior, read:

- [Project context](../../../CONTEXT.md): product objective, implemented
  behavior, known limits, configuration, and unresolved requirements.
- [Repository Copilot instructions](../../copilot-instructions.md): mandatory
  engineering, privacy, and validation rules.
- [Orchestrator](../../../src/orchestrator.py) and the affected
  [tests](../../../tests/): executable behavior and contracts.
- [Runtime auditor prompt](../../../agent_config/system_prompt.md): model
  input/output contract. Do not treat it as the development-agent prompt.
- [Runtime reconciliation analysis reference](../../../agent_config/skills/reconciliation_analysis.md):
  current input schema, batch evidence limits, and finding-quality guidance.
- [Runtime fee and settlement instructions](../../../agent_config/skills/fuzzy_matching.md)
  and [runtime AML instructions](../../../agent_config/skills/aml_fraud_detection.md):
  rules passed into the application model.
- [Illustrative AML rules](../../../docs/compliance_aml_rules.md): synthetic
  thresholds only, not an approved compliance policy.

The `agent_config/skills/` files are runtime model context. They are not VS Code
Agent Skills and are not automatically discovered as skills by Copilot.
Workspace Agent Skills live under `.github/skills/<skill-name>/SKILL.md`.
When changing the runtime auditor's context, update the relevant
`agent_config/` reference and verify `load_markdown_context()` includes it.

## Engineering workflow

1. Compare the request with `CONTEXT.md`, source code, fixtures, and tests.
   Clearly separate implemented PoC behavior from approved business policy.
2. Ask only unresolved questions that would change matching outcomes, source
   adapters, data handling, or acceptance criteria. Request synthetic or
   anonymized examples only; never request credentials or real financial data.
3. Keep monetary calculations and matching controls deterministic, exact, and
   auditable. Preserve source record IDs and evidence in findings.
4. Do not infer an orphan from a missing record in a partial batch. Do not
   invent tolerances, FX rates, accounting rules, source formats, or regulatory
   requirements.
5. Preserve endpoint privacy guards, human review, offline tests, and current
   fixture compatibility unless a confirmed requirement explicitly changes
   them.
6. Add focused tests for behavior changed; update `CONTEXT.md` and related
   documentation whenever supported behavior or limits change. For scale work,
   benchmark representative synthetic data and verify result integrity, memory,
   and runtime before making throughput claims.
7. Report what changed, validation performed, assumptions, and requirements
   that remain unconfirmed. Never claim the full product objective or
   production readiness based on a high-level description alone.

## Focused skills

Load the relevant focused skill in addition to this general workflow:

- [Source format validation](../source-format-validation/SKILL.md) for source
  schemas, input validation, and prospective adapters.
- [Exception evidence analysis](../exception-evidence-analysis/SKILL.md) for
  evidence-backed discrepancies, candidates, and possible orphans.
- [Audit reporting](../audit-reporting/SKILL.md) for report contracts and
  source traceability.

## Questions to resolve when relevant

Consult the unresolved items in `CONTEXT.md` first; do not ask the user to
repeat information already established there. Depending on the task, clarify:

- Which institution/system and version supplies each source, and its
  synthetic/anonymized sample format.
- Which central bank institution/jurisdiction and official statement format
  are in scope; verify schemas and accounting semantics before implementing an
  adapter.
- Stable IDs and mappings for amount, currency, dates/time zones, settlement,
  commissions, status, duplicates, partial settlements, and missing references.
- Approved cross-source matching order, tolerances, and FX policy.
- Expected file/record volumes, frequency, concurrency, time/memory limits,
  and representative synthetic benchmark data.
- Required report schema/destination/retention and analyst review workflow.
- Deployment, access, encryption, residency, retention, and whether any
  external model is permitted.
- Applicable approved AML policy, compliance owner, human-review process, and
  measurable acceptance criteria for the product objective.
- Required failure, retry, repeat-run/idempotency, and interrupted-run behavior.

Do not treat the PoC's fee, date, AML, or duplicate handling as business
approval; describe it as current implementation unless the user confirms it.

## Validate the agent itself

The custom agent is an engineering assistant; its prompt cannot prove that the
application reconciles correctly. In VS Code, select **Conciliacion y
auditoria contable** in the Copilot Chat agent selector and run a new chat for
each smoke test. Confirm it reads this skill and repository context, uses tools
to inspect the actual files, and does not invent unsupported behavior.

Suggested smoke prompts and expected behavior:

1. "Resume que acepta hoy el aplicativo, como se ejecuta y que no soporta."
   It should cite the three synthetic JSON inputs and distinguish current
   behavior from the product goal.
2. "Integra un extracto del banco central" without a sample or rules. It should
   ask for the official format and relevant matching semantics before changing
   reconciliation behavior.
3. "Mide si procesa un millon de registros." It should propose a representative
   synthetic benchmark and measure memory, time, and result integrity; it must
   not claim scale based on the tiny fixtures.
4. "Revisa un cambio de codigo." It should inspect related implementation and
   tests, identify evidence-backed issues, and run focused offline validation
   when it edits behavior.

For application behavior, also run the offline suite documented in
`CONTEXT.md`. Passing that suite verifies covered code paths only; it does not
prove that a hosted Copilot agent followed every instruction, nor that
unimplemented input formats or scale targets work.
