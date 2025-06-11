"""
Pydantic models for LLM interactions
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class DocumentClassification(BaseModel):
    """Document classification result"""
    document_type: str = Field(..., description="Type of document (e.g., invoice, contract, report)")
    confidence: float = Field(..., description="Confidence score for classification (0.0-1.0)")
    key_sections: List[str] = Field(default_factory=list, description="List of key sections identified")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExtractionSchema(BaseModel):
    """Schema for document extraction"""
    fields: Dict[str, Any] = Field(..., description="Fields to extract with their types")
    description: str = Field(default="", description="Description of the extraction task")
    examples: Optional[List[Dict[str, Any]]] = Field(default=None, description="Example extractions")


class ExtractionResult(BaseModel):
    """Result of document extraction"""
    extracted_data: Dict[str, Any] = Field(..., description="Extracted data according to schema")
    confidence: float = Field(..., description="Overall confidence score (0.0-1.0)")
    missing_fields: List[str] = Field(default_factory=list, description="Fields that couldn't be extracted")


class ValidationResult(BaseModel):
    """Result of document validation"""
    validated: bool = Field(..., description="Whether the document passed validation")
    confidence: float = Field(..., description="Overall confidence score (0.0-1.0)")
    field_scores: Dict[str, float] = Field(default_factory=dict, description="Confidence scores per field")
    suggestions: List[Dict[str, Any]] = Field(default_factory=list, description="Suggestions for corrections")


class RelationshipEnhancement(BaseModel):
    """Result of relationship enhancement"""
    elements: List[Dict[str, Any]] = Field(..., description="Enhanced elements with relationships")
    identified_sections: List[Dict[str, Any]] = Field(default_factory=list, description="Identified document sections")
    hierarchy: Dict[str, List[str]] = Field(default_factory=dict, description="Hierarchical relationships")
