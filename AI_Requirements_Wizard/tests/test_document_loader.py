from src.document_processing.document_loader import extract_document_text


def test_extracts_txt_and_csv() -> None:
    assert extract_document_text("requirements.txt", "Login is required.".encode()) == "Login is required."
    assert extract_document_text("requirements.csv", b"Role,Access\nAdmin,Full") == "Role | Access\nAdmin | Full"


def test_rejects_unsupported_extensions() -> None:
    try:
        extract_document_text("requirements.pdf", b"text")
    except ValueError as error:
        assert "Unsupported file type" in str(error)
    else:
        raise AssertionError("Expected unsupported extension to fail")
