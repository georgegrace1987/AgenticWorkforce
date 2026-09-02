# AI Requirements Wizard

Standalone requirements-analysis module for the AgenticWorkforce master application.

The foundation provides a FastAPI runtime, health endpoint, and browser workspace. Requirements ingestion, session persistence, AI clarification, and SRD generation will be added incrementally.

## Run

```powershell
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:8001. The health endpoint is available at http://127.0.0.1:8001/api/health.

## Local AI conversation

The wizard uses an OpenAI-compatible local model endpoint for structured requirement extraction and targeted follow-up questions. LM Studio is the default configuration:

1. Start LM Studio, load a chat model, and start its local server.
2. Copy `.env.example` to `.env` and set `LLM_MODEL` to the loaded model name.
3. Start the wizard and describe the product or attach a DOCX requirements document.

If the model endpoint is unavailable, the wizard continues with its built-in deterministic extraction and clarification questions.

## Filesystem MCP

The wizard uses the MCP filesystem server to reread extracted requirement text from the project data directory before analysis. Install Node.js so `npx` is available, then install the Python dependencies:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Set `MCP_FILESYSTEM_ENABLED=false` in `.env` to use direct local file reads instead. The MCP server is restricted to this project directory.
