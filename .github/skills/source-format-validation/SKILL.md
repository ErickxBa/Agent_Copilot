---
name: source-format-validation
description: Use when reviewing financial source samples, their schemas, or input validation without assuming unsupported file formats.
---

# Validación de fuentes y formatos

Use this skill to inspect source records and the application's input
validation before proposing ingestion or adapter changes.

## Workflow

1. Read `CONTEXT.md`, `src/orchestrator.py`, the relevant tests, and synthetic
   fixtures before describing supported inputs.
2. Compare an available sample with the fields, types, identifiers, currency,
   amount, and timestamp rules implemented by the project.
3. Separate observed sample properties from proposed requirements. Report
   missing, inconsistent, or unsupported fields explicitly.
4. For a new external or central-bank source, ask for its institution,
   jurisdiction, official format/version, field definitions, and a synthetic
   or anonymized sample before designing an adapter.
5. Add offline validation tests for any approved schema change.

## Boundaries

- The current fixtures are synthetic JSON with a top-level `records` array;
  they do not establish support for any institution's official statement.
- Do not invent source schemas, identifiers, date/time-zone conversions,
  currency mappings, amount tolerances, or normalization rules.
- Never ask for credentials or real financial records. Do not claim a format
  is supported until implementation and representative tests verify it.
