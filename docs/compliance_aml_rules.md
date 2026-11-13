# Mock AML Compliance Rules

These are illustrative screening rules for synthetic proof-of-concept data.
They produce review alerts only; they do not establish criminal intent,
constitute a suspicious activity report, or authorize blocking an account.
Production thresholds and escalation must be approved by the institution's
compliance function and applicable law.

## Alert rules

- **Large transaction:** flag a single cash-like deposit or transfer strictly
  greater than USD 10,000.00. A transaction equal to USD 10,000.00 does not
  meet this rule by itself.
- **Potential split deposits:** flag three or more deposits, each strictly
  below USD 10,000.00, whose combined amount is strictly greater than
  USD 10,000.00, when made to the same account by the same customer within an
  inclusive rolling 60-minute window.
- **Velocity anomaly:** flag five or more deposits to the same account by the
  same customer within an inclusive rolling 60-minute window, regardless of
  individual amount.

Only compare amounts in the same currency. Do not compare or aggregate
different currencies without a trusted conversion rate supplied in the input.
When currency or identity information is missing, describe the limitation
rather than assuming equivalence.

For each alert, identify the rule, involved bank record IDs, account/customer
identifiers when present, currency, and a concise factual explanation.
Quarantine the affected payout and related bank, gateway, and ledger records
from ordinary reconciliation; list them under compliance alerts rather than
calling them reconciled or orphaned. Require human review before any action.
