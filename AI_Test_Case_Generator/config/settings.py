from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # LLM configuration
    LLM_PROVIDER: str = Field("lmstudio", description="LLM provider (lmstudio|ollama|openai)")
    LLM_BASE_URL: str = Field("http://127.0.0.1:1234/v1", description="Base URL for the OpenAI-compatible LLM API")
    LLM_MODEL: Optional[str] = Field("local-model", description="Model name to use")
    LLM_API_KEY: Optional[str] = Field(None, description="API key if required")
    LLM_TEMPERATURE: float = Field(0.1, description="LLM temperature")
    LLM_MAX_TOKENS: int = Field(4096, description="Max tokens for LLM responses")

    # Chunking and performance
    CHUNK_SIZE: int = Field(1000, description="Chunk size (tokens/characters) for document chunking")
    CHUNK_OVERLAP: int = Field(100, description="Chunk overlap for context preservation")
    MAX_FILE_SIZE_MB: int = Field(50, description="Maximum allowed upload file size (MB)")
    MAX_FILES: int = Field(10, description="Maximum number of files per upload")

    # Paths
    BASE_DIR: Path = Field(Path(__file__).resolve().parent.parent.parent)
    UPLOAD_DIR: Path = Field(Path("data/uploads"))
    PROCESSED_DIR: Path = Field(Path("data/processed"))
    OUTPUT_DIR: Path = Field(Path("data/outputs"))
    LOG_DIR: Path = Field(Path("logs"))

    MCP_FILESYSTEM_ENABLED: bool = Field(True)
    MCP_FILESYSTEM_COMMAND: str = Field("npx")
    MCP_FILESYSTEM_PACKAGE: str = Field("@modelcontextprotocol/server-filesystem")

    # Timeouts and retries
    REQUEST_TIMEOUT_SECONDS: int = Field(30)
    LLM_RETRY_COUNT: int = Field(2)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def create_dirs(self) -> None:
        """Create runtime directories if they don't exist."""
        for path in (self.UPLOAD_DIR, self.PROCESSED_DIR, self.OUTPUT_DIR, self.LOG_DIR):
            p = Path(path)
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)


# Convenient singleton
settings = Settings()
