# Agentic Document Extraction Platform - Setup Guide

This guide will walk you through setting up and running the complete multi-agent document extraction platform.

## 🎯 Overview

The platform consists of:
- **Backend**: FastAPI server with LangGraph multi-agent workflow
- **Frontend**: React application with PDF viewer and visual grounding
- **Processing Pipeline**: Parse → Structure → Validate → Highlight → Store

## 📋 Prerequisites

### System Requirements
- **Python 3.10+** (required)
- **Node.js 16+** and npm (required)
- **Tesseract OCR** (required for text extraction)
- **Poppler** (required for PDF processing)

### Installation by OS

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 node tesseract poppler
```

#### Ubuntu/Debian
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install python3.10 python3.10-venv nodejs npm tesseract-ocr poppler-utils
```

#### Windows
1. Install Python 3.10+ from [python.org](https://python.org)
2. Install Node.js from [nodejs.org](https://nodejs.org)
3. Install Tesseract from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
4. Add Tesseract to your PATH

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# Clone or navigate to the project directory
cd document-highlighter

# Run the automated setup script
python3 setup.py

# Start all services
./start.sh
```

### Option 2: Manual Setup

#### 1. Backend Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p backend/uploads backend/storage logs
```

#### 2. Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

#### 3. Environment Configuration
```bash
# Copy and edit environment file
cp backend/.env.example backend/.env

# Edit the .env file with your settings (optional)
nano backend/.env
```

#### 4. Start Services

**Terminal 1 - Backend:**
```bash
cd backend
source ../venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## 🌐 Access the Application

Once both services are running:

- **Frontend UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🧪 Running the Demo

### Using the Sample File

The project includes a sample `LoanDisclosure.pdf` file for testing:

```bash
# Run the demo script
python3 run_demo.py
```

This will:
1. Process the sample PDF through the multi-agent workflow
2. Show real-time processing status
3. Display extraction results
4. Save results to a JSON file

### Using the Web Interface

1. Open http://localhost:5173
2. Upload the `LoanDisclosure.pdf` file (or any PDF/image)
3. Watch the multi-agent processing workflow
4. View results with visual grounding overlays
5. Edit and correct extracted content

## 🔧 Configuration

### Environment Variables

Edit `backend/.env` to configure:

```bash
# File Storage
UPLOAD_DIR=./uploads
STORAGE_DIR=./storage
MAX_FILE_SIZE=50000000  # 50MB

# Server Settings
HOST=0.0.0.0
PORT=8000

# Optional: Enhanced Processing
OPENAI_API_KEY=your_openai_key_here
AWS_ACCESS_KEY_ID=your_aws_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_here
```

### Processing Settings

The system uses these default settings:
- **Confidence Threshold**: 0.7 (70%)
- **OCR Language**: English
- **Max File Size**: 50MB
- **Supported Formats**: PDF, PNG, JPEG

## 🧪 Testing

### Run Unit Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run backend tests
cd backend
python -m pytest ../tests/unit/ -v

# Run integration tests
python -m pytest ../tests/integration/ -v
```

### Run BDD Tests
```bash
# Install behave if not already installed
pip install behave

# Run BDD tests
behave tests/features/
```

## 📊 Architecture Overview

### Multi-Agent Workflow

```
Upload → Parse → Structure → Validate → Highlight → Store
   ↓        ↓         ↓          ↓          ↓        ↓
 File    Raw Text  Hierarchy  Confidence  Visual   Results
Input   Elements  Structure   Scores     Grounding Database
```

### Technology Stack

**Backend:**
- FastAPI (REST API)
- LangGraph (Multi-agent orchestration)
- PyPDF2/pdfplumber (PDF processing)
- Tesseract (OCR)
- Pillow (Image processing)

**Frontend:**
- React 18 (UI framework)
- Vite (Build tool)
- Tailwind CSS (Styling)
- PDF.js (PDF rendering)

## 🎨 UI Features

### Document Viewer
- PDF/image rendering with zoom controls
- Interactive bounding box overlays
- Element highlighting by type
- Page navigation for multi-page documents

### Results Panel
- Structured view of extracted elements
- JSON/Markdown export options
- Human-in-the-loop editing
- Confidence score visualization

### Processing Status
- Real-time workflow progress
- Step-by-step status updates
- Error handling and reporting

## 🔍 API Endpoints

### Core Endpoints
- `POST /api/upload` - Upload document for processing
- `GET /api/status/{transaction_id}` - Get processing status
- `GET /api/result/{transaction_id}` - Get extraction results
- `PATCH /api/correct/{transaction_id}` - Submit corrections

### Utility Endpoints
- `GET /api/grounding/{chunk_id}` - Get visual grounding data
- `GET /api/page-image/{transaction_id}` - Get page image
- `DELETE /api/result/{transaction_id}` - Delete results
- `GET /api/health` - Health check

## 🐛 Troubleshooting

### Common Issues

**1. Tesseract not found**
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt install tesseract-ocr

# Windows: Add Tesseract to PATH
```

**2. PDF processing fails**
```bash
# Install poppler
# macOS: brew install poppler
# Ubuntu: sudo apt install poppler-utils
```

**3. Port already in use**
```bash
# Kill processes on ports 8000 and 5173
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9
```

**4. Permission errors**
```bash
# Make scripts executable
chmod +x setup.py start.sh run_demo.py
```

### Logs and Debugging

- Backend logs: Console output from uvicorn
- Frontend logs: Browser developer console
- Processing logs: Stored in results JSON
- File uploads: `backend/uploads/` directory

## 📈 Performance Tips

1. **File Size**: Keep files under 50MB for best performance
2. **Image Quality**: Higher DPI images give better OCR results
3. **PDF Optimization**: Use text-based PDFs when possible
4. **Concurrent Processing**: The system handles multiple uploads

## 🔒 Security Considerations

- File uploads are validated by type and size
- Temporary files are cleaned up automatically
- No persistent database by default (file-based storage)
- API endpoints include basic error handling

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

If you encounter issues:

1. Check this setup guide
2. Review the troubleshooting section
3. Check the GitHub issues
4. Run the demo script to verify setup

---

**Happy Document Extracting! 🎉**
