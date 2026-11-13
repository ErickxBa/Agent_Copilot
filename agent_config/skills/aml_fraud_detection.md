# AML Screening Rules Reference

The application evaluates these rules deterministically before calling the
language model. `docs/compliance_aml_rules.md` is the authoritative threshold
source. The model must not re-screen records, add alerts, or override the
application's quarantine decisions.

The rules are included in the model context only to explain an existing
application-generated alert when relevant. Compare only exact supplied
identifiers, same-currency amounts, and supplied records.

For every triggering pattern, the application:

- Return a `compliance_alerts` item using the required system-prompt schema.
- Identify every participating bank record ID and payout ID; also identify
  related gateway and ledger record IDs when present.
- Name the matching rule (`large_transaction`,
  `potential_split_deposits`, or `velocity_anomaly`) and describe the observed
  facts. Do not characterize a flag as proof of fraud or wrongdoing.
- Set `human_review_required` to `true`.
- Quarantine the flagged payouts and all their related source records from
  ordinary matching, exception, and orphan categories.

The model's batch response must contain an empty `compliance_alerts` array.
If a record is ambiguous or necessary information is missing, describe the
limitation as an unresolved reconciliation exception rather than inventing or
duplicating an AML alert.
