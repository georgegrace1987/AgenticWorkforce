import os

import app as master


def test_resolve_python_uses_project_venv_when_present(tmp_path):
    project_root = tmp_path / "AgenticWorkforce"
    if os.name == "nt":
        expected = project_root / ".venv" / "Scripts" / "python.exe"
    else:
        expected = project_root / ".venv" / "bin" / "python"

    expected.parent.mkdir(parents=True, exist_ok=True)
    expected.touch()

    result = master._resolve_python_executable(project_root)

    assert result == str(expected)
