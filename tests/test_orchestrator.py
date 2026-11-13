import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src import orchestrator


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.fixture_data = orchestrator.load_fixture_data()

    def valid_report_payload(self):
        return {
            "report_type": "financial_reconciliation_audit",
            "exact_matches": [
                {
                    "record_ids": ["POC-BANK-001", "POC-LEDGER-001"],
                    "payout_id": "POC-PAYOUT-EXACT",
                    "status": "exact_match",
                    "reason": "The bank and ledger amounts match.",
                    "details": {"amount": "970.55", "currency": "USD"},
                }
            ],
            "fuzzy_fee_matches": [
                {
                    "record_ids": ["POC-BANK-002", "POC-GW-003"],
                    "payout_id": "POC-PAYOUT-FEE",
                    "status": "fee_match",
                    "reason": "The gateway net matches after fees.",
                    "details": {"net_amount": "485.20"},
                }
            ],
            "reconciliation_exceptions": [],
            "orphan_transactions": [],
            "compliance_alerts": [
                {
                    "rule_id": "large_transaction",
                    "severity": "high",
                    "record_ids": [
                        "POC-BANK-003",
                        "POC-GW-004",
                        "POC-LEDGER-003",
                    ],
                    "payout_ids": ["POC-PAYOUT-AML-LARGE"],
                    "account_id": "POC-ACCOUNT-AML-001",
                    "customer_id": "POC-CUSTOMER-AML-001",
                    "description": "Synthetic amount exceeds the documented threshold.",
                    "human_review_required": True,
                }
            ],
            "summary": {
                "exact_matches": 1,
                "fuzzy_fee_matches": 1,
                "reconciliation_exceptions": 0,
                "orphan_transactions": 0,
                "compliance_alerts": 1,
            },
        }

    def empty_report_payload(self):
        return {
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

    def fake_client(self, response_count):
        completions = [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=json.dumps(self.empty_report_payload())
                        )
                    )
                ]
            )
            for _ in range(response_count)
        ]
        create = unittest.mock.Mock(side_effect=completions)
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create)
            ),
            close=unittest.mock.Mock(),
        )
        return client, create

    def test_context_and_fixture_files_load(self):
        context = orchestrator.load_markdown_context()

        self.assertIn("system_prompt.md", context)
        self.assertIn("reconciliation_analysis.md", context)
        self.assertIn("fuzzy_matching.md", context)
        self.assertIn("aml_fraud_detection.md", context)
        self.assertIn("compliance_aml_rules.md", context)
        self.assertEqual(
            {
                source_name: len(fixture["records"])
                for source_name, fixture in self.fixture_data.items()
            },
            {"poc_bank": 12, "poc_gateway": 11, "poc_ledger": 13},
        )
        self.assertEqual(
            set(self.fixture_data),
            {"poc_bank", "poc_gateway", "poc_ledger"},
        )

    def test_text_extension_files_with_json_content_are_supported(self):
        with tempfile.TemporaryDirectory() as input_dir:
            for source_name, fixture in self.fixture_data.items():
                path = Path(input_dir) / f"{source_name}.txt"
                path.write_text(json.dumps(fixture), encoding="utf-8")

            loaded = orchestrator.load_fixture_data(input_dir)

        self.assertEqual(loaded, self.fixture_data)

    def test_txt_sample_runs_without_calling_the_model(self):
        sample_dir = Path(orchestrator.ROOT_DIR) / "data" / "txt_samples"
        fixture_data = orchestrator.load_fixture_data(sample_dir)
        unused_client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=unittest.mock.Mock())
            )
        )

        with tempfile.TemporaryDirectory() as output_dir:
            report = orchestrator.run_audit(
                fixture_data=fixture_data,
                output_dir=output_dir,
                llm_client=unused_client,
            )

        unused_client.chat.completions.create.assert_not_called()
        self.assertEqual(len(report["exact_matches"]), 2)
        self.assertEqual(len(report["fuzzy_fee_matches"]), 2)
        self.assertEqual(report["reconciliation_exceptions"], [])
        self.assertEqual(report["orphan_transactions"], [])

    def test_expanded_fixtures_cover_reconciliation_edge_cases(self):
        frames = orchestrator.load_dataframes(self.fixture_data)
        aml_alerts = orchestrator.detect_aml_alerts(frames)
        result = orchestrator.run_deterministic_fast_pass(frames, aml_alerts)

        exact_payouts = {item.payout_id for item in result["exact_matches"]}
        fee_matches = {
            item.payout_id: item for item in result["fuzzy_fee_matches"]
        }
        queued_records = {
            (item["source"], item["record_id"])
            for item in result["exception_queue"]
        }

        self.assertIn("POC-PAYOUT-MULTI-GATEWAY", exact_payouts)
        self.assertIn("POC-PAYOUT-LATE-SETTLEMENT", exact_payouts)
        self.assertIn("POC-PAYOUT-AML-BOUNDARY", exact_payouts)
        self.assertIn("POC-PAYOUT-MULTI-GATEWAY", fee_matches)
        self.assertEqual(
            fee_matches["POC-PAYOUT-MULTI-GATEWAY"].record_ids,
            ["POC-BANK-007", "POC-GW-008", "POC-GW-009"],
        )
        self.assertIn("POC-PAYOUT-FEE-DISCREPANCY", exact_payouts)
        self.assertNotIn("POC-PAYOUT-FEE-DISCREPANCY", fee_matches)
        self.assertIn(
            ("poc_gateway", "POC-GW-010"),
            queued_records,
        )
        self.assertNotIn("POC-PAYOUT-DATE-DISCREPANCY", exact_payouts)
        self.assertIn(
            ("poc_bank", "POC-BANK-009"),
            queued_records,
        )
        self.assertNotIn("POC-PAYOUT-CURRENCY-DISCREPANCY", exact_payouts)
        self.assertIn(
            ("poc_ledger", "POC-LEDGER-010"),
            queued_records,
        )
        self.assertNotIn("POC-PAYOUT-LATE-SETTLEMENT", fee_matches)
        self.assertIn(
            ("poc_gateway", "POC-GW-011"),
            queued_records,
        )
        self.assertNotIn(
            "POC-PAYOUT-AML-BOUNDARY",
            {payout_id for alert in aml_alerts for payout_id in alert.payout_ids},
        )

    def test_default_client_is_configured_for_local_ollama(self):
        with patch.dict(
            os.environ,
            {"OPENAI_BASE_URL": "http://localhost:11434/v1"},
            clear=False,
        ):
            client = orchestrator.create_client()

        self.assertEqual(str(client.base_url), "http://localhost:11434/v1/")
        client.close()

    def test_remote_endpoint_is_refused_by_default(self):
        with patch.dict(
            os.environ,
            {
                "OPENAI_BASE_URL": "https://api.groq.com/openai/v1",
                "ALLOW_REMOTE_ENDPOINT": "false",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(ValueError, "Refusing to send"):
                orchestrator.create_client()

    def test_audit_requests_json_mode_and_validates_response(self):
        fake_client, create_call = self.fake_client(response_count=1)

        with tempfile.TemporaryDirectory() as output_dir:
            with (
                patch.object(orchestrator, "load_dotenv"),
                patch.object(orchestrator, "create_client", return_value=fake_client),
                patch.dict(os.environ, {"OPENAI_MODEL": "test-model"}, clear=False),
            ):
                report = orchestrator.run_audit(output_dir=output_dir)

            request = create_call.call_args.kwargs
            saved_reports = list(Path(output_dir).glob("*.json"))

        self.assertEqual(request["temperature"], 0.0)
        self.assertEqual(request["response_format"], {"type": "json_object"})
        self.assertIn(
            "EXCEPTIONS_QUEUE_JSON:",
            request["messages"][1]["content"],
        )
        self.assertNotIn("POC-BANK-001", request["messages"][1]["content"])
        self.assertNotIn("POC-GW-001", request["messages"][1]["content"])
        self.assertNotIn("POC-BANK-003", request["messages"][1]["content"])
        self.assertNotIn("POC-GW-004", request["messages"][1]["content"])
        self.assertEqual(
            {item["payout_id"] for item in report["exact_matches"]},
            {
                "POC-PAYOUT-EXACT",
                "POC-PAYOUT-FEE",
                "POC-PAYOUT-MULTI-GATEWAY",
                "POC-PAYOUT-FEE-DISCREPANCY",
                "POC-PAYOUT-LATE-SETTLEMENT",
                "POC-PAYOUT-AML-BOUNDARY",
            },
        )
        self.assertEqual(
            {item["payout_id"] for item in report["fuzzy_fee_matches"]},
            {
                "POC-PAYOUT-EXACT",
                "POC-PAYOUT-FEE",
                "POC-PAYOUT-MULTI-GATEWAY",
            },
        )
        self.assertEqual(
            {item["rule_id"] for item in report["compliance_alerts"]},
            {"large_transaction", "potential_split_deposits"},
        )
        self.assertEqual(len(saved_reports), 1)

    def test_large_exception_queue_is_split_into_batches_of_ten_to_twenty(self):
        fixture_data = {
            "poc_bank": {
                "records": [
                    {
                        "bank_id": f"BANK-{index:02}",
                        "payout_id": f"PAYOUT-{index:02}",
                        "settled_at": "2026-10-01T10:00:00Z",
                        "amount": "100.00",
                        "currency": "USD",
                        "account_id": f"ACCOUNT-{index:02}",
                        "customer_id": f"CUSTOMER-{index:02}",
                    }
                    for index in range(21)
                ]
            },
            "poc_gateway": {"records": []},
            "poc_ledger": {"records": []},
        }
        fake_client, create_call = self.fake_client(response_count=2)

        with tempfile.TemporaryDirectory() as output_dir:
            with (
                patch.object(orchestrator, "load_dotenv"),
                patch.dict(os.environ, {"OPENAI_MODEL": "test-model"}, clear=False),
            ):
                report = orchestrator.run_audit(
                    fixture_data=fixture_data,
                    output_dir=output_dir,
                    llm_client=fake_client,
                )

        self.assertEqual(create_call.call_count, 2)
        batch_sizes = [
            int(call.kwargs["messages"][1]["content"].split("records: ")[1].split(".")[0])
            for call in create_call.call_args_list
        ]
        self.assertEqual(batch_sizes, [11, 10])
        self.assertEqual(report["exact_matches"], [])
        self.assertEqual(report["summary"]["reconciliation_exceptions"], 0)

    def test_model_cannot_return_deterministic_matches_or_aml_alerts(self):
        response = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(self.valid_report_payload())
                    )
                )
            ]
        )
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=unittest.mock.Mock(return_value=response)
                )
            )
        )
        exception_queue = [
            {
                "source": "poc_bank",
                "record_id": "POC-BANK-002",
                "record": self.fixture_data["poc_bank"]["records"][1],
            }
        ]

        with self.assertRaisesRegex(RuntimeError, "deterministic reconciliation"):
            orchestrator.run_llm_batches(exception_queue, "context", "test-model", client)

    def test_duplicate_payout_records_are_isolated_for_review(self):
        fixture_data = {
            "poc_bank": {
                "records": [
                    {
                        "bank_id": "BANK-1",
                        "payout_id": "PAYOUT-DUPLICATE",
                        "settled_at": "2026-10-01T10:00:00Z",
                        "amount": "100.00",
                        "currency": "USD",
                    },
                    {
                        "bank_id": "BANK-2",
                        "payout_id": "PAYOUT-DUPLICATE",
                        "settled_at": "2026-10-01T10:01:00Z",
                        "amount": "200.00",
                        "currency": "USD",
                    },
                ]
            },
            "poc_gateway": {
                "records": [
                    {
                        "gateway_id": "GATEWAY-1",
                        "payout_id": "PAYOUT-DUPLICATE",
                        "transaction_at": "2026-10-01T09:00:00Z",
                        "gross_amount": "100.00",
                        "currency": "USD",
                    }
                ]
            },
            "poc_ledger": {
                "records": [
                    {
                        "ledger_id": "LEDGER-1",
                        "payout_id": "PAYOUT-DUPLICATE",
                        "posted_at": "2026-10-01T10:00:00Z",
                        "amount": "100.00",
                        "currency": "USD",
                    }
                ]
            },
        }

        frames = orchestrator.load_dataframes(fixture_data)
        result = orchestrator.run_deterministic_fast_pass(
            frames, orchestrator.detect_aml_alerts(frames)
        )

        self.assertEqual(result["exact_matches"], [])
        self.assertEqual(result["fuzzy_fee_matches"], [])
        self.assertEqual(len(result["exception_queue"]), 4)

    def test_quarantined_payout_cannot_appear_in_reconciliation(self):
        report = orchestrator.AuditReport.model_validate(self.valid_report_payload())
        report.fuzzy_fee_matches.append(
            orchestrator.AuditFinding(
                record_ids=["POC-BANK-003"],
                payout_id="POC-PAYOUT-AML-LARGE",
                status="fee_match",
                reason="Should be rejected.",
                details={},
            )
        )

        with self.assertRaisesRegex(ValueError, "quarantined payout"):
            orchestrator.validate_report_consistency(report, self.fixture_data)

    def test_unknown_record_reference_is_rejected(self):
        report = orchestrator.AuditReport.model_validate(self.valid_report_payload())
        report.exact_matches[0].record_ids.append("UNKNOWN-RECORD")

        with self.assertRaisesRegex(ValueError, "unknown source record"):
            orchestrator.validate_report_consistency(report, self.fixture_data)


if __name__ == "__main__":
    unittest.main()
