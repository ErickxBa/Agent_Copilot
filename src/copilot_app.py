"""Streamlit interface for testing the custom Copilot agent locally."""

from datetime import datetime
import hashlib
from html import escape
import json
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from copilot_backend import (
    CopilotAuthStatus,
    CopilotBackend,
    CopilotBackendError,
    CopilotSessionInfo,
)
from copilot_uploads import (
    MAX_UPLOAD_SIZE_MB,
    UploadProcessingError,
    UploadValidationError,
    parse_explanation_upload,
    run_uploaded_reconciliation,
)
from reconciliation_pdf import build_reconciliation_pdf


SKILL_CONTROLS = (
    (
        "reconciliation-engineering",
        "Conciliación y auditoría",
        "Guía de ingeniería financiera del proyecto.",
        "skill_reconciliation_enabled",
    ),
    (
        "source-format-validation",
        "Fuentes y formatos",
        "Revisa estructuras y validaciones sin asumir formatos oficiales.",
        "skill_source_format_enabled",
    ),
    (
        "exception-evidence-analysis",
        "Excepciones y evidencia",
        "Distingue discrepancias, candidatos y posibles huérfanos con evidencia.",
        "skill_exception_evidence_enabled",
    ),
    (
        "audit-reporting",
        "Reportes y trazabilidad",
        "Prioriza referencias de origen, evidencia y revisión analista.",
        "skill_audit_reporting_enabled",
    ),
)


@st.cache_resource
def get_backend() -> CopilotBackend:
    return CopilotBackend()


def _enabled_skills() -> list[str]:
    return [
        skill_id
        for skill_id, _, _, state_key in SKILL_CONTROLS
        if st.session_state[state_key]
    ]


def _session_label(session: CopilotSessionInfo) -> str:
    summary = session.summary or "Conversación sin resumen"
    return f"{summary[:70]} · {session.modified_time:%Y-%m-%d %H:%M}"


def _upload_signature(
    files: tuple[tuple[str, Any], ...],
) -> tuple[tuple[str, str, str], ...]:
    return tuple(
        (
            source,
            file.name,
            hashlib.sha256(file.getvalue()).hexdigest(),
        )
        for source, file in files
        if file is not None
    )


def _show_auth_status(status: CopilotAuthStatus | None) -> None:
    if status is None:
        _show_status("info", "Comprueba la autenticación para conectar con Copilot.")
    elif status.is_authenticated:
        identity = f" como `{status.login}`" if status.login else ""
        _show_status("success", f"Copilot autenticado{identity}.")
    else:
        detail = f" {status.status_message}" if status.status_message else ""
        _show_status(
            "warning",
            "No se detectó una sesión autenticada de Copilot."
            f"{detail} Ejecuta `copilot` en una terminal y completa el inicio "
            "de sesión solicitado."
        )


def _show_status(kind: str, message: str) -> None:
    status_styles = {
        "info": ("badge-info", "i", "status"),
        "success": ("badge-success", "✓", "status"),
        "warning": ("badge-warning", "!", "status"),
        "danger": ("badge-danger", "×", "alert"),
    }
    if kind not in status_styles:
        raise ValueError(f"Unknown status kind: {kind}")
    class_name, icon, role = status_styles[kind]
    st.markdown(
        f'<div class="badge {class_name} status-message" role="{role}">'
        f'<span class="status-indicator" aria-hidden="true">{icon}</span>'
        f"<span>{escape(message)}</span></div>",
        unsafe_allow_html=True,
    )


def _apply_enterprise_styles() -> None:
    css_path = Path(__file__).parent / "assets" / "global.css"
    css = css_path.read_text(encoding="utf-8")
    st.html(f"<style>{css}</style>")


def _render_report_details(report: dict[str, Any]) -> None:
    categories = (
        (
            "Coincidencias exactas",
            "exact_matches",
            "Registros que coinciden según las reglas deterministas actuales.",
        ),
        (
            "Coincidencias de tarifa",
            "fuzzy_fee_matches",
            "Liquidaciones que coinciden aplicando las reglas PoC de tarifa.",
        ),
        (
            "Excepciones",
            "reconciliation_exceptions",
            "Diferencias que necesitan comprobación con las fuentes originales.",
        ),
        (
            "Posibles huérfanas",
            "orphan_transactions",
            "La falta de contraparte en un lote parcial no confirma por sí sola "
            "que un registro sea huérfano.",
        ),
        (
            "Alertas AML ilustrativas",
            "compliance_alerts",
            "Son reglas de prueba, no una política regulatoria ni una conclusión "
            "sobre una persona o transacción.",
        ),
    )
    st.markdown("#### Detalle por categoría")
    for label, key, explanation in categories:
        items = report[key]
        with st.expander(f"{label} · {len(items)}"):
            st.caption(explanation)
            if not items:
                st.write("No se encontraron elementos en esta categoría.")
                continue
            for index, item in enumerate(items, start=1):
                with st.container(border=True):
                    if key == "compliance_alerts":
                        st.markdown(f"**Alerta {index}**")
                        st.text(f"Regla: {item['rule_id']}")
                        st.text(f"Severidad reportada: {item['severity']}")
                        st.text(
                            "Registros: " + ", ".join(item["record_ids"])
                        )
                        st.text("Payouts: " + ", ".join(item["payout_ids"]))
                        st.text(f"Descripción: {item['description']}")
                        st.caption("Requiere revisión humana.")
                    else:
                        st.markdown(f"**Hallazgo {index}**")
                        st.text(
                            "Payout: "
                            + str(item.get("payout_id") or "No especificado")
                        )
                        st.text(
                            "Registros de origen: "
                            + ", ".join(item["record_ids"])
                        )
                        st.text(f"Estado: {item['status']}")
                        st.text(f"Motivo: {item['reason']}")
                        if item.get("details"):
                            st.caption("Evidencia y valores")
                            st.json(item["details"], expanded=False)


def _render_reconciliation_upload() -> None:
    st.markdown("### Conciliar reportes de prueba")
    st.caption(
        "Carga los tres reportes sintéticos y descarga un resumen del cruce."
    )
    with st.expander("¿Qué estructura deben tener los archivos?"):
        st.markdown(
            "Cada archivo debe ser JSON con un arreglo `records`. Un archivo "
            ".txt también debe contener JSON; no se admiten CSV ni formatos "
            "bancarios externos."
        )
        st.code(
            """Banco:       bank_id, payout_id, currency, amount, settled_at
Pasarela:    gateway_id, payout_id, currency, gross_amount, transaction_at
Libro mayor: ledger_id, payout_id, currency, amount, posted_at""",
            language="text",
        )
        st.caption("Tamaño máximo: 1 MB por archivo. Usa datos sintéticos.")

    st.markdown("#### 1. Carga los archivos")
    bank_file = st.file_uploader(
        "Reporte de banco",
        type=["txt", "json"],
        key="reconciliation_bank_file",
        max_upload_size=MAX_UPLOAD_SIZE_MB,
        help="Campos: bank_id, payout_id, currency, amount, settled_at.",
    )
    gateway_file = st.file_uploader(
        "Reporte de pasarela",
        type=["txt", "json"],
        key="reconciliation_gateway_file",
        max_upload_size=MAX_UPLOAD_SIZE_MB,
        help="Campos: gateway_id, payout_id, currency, gross_amount, transaction_at.",
    )
    ledger_file = st.file_uploader(
        "Reporte de libro mayor",
        type=["txt", "json"],
        key="reconciliation_ledger_file",
        max_upload_size=MAX_UPLOAD_SIZE_MB,
        help="Campos: ledger_id, payout_id, currency, amount, posted_at.",
    )
    selected_files = (
        ("Banco", bank_file),
        ("Pasarela", gateway_file),
        ("Libro mayor", ledger_file),
    )
    current_signature = _upload_signature(selected_files)
    if (
        st.session_state.get("uploaded_reconciliation_signature")
        and st.session_state.uploaded_reconciliation_signature != current_signature
    ):
        st.session_state.pop("uploaded_reconciliation_report", None)
        st.session_state.pop("uploaded_reconciliation_pdf", None)
        st.session_state.pop("uploaded_reconciliation_signature", None)
        st.session_state.pop("uploaded_reconciliation_sources", None)
        _show_status(
            "info",
            "Cambió una fuente; el resultado anterior se descartó.",
        )

    ready_count = sum(file is not None for _, file in selected_files)
    if ready_count == len(selected_files):
        _show_status(
            "info",
            "3 de 3 fuentes seleccionadas; aún falta validar el contenido.",
        )
    else:
        _show_status("info", f"{ready_count} de 3 fuentes seleccionadas.")

    with st.expander("Privacidad y procesamiento"):
        st.info(
            "El cruce se ejecuta localmente. Si quedan excepciones, solo esas "
            "pueden enviarse al modelo configurado. No uses datos reales ni "
            "secretos; el envío remoto requiere ALLOW_REMOTE_ENDPOINT."
        )
    data_consent = st.checkbox(
        "Confirmo que los tres archivos contienen datos sintéticos.",
        key="reconciliation_data_consent",
    )
    if ready_count != len(selected_files):
        st.caption("Selecciona las tres fuentes para habilitar la conciliación.")
    elif not data_consent:
        st.caption("Marca la confirmación para habilitar la conciliación.")

    submitted = st.button(
        "Validar y conciliar",
        type="primary",
        disabled=ready_count != len(selected_files) or not data_consent,
        use_container_width=True,
    )
    if submitted:
        st.session_state.pop("uploaded_reconciliation_report", None)
        st.session_state.pop("uploaded_reconciliation_pdf", None)
        upload_payload = {
            source: (uploaded_file.name, uploaded_file.getvalue())
            for source, uploaded_file in (
                ("poc_bank", bank_file),
                ("poc_gateway", gateway_file),
                ("poc_ledger", ledger_file),
            )
            if uploaded_file is not None
        }
        source_labels = [
            f"{label}: {file.name}"
            for label, file in selected_files
            if file is not None
        ]
        try:
            with st.spinner("Validando archivos y conciliando registros…"):
                with tempfile.TemporaryDirectory(
                    prefix="agent-banca-upload-report-"
                ) as output_dir:
                    report = run_uploaded_reconciliation(
                        upload_payload,
                        output_dir=output_dir,
                    )
                    report_json = json.dumps(
                        report,
                        ensure_ascii=False,
                        indent=2,
                    )
                    report_pdf = build_reconciliation_pdf(
                        report,
                        sources=source_labels,
                    )
        except UploadValidationError as error:
            _show_status("danger", str(error))
            return
        except UploadProcessingError as error:
            _show_status("danger", str(error))
            return

        st.session_state.uploaded_reconciliation_report = report_json
        st.session_state.uploaded_reconciliation_pdf = report_pdf
        st.session_state.uploaded_reconciliation_signature = current_signature
        st.session_state.uploaded_reconciliation_sources = source_labels
        _show_status(
            "success",
            "Proceso completado. Revisa los conteos y descarga el reporte.",
        )

    report_json = st.session_state.get("uploaded_reconciliation_report")
    if report_json:
        report = json.loads(report_json)
        st.markdown("#### 2. Resultado")
        st.caption(
            "Fuentes: "
            + " · ".join(
                st.session_state.get("uploaded_reconciliation_sources", [])
            )
        )
        st.caption("Los hallazgos son informativos y requieren revisión humana.")
        categories = (
            ("Coincidencias exactas", "exact_matches"),
            ("Coincidencias de tarifa", "fuzzy_fee_matches"),
            ("Excepciones", "reconciliation_exceptions"),
            ("Huérfanas", "orphan_transactions"),
            ("Alertas AML", "compliance_alerts"),
        )
        primary_metrics = st.columns(3)
        for column, (label, key) in zip(primary_metrics, categories[:3]):
            with column:
                st.metric(label, report["summary"][key])
        secondary_metrics = st.columns(2)
        for column, (label, key) in zip(secondary_metrics, categories[3:]):
            with column:
                st.metric(label, report["summary"][key])
        _render_report_details(report)
        st.download_button(
            "Descargar informe explicado (PDF)",
            data=st.session_state.uploaded_reconciliation_pdf,
            file_name="informe_conciliacion_agent_concilation.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
        with st.expander("Ver o descargar el JSON técnico"):
            st.download_button(
                "Descargar reporte detallado (JSON)",
                data=report_json,
                file_name="financial_reconciliation_audit.json",
                mime="application/json",
                use_container_width=True,
            )
            st.json(report)


def _render_workspace_sources(backend: CopilotBackend) -> CopilotAuthStatus | None:
    st.markdown("#### Fuentes")
    st.caption(
        "Adjunta un documento con el clip del chat. Para comparar reportes, "
        "abre «Conciliar reportes»."
    )
    if st.button(
        "Comprobar conexión con Copilot",
        type="primary",
        use_container_width=True,
    ):
        try:
            st.session_state.auth_status = backend.get_auth_status()
            if st.session_state.auth_status.is_authenticated:
                st.session_state.sessions = backend.list_sessions()
        except CopilotBackendError as error:
            st.session_state.auth_status = None
            _show_status("danger", str(error))
    _show_auth_status(st.session_state.auth_status)

    if (
        st.session_state.auth_status is not None
        and st.session_state.auth_status.is_authenticated
    ):
        if st.button(
            "Nueva conversación",
            use_container_width=True,
        ):
            try:
                session_id = backend.create_session(
                    name=f"Agent Concilation · {datetime.now():%Y-%m-%d %H:%M}",
                    enabled_skills=_enabled_skills(),
                )
                st.session_state.current_session_id = session_id
                st.session_state.messages = []
                st.session_state.sessions = backend.list_sessions()
                st.session_state.selected_session_id = session_id
            except CopilotBackendError as error:
                _show_status("danger", str(error))

        sessions = st.session_state.sessions
        session_by_id = {session.session_id: session for session in sessions}
        if sessions:
            session_ids = list(session_by_id)
            current_id = st.session_state.current_session_id
            selected_id = st.session_state.get("selected_session_id")
            if selected_id not in session_ids:
                selected_id = current_id if current_id in session_ids else session_ids[0]
            selected_id = st.selectbox(
                "Conversación",
                options=session_ids,
                index=session_ids.index(selected_id),
                format_func=lambda value: _session_label(session_by_id[value]),
                key="selected_session_id",
            )
            if selected_id != st.session_state.current_session_id:
                try:
                    st.session_state.messages = backend.load_session(
                        selected_id,
                        enabled_skills=_enabled_skills(),
                    )
                    st.session_state.current_session_id = selected_id
                except CopilotBackendError as error:
                    _show_status("danger", str(error))

    st.divider()
    st.markdown("#### Skills del asistente")
    for _, label, help_text, state_key in SKILL_CONTROLS:
        st.toggle(label, key=state_key, help=help_text)
    st.caption(
        "Cambian la activación automática del SDK en los próximos turnos."
    )
    return st.session_state.auth_status


def _render_chat_workspace(
    backend: CopilotBackend,
    status: CopilotAuthStatus | None,
) -> None:
    st.markdown("#### Conversación")
    st.caption(
        "Pregunta sobre Agent Banca o adjunta un archivo sintético con el clip."
    )
    if status is None or not status.is_authenticated:
        st.info("Primero conecta Copilot desde el panel **Fuentes**.")
        return

    st.info(
        "Usa datos sintéticos. Los mensajes y adjuntos se procesan con tu cuenta "
        "de Copilot; no cargues información financiera real ni secretos."
    )
    consent = st.checkbox(
        "Entiendo y quiero continuar",
        key="copilot_processing_consent",
    )
    if not consent:
        st.caption("Confirma el aviso para habilitar el chat.")
        return
    if not st.session_state.current_session_id:
        st.info("Crea o selecciona una conversación en el panel **Fuentes**.")
        return

    active_session = next(
        (
            session
            for session in st.session_state.sessions
            if session.session_id == st.session_state.current_session_id
        ),
        None,
    )
    if active_session:
        st.caption(
            f"{_session_label(active_session)} · asistente de solo lectura"
        )
    if not st.session_state.messages:
        st.markdown("### ¿Qué quieres entender hoy?")
        st.write(
            "Consulta cómo funciona el PoC, pregunta por Agent Banca o adjunta "
            "un JSON para entender sus campos."
        )
        st.markdown(
            '<div class="prompt-suggestions">'
            '<span>¿Qué acepta hoy el sistema?</span>'
            '<span>Explica las secciones de este JSON</span>'
            '<span>¿Qué significa una excepción?</span>'
            "</div>",
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.text(message["content"])
            else:
                st.markdown(message["content"])

    submission = st.chat_input(
        "Pregunta algo o adjunta un archivo sintético…",
        accept_file=True,
        file_type=["txt", "json"],
        max_upload_size=MAX_UPLOAD_SIZE_MB,
    )
    if submission is None:
        return

    prompt = submission.text.strip()
    uploaded_files = submission.files
    try:
        if len(uploaded_files) > 1:
            raise UploadValidationError("Adjunta un solo archivo por mensaje.")
        if uploaded_files:
            uploaded_file = uploaded_files[0]
            question = prompt or (
                "Explica de manera sencilla el propósito del archivo, sus "
                "secciones y los campos principales."
            )
            content = parse_explanation_upload(
                uploaded_file.name,
                uploaded_file.getvalue(),
            )
            with st.spinner("Analizando el archivo adjunto…"):
                answer = backend.send_file_message(
                    st.session_state.current_session_id,
                    question,
                    uploaded_file.name,
                    content,
                    enabled_skills=_enabled_skills(),
                )
            user_content = question + "\n\nAdjunto: " + Path(uploaded_file.name).name
        else:
            if not prompt:
                raise UploadValidationError(
                    "Escribe una pregunta o adjunta un archivo."
                )
            with st.spinner("Preparando respuesta…"):
                answer = backend.send_message(
                    st.session_state.current_session_id,
                    prompt,
                    enabled_skills=_enabled_skills(),
                )
            user_content = prompt
    except UploadValidationError as error:
        _show_status("danger", str(error))
    except CopilotBackendError as error:
        _show_status("danger", str(error))
    else:
        st.session_state.messages.extend(
            [
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": answer},
            ]
        )
        st.rerun()


def _render_studio_panel() -> None:
    st.markdown("#### Studio")
    st.caption("Guía rápida del flujo y alcance del PoC.")
    st.markdown("**Objetivo del producto**")
    st.write(
        "Cruzar reportes de pasarelas, libro mayor y extractos bancarios, "
        "identificar diferencias con evidencia y preparar información para "
        "analistas."
    )
    st.markdown("**Cómo usar esta app**")
    st.markdown(
        "1. **Chat:** pregunta sobre el proyecto o sus archivos.\n"
        "2. **Adjunto:** usa el clip para pedir explicación de un TXT/JSON.\n"
        "3. **Conciliar reportes:** compara tres fuentes sintéticas y descarga "
        "el PDF explicado."
    )
    st.markdown("**Prueba con preguntas como**")
    st.caption("¿Qué campos contiene este reporte?")
    st.caption("¿Qué significa cada categoría del resultado?")
    st.warning(
        "Alcance actual: PoC con JSON sintético de banco, pasarela y libro "
        "mayor. No procesa formatos oficiales del banco central ni demuestra "
        "escala o uso en producción."
    )


def main() -> None:
    st.set_page_config(
        page_title="Agent Concilation · Workspace",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    _apply_enterprise_styles()

    st.title("Agent Concilation")
    st.caption(
        "Workspace de conciliación: comprende reportes y revisa diferencias "
        "con evidencia."
    )
    st.markdown(
        '<div class="badge badge-info environment-badge" '
        'aria-label="Prueba local, no es un sistema de producción">'
        '<span class="environment-dot"></span>'
        "PRUEBA LOCAL · DATOS SINTÉTICOS · SOLO LECTURA</div>",
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("auth_status", None)
    st.session_state.setdefault("sessions", [])
    st.session_state.setdefault("current_session_id", None)
    st.session_state.setdefault("messages", [])
    for _, _, _, state_key in SKILL_CONTROLS:
        st.session_state.setdefault(state_key, True)
    backend = get_backend()

    workspace_tab, reconciliation_tab = st.tabs(
        ["Espacio de trabajo", "Conciliar reportes"]
    )
    with workspace_tab:
        sources_column, chat_column, studio_column = st.columns(
            [1.05, 2.1, 1.05],
            gap="medium",
        )
        with sources_column:
            with st.container(border=True):
                status = _render_workspace_sources(backend)
        with chat_column:
            with st.container(border=True):
                _render_chat_workspace(backend, status)
        with studio_column:
            with st.container(border=True):
                _render_studio_panel()

    with reconciliation_tab:
        _render_reconciliation_upload()


if __name__ == "__main__":
    main()
