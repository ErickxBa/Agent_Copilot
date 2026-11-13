"""FastAPI Backend Server for Agent_Banca Modern Architecture.

Exposes REST and streaming APIs for:
- Reconciliation engine (deterministic matching, fee checks, AML alerts, LLM exception audit)
- PDF report generation
- Copilot CLI authentication, sessions, and chat
- Synthetic fixtures loading for quick testing
"""

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

# Ensure src directory is in sys.path
SRC_DIR = Path(__file__).resolve().parent
ROOT_DIR = SRC_DIR.parent
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from copilot_backend import (
    AVAILABLE_SKILLS,
    CopilotAuthStatus,
    CopilotBackend,
    CopilotBackendError,
    CopilotSessionInfo,
)
from copilot_uploads import (
    MAX_UPLOAD_SIZE_BYTES,
    MAX_UPLOAD_SIZE_MB,
    UploadProcessingError,
    UploadValidationError,
    parse_explanation_upload,
    run_uploaded_reconciliation,
)
from reconciliation_pdf import build_reconciliation_pdf

app = FastAPI(
    title="Agent_Banca Financial Reconciliation & Copilot API",
    version="1.0.0",
    description="Modern REST and streaming API for financial reconciliation and compliance audit.",
)

# Allow CORS for development (Vite frontend on 5173, Next on 3000, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

backend_instance: CopilotBackend | None = None


def get_copilot_backend() -> CopilotBackend:
    global backend_instance
    if backend_instance is None:
        backend_instance = CopilotBackend()
    return backend_instance


def set_copilot_backend(instance: Any) -> None:
    global backend_instance
    backend_instance = instance


# -------------------------------------------------------------------------
# Models
# -------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str
    version: str
    copilot_authenticated: bool
    local_fixtures_available: bool


class CreateSessionRequest(BaseModel):
    name: str | None = None
    enabled_skills: list[str] = Field(
        default_factory=lambda: list(AVAILABLE_SKILLS)
    )


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str
    enabled_skills: list[str] = Field(
        default_factory=lambda: list(AVAILABLE_SKILLS)
    )


class SessionItem(BaseModel):
    session_id: str
    summary: str | None
    start_time: str
    modified_time: str


class PDFGenerationRequest(BaseModel):
    report: dict[str, Any]
    sources: list[str] = Field(default_factory=list)


# -------------------------------------------------------------------------
# Endpoints: System & Health
# -------------------------------------------------------------------------


@app.get("/api/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    fixtures_ok = (
        (ROOT_DIR / "data" / "poc_bank.json").exists()
        and (ROOT_DIR / "data" / "poc_gateway.json").exists()
        and (ROOT_DIR / "data" / "poc_ledger.json").exists()
    )

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        copilot_authenticated=False,
        local_fixtures_available=fixtures_ok,
    )


# -------------------------------------------------------------------------
# Endpoints: Fixtures & Samples
# -------------------------------------------------------------------------


@app.get("/api/fixtures/samples")
def get_sample_fixtures() -> dict[str, Any]:
    """Return synthetic sample fixtures directly so users can run a reconciliation with 1 click."""
    fixtures = {}
    mapping = {
        "poc_bank": ROOT_DIR / "data" / "poc_bank.json",
        "poc_gateway": ROOT_DIR / "data" / "poc_gateway.json",
        "poc_ledger": ROOT_DIR / "data" / "poc_ledger.json",
    }
    for key, path in mapping.items():
        if path.exists():
            try:
                fixtures[key] = json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                fixtures[key] = {"error": str(e)}
    return fixtures


# -------------------------------------------------------------------------
# Endpoints: Reconciliation Engine
# -------------------------------------------------------------------------


@app.post("/api/reconcile/upload")
async def reconcile_uploaded_files(
    bank_file: UploadFile | None = File(None),
    gateway_file: UploadFile | None = File(None),
    ledger_file: UploadFile | None = File(None),
) -> dict[str, Any]:
    """Execute hybrid reconciliation on 3 uploaded files."""
    if not bank_file or not gateway_file or not ledger_file:
        raise HTTPException(
            status_code=400,
            detail="Se requieren los 3 reportes: bank_file, gateway_file y ledger_file.",
        )

    bank_bytes = await bank_file.read()
    gateway_bytes = await gateway_file.read()
    ledger_bytes = await ledger_file.read()

    for name, content in (
        (bank_file.filename or "banco", bank_bytes),
        (gateway_file.filename or "pasarela", gateway_bytes),
        (ledger_file.filename or "libro_mayor", ledger_bytes),
    ):
        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"El archivo {name} excede el tamaño máximo permitido ({MAX_UPLOAD_SIZE_MB} MB).",
            )

    upload_payload = {
        "poc_bank": (bank_file.filename or "bank.json", bank_bytes),
        "poc_gateway": (gateway_file.filename or "gateway.json", gateway_bytes),
        "poc_ledger": (ledger_file.filename or "ledger.json", ledger_bytes),
    }

    source_labels = [
        f"Banco: {bank_file.filename}",
        f"Pasarela: {gateway_file.filename}",
        f"Libro mayor: {ledger_file.filename}",
    ]

    try:
        with tempfile.TemporaryDirectory(prefix="agent-banca-api-report-") as tmpdir:
            report = run_uploaded_reconciliation(upload_payload, output_dir=tmpdir)
            return {
                "success": True,
                "sources": source_labels,
                "report": report,
            }
    except UploadValidationError as err:
        raise HTTPException(status_code=422, detail=str(err))
    except UploadProcessingError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error inesperado: {err}")


@app.post("/api/reconcile/run-samples")
def reconcile_samples() -> dict[str, Any]:
    """Execute reconciliation using repository fixtures directly.
    
    Prefers deterministic txt_samples for offline execution without external LLM latency.
    """
    samples_dir = ROOT_DIR / "data" / "txt_samples"
    if (samples_dir / "poc_bank.txt").exists():
        mapping = {
            "poc_bank": samples_dir / "poc_bank.txt",
            "poc_gateway": samples_dir / "poc_gateway.txt",
            "poc_ledger": samples_dir / "poc_ledger.txt",
        }
    else:
        mapping = {
            "poc_bank": ROOT_DIR / "data" / "poc_bank.json",
            "poc_gateway": ROOT_DIR / "data" / "poc_gateway.json",
            "poc_ledger": ROOT_DIR / "data" / "poc_ledger.json",
        }

    payload = {
        key: (path.name, path.read_bytes())
        for key, path in mapping.items()
        if path.exists()
    }
    if len(payload) != 3:
        raise HTTPException(status_code=404, detail="Fixtures sintéticas no encontradas en disco.")

    sources = [f"{k}: {v[0]}" for k, v in payload.items()]
    try:
        with tempfile.TemporaryDirectory(prefix="agent-banca-sample-report-") as tmpdir:
            report = run_uploaded_reconciliation(payload, output_dir=tmpdir)
            return {
                "success": True,
                "sources": sources,
                "report": report,
            }
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/reconcile/generate-pdf")
def generate_pdf(request: PDFGenerationRequest) -> Response:
    """Generate professional PDF audit report from reconciliation output."""
    try:
        pdf_bytes = build_reconciliation_pdf(request.report, sources=request.sources)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="informe_conciliacion_agent_banca.pdf"'
            },
        )
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Error generando PDF: {err}")


# -------------------------------------------------------------------------
# Endpoints: Copilot Agent & Sessions
# -------------------------------------------------------------------------


@app.get("/api/copilot/auth")
def get_auth_status() -> dict[str, Any]:
    backend = get_copilot_backend()
    try:
        status = backend.get_auth_status()
        return {
            "is_authenticated": status.is_authenticated,
            "login": status.login,
            "auth_type": status.auth_type,
            "status_message": status.status_message,
        }
    except CopilotBackendError as err:
        return {
            "is_authenticated": False,
            "login": None,
            "auth_type": None,
            "status_message": str(err),
        }


@app.get("/api/copilot/sessions")
def list_sessions() -> list[SessionItem]:
    backend = get_copilot_backend()
    try:
        sessions = backend.list_sessions()
        return [
            SessionItem(
                session_id=s.session_id,
                summary=s.summary,
                start_time=s.start_time.isoformat(),
                modified_time=s.modified_time.isoformat(),
            )
            for s in sessions
        ]
    except CopilotBackendError as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/copilot/sessions")
def create_session(request: CreateSessionRequest) -> dict[str, str]:
    backend = get_copilot_backend()
    try:
        session_id = backend.create_session(
            name=request.name,
            enabled_skills=request.enabled_skills,
        )
        return {"session_id": session_id}
    except CopilotBackendError as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/copilot/sessions/{session_id}/messages")
def get_session_messages(
    session_id: str,
    skills: str | None = None,
) -> list[dict[str, str]]:
    backend = get_copilot_backend()
    enabled_skills = skills.split(",") if skills else list(AVAILABLE_SKILLS)
    try:
        return backend.load_session(session_id, enabled_skills=enabled_skills)
    except CopilotBackendError as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/copilot/chat")
async def chat_message(
    session_id: str = Form(...),
    message: str = Form(...),
    skills: str = Form(",".join(AVAILABLE_SKILLS)),
    attachment: UploadFile | None = File(None),
) -> dict[str, str]:
    backend = get_copilot_backend()
    enabled_skills = [s.strip() for s in skills.split(",") if s.strip()]

    try:
        if attachment:
            content_bytes = await attachment.read()
            if len(content_bytes) > MAX_UPLOAD_SIZE_BYTES:
                raise HTTPException(
                    status_code=400,
                    detail=f"El archivo excede el límite de {MAX_UPLOAD_SIZE_MB} MB.",
                )
            content_str = parse_explanation_upload(
                attachment.filename or "file.json", content_bytes
            )
            question = message or "Explica de manera sencilla el propósito del archivo, sus secciones y campos."
            answer = await run_in_threadpool(
                backend.send_file_message,
                session_id=session_id,
                prompt=question,
                filename=attachment.filename or "archivo.json",
                content=content_str,
                enabled_skills=enabled_skills,
            )
            user_content = f"{question}\n\nAdjunto: {attachment.filename}"
        else:
            if not message.strip():
                raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío.")
            answer = await run_in_threadpool(
                backend.send_message,
                session_id=session_id,
                prompt=message,
                enabled_skills=enabled_skills,
            )
            user_content = message

        return {
            "user_content": user_content,
            "assistant_content": answer,
        }
    except UploadValidationError as err:
        raise HTTPException(status_code=422, detail=str(err))
    except CopilotBackendError as err:
        err_msg = str(err)
        if (
            "No GitHub OAuth token" in err_msg
            or "HMAC key" in err_msg
            or "not authenticated" in err_msg.lower()
        ):
            return {
                "user_content": user_content if "user_content" in locals() else message,
                "assistant_content": (
                    "**No se detectó una sesión autenticada de GitHub Copilot en esta terminal.**\n\n"
                    "Para interactuar con el agente Copilot en tiempo real, ejecuta uno de los siguientes comandos en tu terminal de Windows:\n\n"
                    "```powershell\n"
                    "# Opción 1: Iniciar el asistente CLI de Copilot\n"
                    "copilot\n\n"
                    "# Opción 2: Autenticar mediante GitHub CLI\n"
                    "gh auth login\n"
                    "```\n\n"
                    "Una vez completado el inicio de sesión en tu navegador, podrás conversar con el agente y analizar archivos automáticamente.\n\n"
                    ">**Tip**: Todo el motor de conciliación financiera, matrices de cruce, reglas de tarifa y reportes PDF funcionan al 100% en la pestaña **«Conciliación Financiera»** sin necesidad de Copilot."
                ),
            }
        raise HTTPException(status_code=500, detail=str(err))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)

