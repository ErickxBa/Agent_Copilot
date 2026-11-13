---
name: audit-reporting
description: Use when improving reconciliation reports, source traceability, or analyst-facing explanations while preserving the implemented report contract.
---

# Reportes y trazabilidad

Use this skill to review or improve the presentation and traceability of
reconciliation findings for analyst review.

## Workflow

1. Inspect the existing report schema, its validation, consumers, and tests
   before proposing changes.
2. Keep each finding linked to exact source record IDs and the evidence
   supporting its status and explanation.
3. Separate confirmed results, discrepancies, candidates, missing evidence,
   and unresolved questions. Make uncertainty visible.
4. Preserve source references through report generation and exports; add
   offline tests for any approved contract change.

## Boundaries

- Do not invent report fields, categories, dispositions, or accounting policy.
  Ask before changing an output contract that affects consumers.
- Do not present an unverified hypothesis as a fact or a possible orphan as
  proven without complete-source evidence.
- Reports support analyst review; they do not authorize payments, ledger
  postings, account restrictions, or regulatory submissions.
