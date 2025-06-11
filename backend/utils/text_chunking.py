"""
Utilities for chunking text and elements to avoid token limits
"""

import asyncio
import logging
from typing import List, Dict, Any, TypeVar, Callable, Awaitable

logger = logging.getLogger(__name__)

T = TypeVar('T')

def chunk_text(text: str, max_chunk_size: int = 4000) -> List[str]:
    """
    Split text into chunks of approximately max_chunk_size characters.
    Try to split at paragraph boundaries when possible.
    
    Args:
        text: Text to split into chunks
        max_chunk_size: Maximum size of each chunk in characters
        
    Returns:
        List of text chunks
    """
    # If text is small enough, return as is
    if len(text) <= max_chunk_size:
        return [text]
    
    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the chunk size
        if len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            # If current chunk is not empty, add it to chunks
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            
            # If paragraph itself is too large, split it further
            if len(paragraph) > max_chunk_size:
                sentences = paragraph.split(". ")
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 2 > max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk)
                            current_chunk = ""
                        
                        # If sentence is still too large, split by character
                        if len(sentence) > max_chunk_size:
                            for i in range(0, len(sentence), max_chunk_size):
                                chunks.append(sentence[i:i+max_chunk_size])
                        else:
                            current_chunk = sentence
                    else:
                        if current_chunk:
                            current_chunk += ". " + sentence
                        else:
                            current_chunk = sentence
            else:
                current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

def chunk_elements(elements: List[Dict[str, Any]], max_elements_per_chunk: int = 50) -> List[List[Dict[str, Any]]]:
    """
    Split elements into chunks of max_elements_per_chunk.
    Try to keep related elements together when possible.
    
    Args:
        elements: List of elements to split
        max_elements_per_chunk: Maximum number of elements per chunk
        
    Returns:
        List of element chunks
    """
    if len(elements) <= max_elements_per_chunk:
        return [elements]
    
    chunks = []
    current_chunk = []
    current_page = None
    
    for element in elements:
        # Try to keep elements from the same page together
        page_num = None
        if isinstance(element, dict):
            if 'grounding' in element and isinstance(element['grounding'], dict):
                page_num = element['grounding'].get('page_number')
            elif 'page_number' in element:
                page_num = element['page_number']
        
        # If we're starting a new page and the current chunk is getting large
        if page_num != current_page and len(current_chunk) > max_elements_per_chunk * 0.8:
            chunks.append(current_chunk)
            current_chunk = []
        
        current_chunk.append(element)
        current_page = page_num
        
        # If we've reached the maximum chunk size, start a new chunk
        if len(current_chunk) >= max_elements_per_chunk:
            chunks.append(current_chunk)
            current_chunk = []
    
    # Add the last chunk if not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

async def process_chunks_with_rate_limit(
    chunks: List[T], 
    process_func: Callable[[T, int, int], Awaitable[Any]], 
    max_concurrent: int = 2,
    delay_between_chunks: float = 1.0
) -> List[Any]:
    """
    Process chunks with rate limiting to avoid API rate limits.
    
    Args:
        chunks: List of chunks to process
        process_func: Async function that processes a chunk (chunk, chunk_index, total_chunks)
        max_concurrent: Maximum number of concurrent tasks
        delay_between_chunks: Delay between chunk processing in seconds
        
    Returns:
        List of results from processing each chunk
    """
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)
    total_chunks = len(chunks)
    
    async def process_with_semaphore(chunk: T, index: int) -> Any:
        async with semaphore:
            logger.info(f"Processing chunk {index+1}/{total_chunks}")
            result = await process_func(chunk, index, total_chunks)
            await asyncio.sleep(delay_between_chunks)  # Add delay to avoid rate limits
            return result
    
    # Create tasks for all chunks
    tasks = [process_with_semaphore(chunk, i) for i, chunk in enumerate(chunks)]
    
    # Process chunks and collect results
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task
        results.append(result)
    
    return results
