"""Integration and unit tests for the Agent_Banca FastAPI backend server functions."""

import asyncio
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

from fastapi import HTTPException
from src.api_server import (
    ChatMessageRequest,
    CreateSessionRequest,
    PDFGenerationRequest,
    generate_pdf,
    get_sample_fixtures,
    health_check,
    reconcile_samples,
    set_copilot_backend,
    get_auth_status,
    list_sessions,
    chat_message,
    request_validation_error_handler,
    CopilotBackendError,
)
from fastapi.exceptions import RequestValidationError
from src.copilot_backend import (
    AVAILABLE_SKILLS,
    CopilotAuthStatus,
    CopilotSessionInfo,
)


class ApiServerTests(unittest.TestCase):
    def setUp(self):
        self.mock_backend = MagicMock()
        self.mock_backend.get_auth_status.return_value = CopilotAuthStatus(
            is_authenticated=True,
            login="testuser",
            auth_type="user",
            status_message="OK",
        )
        self.mock_backend.list_sessions.return_value = [
            CopilotSessionInfo(
                session_id="test-session-123",
                summary="Test Session",
                start_time=datetime.now(timezone.utc),
                modified_time=datetime.now(timezone.utc),
            )
        ]
        set_copilot_backend(self.mock_backend)

    def tearDown(self):
        set_copilot_backend(None)

    def test_health_check(self):
        res = health_check()
        self.assertEqual(res.status, "healthy")
        self.assertTrue(res.local_fixtures_available)

    def test_get_sample_fixtures(self):
        fixtures = get_sample_fixtures()
        self.assertIn("poc_bank", fixtures)
        self.assertIn("poc_gateway", fixtures)
        self.assertIn("poc_ledger", fixtures)
        self.assertIn("records", fixtures["poc_bank"])

    def test_reconcile_samples_deterministic(self):
        result = reconcile_samples()
        self.assertTrue(result["success"])
        self.assertIn("report", result)
        summary = result["report"]["summary"]
        self.assertIn("exact_matches", summary)
        self.assertIn("reconciliation_exceptions", summary)
        self.assertGreater(summary["exact_matches"], 0)
        self.assertGreater(summary["fuzzy_fee_matches"], 0)
        self.assertGreater(summary["reconciliation_exceptions"], 0)
        self.assertGreater(summary["orphan_transactions"], 0)
        self.assertGreater(summary["compliance_alerts"], 0)

    def test_chat_validation_error_lists_missing_form_fields(self):
        response = asyncio.run(
            request_validation_error_handler(
                None,
                RequestValidationError(
                    [
                        {
                            "type": "missing",
                            "loc": ("body", "session_id"),
                            "msg": "Field required",
                            "input": None,
                        }
                    ]
                ),
            )
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(
            response.body,
            b'{"detail":"Solicitud de chat incompleta. Faltan los campos: session_id"}',
        )

    def test_generate_pdf_from_report(self):
        result = reconcile_samples()
        report = result["report"]
        sources = result["sources"]
        req = PDFGenerationRequest(report=report, sources=sources)
        pdf_response = generate_pdf(req)
        self.assertEqual(pdf_response.media_type, "application/pdf")
        self.assertTrue(pdf_response.body.startswith(b"%PDF"))

    def test_copilot_auth_and_sessions(self):
        auth = get_auth_status()
        self.assertTrue(auth["is_authenticated"])
        self.assertEqual(auth["login"], "testuser")

        sessions = list_sessions()
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0].session_id, "test-session-123")

    def test_api_defaults_enable_all_selectable_skills(self):
        self.assertEqual(
            CreateSessionRequest().enabled_skills,
            list(AVAILABLE_SKILLS),
        )
        self.assertEqual(
            ChatMessageRequest(
                session_id="test-session-123",
                message="Pregunta de prueba",
            ).enabled_skills,
            list(AVAILABLE_SKILLS),
        )

    def test_chat_runs_sync_copilot_backend_outside_event_loop(self):
        def send_message(**_kwargs):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return "Respuesta de prueba"
            raise AssertionError("El backend síncrono se ejecutó en el event loop")

        self.mock_backend.send_message.side_effect = send_message

        result = asyncio.run(
            chat_message(
                session_id="test-session-123",
                message="Pregunta de prueba",
                skills="reconciliation-engineering",
                attachment=None,
            )
        )

        self.assertEqual(result["assistant_content"], "Respuesta de prueba")

    def test_chat_does_not_return_a_hardcoded_response_when_copilot_is_unavailable(self):
        self.mock_backend.send_message.side_effect = CopilotBackendError(
            "No GitHub OAuth token is available"
        )

        with self.assertRaisesRegex(
            HTTPException,
            "Copilot no está autenticado",
        ):
            asyncio.run(
                chat_message(
                    session_id="test-session-123",
                    message="Pregunta de prueba",
                    skills="reconciliation-engineering",
                    attachment=None,
                )
            )

    def test_chat_attachment_runs_sync_copilot_backend_outside_event_loop(self):
        class TestAttachment:
            filename = "referencia.txt"

            async def read(self):
                return b"contenido de referencia"

        def send_file_message(**_kwargs):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return "Explicación de prueba"
            raise AssertionError("El backend síncrono se ejecutó en el event loop")

        self.mock_backend.send_file_message.side_effect = send_file_message

        result = asyncio.run(
            chat_message(
                session_id="test-session-123",
                message="Explica el archivo",
                skills="reconciliation-engineering",
                attachment=TestAttachment(),
            )
        )

        self.assertEqual(result["assistant_content"], "Explicación de prueba")
        self.mock_backend.send_file_message.assert_called_once_with(
            session_id="test-session-123",
            question="Explica el archivo",
            file_name="referencia.txt",
            file_content="contenido de referencia",
            enabled_skills=["reconciliation-engineering"],
        )


if __name__ == "__main__":
    unittest.main()
