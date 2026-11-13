# Reconciliation Exception Analysis Reference

This reference describes how to interpret the exception records supplied to
the runtime auditor. It does not add accounting rules or replace the
deterministic controls in `src/orchestrator.py`.

## Current input schema

The application currently loads three synthetic JSON files. Each file has a
top-level `records` array:

| Source | Record ID | Cross-source reference | Amount | Timestamp | Other fields |
|---|---|---|---|---|---|
| `poc_bank` | `bank_id` | `payout_id` | `amount` | `settled_at` | `currency`, optional `account_id`, `customer_id`, optional `description` |
| `poc_gateway` | `gateway_id` | `payout_id` | `gross_amount` | `transaction_at` | `currency` |
| `poc_ledger` | `ledger_id` | `payout_id` | `amount` | `posted_at` | `currency`, optional `account` |

These are PoC field names, not an external bank, gateway, or ledger standard.
The loader requires a non-empty source record ID, `payout_id`, currency,
amount, and timestamp. Record IDs must be unique across all three sources.
Fixtures represent amounts as decimal strings with at most two decimal places;
the loader converts supported numeric/string values to decimal and rejects
sub-cent precision. Timestamps are parsed as UTC. Bank account/customer fields
and descriptive fields are not a cross-source matching key.

The current sample fixtures also include synthetic cases for aggregated
gateway transactions, a one-cent fee discrepancy, a UTC business-date
mismatch, a same-reference currency mismatch, a settlement outside the
configured window, an unmatched ledger row, and a transaction exactly at the
illustrative AML threshold. These scenarios exercise the current PoC; they are
not additional approved accounting policies.

## What the model receives

The application performs its deterministic matching and illustrative AML
screening before calling the model. The model receives only unresolved,
non-quarantined records, serialized with a `source`, `record_id`, and `record`
for each item. It does not receive records already matched or quarantined.
The exception queue may be divided into batches, so a batch is not a complete
copy of any source report and may not contain every record with the same
`payout_id`.

Therefore:

- A missing counterpart in the model input is not proof that the counterpart
  does not exist in the source system.
- Do not infer an orphan from the contents of a batch. The current payload
  contains no source-completeness manifest or proof of a closed reporting
  period. Use an unresolved exception and identify the missing evidence.
- Do not attempt to reinstate or override deterministic matches or AML
  quarantine decisions.

## Evidence-first workflow

For each supplied unresolved item:

1. Read `source`, `record_id`, and the record's exact `payout_id`. Relate items
   only when the exact payout IDs match; do not infer approximate IDs.
2. Compare only facts explicitly present in this batch: source IDs, payout IDs,
   currency strings, amount strings, timestamps, and supplied descriptive
   fields. State which records support each observation.
3. Keep facts separate from possible explanations. If a description suggests
   a cause, label it as unverified and do not treat it as a reconciliation
   result.
4. Do not recalculate fees, create a match, convert currencies, add amount
   tolerances, or apply a date window. The application owns the documented
   deterministic fee, date, and settlement rules.
5. If required information is absent, inconsistent, or split across incomplete
   evidence, report an unresolved exception and name the missing field or
   source evidence. Avoid assigning blame or making a final accounting,
   compliance, or fraud determination.
6. Cite only record IDs included in this batch. If a finding concerns one
   record, use that record ID; include related records only when they are
   actually present and relevant.

## Finding quality

Each exception finding must use the runtime schema:

- `record_ids`: one or more IDs from this batch.
- `payout_id`: the exact supplied payout ID, or `null` only if unavailable.
- `status`: a concise review state, not an invented accounting disposition.
- `reason`: a short factual statement of the mismatch or information gap.
- `details`: an object that identifies source evidence, observed values, and
  missing information where applicable.

Good explanations make the evidence independently checkable, for example:
"Bank record BANK-1 and ledger record LEDGER-1 share payout PAYOUT-1, but the
provided amounts differ (bank 100.00 USD; ledger 99.00 USD). Confirm the
source reports and approved adjustment rules." Do not call either record
orphaned solely because the batch has no third-source record.

For narrative fields, write concise Spanish suitable for the project's
financial analysts unless the user requests another language. Keep JSON keys
and required category names exactly as specified by the schema.

Example shape for a factual exception (illustrative values only):

```json
{
  "record_ids": ["BANK-1", "LEDGER-1"],
  "payout_id": "PAYOUT-1",
  "status": "needs_review",
  "reason": "Los importes informados difieren; falta confirmar la regla de ajuste aplicable.",
  "details": {
    "evidence": [
      {"source": "poc_bank", "record_id": "BANK-1", "amount": "100.00", "currency": "USD"},
      {"source": "poc_ledger", "record_id": "LEDGER-1", "amount": "99.00", "currency": "USD"}
    ],
    "missing_information": ["Regla aprobada para diferencias de importe"]
  }
}
```

The response must still obey the exact JSON contract and category restrictions
in `agent_config/system_prompt.md`. In particular, the model's
`exact_matches`, `fuzzy_fee_matches`, and `compliance_alerts` arrays must be
empty. All counts in `summary` must match the returned arrays.

## Coverage limits

The current payload does not provide authoritative source-system names,
statement-period completeness, settlement status, separate fee entries,
partial-settlement references, FX rates, or approval history. Do not guess
these facts or imply support for production formats not present in the
fixtures. Ask for a synthetic/anonymized schema sample or approved rule when a
requested interpretation depends on them.
