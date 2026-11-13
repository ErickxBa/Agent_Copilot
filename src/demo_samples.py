"""Offline synthetic responses used only by the sample dashboard."""

import json
from types import SimpleNamespace


class DemoSampleClient:
    """Return bounded, pre-authored findings for the visual sample flow."""

    def __init__(self):
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(create=self._create_completion)
        )

    def _create_completion(self, **request):
        prompt = request["messages"][1]["content"]
        batch_json = prompt.split("EXCEPTIONS_QUEUE_JSON:\n", 1)[1]
        batch = json.loads(batch_json)
        records = {item["record_id"] for item in batch}

        report = {
            "report_type": "financial_reconciliation_audit",
            "exact_matches": [],
            "fuzzy_fee_matches": [],
            "reconciliation_exceptions": [],
            "orphan_transactions": [],
            "compliance_alerts": [],
            "summary": {
                "exact_matches": 0,
                "fuzzy_fee_matches": 0,
                "reconciliation_exceptions": 0,
                "orphan_transactions": 0,
                "compliance_alerts": 0,
            },
        }

        exception_ids = {
            "DEMO-BANK-003",
            "DEMO-GW-003",
            "DEMO-LEDGER-003",
        }
        if exception_ids.issubset(records):
            report["reconciliation_exceptions"].append(
                {
                    "record_ids": sorted(exception_ids),
                    "payout_id": "DEMO-PAYOUT-003",
                    "status": "amount_difference",
                    "reason": (
                        "El importe del banco y del libro mayor es de 125.00 "
                        "USD, mientras que el importe bruto de la pasarela "
                        "es de 130.00 USD antes de las comisiones."
                    ),
                    "details": {
                        "bank_amount": "125.00",
                        "ledger_amount": "125.00",
                        "gateway_gross_amount": "130.00",
                        "evidence": "Synthetic demonstration records",
                    },
                }
            )

        if "DEMO-BANK-004" in records:
            report["orphan_transactions"].append(
                {
                    "record_ids": ["DEMO-BANK-004"],
                    "payout_id": "DEMO-PAYOUT-004",
                    "status": "possible_orphan",
                    "reason": (
                        "El lote de demostración sintético completo no contiene "
                        "una transacción equivalente en la pasarela ni en el "
                        "libro mayor para este pago."
                    ),
                    "details": {
                        "source_coverage": "complete_demo_batch",
                        "amount": "220.00",
                        "currency": "USD",
                        "human_review_required": True,
                    },
                }
            )

        report["summary"]["reconciliation_exceptions"] = len(
            report["reconciliation_exceptions"]
        )
        report["summary"]["orphan_transactions"] = len(
            report["orphan_transactions"]
        )
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(report))
                )
            ]
        )
