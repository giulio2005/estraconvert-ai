from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum


class ColumnType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CURRENCY = "currency"


class DetectedColumn(BaseModel):
    id: str
    name: str
    type: ColumnType
    confidence: float = Field(ge=0.0, le=1.0)


class SelectedColumn(BaseModel):
    id: str
    name: str
    type: ColumnType
    output_name: str
    order: int


class FormatConfig(BaseModel):
    delimiter: Literal[",", ";", "|", "\t"] = ";"
    decimal_separator: Literal[".", ","] = ","
    thousands_separator: Literal[".", ",", " ", "none"] = "."
    date_format: str = "DD/MM/YYYY"
    encoding: Literal["UTF-8", "ISO-8859-1"] = "UTF-8"
    include_headers: bool = True


class DetectColumnsRequest(BaseModel):
    document_id: str


class DetectColumnsResponse(BaseModel):
    document_id: str
    columns: List[DetectedColumn]
    processing_time: float


class ExtractDataRequest(BaseModel):
    document_id: str
    selected_columns: List[SelectedColumn]
    format_config: FormatConfig


class ExtractDataResponse(BaseModel):
    document_id: str
    data: List[List[str]]
    rows_extracted: int
    processing_time: float


# Async Job Schemas

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: Optional[int] = None
    step: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
