"""Validation and local processing for text uploads in the Streamlit app."""

import json
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from openai import OpenAIError


MAX_UPLOAD_SIZE_BYTES = 1_048_576
MAX_UPLOAD_SIZE_MB = 1
RECONCILIATION_SOURCES = ("poc_bank", "poc_gateway", "poc_ledger")


class UploadValidationError(ValueError):
    """An uploaded file is invalid or outside the supported PoC input contract."""


class UploadProcessingError(RuntimeError):
    """The uploaded reconciliation inputs could not be processed."""


def _load_orchestrator():
    try:
        from src.orchestrator import load_fixture_data, run_audit
    except ModuleNotFoundError as error:
        if error.name != "src":
            raise
        from orchestrator import load_fixture_data, run_audit

    return load_fixture_data, run_audit


def decode_text_upload(file_name: str, content: bytes) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix not in {".txt", ".json"}:
        raise UploadValidationError("Solo se aceptan archivos .txt o .json.")
    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise UploadValidationError(
            f"El archivo supera el límite de {MAX_UPLOAD_SIZE_MB} MB."
        )
    if not content:
        raise UploadValidationError("El archivo está vacío.")
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise UploadValidationError(
            "El archivo debe estar codificado como texto UTF-8."
        ) from error


def parse_explanation_upload(file_name: str, content: bytes) -> str:
    text = decode_text_upload(file_name, content)
    if Path(file_name).suffix.lower() != ".json":
        return text
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise UploadValidationError(
            "El archivo .json no contiene JSON válido."
        ) from error
    return json.dumps(value, ensure_ascii=False, indent=2)


def _parse_reconciliation_upload(file_name: str, content: bytes) -> str:
    text = decode_text_upload(file_name, content)
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise UploadValidationError(
            f"{file_name} debe contener JSON válido, incluso si termina en .txt."
        ) from error
    if not isinstance(value, dict) or not isinstance(value.get("records"), list):
        raise UploadValidationError(
            f"{file_name} debe ser un objeto JSON con un arreglo 'records'."
        )
    return json.dumps(value, ensure_ascii=False)


def run_uploaded_reconciliation(
    files: Mapping[str, tuple[str, bytes]],
    *,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    expected_sources = set(RECONCILIATION_SOURCES)
    if set(files) != expected_sources:
        raise UploadValidationError(
            "Carga exactamente un archivo para banco, pasarela y libro mayor."
        )

    try:
        with TemporaryDirectory(prefix="agent-banca-upload-") as upload_dir:
            for source in RECONCILIATION_SOURCES:
                file_name, content = files[source]
                normalized_json = _parse_reconciliation_upload(file_name, content)
                (Path(upload_dir) / f"{source}.json").write_text(
                    normalized_json,
                    encoding="utf-8",
                )

            load_fixture_data, run_audit = _load_orchestrator()
            fixture_data = load_fixture_data(upload_dir)
            return run_audit(fixture_data=fixture_data, output_dir=output_dir)
    except UploadValidationError:
        raise
    except (
        FileNotFoundError,
        KeyError,
        OpenAIError,
        OSError,
        RuntimeError,
        ValueError,
    ) as error:
        raise UploadProcessingError(
            f"No se pudo validar o completar la conciliación: {error}"
        ) from error
    except ImportError as error:
        raise UploadProcessingError(
            "No se pudo cargar el orquestador financiero de la aplicación: "
            f"{error}"
        ) from error
