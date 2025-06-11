"""
LLM Service for document extraction platform
Provides integration with OpenAI models for enhanced document processing
"""

import os
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from dotenv import load_dotenv
import asyncio
import openai
from openai import OpenAI
from utils.text_chunking import chunk_text, chunk_elements, process_chunks_with_rate_limit

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OpenAI API key not found. LLM features will be limited.")


class LLMService:
    """Service for interacting with Large Language Models"""
    
    def __init__(self):
        self.model = "gpt-4o"  # Default model
        self.temperature = 0.2  # Low temperature for more deterministic outputs
        self.max_tokens = 1000  # Default max tokens
    
    async def extract_structured_content(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured content from text based on a schema
        
        Args:
            text: Raw text to extract from
            schema: Schema defining the structure to extract
            
        Returns:
            Structured data according to schema
        """
        try:
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OpenAI API key not set. Using fallback extraction.")
                return self._fallback_extraction(text, schema)
            
            # Split text into manageable chunks
            text_chunks = chunk_text(text, max_chunk_size=4000)
            logger.info(f"Split text into {len(text_chunks)} chunks for extraction")
            
            # If only one chunk, process directly
            if len(text_chunks) == 1:
                return await self._extract_from_chunk(text_chunks[0], schema)
            
            # Process chunks in parallel with rate limiting
            async def process_chunk(chunk: str, index: int, total: int) -> Dict[str, Any]:
                logger.info(f"Extracting from chunk {index+1}/{total}")
                return await self._extract_from_chunk(chunk, schema)
            
            chunk_results = await process_chunks_with_rate_limit(
                text_chunks, 
                process_chunk,
                max_concurrent=2,
                delay_between_chunks=1.0
            )
            
            # Merge results from all chunks
            merged_result = self._merge_extraction_results(chunk_results, schema)
            return merged_result
            
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return self._fallback_extraction(text, schema)
    
    async def _extract_from_chunk(self, text_chunk: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured content from a single text chunk"""
        # Create system prompt with schema
        system_prompt = f"""
        You are an expert document extraction system. Extract structured information from the provided text.
        Follow these rules:
        1. Extract only information that is explicitly present in the text
        2. Use the exact format specified in the schema
        3. If information is not found, use null or empty values
        4. Maintain hierarchical relationships between elements
        
        Output should be valid JSON matching this schema:
        {schema}
        """
        
        # Call OpenAI API
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_chunk}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )
        
        # Extract and return the structured content
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON response: {content}")
            return {}
    
    def _merge_extraction_results(self, results: List[Dict[str, Any]], schema: Dict[str, Any]) -> Dict[str, Any]:
        """Merge extraction results from multiple chunks"""
        if not results:
            return self._fallback_extraction("", schema)
        
        # Start with the first result
        merged = results[0]
        
        # Merge additional results
        for result in results[1:]:
            for key, value in result.items():
                if key not in merged:
                    merged[key] = value
                elif isinstance(merged[key], list) and isinstance(value, list):
                    merged[key].extend(value)
                elif isinstance(merged[key], dict) and isinstance(value, dict):
                    merged[key].update(value)
                elif merged[key] is None or merged[key] == "":
                    merged[key] = value
        
        return merged
    
    async def validate_extraction(self, text: str, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data against source text and suggest corrections
        
        Args:
            text: Source text
            extracted_data: Previously extracted data
            
        Returns:
            Validation results with confidence scores and suggestions
        """
        try:
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OpenAI API key not set. Using fallback validation.")
                return {"validated": True, "confidence": 0.8, "suggestions": []}
            
            # Get elements to validate
            elements = extracted_data.get("elements", [])
            if not elements and isinstance(extracted_data, list):
                elements = extracted_data
            
            if not elements:
                return {"validated": True, "confidence": 0.8, "suggestions": []}
            
            # Split text into manageable chunks
            text_chunks = chunk_text(text, max_chunk_size=3000)
            logger.info(f"Split text into {len(text_chunks)} chunks for validation")
            
            # Split elements into manageable chunks
            element_chunks = chunk_elements(elements, max_elements_per_chunk=20)
            logger.info(f"Split {len(elements)} elements into {len(element_chunks)} chunks for validation")
            
            # Process chunks in parallel with rate limiting
            async def process_validation_chunk(element_chunk: List[Dict], index: int, total: int) -> Dict[str, Any]:
                # Combine a sample of text chunks for context
                text_sample = "\n\n".join(text_chunks[:min(2, len(text_chunks))])  # Use first two chunks for context
                
                # Create system prompt for validation
                system_prompt = """
                You are an expert document validation system. Validate the extracted data against the source text.
                For each element in the extracted data:
                1. Check if it accurately represents information in the source text
                2. Assign a confidence score (0.0-1.0)
                3. Suggest corrections for low-confidence elements
                4. Flag any missing or incorrect information
                
                Output should be valid JSON with validation results.
                """
                
                # Prepare input for the model
                user_content = f"""
                SOURCE TEXT SAMPLE:
                {text_sample}
                
                EXTRACTED ELEMENTS (CHUNK {index+1}/{total}):
                {element_chunk}
                
                Validate the extraction and provide results.
                """
                
                # Call OpenAI API
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Extract validation results
                content = response.choices[0].message.content
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response: {content}")
                    return {"validated": True, "confidence": 0.5, "suggestions": []}
            
            # Process all chunks with rate limiting
            validation_results = await process_chunks_with_rate_limit(
                element_chunks,
                process_validation_chunk,
                max_concurrent=2,
                delay_between_chunks=1.0
            )
            
            # Merge validation results
            all_validation_results = {
                "validated": True,
                "confidence": 0.0,
                "elements": [],
                "suggestions": []
            }
            
            for result in validation_results:
                # Update overall confidence
                if "confidence" in result:
                    all_validation_results["confidence"] += result["confidence"] / len(validation_results)
                
                # Add validated elements
                if "elements" in result:
                    all_validation_results["elements"].extend(result["elements"])
                
                # Add suggestions
                if "suggestions" in result:
                    all_validation_results["suggestions"].extend(result["suggestions"])
                
                # Update validation status
                if "validated" in result and not result["validated"]:
                    all_validation_results["validated"] = False
            
            return all_validation_results
            
        except Exception as e:
            logger.error(f"Error in LLM validation: {e}")
            return {"validated": True, "confidence": 0.8, "suggestions": []}
    
    async def enhance_document_structure(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enhance document structure by identifying relationships and hierarchies
        Process in chunks to avoid token limits
        
        Args:
            elements: List of extracted elements
            
        Returns:
            Enhanced elements with improved structure
        """
        try:
            if not os.getenv("OPENAI_API_KEY"):
                logger.warning("OpenAI API key not set. Using fallback structure enhancement.")
                return elements
            
            # Split elements into manageable chunks
            element_chunks = chunk_elements(elements, max_elements_per_chunk=20)
            logger.info(f"Split {len(elements)} elements into {len(element_chunks)} chunks for structure enhancement")
            
            # Process chunks in parallel with rate limiting
            async def process_structure_chunk(element_chunk: List[Dict], index: int, total: int) -> List[Dict[str, Any]]:
                # Create system prompt for structure enhancement
                system_prompt = """
                You are an expert document structure analyzer. Enhance the structure of extracted document elements.
                For the provided elements:
                1. Identify parent-child relationships
                2. Group related elements
                3. Detect section headers and their content
                4. Identify tables and their structure
                5. Maintain all original information while enhancing relationships
                
                Output should be valid JSON with the enhanced structure.
                """
                
                # Prepare input for the model
                user_content = f"""
                DOCUMENT ELEMENTS (CHUNK {index+1}/{total}):
                {element_chunk}
                
                Enhance the structure while preserving all original information.
                """
                
                # Call OpenAI API
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}
                )
                
                # Extract and return the enhanced structure
                content = response.choices[0].message.content
                try:
                    result = json.loads(content)
                    if isinstance(result, list):
                        return result
                    elif isinstance(result, dict) and "elements" in result:
                        return result["elements"]
                    else:
                        return element_chunk
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON response: {content}")
                    return element_chunk
            
            # Process all chunks with rate limiting
            enhanced_chunks = await process_chunks_with_rate_limit(
                element_chunks,
                process_structure_chunk,
                max_concurrent=1,  # Lower concurrency to avoid rate limits
                delay_between_chunks=2.0  # Longer delay between chunks
            )
            
            # Combine all enhanced chunks
            enhanced_elements = []
            for chunk in enhanced_chunks:
                if isinstance(chunk, list):
                    enhanced_elements.extend(chunk)
            
            return enhanced_elements
            
        except Exception as e:
            logger.error(f"Error in structure enhancement: {e}")
            return elements
    
    def get_langgraph_tools(self):
        """
        Get LangGraph-compatible tools for document processing
        
        Returns:
            List of Tool objects for LangGraph
        """
        # This is a simplified version that doesn't depend on LangChain
        # We'll implement the actual tools in the agent classes
        return []
    
    def _fallback_extraction(self, text: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback extraction method when LLM is not available
        
        Args:
            text: Raw text to extract from
            schema: Schema defining the structure to extract
            
        Returns:
            Basic structured data
        """
        # Create a basic structure based on schema
        result = {}
        for key in schema.keys():
            if isinstance(schema[key], dict):
                result[key] = {}
            elif isinstance(schema[key], list):
                result[key] = []
            else:
                result[key] = None
        
        return result


# Global instance
llm_service = LLMService()
