from __future__ import annotations

import atexit
import os
import socket
import subprocess
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT_DIR = Path(__file__).resolve().parent
MASTER_HOST = "127.0.0.1"
MASTER_PORT = 8000

APPLICATIONS = {
    "requirements": {
        "name": "AI Requirements Wizard",
        "directory": ROOT_DIR / "AI_Requirements_Wizard",
        "port": 8001,
    },
    "test-cases": {
        "name": "AI Test Case Generator",
        "directory": ROOT_DIR / "AI_Test_Case_Generator",
        "port": 7860,
    },
    "playwright": {
        "name": "Playwright Test Executor",
        "directory": ROOT_DIR / "Playwright_Executor",
        "port": 8002,
    },
}

child_processes: dict[str, subprocess.Popen] = {}


def _resolve_python_executable(root_dir: Path | None = None) -> str:
    target_root = root_dir or ROOT_DIR
    venv_python = target_root / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if venv_python.exists():
        return str(venv_python)
    return sys.executable


def _port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(0.2)
        return connection.connect_ex((MASTER_HOST, port)) == 0


def _start_application(application_id: str) -> int:
    application = APPLICATIONS[application_id]
    process = child_processes.get(application_id)
    if process is None or process.poll() is not None:
        child_processes[application_id] = subprocess.Popen(
            [_resolve_python_executable(), "app.py"],
            cwd=application["directory"],
        )

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if _port_is_open(application["port"]):
            return application["port"]
        time.sleep(0.1)
    raise RuntimeError(f"{application['name']} did not start on port {application['port']}.")


def _stop_children() -> None:
    for process in child_processes.values():
        if process.poll() is None:
            process.terminate()


atexit.register(_stop_children)


class MasterRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/":
            self._send_html()
            return

        if path.startswith("/launch/"):
            application_id = path.removeprefix("/launch/")
            if application_id not in APPLICATIONS:
                self.send_error(HTTPStatus.NOT_FOUND, "Unknown application")
                return
            try:
                port = _start_application(application_id)
            except (OSError, RuntimeError) as error:
                self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
                return
            self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
            self.send_header("Location", f"http://{MASTER_HOST}:{port}/")
            self.end_headers()
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def _send_html(self) -> None:
        cards = "".join(
            f"""
            <article class="app-card">
                <p class="eyebrow">{application_id.replace('-', ' ').upper()}</p>
                <h2>{application['name']}</h2>
                <p>{'Turn informal ideas into structured software requirements.' if application_id == 'requirements' else 'Analyze source documents and generate complete test cases.' if application_id == 'test-cases' else 'Generate and execute Playwright tests from test case data.'}</p>
                <a class="launch-button" href="/launch/{application_id}">Launch workspace <span aria-hidden="true">&rarr;</span></a>
            </article>
            """
            for application_id, application in APPLICATIONS.items()
        )
        html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AgenticWorkforce</title>
    <style>
        :root {{ color-scheme: light; --ink: #17252a; --muted: #587075; --paper: #f5f3ed; --accent: #e26d3f; --line: #d7ded8; }}
        * {{ box-sizing: border-box; }}
        body {{ margin: 0; min-height: 100vh; color: var(--ink); background: radial-gradient(circle at 80% 10%, #dcece2, transparent 34rem), var(--paper); font: 16px/1.5 Georgia, serif; }}
        main {{ width: min(1080px, calc(100% - 40px)); margin: 0 auto; padding: 9vh 0 12vh; }}
        .kicker, .eyebrow {{ font: 700 11px/1.2 'Trebuchet MS', sans-serif; letter-spacing: 2px; }}
        .kicker {{ color: var(--accent); }}
        h1 {{ max-width: 650px; margin: 18px 0 20px; font: 700 clamp(3rem, 8vw, 6.5rem)/.92 Georgia, serif; letter-spacing: 0; }}
        .intro {{ max-width: 570px; margin-bottom: 56px; color: var(--muted); font-size: 1.2rem; }}
        .app-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px; }}
        .app-card {{ display: flex; min-height: 280px; flex-direction: column; padding: 30px; border: 1px solid var(--line); background: rgba(255,255,255,.62); }}
        .eyebrow {{ margin: 0 0 42px; color: var(--muted); }}
        h2 {{ margin: 0 0 12px; font-size: 2rem; }}
        .app-card p:not(.eyebrow) {{ max-width: 360px; margin: 0; color: var(--muted); }}
        .launch-button {{ width: fit-content; margin-top: auto; padding: 12px 0 2px; color: var(--ink); border-bottom: 2px solid var(--accent); font: 700 14px 'Trebuchet MS', sans-serif; text-decoration: none; }}
        .launch-button span {{ margin-left: 12px; color: var(--accent); font-size: 20px; }}
        @media (max-width: 680px) {{ main {{ padding-top: 48px; }} .app-grid {{ grid-template-columns: 1fr; }} .app-card {{ min-height: 240px; }} }}
    </style>
</head>
<body><main>
    <p class="kicker">AGENTICWORKFORCE / LOCAL TOOLS</p>
    <h1>Choose your workspace.</h1>
    <p class="intro">A single starting point for shaping requirements and turning them into testable software.</p>
    <section class="app-grid" aria-label="Available applications">{cards}</section>
</main></body>
</html>"""
        payload = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"[master] {format % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer((MASTER_HOST, MASTER_PORT), MasterRequestHandler)
    print(f"AgenticWorkforce launcher: http://{MASTER_HOST}:{MASTER_PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()