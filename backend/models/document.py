from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    PNG = "png"
    JPEG = "jpeg"
    JPG = "jpg"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PARSING = "parsing"
    STRUCTURING = "structuring"
    VALIDATING = "validating"
    HIGHLIGHTING = "highlighting"
    STORING = "storing"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    x: float = Field(..., description="X coordinate (0-1 normalized)")
    y: float = Field(..., description="Y coordinate (0-1 normalized)")
    width: float = Field(..., description="Width (0-1 normalized)")
    height: float = Field(..., description="Height (0-1 normalized)")


class VisualGrounding(BaseModel):
    page_number: int = Field(..., description="Page number (1-indexed)")
    bounding_box: BoundingBox = Field(..., description="Bounding box coordinates")
    confidence: float = Field(default=0.0, description="Extraction confidence score")


class ExtractedElement(BaseModel):
    id: str = Field(..., description="Unique element identifier")
    type: str = Field(..., description="Element type (text, table, form_field, image, etc.)")
    content: Union[str, Dict[str, Any]] = Field(..., description="Extracted content")
    parent_id: Optional[str] = Field(None, description="Parent element ID for hierarchy")
    children_ids: List[str] = Field(default_factory=list, description="Child element IDs")
    grounding: VisualGrounding = Field(..., description="Visual grounding information")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    confidence: float = Field(default=0.0, description="Extraction confidence score")
    validated: bool = Field(default=False, description="Human validation status")
    corrections: Optional[Dict[str, Any]] = Field(None, description="Human corrections")


class DocumentMetadata(BaseModel):
    filename: str
    file_size: int
    document_type: DocumentType
    page_count: int
    upload_timestamp: datetime
    processing_start: Optional[datetime] = None
    processing_end: Optional[datetime] = None
    ocr_languages: List[str] = Field(default_factory=list)
    ocr_models_used: List[str] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    transaction_id: str
    status: ProcessingStatus
    metadata: DocumentMetadata
    extracted_elements: List[ExtractedElement] = Field(default_factory=list)
    raw_text: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_log: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UploadResponse(BaseModel):
    transaction_id: str
    status: ProcessingStatus
    message: str


class StatusResponse(BaseModel):
    transaction_id: str
    status: ProcessingStatus
    progress: float = Field(default=0.0, description="Processing progress (0-100)")
    message: Optional[str] = None
    error: Optional[str] = None


class CorrectionRequest(BaseModel):
    element_id: str
    corrected_content: Union[str, Dict[str, Any]]
    corrected_type: Optional[str] = None
    notes: Optional[str] = None


class GroundingRequest(BaseModel):
    chunk_id: str


class GroundingResponse(BaseModel):
    chunk_id: str
    page_number: int
    bounding_box: BoundingBox
    cropped_image_base64: Optional[str] = None
    context: Optional[str] = None
