import unittest

from src.reconciliation_pdf import build_reconciliation_pdf


class ReconciliationPdfTests(unittest.TestCase):
    def test_builds_explanatory_pdf_for_all_report_sections(self):
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

        result = build_reconciliation_pdf(
            report,
            sources=["Banco: banco.json", "Pasarela: pasarela.json"],
        )

        self.assertTrue(result.startswith(b"%PDF-"))
        self.assertGreater(len(result), 3000)

    def test_includes_findings_with_special_characters(self):
        report = {
            "report_type": "financial_reconciliation_audit",
            "exact_matches": [],
            "fuzzy_fee_matches": [],
            "reconciliation_exceptions": [
                {
                    "record_ids": ["BANCO-001", "LIBRO-002"],
                    "payout_id": "PAGO-001",
                    "status": "needs_review",
                    "reason": "Diferencia de importe: revisar cuenta & período.",
                    "details": {"currency": "USD", "note": "<dato>"},
                }
            ],
            "orphan_transactions": [],
            "compliance_alerts": [],
            "summary": {
                "exact_matches": 0,
                "fuzzy_fee_matches": 0,
                "reconciliation_exceptions": 1,
                "orphan_transactions": 0,
                "compliance_alerts": 0,
            },
        }

        result = build_reconciliation_pdf(report)

        self.assertTrue(result.startswith(b"%PDF-"))
        self.assertGreater(len(result), 3000)

    def test_rejects_unrecognized_report_type(self):
        with self.assertRaisesRegex(ValueError, "tipo de conciliación"):
            build_reconciliation_pdf({"report_type": "other"})


if __name__ == "__main__":
    unittest.main()
