import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from backend.services.document_processor import DocumentProcessor
from backend.models.document import DocumentType


@pytest.fixture
def processor():
    return DocumentProcessor()


@pytest.fixture
def sample_pdf_path():
    # Create a temporary PDF file for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        # This would be a real PDF in practice
        f.write(b'%PDF-1.4 fake pdf content')
        return f.name


@pytest.fixture
def sample_image_path():
    # Create a temporary image file for testing
    img = Image.new('RGB', (100, 100), color='white')
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f, 'PNG')
        return f.name


class TestDocumentProcessor:
    
    def test_is_supported_format(self, processor):
        """Test file format validation"""
        assert processor.is_supported_format('test.pdf') == True
        assert processor.is_supported_format('test.PNG') == True
        assert processor.is_supported_format('test.jpg') == True
        assert processor.is_supported_format('test.jpeg') == True
        assert processor.is_supported_format('test.txt') == False
        assert processor.is_supported_format('test.docx') == False
    
    @patch('backend.services.document_processor.pdfplumber')
    async def test_extract_text_from_pdf(self, mock_pdfplumber, processor, sample_pdf_path):
        """Test PDF text extraction"""
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.chars = []
        mock_page.extract_words.return_value = [
            {
                'text': 'Hello',
                'x0': 10, 'x1': 50, 'top': 20, 'bottom': 40
            }
        ]
        mock_page.extract_text.return_value = 'Hello World'
        mock_page.width = 100
        mock_page.height = 100
        
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        text, blocks = await processor.extract_text_from_pdf(sample_pdf_path)
        
        assert 'Hello World' in text
        assert len(blocks) == 1
        assert blocks[0]['text'] == 'Hello'
        assert blocks[0]['type'] == 'text'
        assert 'bbox' in blocks[0]
    
    @patch('backend.services.document_processor.pytesseract')
    async def test_extract_from_image(self, mock_tesseract, processor, sample_image_path):
        """Test image OCR extraction"""
        # Mock tesseract
        mock_tesseract.image_to_data.return_value = {
            'text': ['Hello', 'World'],
            'conf': [85, 90],
            'left': [10, 60],
            'top': [20, 20],
            'width': [40, 50],
            'height': [20, 20]
        }
        
        text, blocks = await processor.extract_from_image(sample_image_path)
        
        assert 'Hello World' in text
        assert len(blocks) == 2
        assert blocks[0]['text'] == 'Hello'
        assert blocks[0]['confidence'] == 0.85
    
    @patch('backend.services.document_processor.pdfplumber')
    async def test_extract_tables_from_pdf(self, mock_pdfplumber, processor, sample_pdf_path):
        """Test PDF table extraction"""
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_tables.return_value = [
            [['Header1', 'Header2'], ['Row1Col1', 'Row1Col2']]
        ]
        mock_page.bbox = (0, 0, 100, 100)
        
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        tables = await processor.extract_tables_from_pdf(sample_pdf_path)
        
        assert len(tables) == 1
        assert tables[0]['type'] == 'table'
        assert len(tables[0]['content']) == 2  # Header + 1 row
    
    @patch('backend.services.document_processor.PyPDF2')
    @patch('backend.services.document_processor.pdfplumber')
    async def test_process_pdf_document(self, mock_pdfplumber, mock_pypdf2, processor, sample_pdf_path):
        """Test complete PDF processing"""
        # Mock PyPDF2 for page count
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]  # 2 pages
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        # Mock pdfplumber
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.chars = []
        mock_page.extract_words.return_value = []
        mock_page.extract_text.return_value = 'Test content'
        mock_page.extract_tables.return_value = []
        mock_page.width = 100
        mock_page.height = 100
        
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        text, elements, metadata = await processor.process_document(sample_pdf_path, 'test.pdf')
        
        assert metadata.document_type == DocumentType.PDF
        assert metadata.page_count == 2
        assert metadata.filename == 'test.pdf'
        assert 'Test content' in text
    
    @patch('backend.services.document_processor.convert_from_path')
    async def test_get_page_image_pdf(self, mock_convert, processor, sample_pdf_path):
        """Test PDF page image extraction"""
        # Mock pdf2image
        mock_image = Image.new('RGB', (100, 100), color='white')
        mock_convert.return_value = [mock_image]
        
        result = await processor.get_page_image(sample_pdf_path, 1)
        
        assert result is not None
        assert isinstance(result, str)  # base64 string
    
    async def test_get_page_image_regular_image(self, processor, sample_image_path):
        """Test regular image loading"""
        result = await processor.get_page_image(sample_image_path, 1)
        
        assert result is not None
        assert isinstance(result, str)  # base64 string


@pytest.mark.asyncio
class TestDocumentProcessorIntegration:
    """Integration tests that require actual files"""
    
    async def test_process_real_image(self, processor):
        """Test processing a real image file"""
        # Create a simple test image with text
        img = Image.new('RGB', (200, 100), color='white')
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f, 'PNG')
            temp_path = f.name
        
        try:
            # This will use real OCR if tesseract is installed
            text, elements, metadata = await processor.process_document(temp_path, 'test.png')
            
            assert metadata.document_type == DocumentType.PNG
            assert metadata.page_count == 1
            assert isinstance(elements, list)
            
        finally:
            os.unlink(temp_path)


# Cleanup fixtures
def teardown_module():
    """Clean up temporary files"""
    import glob
    temp_files = glob.glob('/tmp/tmp*')
    for f in temp_files:
        try:
            os.unlink(f)
        except:
            pass
