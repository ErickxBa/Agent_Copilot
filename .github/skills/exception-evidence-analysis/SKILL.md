---
name: exception-evidence-analysis
description: Use when analyzing reconciliation discrepancies, match candidates, or possible orphans while preserving source evidence and batch limits.
---

# Análisis de excepciones y evidencia

Use this skill to explain current reconciliation results or review changes to
exception analysis. Ground every conclusion in records and behavior present in
the repository.

## Workflow

1. Inspect the current implementation, report contract, tests, and the
   relevant source records.
2. Distinguish deterministic matches, observed discrepancies, unverified
   match candidates, unresolved exceptions, and evidence-backed orphans.
3. Cite the exact source record IDs and observed fields supporting each
   finding. Label possible causes as hypotheses, not facts.
4. Identify missing source coverage or fields and state what evidence is
   needed to resolve the exception.

## Boundaries

- A missing counterpart in an incomplete file or model batch does not prove an
  orphan. Require explicit evidence of source completeness and absence.
- Do not override deterministic matching, invent accounting rules, add
  tolerances, convert currencies, or join records using approximate IDs.
- Preserve human review for unresolved findings; do not make final accounting
  or compliance decisions.
