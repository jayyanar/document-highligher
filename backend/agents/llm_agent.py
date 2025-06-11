"""
LLM-powered agent for document processing
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from models.document import (
    ExtractedElement, ProcessingStatus, DocumentMetadata
)
from models.llm_models import (
    DocumentClassification, ExtractionSchema, ExtractionResult,
    ValidationResult, RelationshipEnhancement
)
from services.llm_service import llm_service

logger = logging.getLogger(__name__)


class LLMDocumentAgent:
    """LLM-powered agent for document processing using LangGraph"""
    
    def __init__(self):
        # Get LLM tools for LangGraph integration
        self.llm_tools = llm_service.get_langgraph_tools()
        
        # Create workflow graph
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> StateGraph:
        """Create LangGraph workflow for LLM processing"""
        
        # Create graph
        workflow = StateGraph(dict)
        
        # Add LLM-powered tool node
        llm_tool_node = ToolNode(tools=self.llm_tools)
        workflow.add_node("llm_tools", llm_tool_node)
        
        # Define conditional routing based on document type
        def route_by_document_type(state: Dict) -> str:
            doc_type = state.get("document_classification", {}).get("document_type", "unknown")
            if doc_type == "form":
                return "process_form"
            elif doc_type == "table":
                return "process_table"
            else:
                return "process_text"
        
        # Add processing nodes
        async def process_text(state: Dict) -> Dict:
            logger.info("Processing text document")
            # Process text document
            return state
        
        async def process_form(state: Dict) -> Dict:
            logger.info("Processing form document")
            # Process form document
            return state
        
        async def process_table(state: Dict) -> Dict:
            logger.info("Processing table document")
            # Process table document
            return state
        
        workflow.add_node("process_text", process_text)
        workflow.add_node("process_form", process_form)
        workflow.add_node("process_table", process_table)
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "llm_tools",
            route_by_document_type,
            {
                "process_text": "process_text",
                "process_form": "process_form",
                "process_table": "process_table"
            }
        )
        
        # Add final edges
        workflow.add_edge("process_text", END)
        workflow.add_edge("process_form", END)
        workflow.add_edge("process_table", END)
        
        # Set entry point
        workflow.set_entry_point("llm_tools")
        
        return workflow.compile()
    
    async def process_document(self, text: str, metadata: Optional[DocumentMetadata] = None) -> Dict[str, Any]:
        """
        Process document using LLM-powered workflow
        
        Args:
            text: Document text to process
            metadata: Optional document metadata
            
        Returns:
            Processing results
        """
        try:
            # Initialize state
            initial_state = {
                "text": text,
                "metadata": metadata.dict() if metadata else {},
                "status": ProcessingStatus.PENDING.value,
                "processing_log": [f"Started LLM processing: {datetime.utcnow()}"],
                "extracted_elements": [],
                "document_classification": None,
                "validation_results": None
            }
            
            # Run workflow
            logger.info("Starting LLM workflow")
            final_state = await self.workflow.ainvoke(initial_state)
            
            logger.info("LLM workflow completed")
            return final_state
            
        except Exception as e:
            logger.error(f"LLM workflow error: {e}")
            return {
                "status": ProcessingStatus.FAILED.value,
                "error_message": str(e),
                "processing_log": [f"Error in LLM processing: {e}"]
            }


# Global instance
llm_agent = LLMDocumentAgent()
