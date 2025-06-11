import React, { useState } from 'react';
import { FileText, Zap, Eye, Settings } from 'lucide-react';
import FileUpload from './components/FileUpload';
import ProcessingStatus from './components/ProcessingStatus';
import DocumentViewer from './components/DocumentViewer';
import ResultsPanel from './components/ResultsPanel';
import useDocumentProcessing from './hooks/useDocumentProcessing';

function App() {
  const [currentPage, setCurrentPage] = useState(1);
  const {
    processing,
    results,
    uploadDocument,
    selectElement,
    submitCorrections,
    getGrounding,
    reset,
  } = useDocumentProcessing();

  const handleFileUpload = async (file) => {
    try {
      await uploadDocument(file);
    } catch (error) {
      console.error('Upload failed:', error);
    }
  };

  const handleElementSelect = (element) => {
    selectElement(element);
    // Switch to the page containing this element
    if (element.grounding?.page_number) {
      setCurrentPage(element.grounding.page_number);
    }
  };

  const handleCorrection = async (corrections) => {
    try {
      await submitCorrections(corrections);
    } catch (error) {
      console.error('Correction failed:', error);
      throw error;
    }
  };

  const handleNewDocument = () => {
    reset();
    setCurrentPage(1);
  };

  const isProcessingComplete = processing.status === 'completed' && results.data;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-primary-100 rounded-lg">
                <FileText className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">
                  Document Extraction Platform
                </h1>
                <p className="text-sm text-gray-500">
                  AI-powered document analysis with visual grounding
                </p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {results.transactionId && (
                <button
                  onClick={handleNewDocument}
                  className="btn btn-secondary"
                >
                  New Document
                </button>
              )}
              
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Zap className="w-4 h-4" />
                <span>Multi-Agent Processing</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload Stage */}
        {!results.transactionId && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-gray-900 mb-4">
                Extract Structured Data from Documents
              </h2>
              <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                Upload PDF, PNG, or JPEG documents to automatically extract text, tables, 
                and form fields with precise visual grounding and hierarchical structure.
              </p>
            </div>
            
            <FileUpload
              onFileUpload={handleFileUpload}
              isUploading={processing.isUploading}
              uploadProgress={processing.uploadProgress}
              error={processing.error}
            />

            {/* Features */}
            <div className="grid md:grid-cols-3 gap-6 mt-12">
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Zap className="w-6 h-6 text-blue-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Multi-Agent Processing</h3>
                <p className="text-gray-600 text-sm">
                  LangGraph orchestrated agents handle parsing, structuring, validation, and highlighting
                </p>
              </div>
              
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Eye className="w-6 h-6 text-green-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Visual Grounding</h3>
                <p className="text-gray-600 text-sm">
                  Every extracted element includes precise bounding box coordinates for auditability
                </p>
              </div>
              
              <div className="text-center p-6">
                <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Settings className="w-6 h-6 text-purple-600" />
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">Human-in-the-Loop</h3>
                <p className="text-gray-600 text-sm">
                  Review, validate, and correct extracted content with interactive editing
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Processing Stage */}
        {results.transactionId && processing.isProcessing && (
          <ProcessingStatus
            status={processing.status}
            progress={processing.processingProgress}
            isProcessing={processing.isProcessing}
            error={processing.error}
            transactionId={results.transactionId}
          />
        )}

        {/* Results Stage */}
        {isProcessingComplete && (
          <div className="space-y-6">
            {/* Document Info */}
            <div className="bg-white rounded-lg border border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    {results.data.metadata?.filename || 'Document'}
                  </h2>
                  <p className="text-sm text-gray-500">
                    {results.data.metadata?.page_count} pages • 
                    {results.data.extracted_elements?.length || 0} elements extracted • 
                    Processing completed
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-sm text-gray-500">Transaction ID</div>
                  <div className="font-mono text-xs text-gray-700">
                    {results.transactionId}
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="grid lg:grid-cols-2 gap-6 h-[800px]">
              {/* Document Viewer */}
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <DocumentViewer
                  pageImages={results.pageImages}
                  extractedElements={results.data.extracted_elements}
                  selectedElement={results.selectedElement}
                  onElementSelect={handleElementSelect}
                  currentPage={currentPage}
                  onPageChange={setCurrentPage}
                />
              </div>

              {/* Results Panel */}
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                <ResultsPanel
                  results={results.data}
                  selectedElement={results.selectedElement}
                  onElementSelect={handleElementSelect}
                  onCorrection={handleCorrection}
                  onGetGrounding={getGrounding}
                />
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-gray-500">
            <p>
              Powered by LangGraph Multi-Agent Architecture • 
              Built with React, FastAPI, and Tailwind CSS
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
