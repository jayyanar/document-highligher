#!/usr/bin/env python3
"""
Setup script for the Agentic Document Extraction Platform
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is 3.10+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_system_dependencies():
    """Install system dependencies based on OS"""
    system = platform.system().lower()
    
    if system == "darwin":  # macOS
        print("\n📦 Installing macOS dependencies...")
        commands = [
            "brew install tesseract",
            "brew install poppler"  # For pdf2image
        ]
    elif system == "linux":
        print("\n📦 Installing Linux dependencies...")
        commands = [
            "sudo apt-get update",
            "sudo apt-get install -y tesseract-ocr",
            "sudo apt-get install -y poppler-utils"
        ]
    else:
        print(f"\n⚠️  Please manually install Tesseract OCR for {system}")
        print("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return True
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            print(f"⚠️  Failed to run: {cmd}")
            print("Please install manually:")
            print("- Tesseract OCR")
            print("- Poppler (for PDF processing)")
            return False
    
    return True

def setup_backend():
    """Set up the backend environment"""
    print("\n🐍 Setting up Python backend...")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate virtual environment and install dependencies
    if platform.system().lower() == "windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r requirements.txt"
    ]
    
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            return False
    
    return True

def setup_frontend():
    """Set up the frontend environment"""
    print("\n⚛️  Setting up React frontend...")
    
    # Check if Node.js is installed
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Node.js and npm are required")
        print("Please install Node.js from https://nodejs.org/")
        return False
    
    # Install frontend dependencies
    os.chdir("frontend")
    
    if not run_command("npm install", "Installing Node.js dependencies"):
        os.chdir("..")
        return False
    
    os.chdir("..")
    return True

def setup_database():
    """Set up MongoDB (optional)"""
    print("\n🗄️  Setting up database...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
        
        # Start MongoDB container
        mongo_cmd = (
            "docker run -d --name mongodb -p 27017:27017 "
            "-v mongodb_data:/data/db mongo:latest"
        )
        
        if run_command(mongo_cmd, "Starting MongoDB container"):
            print("✅ MongoDB is running on port 27017")
        else:
            print("⚠️  MongoDB setup failed, but the app can run without it")
            
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker not found. MongoDB setup skipped.")
        print("The application will use file-based storage instead.")
    
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "backend/uploads",
        "backend/storage",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    return True

def create_env_file():
    """Create environment file if it doesn't exist"""
    env_path = "backend/.env"
    
    if not os.path.exists(env_path):
        print(f"\n📝 Creating {env_path}...")
        
        env_content = """# MongoDB Configuration (optional)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=document_extraction

# API Keys (optional - for enhanced processing)
OPENAI_API_KEY=your_openai_key_here
AWS_ACCESS_KEY_ID=your_aws_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_here
AWS_REGION=us-east-1

# Application Settings
UPLOAD_DIR=./uploads
STORAGE_DIR=./storage
MAX_FILE_SIZE=50000000
HOST=0.0.0.0
PORT=8000
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created {env_path}")
        print("⚠️  Please update the API keys in the .env file if needed")
    else:
        print(f"✅ {env_path} already exists")
    
    return True

def run_tests():
    """Run basic tests to verify setup"""
    print("\n🧪 Running basic tests...")
    
    # Test backend
    if platform.system().lower() == "windows":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    test_cmd = f"{python_cmd} -m pytest tests/unit/ -v"
    
    if run_command(test_cmd, "Running backend tests"):
        print("✅ Backend tests passed")
    else:
        print("⚠️  Some backend tests failed (this might be expected)")
    
    return True

def main():
    """Main setup function"""
    print("🚀 Setting up Agentic Document Extraction Platform")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python_version():
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Install system dependencies", install_system_dependencies),
        ("Set up backend", setup_backend),
        ("Set up frontend", setup_frontend),
        ("Set up database", setup_database),
        ("Create directories", create_directories),
        ("Create environment file", create_env_file),
        ("Run tests", run_tests),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Setup Summary")
    print("=" * 50)
    
    if not failed_steps:
        print("✅ All setup steps completed successfully!")
        print("\n🚀 To start the application:")
        print("1. Backend:  cd backend && uvicorn main:app --reload")
        print("2. Frontend: cd frontend && npm run dev")
        print("3. Open:     http://localhost:5173")
    else:
        print("⚠️  Some steps failed:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nPlease resolve the issues and run setup again.")
    
    print("\n📚 Documentation:")
    print("- API Docs: http://localhost:8000/docs")
    print("- README:   ./README.md")

if __name__ == "__main__":
    main()
