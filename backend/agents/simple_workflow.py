import os
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import asyncio
from models.document import (
    ExtractedElement, VisualGrounding, BoundingBox, 
    ProcessingResult, ProcessingStatus, DocumentMetadata,
    DocumentType
)
from services.document_processor import processor
from services.storage import storage
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class DocumentProcessingState:
    """State object for document processing workflow"""
    
    def __init__(self):
        self.transaction_id: str = ""
        self.file_path: str = ""
        self.filename: str = ""
        self.raw_text: str = ""
        self.raw_elements: List[Dict] = []
        self.extracted_elements: List[ExtractedElement] = []
        self.structured_data: Dict[str, Any] = {}
        self.metadata: Optional[DocumentMetadata] = None
        self.status: ProcessingStatus = ProcessingStatus.PENDING
        self.error_message: Optional[str] = None
        self.processing_log: List[str] = []
        self.confidence_threshold: float = 0.7


class SimpleDocumentWorkflow:
    """Simplified document processing workflow without LangGraph"""
    
    async def process_document(self, file_path: str, filename: str) -> str:
        """Process document through the workflow"""
        try:
            transaction_id = str(uuid.uuid4())
            
            # Initialize state
            state = DocumentProcessingState()
            state.transaction_id = transaction_id
            state.file_path = file_path
            state.filename = filename
            
            # Create initial result in storage
            initial_metadata = DocumentMetadata(
                filename=filename,
                file_size=os.path.getsize(file_path),
                document_type=DocumentType.PDF if filename.lower().endswith('.pdf') 
                           else DocumentType.PNG if filename.lower().endswith('.png')
                           else DocumentType.JPEG,
                page_count=1,  # Will be updated after processing
                upload_timestamp=datetime.utcnow(),
                ocr_languages=['en'],
                ocr_models_used=['tesseract']
            )
            
            initial_result = ProcessingResult(
                transaction_id=transaction_id,
                status=ProcessingStatus.PENDING,
                metadata=initial_metadata,
                processing_log=[f"Started processing: {datetime.utcnow()}"]
            )
            await storage.store_result(initial_result)
            
            logger.info(f"Starting workflow for transaction: {transaction_id}")
            
            # Execute workflow steps
            state = await self._parse_step(state)
            if state.status == ProcessingStatus.FAILED:
                return transaction_id
                
            state = await self._structure_step(state)
            if state.status == ProcessingStatus.FAILED:
                return transaction_id
                
            state = await self._validate_step(state)
            if state.status == ProcessingStatus.FAILED:
                return transaction_id
                
            state = await self._highlight_step(state)
            if state.status == ProcessingStatus.FAILED:
                return transaction_id
                
            state = await self._store_step(state)
            
            logger.info(f"Workflow completed for transaction: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            raise
    
    async def _parse_step(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Parse document and extract raw content"""
        try:
            logger.info(f"ParseAgent: Processing {state.filename}")
            state.status = ProcessingStatus.PARSING
            state.processing_log.append(f"Started parsing: {datetime.utcnow()}")
            
            # Update status in storage
            await storage.update_status(state.transaction_id, ProcessingStatus.PARSING)
            
            # Process document
            raw_text, raw_elements, metadata = await processor.process_document(
                state.file_path, state.filename
            )
            
            state.raw_text = raw_text
            state.raw_elements = raw_elements
            state.metadata = metadata
            state.processing_log.append(f"Parsed {len(raw_elements)} elements")
            
            logger.info(f"ParseAgent: Extracted {len(raw_elements)} elements")
            return state
            
        except Exception as e:
            logger.error(f"ParseAgent error: {e}")
            state.error_message = str(e)
            state.status = ProcessingStatus.FAILED
            await storage.update_status(state.transaction_id, ProcessingStatus.FAILED, str(e))
            return state
    
    async def _structure_step(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Structure raw elements into hierarchical format"""
        try:
            logger.info(f"StructureAgent: Structuring {len(state.raw_elements)} elements")
            state.status = ProcessingStatus.STRUCTURING
            state.processing_log.append(f"Started structuring: {datetime.utcnow()}")
            
            # Update status in storage
            await storage.update_status(state.transaction_id, ProcessingStatus.STRUCTURING)
            
            extracted_elements = []
            
            # Group elements by page and type
            pages = {}
            for element in state.raw_elements:
                page_num = element.get('page', 1)
                if page_num not in pages:
                    pages[page_num] = {'text': [], 'tables': [], 'other': []}
                
                if element.get('type') == 'table':
                    pages[page_num]['tables'].append(element)
                elif element.get('type') == 'text':
                    pages[page_num]['text'].append(element)
                else:
                    pages[page_num]['other'].append(element)
            
            # Create structured elements
            for page_num, page_elements in pages.items():
                # Create page container
                page_id = f"page_{page_num}"
                page_element = ExtractedElement(
                    id=page_id,
                    type="page",
                    content=f"Page {page_num}",
                    grounding=VisualGrounding(
                        page_number=page_num,
                        bounding_box=BoundingBox(x=0, y=0, width=1, height=1),
                        confidence=1.0
                    ),
                    confidence=1.0
                )
                extracted_elements.append(page_element)
                
                # Add text elements
                for i, text_elem in enumerate(page_elements['text']):
                    elem_id = f"text_{page_num}_{i}"
                    bbox = text_elem.get('bbox', {})
                    
                    element = ExtractedElement(
                        id=elem_id,
                        type="text",
                        content=text_elem.get('text', ''),
                        parent_id=page_id,
                        grounding=VisualGrounding(
                            page_number=page_num,
                            bounding_box=BoundingBox(
                                x=bbox.get('x', 0),
                                y=bbox.get('y', 0),
                                width=bbox.get('width', 0.1),
                                height=bbox.get('height', 0.05)
                            ),
                            confidence=text_elem.get('confidence', 0.8)
                        ),
                        confidence=text_elem.get('confidence', 0.8)
                    )
                    extracted_elements.append(element)
                    page_element.children_ids.append(elem_id)
                
                # Add table elements
                for i, table_elem in enumerate(page_elements['tables']):
                    elem_id = f"table_{page_num}_{i}"
                    bbox = table_elem.get('bbox', {})
                    
                    element = ExtractedElement(
                        id=elem_id,
                        type="table",
                        content={
                            "rows": table_elem.get('content', []),
                            "table_id": table_elem.get('table_id', elem_id)
                        },
                        parent_id=page_id,
                        grounding=VisualGrounding(
                            page_number=page_num,
                            bounding_box=BoundingBox(
                                x=bbox.get('x', 0),
                                y=bbox.get('y', 0),
                                width=bbox.get('width', 0.8),
                                height=bbox.get('height', 0.3)
                            ),
                            confidence=0.9
                        ),
                        confidence=0.9
                    )
                    extracted_elements.append(element)
                    page_element.children_ids.append(elem_id)
            
            state.extracted_elements = extracted_elements
            state.processing_log.append(f"Structured into {len(extracted_elements)} elements")
            
            # Use LLM to enhance document structure if available
            try:
                logger.info(f"Enhancing structure with LLM for {len(extracted_elements)} elements")
                element_dicts = [elem.dict() for elem in extracted_elements]
                enhanced_elements = await llm_service.enhance_document_structure(element_dicts)
                
                if enhanced_elements and isinstance(enhanced_elements, list):
                    # Convert back to ExtractedElement objects
                    try:
                        new_elements = []
                        for elem in enhanced_elements:
                            # Handle potential missing fields by using the original element as a base
                            new_elem = ExtractedElement(**elem)
                            new_elements.append(new_elem)
                        
                        if new_elements:
                            state.extracted_elements = new_elements
                            state.processing_log.append(f"Enhanced structure using LLM: {len(new_elements)} elements")
                            logger.info(f"Successfully enhanced structure: {len(new_elements)} elements")
                    except Exception as conversion_error:
                        logger.error(f"Error converting enhanced elements: {conversion_error}")
            except Exception as llm_error:
                logger.warning(f"LLM enhancement failed, using basic structure: {llm_error}")
            
            logger.info(f"StructureAgent: Created {len(state.extracted_elements)} structured elements")
            return state
            
        except Exception as e:
            logger.error(f"StructureAgent error: {e}")
            state.error_message = str(e)
            state.status = ProcessingStatus.FAILED
            await storage.update_status(state.transaction_id, ProcessingStatus.FAILED, str(e))
            return state
    
    async def _validate_step(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Validate extracted elements and assign confidence scores"""
        try:
            logger.info(f"ValidateAgent: Validating {len(state.extracted_elements)} elements")
            state.status = ProcessingStatus.VALIDATING
            state.processing_log.append(f"Started validation: {datetime.utcnow()}")
            
            # Update status in storage
            await storage.update_status(state.transaction_id, ProcessingStatus.VALIDATING)
            
            validated_count = 0
            
            # Basic validation for all elements
            for element in state.extracted_elements:
                # Basic validation rules
                if element.type == "text":
                    # Text validation
                    if isinstance(element.content, str) and len(element.content.strip()) > 0:
                        element.confidence = max(element.confidence, 0.8)
                        validated_count += 1
                    else:
                        element.confidence = 0.3
                
                elif element.type == "table":
                    # Table validation
                    if isinstance(element.content, dict) and element.content.get('rows'):
                        element.confidence = max(element.confidence, 0.9)
                        validated_count += 1
                    else:
                        element.confidence = 0.4
                
                elif element.type == "page":
                    # Page containers are always valid
                    element.confidence = 1.0
                    validated_count += 1
                
                # Mark as validated if confidence is above threshold
                element.validated = element.confidence >= state.confidence_threshold
            
            # Use LLM for enhanced validation if available
            try:
                # Extract a sample of text for context
                sample_text = state.raw_text[:5000]  # Limit to first 5K chars
                
                # Convert elements to dict for LLM processing
                elements_dict = [elem.dict() for elem in state.extracted_elements]
                
                logger.info(f"Validating {len(elements_dict)} elements with LLM")
                
                # Get validation results from LLM
                validation_results = await llm_service.validate_extraction(
                    sample_text, 
                    elements_dict
                )
                
                if validation_results and isinstance(validation_results, dict):
                    # Apply LLM validation results if available
                    if "elements" in validation_results:
                        validated_elements = validation_results["elements"]
                        updated_count = 0
                        
                        # Create a mapping of element IDs to their indices
                        element_id_map = {elem.id: i for i, elem in enumerate(state.extracted_elements)}
                        
                        for val_elem in validated_elements:
                            if "id" in val_elem and val_elem["id"] in element_id_map:
                                idx = element_id_map[val_elem["id"]]
                                # Update confidence based on LLM validation
                                if "confidence" in val_elem:
                                    state.extracted_elements[idx].confidence = val_elem["confidence"]
                                    # Update validation status
                                    state.extracted_elements[idx].validated = (
                                        val_elem["confidence"] >= state.confidence_threshold
                                    )
                                    updated_count += 1
                        
                        logger.info(f"Updated {updated_count} elements with LLM validation results")
                    
                    state.processing_log.append(f"Enhanced validation using LLM: updated {updated_count} elements")
            except Exception as llm_error:
                logger.warning(f"LLM validation failed, using basic validation: {llm_error}")
            
            # Final count of validated elements
            validated_count = sum(1 for elem in state.extracted_elements if elem.validated)
            state.processing_log.append(f"Validated {validated_count} elements")
            
            logger.info(f"ValidateAgent: Validated {validated_count}/{len(state.extracted_elements)} elements")
            return state
            
        except Exception as e:
            logger.error(f"ValidateAgent error: {e}")
            state.error_message = str(e)
            state.status = ProcessingStatus.FAILED
            await storage.update_status(state.transaction_id, ProcessingStatus.FAILED, str(e))
            return state
    
    async def _highlight_step(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Create visual highlights for extracted elements"""
        try:
            logger.info(f"HighlightAgent: Creating highlights for {len(state.extracted_elements)} elements")
            state.status = ProcessingStatus.HIGHLIGHTING
            state.processing_log.append(f"Started highlighting: {datetime.utcnow()}")
            
            # Update status in storage
            await storage.update_status(state.transaction_id, ProcessingStatus.HIGHLIGHTING)
            
            # Enhance grounding information
            for element in state.extracted_elements:
                if element.type != "page":
                    # Add metadata for visual rendering
                    element.metadata.update({
                        "highlight_color": self._get_highlight_color(element.type),
                        "border_width": 2,
                        "opacity": 0.3
                    })
            
            state.processing_log.append("Created visual highlights")
            
            logger.info("HighlightAgent: Created visual highlights")
            return state
            
        except Exception as e:
            logger.error(f"HighlightAgent error: {e}")
            state.error_message = str(e)
            state.status = ProcessingStatus.FAILED
            await storage.update_status(state.transaction_id, ProcessingStatus.FAILED, str(e))
            return state
    
    def _get_highlight_color(self, element_type: str) -> str:
        """Get highlight color based on element type"""
        colors = {
            "text": "#3B82F6",      # Blue
            "table": "#10B981",     # Green
            "form_field": "#F59E0B", # Yellow
            "image": "#8B5CF6",     # Purple
            "header": "#EF4444",    # Red
        }
        return colors.get(element_type, "#6B7280")  # Gray default
    
    async def _store_step(self, state: DocumentProcessingState) -> DocumentProcessingState:
        """Store final processing results"""
        try:
            logger.info(f"StoreAgent: Storing results for {state.transaction_id}")
            state.status = ProcessingStatus.STORING
            state.processing_log.append(f"Started storing: {datetime.utcnow()}")
            
            # Update status in storage
            await storage.update_status(state.transaction_id, ProcessingStatus.STORING)
            
            # Create structured data summary
            state.structured_data = {
                "summary": {
                    "total_elements": len(state.extracted_elements),
                    "pages": state.metadata.page_count if state.metadata else 1,
                    "text_elements": len([e for e in state.extracted_elements if e.type == "text"]),
                    "table_elements": len([e for e in state.extracted_elements if e.type == "table"]),
                    "validated_elements": len([e for e in state.extracted_elements if e.validated])
                },
                "elements_by_page": self._group_elements_by_page(state.extracted_elements)
            }
            
            # Create final result
            result = ProcessingResult(
                transaction_id=state.transaction_id,
                status=ProcessingStatus.COMPLETED,
                metadata=state.metadata,
                extracted_elements=state.extracted_elements,
                raw_text=state.raw_text,
                structured_data=state.structured_data,
                processing_log=state.processing_log,
                updated_at=datetime.utcnow()
            )
            
            # Store result
            await storage.store_result(result)
            
            state.status = ProcessingStatus.COMPLETED
            state.processing_log.append(f"Completed processing: {datetime.utcnow()}")
            
            logger.info(f"StoreAgent: Successfully stored results for {state.transaction_id}")
            return state
            
        except Exception as e:
            logger.error(f"StoreAgent error: {e}")
            state.error_message = str(e)
            state.status = ProcessingStatus.FAILED
            await storage.update_status(state.transaction_id, ProcessingStatus.FAILED, str(e))
            return state
    
    def _group_elements_by_page(self, elements: List[ExtractedElement]) -> Dict[int, List[Dict]]:
        """Group elements by page number"""
        pages = {}
        for element in elements:
            page_num = element.grounding.page_number
            if page_num not in pages:
                pages[page_num] = []
            
            pages[page_num].append({
                "id": element.id,
                "type": element.type,
                "content": element.content if isinstance(element.content, str) else str(element.content)[:100],
                "confidence": element.confidence,
                "validated": element.validated
            })
        
        return pages


# Global workflow instance
workflow = SimpleDocumentWorkflow()
