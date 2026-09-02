from pathlib import Path
from typing import List
import pandas as pd
from src.models.document_models import DocumentModel, TableModel, SourceLocation
from src.utils.logger import get_logger

logger = get_logger("excel_parser")


def parse_excel(path: Path) -> DocumentModel:
    """Parse Excel files (xlsx/xlsm/csv) into a DocumentModel with tables per sheet."""
    try:
        # read all sheets
        data = pd.read_excel(str(path), sheet_name=None, engine="openpyxl")
    except Exception:
        # fallback for CSV
        try:
            df = pd.read_csv(str(path))
            data = {"sheet1": df}
        except Exception:
            logger.exception("Failed to read Excel/CSV: %s", path)
            data = {}

    tables: List[TableModel] = []
    for sheet_name, df in data.items():
        df = df.fillna("")
        headers = [str(c) for c in df.columns.tolist()]
        rows = df.astype(str).values.tolist()
        loc = SourceLocation(filename=str(path), sheet_name=sheet_name)
        tables.append(TableModel(headers=headers, rows=rows, location=loc))

    document = DocumentModel(
        filename=str(path.name),
        document_type="excel",
        tables=tables,
        metadata={},
        source_locations=[{"filename": str(path)}],
    )
    return document
