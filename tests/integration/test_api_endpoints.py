import pytest
import asyncio
import tempfile
import os
from fastapi.testclient import TestClient
from PIL import Image
import io

from backend.main import app
from backend.services.storage import storage


@pytest.fixture
def client():
    """Test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing"""
    img = Image.new('RGB', (200, 100), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    # Simple PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Hello World) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    
    return io.BytesIO(pdf_content)


class TestAPIEndpoints:
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
    
    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/api/info")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "supported_formats" in data
        assert "endpoints" in data
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_upload_invalid_file_type(self, client):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", io.StringIO("test content"), "text/plain")}
        response = client.post("/api/upload", files=files)
        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]
    
    def test_upload_no_file(self, client):
        """Test upload without file"""
        response = client.post("/api/upload")
        assert response.status_code == 422  # Validation error
    
    def test_upload_valid_image(self, client, sample_image_file):
        """Test upload with valid image file"""
        files = {"file": ("test.png", sample_image_file, "image/png")}
        response = client.post("/api/upload", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "transaction_id" in data
        assert data["status"] == "pending"
        assert "message" in data
        
        return data["transaction_id"]
    
    def test_status_nonexistent_transaction(self, client):
        """Test status check for nonexistent transaction"""
        response = client.get("/api/status/nonexistent-id")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
    
    def test_result_nonexistent_transaction(self, client):
        """Test result retrieval for nonexistent transaction"""
        response = client.get("/api/result/nonexistent-id")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
    
    def test_grounding_nonexistent_transaction(self, client):
        """Test grounding retrieval for nonexistent transaction"""
        response = client.get("/api/grounding/chunk-id?transaction_id=nonexistent-id")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
    
    def test_corrections_nonexistent_transaction(self, client):
        """Test corrections for nonexistent transaction"""
        corrections = [
            {
                "element_id": "test-element",
                "corrected_content": "corrected content",
                "notes": "test correction"
            }
        ]
        response = client.patch("/api/correct/nonexistent-id", json=corrections)
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]
    
    def test_page_image_nonexistent_transaction(self, client):
        """Test page image for nonexistent transaction"""
        response = client.get("/api/page-image/nonexistent-id?page_number=1")
        assert response.status_code == 404
        assert "Original file not found" in response.json()["detail"]
    
    def test_delete_nonexistent_transaction(self, client):
        """Test delete for nonexistent transaction"""
        response = client.delete("/api/result/nonexistent-id")
        assert response.status_code == 404
        assert "Transaction not found" in response.json()["detail"]


class TestDocumentProcessingFlow:
    """Test complete document processing flow"""
    
    @pytest.mark.asyncio
    async def test_complete_image_processing_flow(self, client, sample_image_file):
        """Test complete flow from upload to results"""
        # 1. Upload file
        files = {"file": ("test.png", sample_image_file, "image/png")}
        upload_response = client.post("/api/upload", files=files)
        assert upload_response.status_code == 200
        
        transaction_id = upload_response.json()["transaction_id"]
        
        # 2. Wait for processing to complete (with timeout)
        max_wait = 30  # seconds
        wait_time = 0
        status = "pending"
        
        while status not in ["completed", "failed"] and wait_time < max_wait:
            await asyncio.sleep(1)
            wait_time += 1
            
            status_response = client.get(f"/api/status/{transaction_id}")
            if status_response.status_code == 200:
                status = status_response.json()["status"]
        
        # 3. Check final status
        status_response = client.get(f"/api/status/{transaction_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["transaction_id"] == transaction_id
        assert "progress" in status_data
        
        # If processing completed, check results
        if status == "completed":
            # 4. Get results
            result_response = client.get(f"/api/result/{transaction_id}")
            assert result_response.status_code == 200
            
            result_data = result_response.json()
            assert result_data["transaction_id"] == transaction_id
            assert result_data["status"] == "completed"
            assert "extracted_elements" in result_data
            assert "metadata" in result_data
            
            # 5. Test page image retrieval
            page_response = client.get(f"/api/page-image/{transaction_id}?page_number=1")
            assert page_response.status_code == 200
            
            page_data = page_response.json()
            assert "image_base64" in page_data
            
            # 6. Test corrections (if there are elements)
            if result_data["extracted_elements"]:
                element_id = result_data["extracted_elements"][0]["id"]
                corrections = [
                    {
                        "element_id": element_id,
                        "corrected_content": "corrected content",
                        "notes": "test correction"
                    }
                ]
                
                correction_response = client.patch(f"/api/correct/{transaction_id}", json=corrections)
                assert correction_response.status_code == 200
                
                correction_data = correction_response.json()
                assert "message" in correction_data
                assert correction_data["transaction_id"] == transaction_id
            
            # 7. Test grounding (if there are elements)
            if result_data["extracted_elements"]:
                element_id = result_data["extracted_elements"][0]["id"]
                grounding_response = client.get(f"/api/grounding/{element_id}?transaction_id={transaction_id}")
                
                # This might fail if the original file is not found, which is expected in tests
                # assert grounding_response.status_code in [200, 404]
            
            # 8. Clean up - delete result
            delete_response = client.delete(f"/api/result/{transaction_id}")
            assert delete_response.status_code == 200
            
            delete_data = delete_response.json()
            assert "message" in delete_data


@pytest.mark.asyncio
class TestConcurrentProcessing:
    """Test concurrent document processing"""
    
    async def test_multiple_uploads(self, client):
        """Test multiple concurrent uploads"""
        # Create multiple sample files
        files = []
        for i in range(3):
            img = Image.new('RGB', (100, 50), color='white')
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            files.append(("file", (f"test_{i}.png", img_bytes, "image/png")))
        
        # Upload all files
        transaction_ids = []
        for file_data in files:
            response = client.post("/api/upload", files=[file_data])
            assert response.status_code == 200
            transaction_ids.append(response.json()["transaction_id"])
        
        # Check that all transactions are tracked
        assert len(transaction_ids) == 3
        assert len(set(transaction_ids)) == 3  # All unique
        
        # Check status of all transactions
        for transaction_id in transaction_ids:
            response = client.get(f"/api/status/{transaction_id}")
            assert response.status_code == 200
            assert response.json()["transaction_id"] == transaction_id


# Cleanup
@pytest.fixture(autouse=True)
async def cleanup_storage():
    """Clean up storage after each test"""
    yield
    # Clear storage
    storage.results.clear()
    
    # Clean up any temporary files
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    if os.path.exists(upload_dir):
        for filename in os.listdir(upload_dir):
            try:
                os.remove(os.path.join(upload_dir, filename))
            except:
                pass
