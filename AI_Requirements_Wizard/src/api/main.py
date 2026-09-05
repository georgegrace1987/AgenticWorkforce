from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config.settings import settings
from src.utils.logger import get_logger
from src.models.requirements import ChatRequest, ChatResponse, GenerateRequest
from src.services.wizard_service import WizardService
from src.services.srd_generator import SRDGenerator
from src.document_processing.document_loader import extract_document_text, SUPPORTED_EXTENSIONS
from src.integrations.filesystem_mcp import FilesystemMCP

logger = get_logger("api")
FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
sessions = {}
wizard_service = WizardService(sessions)
srd_generator = SRDGenerator()
filesystem_mcp = FilesystemMCP()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.create_dirs()
    logger.info("AI Requirements Wizard API started")
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title="AI Requirements Wizard",
        version="0.1.0",
        description="Turn informal requirements and source documents into a professional SRD.",
        lifespan=lifespan,
    )

    @application.get("/api/health", tags=["system"])
    def health() -> dict[str, Any]:
        return {"status": "ok", "service": "ai-requirements-wizard"}

    @application.post("/api/chat", response_model=ChatResponse, tags=["requirements"])
    def chat(request: ChatRequest) -> ChatResponse:
        logger.info("Processing requirements chat for session %s", request.session_id)
        return wizard_service.process_message(request.session_id, request.message)

    @application.post("/api/documents", response_model=ChatResponse, tags=["requirements"])
    async def ingest_document(session_id: str, file: UploadFile = File(...)) -> ChatResponse:
        if file.filename is None or Path(file.filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
            from fastapi import HTTPException

            supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
            raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported formats: {supported}")
        content = await file.read()
        try:
            extracted_text = extract_document_text(file.filename, content)
        except Exception as error:
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail=f"Could not read document: {error}") from error
        if not extracted_text.strip():
            from fastapi import HTTPException

            raise HTTPException(status_code=400, detail="The DOCX did not contain readable text.")
        processed_path = Path(settings.PROCESSED_DIR) / f"{session_id}-requirements.txt"
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        processed_path.write_text(extracted_text, encoding="utf-8")
        extracted_text = filesystem_mcp.read_text_or_local(processed_path)
        return wizard_service.process_message(session_id, extracted_text)

    @application.post("/api/srd/generate", tags=["srd"])
    def generate_srd(request: GenerateRequest) -> FileResponse:
        state = sessions.get(request.session_id)
        if state is None:
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Requirements session not found")
        output_path = Path(settings.OUTPUT_DIR) / f"srd-{request.session_id}.docx"
        srd_generator.generate(state, output_path)
        logger.info("Generated SRD for session %s", request.session_id)
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="software-requirements-document.docx",
        )

    if FRONTEND_DIR.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=FRONTEND_DIR),
            name="static",
        )

        @application.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(FRONTEND_DIR / "index.html")

    return application


app = create_app()
