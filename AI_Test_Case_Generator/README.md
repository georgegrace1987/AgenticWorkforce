# AI Test Case Generator (Phase 1)

This repository contains the Phase 1 baseline for the AI Test Case Generator.

Phase 1 includes:

- Project skeleton and directories
- Configuration via `config/settings.py` (Pydantic + dotenv)
- Application logger in `src/utils/logger.py`
- Pydantic models for documents, requirements, scenarios, test cases, and validation
- A minimal `app.py` entrypoint that initializes configuration and logging

Next phases will implement document processing, LLM clients, agents, Gradio UI, and export features.

Quickstart (Windows PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

## Filesystem MCP

Text requirement files are read through the MCP filesystem server. Install Node.js so `npx` is available, then install the Python dependencies with `pip install -r requirements.txt`. Set `MCP_FILESYSTEM_ENABLED=false` in `.env` to use direct local file reads instead. The MCP server is restricted to this project directory; format-specific parsers continue to handle PDF, DOCX, Excel, PowerPoint, and image files.

