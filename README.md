# Agentic Document Extraction Platform

A multi-agent document extraction platform built with LangGraph, FastAPI, and React that extracts structured data from PDFs, images, and provides visual grounding with bounding box overlays.

## Features

- **Multi-Agent Processing**: LangGraph orchestrated agents (Parse → Structure → Validate → Highlight → Store)
- **Document Support**: PDF, PNG, JPEG with OCR capabilities
- **Visual Grounding**: Bounding box overlays on original documents
- **Hierarchical Data**: Parent-child relationships with page and coordinate tracking
- **Human-in-the-Loop**: Interactive validation and correction interface
- **Real-time Processing**: Async extraction with status tracking

## Tech Stack

### Backend
- **Python 3.10+**
- **LangGraph** - Multi-agent orchestration
- **FastAPI** - REST API server
- **MongoDB** - Document storage
- **PyPDF2/pdfplumber** - PDF parsing
- **pytesseract** - OCR processing
- **Pillow** - Image processing

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **PDF.js** - PDF rendering
- **Axios** - HTTP client

## Quick Start

### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd frontend && npm install

# Install Tesseract OCR
# macOS: brew install tesseract
# Ubuntu: sudo apt-get install tesseract-ocr
# Windows: Download from GitHub releases

# Start MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Running the Application

1. **Start Backend**:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

2. **Start Frontend**:
```bash
cd frontend
npm run dev
```

3. **Access Application**:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
document-highlighter/
├── backend/
│   ├── agents/              # LangGraph agent implementations
│   ├── models/              # Pydantic models
│   ├── services/            # Business logic
│   ├── routers/             # FastAPI routes
│   ├── database/            # MongoDB connection
│   └── main.py              # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   ├── hooks/           # Custom hooks
│   │   └── utils/           # Utilities
│   └── public/              # Static assets
├── tests/                   # Test files
├── requirements.txt         # Python dependencies
└── README.md
```

## API Endpoints

- `POST /upload` - Upload document for processing
- `GET /status/{transaction_id}` - Get processing status
- `GET /result/{transaction_id}` - Get extraction results
- `GET /grounding/{chunk_id}` - Get visual grounding data
- `PATCH /correct/{transaction_id}` - Submit corrections

## Usage Example

1. Upload a document (PDF/PNG/JPEG)
2. Monitor processing status via transaction ID
3. View results with visual overlays
4. Make corrections through the UI
5. Export structured data (JSON/Markdown)

## Development

### Running Tests
```bash
# Backend tests
cd backend && python -m pytest

# Frontend tests
cd frontend && npm test
```

### Environment Variables
```bash
# Backend (.env)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=document_extraction
OPENAI_API_KEY=your_openai_key  # Optional for enhanced processing
AWS_ACCESS_KEY_ID=your_aws_key  # Optional for Textract
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details
