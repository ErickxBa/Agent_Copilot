import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.copilot_backend import CopilotAuthStatus


ROOT_DIR = Path(__file__).resolve().parents[1]
APP_PATH = ROOT_DIR / "src" / "copilot_app.py"


class CopilotAppTests(unittest.TestCase):
    def test_reconciliation_flow_guides_files_consent_and_report(self):
        app = AppTest.from_file(str(APP_PATH)).run()

        self.assertFalse(app.exception)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Espacio de trabajo", "Conciliar reportes"],
        )
        self.assertTrue(
            any(item.value == "Agent Concilation" for item in app.title)
        )
        self.assertTrue(
            all(
                any(heading in item.value for item in app.markdown)
                for heading in ("Fuentes", "Conversación", "Studio")
            )
        )
        submit_button = next(
            button
            for button in app.button
            if button.label == "Validar y conciliar"
        )
        self.assertTrue(submit_button.disabled)

        source_by_label = {
            "Reporte de banco": "poc_bank",
            "Reporte de pasarela": "poc_gateway",
            "Reporte de libro mayor": "poc_ledger",
        }
        for uploader in app.get("file_uploader"):
            source = source_by_label[uploader.label]
            uploader.set_value(
                (
                    f"{source}.txt",
                    (
                        ROOT_DIR
                        / "data"
                        / "txt_samples"
                        / f"{source}.txt"
                    ).read_bytes(),
                    "text/plain",
                )
            )
        app.run()
        self.assertTrue(
            next(
                button
                for button in app.button
                if button.label == "Validar y conciliar"
            ).disabled
        )

        app.session_state["reconciliation_data_consent"] = True
        app.run()
        self.assertFalse(
            next(
                button
                for button in app.button
                if button.label == "Validar y conciliar"
            ).disabled
        )
        next(
            button
            for button in app.button
            if button.label == "Validar y conciliar"
        ).click().run()

        self.assertFalse(app.exception)
        self.assertFalse(app.error)
        self.assertTrue(
            any(
                "Proceso completado" in item.value
                and "badge-success status-message" in item.value
                for item in app.markdown
            )
        )
        self.assertTrue(
            any(
                item.label == "Descargar reporte detallado (JSON)"
                for item in app.get("download_button")
            )
        )
        self.assertTrue(
            any(
                item.label == "Descargar informe explicado (PDF)"
                for item in app.get("download_button")
            )
        )
        self.assertTrue(
            any("Detalle por categoría" in item.value for item in app.markdown)
        )
        self.assertTrue(
            any(
                item.label.startswith("Coincidencias exactas ·")
                for item in app.get("expander")
            )
        )
        bank_upload = next(
            uploader
            for uploader in app.get("file_uploader")
            if uploader.label == "Reporte de banco"
        )
        bank_upload.set_value(
            ("changed.txt", b'{"records":[]}', "text/plain")
        ).run()
        self.assertFalse(
            any(
                item.label == "Descargar reporte detallado (JSON)"
                for item in app.get("download_button")
            )
        )
        self.assertFalse(
            any(
                item.label == "Descargar informe explicado (PDF)"
                for item in app.get("download_button")
            )
        )
        self.assertTrue(
            any(
                "resultado anterior se descartó" in item.value
                and "badge-info status-message" in item.value
                for item in app.markdown
            )
        )

    def test_design_tokens_and_single_stylesheet_injection(self):
        app = AppTest.from_file(str(APP_PATH)).run()
        css_path = ROOT_DIR / "src" / "assets" / "global.css"
        css = css_path.read_text(encoding="utf-8")
        for token in (
            "--color-tcs-white",
            "--color-surface-subtle",
            "--color-tcs-black-900",
            "--color-tcs-gray-700",
            "--color-tcs-gray-100",
            "--color-tcs-blue",
            "--color-tcs-yellow",
            "--color-tcs-green",
            "--color-tcs-red",
            "--color-tcs-orange",
        ):
            self.assertIn(token, css)
        self.assertEqual(APP_PATH.read_text(encoding="utf-8").count("<style>"), 1)
        self.assertFalse(app.exception)

    def test_chat_composer_has_file_attachment_and_skill_controls(self):
        app = AppTest.from_file(str(APP_PATH))
        app.session_state["auth_status"] = CopilotAuthStatus(
            is_authenticated=True,
            login="synthetic-user",
            auth_type="github",
            status_message=None,
        )
        app.session_state["current_session_id"] = "synthetic-session"
        app.session_state["copilot_processing_consent"] = True
        app.run()

        self.assertFalse(app.exception)
        self.assertEqual(len(app.chat_input), 1)
        self.assertTrue(app.chat_input[0].proto.accept_file)
        self.assertTrue(
            any(item.label == "Conciliación y auditoría" for item in app.toggle)
        )
        self.assertEqual(
            {item.label for item in app.toggle},
            {
                "Conciliación y auditoría",
                "Fuentes y formatos",
                "Excepciones y evidencia",
                "Reportes y trazabilidad",
            },
        )


if __name__ == "__main__":
    unittest.main()
