import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.copilot_uploads import (
    MAX_UPLOAD_SIZE_BYTES,
    UploadValidationError,
    decode_text_upload,
    parse_explanation_upload,
    run_uploaded_reconciliation,
)


ROOT_DIR = Path(__file__).resolve().parents[1]


class CopilotUploadTests(unittest.TestCase):
    def test_text_upload_decodes_utf8_and_rejects_unsupported_extensions(self):
        self.assertEqual(
            decode_text_upload("nota.txt", "Conciliación".encode("utf-8")),
            "Conciliación",
        )

        with self.assertRaisesRegex(UploadValidationError, r"\.txt o \.json"):
            decode_text_upload("nota.csv", b"contenido")

    def test_json_explanation_requires_valid_json(self):
        explanation = parse_explanation_upload("datos.json", b'{"records":[]}')

        self.assertEqual(json.loads(explanation), {"records": []})
        with self.assertRaisesRegex(UploadValidationError, "JSON válido"):
            parse_explanation_upload("datos.json", b"{mal formado")

    def test_upload_rejects_empty_oversized_and_non_utf8_content(self):
        for file_name, content in (
            ("vacio.txt", b""),
            ("grande.txt", b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)),
            ("binario.txt", b"\xff"),
        ):
            with self.subTest(file_name=file_name):
                with self.assertRaises(UploadValidationError):
                    decode_text_upload(file_name, content)

    def test_reconciliation_uploads_run_offline_and_write_a_report(self):
        sample_dir = ROOT_DIR / "data" / "txt_samples"
        files = {
            source: (f"{source}.txt", (sample_dir / f"{source}.txt").read_bytes())
            for source in ("poc_bank", "poc_gateway", "poc_ledger")
        }

        with tempfile.TemporaryDirectory() as output_dir:
            with patch(
                "src.orchestrator.run_llm_batches",
                side_effect=AssertionError("Sample upload must not call a model"),
            ):
                report = run_uploaded_reconciliation(
                    files,
                    output_dir=output_dir,
                )

            self.assertEqual(
                report["report_type"],
                "financial_reconciliation_audit",
            )
            self.assertEqual(report["summary"]["reconciliation_exceptions"], 0)
            self.assertEqual(report["summary"]["orphan_transactions"], 0)
            self.assertEqual(
                len(list(Path(output_dir).glob("financial_reconciliation_audit_*.json"))),
                1,
            )

    def test_reconciliation_requires_all_three_sources(self):
        with self.assertRaisesRegex(UploadValidationError, "exactamente un archivo"):
            run_uploaded_reconciliation({})

    def test_orchestrator_import_works_with_streamlit_script_path(self):
        repository_root = ROOT_DIR.as_posix()
        script = f"""
import sys
from pathlib import Path
repository_root = Path({repository_root!r}).resolve()
sys.path = [
    entry for entry in sys.path
    if Path(entry or ".").resolve() != repository_root
]
sys.path.insert(0, str(repository_root / "src"))
from copilot_uploads import _load_orchestrator
load_fixture_data, run_audit = _load_orchestrator()
assert load_fixture_data.__module__ == "orchestrator"
assert run_audit.__module__ == "orchestrator"
"""
        subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT_DIR,
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
