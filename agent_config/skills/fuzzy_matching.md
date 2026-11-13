# Gateway Fee and Settlement Reference

The application applies these rules deterministically before sending unresolved
records to the language model. The model may use this document to explain an
exception, but must not recalculate fees, create a fee match, or override the
application result.

Use only exact `payout_id` joins. Reconcile transactions in the same currency;
do not apply these rules to a cross-currency amount without an explicitly
provided conversion rule.

For each gateway transaction:

1. Calculate the percentage fee as `gross_amount * 0.029`.
2. Round that fee to cents using decimal `ROUND_HALF_UP`.
3. Subtract the fixed fee of `0.30` in the transaction currency.
4. Round each transaction's net amount to cents, then sum the transaction nets
   for the payout.
5. A fee match requires exact equality to the bank settlement amount to the
   cent; do not create an amount tolerance.

The settlement timestamp must be at or after the gateway transaction time and
within an inclusive 48-hour settlement window. A payout outside this window
is a discrepancy even if its net amount matches.

Clearly distinguish a bank-to-ledger exact match from a bank-to-gateway
fuzzy/fee match. Report amount or timing discrepancies for human review.
