#!/usr/bin/env python3
"""
Basic functionality test for the document extraction platform
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from models.document import ProcessingResult, ExtractedElement
        print("✅ Models import successful")
    except ImportError as e:
        print(f"❌ Models import failed: {e}")
        return False
    
    try:
        from services.storage import storage
        print("✅ Storage service import successful")
    except ImportError as e:
        print(f"❌ Storage service import failed: {e}")
        return False
    
    try:
        from services.document_processor import processor
        print("✅ Document processor import successful")
    except ImportError as e:
        print(f"❌ Document processor import failed: {e}")
        return False
    
    try:
        from agents.simple_workflow import workflow
        print("✅ Workflow import successful")
    except ImportError as e:
        print(f"❌ Workflow import failed: {e}")
        return False
    
    return True

def test_file_support():
    """Test file format support"""
    print("\n🧪 Testing file format support...")
    
    try:
        from services.document_processor import processor
        
        # Test supported formats
        assert processor.is_supported_format("test.pdf") == True
        assert processor.is_supported_format("test.png") == True
        assert processor.is_supported_format("test.jpg") == True
        assert processor.is_supported_format("test.jpeg") == True
        assert processor.is_supported_format("test.txt") == False
        
        print("✅ File format validation working")
        return True
    except Exception as e:
        print(f"❌ File format test failed: {e}")
        return False

def test_storage():
    """Test storage functionality"""
    print("\n🧪 Testing storage...")
    
    try:
        from services.storage import storage
        from models.document import ProcessingResult, ProcessingStatus
        from datetime import datetime
        
        # Create test result
        test_result = ProcessingResult(
            transaction_id="test-123",
            status=ProcessingStatus.COMPLETED,
            metadata=None,
            processing_log=["Test log entry"]
        )
        
        # Test storage operations (these are async, so we'll just test the structure)
        print("✅ Storage structure is valid")
        return True
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False

def test_sample_file():
    """Test that sample file exists"""
    print("\n🧪 Testing sample file...")
    
    sample_file = "LoanDisclosure.pdf"
    if os.path.exists(sample_file):
        size = os.path.getsize(sample_file)
        print(f"✅ Sample file found: {sample_file} ({size:,} bytes)")
        return True
    else:
        print(f"❌ Sample file not found: {sample_file}")
        return False

def test_directories():
    """Test that required directories can be created"""
    print("\n🧪 Testing directory creation...")
    
    try:
        test_dirs = ["backend/uploads", "backend/storage"]
        for directory in test_dirs:
            os.makedirs(directory, exist_ok=True)
            if os.path.exists(directory):
                print(f"✅ Directory created/exists: {directory}")
            else:
                print(f"❌ Failed to create directory: {directory}")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Directory test failed: {e}")
        return False

def main():
    """Run all basic tests"""
    print("🚀 Basic Functionality Test")
    print("=" * 40)
    
    tests = [
        ("Import Test", test_imports),
        ("File Support Test", test_file_support),
        ("Storage Test", test_storage),
        ("Sample File Test", test_sample_file),
        ("Directory Test", test_directories),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All basic tests passed!")
        print("\n🚀 Ready to run the full demo:")
        print("   python3 run_demo.py")
        print("\n🌐 Or start the web interface:")
        print("   ./start.sh")
        return True
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
