import json
from pathlib import Path
from typing import Any

import gradio as gr
import pandas as pd

from src.document_processing.document_loader import load_documents
from src.document_processing.document_normalizer import normalize_documents
from src.services.testcase_service import TestCaseService
from src.integrations.filesystem_mcp import FilesystemMCP


SUPPORTED_FILE_TYPES = [
    ".pdf",
    ".docx",
    ".xlsx",
    ".xlsm",
    ".csv",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tiff",
    ".txt",
]


EXPORT_DIR = Path("data") / "exports"
filesystem_mcp = FilesystemMCP()


def _load_user_documents(files: list[str] | None):
    if not files:
        return None, "Upload at least one supported document."

    paths = [Path(file_path) for file_path in files]
    unsupported = [path.name for path in paths if path.suffix.lower() not in SUPPORTED_FILE_TYPES]
    if unsupported:
        return None, f"Unsupported file type: {', '.join(unsupported)}"

    try:
        documents = normalize_documents(load_documents(paths, text_reader=filesystem_mcp.read_text_or_local))
        return documents, None
    except Exception as error:
        return None, str(error)


def analyze_documents(files: list[str] | None) -> dict[str, Any]:
    documents, error = _load_user_documents(files)
    if error:
        return {"error": error}
    try:
        result = TestCaseService().generate_artifacts(documents, EXPORT_DIR)
        return {
            "requirements_outline": result["outline"],
            "requirements": json.loads(result["requirements"].model_dump_json()),
            "scenarios": json.loads(result["scenarios"].model_dump_json()),
            "test_cases": json.loads(result["test_cases"].model_dump_json()),
            "export_path": str(result["export_path"]),
        }
    except Exception as error:
        return {"error": str(error)}


def _format_summary(result: dict[str, Any]) -> str:
    if result.get("error"):
        return f"Could not complete analysis: {result['error']}"

    reqs = result.get("requirements", {}).get("requirements", [])
    outline = result.get("requirements_outline", [])
    scenarios = result.get("scenarios", {}).get("scenarios", [])
    cases = result.get("test_cases", {}).get("test_cases", [])
    export_path = result.get("export_path")

    lines = [
        "I analyzed the uploaded documents and generated the following outputs:",
        "",
        f"Requirements extracted: {len(reqs)}",
        "Requirements outline:",
    ]
    if outline:
        lines.extend(f"- {item}" for item in outline[:10])
    else:
        lines.append("- No outline could be created.")
    lines.extend(
        [
            "",
            f"Scenarios generated: {len(scenarios)}",
            f"Test cases generated: {len(cases)}",
            f"Excel export: {export_path}",
        ]
    )
    return "\n".join(lines)


def _table_from_items(items: list[dict[str, Any]], fields: list[str]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame([{field: "" for field in fields}])
    rows = []
    for item in items:
        row = {}
        for field in fields:
            value = item.get(field, "")
            if isinstance(value, list):
                value = " | ".join(str(v) for v in value)
            elif isinstance(value, dict):
                value = json.dumps(value, ensure_ascii=False)
            row[field] = value
        rows.append(row)
    return pd.DataFrame(rows)


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="AI Test Case Generator") as demo:
        gr.Markdown(
            "# AI Test Case Generator\n"
            "Upload your documents, then talk to the assistant to analyze them, review requirements, and generate test scenarios and test cases."
        )
        session_state = gr.State({"files": [], "analysis": None})
        files = gr.File(
            label="Upload documents",
            file_count="multiple",
            file_types=SUPPORTED_FILE_TYPES,
            type="filepath",
        )
        upload_status = gr.Markdown("No documents uploaded yet.")
        chat = gr.Chatbot(label="Assistant", height=520)
        message = gr.Textbox(label="Message", placeholder="Ask me to analyze the uploaded documents.")
        analyze_button = gr.Button("Analyze documents", variant="primary")
        summary = gr.Markdown()
        requirements_table = gr.Dataframe(label="Requirements", interactive=False, wrap=True)
        scenarios_table = gr.Dataframe(label="Test Scenarios", interactive=False, wrap=True)
        test_cases_table = gr.Dataframe(label="Test Cases", interactive=False, wrap=True)
        results = gr.JSON(label="Latest analysis")
        export_file = gr.File(label="Excel export")

        def remember_files(filepaths, state):
            state = state or {"files": [], "analysis": None}
            state["files"] = filepaths or []
            state["analysis"] = None
            if not filepaths:
                return state, "No documents uploaded yet."
            return state, f"Uploaded {len(filepaths)} document(s). You can now ask me to analyze them."

        def respond(user_message, history, state):
            history = history or []
            state = state or {"files": [], "analysis": None}
            files = state.get("files") or []
            if not files:
                answer = "Please upload one or more documents first, then I can analyze them."
                history = history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": answer},
                ]
                empty_df = pd.DataFrame([{"Message": answer}])
                return "", history, state, {"error": answer}, None, answer, empty_df, empty_df, empty_df

            if state.get("analysis") is None:
                analysis = analyze_documents(files)
                state["analysis"] = analysis
            else:
                analysis = state["analysis"]

            if analysis.get("error"):
                answer = f"I could not complete the analysis: {analysis['error']}"
                history = history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": answer},
                ]
                empty_df = pd.DataFrame([{"Message": answer}])
                return "", history, state, analysis, None, answer, empty_df, empty_df, empty_df

            answer = _format_summary(analysis)
            history = history + [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": answer},
            ]
            export_path = analysis.get("export_path")
            req_rows = analysis.get("requirements", {}).get("requirements", [])
            scenario_rows = analysis.get("scenarios", {}).get("scenarios", [])
            case_rows = analysis.get("test_cases", {}).get("test_cases", [])
            requirements_df = _table_from_items(
                req_rows,
                ["requirement_id", "requirement_text", "requirement_type", "priority", "source_file", "source_location"],
            )
            scenarios_df = _table_from_items(
                scenario_rows,
                ["scenario_id", "requirement_id", "scenario_title", "scenario_description", "scenario_type", "priority"],
            )
            test_cases_df = _table_from_items(
                case_rows,
                [
                    "test_case_id",
                    "requirement_id",
                    "scenario_id",
                    "title",
                    "test_type",
                    "priority",
                    "expected_result",
                    "positive",
                    "automation_candidate",
                ],
            )
            return "", history, state, analysis, export_path, answer, requirements_df, scenarios_df, test_cases_df

        def run_analysis(history, state):
            history = history or []
            state = state or {"files": [], "analysis": None}
            files = state.get("files") or []
            if not files:
                answer = "Please upload one or more documents first, then I can analyze them."
                history = history + [
                    {"role": "user", "content": "Analyze the uploaded documents"},
                    {"role": "assistant", "content": answer},
                ]
                empty_df = pd.DataFrame([{"Message": answer}])
                return history, state, {"error": answer}, None, answer, empty_df, empty_df, empty_df

            analysis = analyze_documents(files)
            state["analysis"] = analysis
            if analysis.get("error"):
                answer = f"I could not complete the analysis: {analysis['error']}"
                history = history + [
                    {"role": "user", "content": "Analyze the uploaded documents"},
                    {"role": "assistant", "content": answer},
                ]
                empty_df = pd.DataFrame([{"Message": answer}])
                return history, state, analysis, None, answer, empty_df, empty_df, empty_df

            answer = _format_summary(analysis)
            history = history + [
                {"role": "user", "content": "Analyze the uploaded documents"},
                {"role": "assistant", "content": answer},
            ]
            req_rows = analysis.get("requirements", {}).get("requirements", [])
            scenario_rows = analysis.get("scenarios", {}).get("scenarios", [])
            case_rows = analysis.get("test_cases", {}).get("test_cases", [])
            requirements_df = _table_from_items(
                req_rows,
                ["requirement_id", "requirement_text", "requirement_type", "priority", "source_file", "source_location"],
            )
            scenarios_df = _table_from_items(
                scenario_rows,
                ["scenario_id", "requirement_id", "scenario_title", "scenario_description", "scenario_type", "priority"],
            )
            test_cases_df = _table_from_items(
                case_rows,
                [
                    "test_case_id",
                    "requirement_id",
                    "scenario_id",
                    "title",
                    "test_type",
                    "priority",
                    "expected_result",
                    "positive",
                    "automation_candidate",
                ],
            )
            return history, state, analysis, analysis.get("export_path"), answer, requirements_df, scenarios_df, test_cases_df

        files.change(remember_files, inputs=[files, session_state], outputs=[session_state, upload_status])
        message.submit(
            respond,
            inputs=[message, chat, session_state],
            outputs=[message, chat, session_state, results, export_file, summary, requirements_table, scenarios_table, test_cases_table],
        )
        analyze_button.click(
            run_analysis,
            inputs=[chat, session_state],
            outputs=[chat, session_state, results, export_file, summary, requirements_table, scenarios_table, test_cases_table],
        )
    return demo


if __name__ == "__main__":
    build_ui().launch()
