from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class SourceLocation(BaseModel):
    filename: str
    page_number: Optional[int] = None
    sheet_name: Optional[str] = None
    slide_number: Optional[int] = None
    section: Optional[str] = None


class TableModel(BaseModel):
    headers: List[str]
    rows: List[List[str]]
    location: SourceLocation


class ImageModel(BaseModel):
    filename: str
    description: Optional[str] = None
    location: SourceLocation


class ParagraphModel(BaseModel):
    text: str
    location: SourceLocation


class DocumentModel(BaseModel):
    filename: str
    document_type: str
    sections: Optional[List[str]] = []
    paragraphs: Optional[List[ParagraphModel]] = []
    tables: Optional[List[TableModel]] = []
    images: Optional[List[ImageModel]] = []
    metadata: Optional[Dict[str, Any]] = {}
    source_locations: Optional[List[SourceLocation]] = []
