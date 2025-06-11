import os
import io
import base64
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from PIL import Image
import pytesseract
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path, convert_from_bytes
import cv2
import numpy as np
import logging
from models.document import (
    ExtractedElement, VisualGrounding, BoundingBox, 
    DocumentType, DocumentMetadata
)

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Core document processing service"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg']
        
    def is_supported_format(self, filename: str) -> bool:
        """Check if file format is supported"""
        ext = os.path.splitext(filename.lower())[1]
        return ext in self.supported_formats
    
    async def extract_text_from_pdf(self, file_path: str) -> Tuple[str, List[Dict]]:
        """Extract text from PDF using pdfplumber for better structure"""
        try:
            text_blocks = []
            full_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text with bounding boxes
                    chars = page.chars
                    words = page.extract_words()
                    
                    page_text = page.extract_text() or ""
                    full_text += f"\n--- Page {page_num} ---\n{page_text}\n"
                    
                    # Group words into text blocks
                    for word in words:
                        text_blocks.append({
                            'text': word['text'],
                            'page': page_num,
                            'bbox': {
                                'x': word['x0'] / page.width,
                                'y': word['top'] / page.height,
                                'width': (word['x1'] - word['x0']) / page.width,
                                'height': (word['bottom'] - word['top']) / page.height
                            },
                            'type': 'text'
                        })
            
            return full_text, text_blocks
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return "", []
    
    async def extract_tables_from_pdf(self, file_path: str) -> List[Dict]:
        """Extract tables from PDF"""
        try:
            tables = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    
                    for i, table in enumerate(page_tables):
                        if table:
                            # Calculate approximate bounding box for table
                            bbox = page.bbox
                            tables.append({
                                'content': table,
                                'page': page_num,
                                'table_id': f"table_{page_num}_{i}",
                                'bbox': {
                                    'x': 0.1,  # Approximate - would need more sophisticated detection
                                    'y': 0.1,
                                    'width': 0.8,
                                    'height': 0.3
                                },
                                'type': 'table'
                            })
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            return []
    
    async def extract_from_image(self, file_path: str) -> Tuple[str, List[Dict]]:
        """Extract text from image using OCR"""
        try:
            image = Image.open(file_path)
            
            # Get OCR data with bounding boxes
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            text_blocks = []
            full_text = ""
            
            # Process OCR results
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                if text and int(ocr_data['conf'][i]) > 30:  # Confidence threshold
                    x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], 
                                 ocr_data['width'][i], ocr_data['height'][i])
                    
                    text_blocks.append({
                        'text': text,
                        'page': 1,
                        'bbox': {
                            'x': x / image.width,
                            'y': y / image.height,
                            'width': w / image.width,
                            'height': h / image.height
                        },
                        'confidence': int(ocr_data['conf'][i]) / 100.0,
                        'type': 'text'
                    })
                    
                    full_text += text + " "
            
            return full_text.strip(), text_blocks
            
        except Exception as e:
            logger.error(f"Error extracting from image: {e}")
            return "", []
    
    async def process_document(self, file_path: str, filename: str) -> Tuple[str, List[Dict], DocumentMetadata]:
        """Main document processing function"""
        try:
            file_ext = os.path.splitext(filename.lower())[1]
            file_size = os.path.getsize(file_path)
            
            # Determine document type
            if file_ext == '.pdf':
                doc_type = DocumentType.PDF
                full_text, elements = await self.extract_text_from_pdf(file_path)
                
                # Also extract tables
                tables = await self.extract_tables_from_pdf(file_path)
                elements.extend(tables)
                
                # Get page count
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    page_count = len(pdf_reader.pages)
                    
            else:
                doc_type = DocumentType.PNG if file_ext == '.png' else DocumentType.JPEG
                full_text, elements = await self.extract_from_image(file_path)
                page_count = 1
            
            # Create metadata
            metadata = DocumentMetadata(
                filename=filename,
                file_size=file_size,
                document_type=doc_type,
                page_count=page_count,
                upload_timestamp=datetime.utcnow(),
                ocr_languages=['en'],  # Default to English
                ocr_models_used=['tesseract']
            )
            
            return full_text, elements, metadata
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            raise
    
    async def get_page_image(self, file_path: str, page_number: int = 1) -> Optional[str]:
        """Get base64 encoded image of a specific page"""
        try:
            file_ext = os.path.splitext(file_path.lower())[1]
            
            if file_ext == '.pdf':
                # Convert PDF page to image
                images = convert_from_path(file_path, first_page=page_number, 
                                        last_page=page_number, dpi=150)
                if images:
                    img = images[0]
                else:
                    return None
            else:
                # Load image directly
                img = Image.open(file_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Error getting page image: {e}")
            return None
    
    async def crop_element_image(self, file_path: str, page_number: int, 
                               bounding_box: BoundingBox) -> Optional[str]:
        """Crop element from document based on bounding box"""
        try:
            # Get page image
            page_img_b64 = await self.get_page_image(file_path, page_number)
            if not page_img_b64:
                return None
            
            # Decode image
            img_data = base64.b64decode(page_img_b64)
            img = Image.open(io.BytesIO(img_data))
            
            # Calculate crop coordinates
            width, height = img.size
            left = int(bounding_box.x * width)
            top = int(bounding_box.y * height)
            right = int((bounding_box.x + bounding_box.width) * width)
            bottom = int((bounding_box.y + bounding_box.height) * height)
            
            # Crop image
            cropped = img.crop((left, top, right, bottom))
            
            # Convert to base64
            buffer = io.BytesIO()
            cropped.save(buffer, format='PNG')
            cropped_b64 = base64.b64encode(buffer.getvalue()).decode()
            
            return cropped_b64
            
        except Exception as e:
            logger.error(f"Error cropping element image: {e}")
            return None


# Global processor instance
processor = DocumentProcessor()
