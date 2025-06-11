import React, { useState, useCallback } from 'react';
import { 
  FileText, 
  Table, 
  Edit3, 
  Check, 
  X, 
  Download, 
  Copy,
  ChevronDown,
  ChevronRight,
  Eye
} from 'lucide-react';

const ResultsPanel = ({ 
  results, 
  selectedElement, 
  onElementSelect, 
  onCorrection,
  onGetGrounding 
}) => {
  const [viewMode, setViewMode] = useState('structured'); // 'structured', 'json', 'markdown'
  const [editingElement, setEditingElement] = useState(null);
  const [editContent, setEditContent] = useState('');
  const [expandedSections, setExpandedSections] = useState(new Set(['summary']));

  const handleEdit = useCallback((element) => {
    setEditingElement(element.id);
    setEditContent(typeof element.content === 'string' ? element.content : JSON.stringify(element.content, null, 2));
  }, []);

  const handleSaveEdit = useCallback(async () => {
    if (!editingElement) return;

    try {
      await onCorrection([{
        element_id: editingElement,
        corrected_content: editContent,
        notes: 'Manual correction via UI'
      }]);
      
      setEditingElement(null);
      setEditContent('');
    } catch (error) {
      console.error('Failed to save correction:', error);
      alert('Failed to save correction. Please try again.');
    }
  }, [editingElement, editContent, onCorrection]);

  const handleCancelEdit = useCallback(() => {
    setEditingElement(null);
    setEditContent('');
  }, []);

  const toggleSection = useCallback((sectionId) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sectionId)) {
        newSet.delete(sectionId);
      } else {
        newSet.add(sectionId);
      }
      return newSet;
    });
  }, []);

  const handleViewGrounding = useCallback(async (element) => {
    try {
      const grounding = await onGetGrounding(element.id);
      if (grounding) {
        // Show grounding in a modal or side panel
        console.log('Grounding data:', grounding);
      }
    } catch (error) {
      console.error('Failed to get grounding:', error);
    }
  }, [onGetGrounding]);

  const exportData = useCallback((format) => {
    let content = '';
    let filename = '';
    let mimeType = '';

    if (format === 'json') {
      content = JSON.stringify(results, null, 2);
      filename = 'extraction-results.json';
      mimeType = 'application/json';
    } else if (format === 'markdown') {
      content = generateMarkdown(results);
      filename = 'extraction-results.md';
      mimeType = 'text/markdown';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [results]);

  const copyToClipboard = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      // Show success feedback
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  }, []);

  if (!results) {
    return (
      <div className="h-full flex items-center justify-center text-gray-500">
        No results to display
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Extraction Results</h2>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => exportData('json')}
              className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
              title="Export JSON"
            >
              <Download className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* View Mode Tabs */}
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          {[
            { id: 'structured', label: 'Structured' },
            { id: 'json', label: 'JSON' },
            { id: 'markdown', label: 'Markdown' }
          ].map((mode) => (
            <button
              key={mode.id}
              onClick={() => setViewMode(mode.id)}
              className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                viewMode === mode.id
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {viewMode === 'structured' && (
          <StructuredView
            results={results}
            selectedElement={selectedElement}
            onElementSelect={onElementSelect}
            editingElement={editingElement}
            editContent={editContent}
            onEdit={handleEdit}
            onSaveEdit={handleSaveEdit}
            onCancelEdit={handleCancelEdit}
            onEditContentChange={setEditContent}
            expandedSections={expandedSections}
            onToggleSection={toggleSection}
            onViewGrounding={handleViewGrounding}
          />
        )}
        
        {viewMode === 'json' && (
          <JsonView 
            data={results} 
            onCopy={copyToClipboard}
          />
        )}
        
        {viewMode === 'markdown' && (
          <MarkdownView 
            results={results} 
            onCopy={copyToClipboard}
          />
        )}
      </div>
    </div>
  );
};

const StructuredView = ({ 
  results, 
  selectedElement, 
  onElementSelect, 
  editingElement, 
  editContent, 
  onEdit, 
  onSaveEdit, 
  onCancelEdit, 
  onEditContentChange,
  expandedSections,
  onToggleSection,
  onViewGrounding
}) => {
  const summary = results.structured_data?.summary || {};
  const elementsByPage = results.structured_data?.elements_by_page || {};

  return (
    <div className="p-4 space-y-6">
      {/* Summary Section */}
      <div className="bg-white rounded-lg border border-gray-200">
        <button
          onClick={() => onToggleSection('summary')}
          className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
        >
          <h3 className="font-semibold text-gray-900">Document Summary</h3>
          {expandedSections.has('summary') ? (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-500" />
          )}
        </button>
        
        {expandedSections.has('summary') && (
          <div className="px-4 pb-4 border-t border-gray-100">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-primary-600">{summary.total_elements || 0}</div>
                <div className="text-sm text-gray-500">Total Elements</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{summary.text_elements || 0}</div>
                <div className="text-sm text-gray-500">Text Blocks</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{summary.table_elements || 0}</div>
                <div className="text-sm text-gray-500">Tables</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{summary.pages || 0}</div>
                <div className="text-sm text-gray-500">Pages</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Elements by Page */}
      {Object.entries(elementsByPage).map(([pageNum, elements]) => (
        <div key={pageNum} className="bg-white rounded-lg border border-gray-200">
          <button
            onClick={() => onToggleSection(`page-${pageNum}`)}
            className="w-full p-4 flex items-center justify-between text-left hover:bg-gray-50"
          >
            <h3 className="font-semibold text-gray-900">Page {pageNum} ({elements.length} elements)</h3>
            {expandedSections.has(`page-${pageNum}`) ? (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronRight className="w-5 h-5 text-gray-500" />
            )}
          </button>
          
          {expandedSections.has(`page-${pageNum}`) && (
            <div className="border-t border-gray-100">
              {elements.map((element, index) => (
                <ElementCard
                  key={element.id || index}
                  element={element}
                  isSelected={selectedElement?.id === element.id}
                  isEditing={editingElement === element.id}
                  editContent={editContent}
                  onSelect={() => onElementSelect(element)}
                  onEdit={() => onEdit(element)}
                  onSaveEdit={onSaveEdit}
                  onCancelEdit={onCancelEdit}
                  onEditContentChange={onEditContentChange}
                  onViewGrounding={() => onViewGrounding(element)}
                />
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

const ElementCard = ({ 
  element, 
  isSelected, 
  isEditing, 
  editContent, 
  onSelect, 
  onEdit, 
  onSaveEdit, 
  onCancelEdit, 
  onEditContentChange,
  onViewGrounding
}) => {
  const getElementIcon = (type) => {
    switch (type) {
      case 'text':
        return <FileText className="w-4 h-4" />;
      case 'table':
        return <Table className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getElementColor = (type) => {
    switch (type) {
      case 'text':
        return 'text-blue-600 bg-blue-50';
      case 'table':
        return 'text-green-600 bg-green-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <div 
      className={`p-4 border-b border-gray-100 last:border-b-0 cursor-pointer transition-colors ${
        isSelected ? 'bg-primary-50 border-primary-200' : 'hover:bg-gray-50'
      }`}
      onClick={onSelect}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <div className={`p-2 rounded-lg ${getElementColor(element.type)}`}>
            {getElementIcon(element.type)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-sm font-medium text-gray-900 capitalize">
                {element.type}
              </span>
              {element.confidence && (
                <span className="text-xs text-gray-500">
                  {Math.round(element.confidence * 100)}% confidence
                </span>
              )}
              {element.validated && (
                <Check className="w-4 h-4 text-green-500" />
              )}
            </div>
            
            {isEditing ? (
              <div className="space-y-2">
                <textarea
                  value={editContent}
                  onChange={(e) => onEditContentChange(e.target.value)}
                  className="textarea text-sm"
                  rows={4}
                />
                <div className="flex space-x-2">
                  <button onClick={onSaveEdit} className="btn btn-primary text-xs">
                    Save
                  </button>
                  <button onClick={onCancelEdit} className="btn btn-secondary text-xs">
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-700">
                {typeof element.content === 'string' 
                  ? element.content.length > 200 
                    ? `${element.content.substring(0, 200)}...`
                    : element.content
                  : JSON.stringify(element.content).substring(0, 200) + '...'
                }
              </div>
            )}
          </div>
        </div>
        
        {!isEditing && (
          <div className="flex items-center space-x-1 ml-2">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onViewGrounding();
              }}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="View Grounding"
            >
              <Eye className="w-4 h-4" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onEdit();
              }}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Edit"
            >
              <Edit3 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const JsonView = ({ data, onCopy }) => {
  const jsonString = JSON.stringify(data, null, 2);
  
  return (
    <div className="p-4">
      <div className="bg-gray-900 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-3 bg-gray-800">
          <span className="text-sm font-medium text-gray-300">JSON Output</span>
          <button
            onClick={() => onCopy(jsonString)}
            className="p-1 text-gray-400 hover:text-gray-200 transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        <pre className="p-4 text-sm text-gray-300 overflow-auto max-h-96 scrollbar-thin">
          {jsonString}
        </pre>
      </div>
    </div>
  );
};

const MarkdownView = ({ results, onCopy }) => {
  const markdown = generateMarkdown(results);
  
  return (
    <div className="p-4">
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="flex items-center justify-between p-3 bg-gray-50 border-b border-gray-200">
          <span className="text-sm font-medium text-gray-700">Markdown Output</span>
          <button
            onClick={() => onCopy(markdown)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
            title="Copy to clipboard"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
        <pre className="p-4 text-sm text-gray-700 overflow-auto max-h-96 scrollbar-thin whitespace-pre-wrap">
          {markdown}
        </pre>
      </div>
    </div>
  );
};

const generateMarkdown = (results) => {
  let markdown = `# Document Extraction Results\n\n`;
  
  if (results.metadata) {
    markdown += `## Document Information\n\n`;
    markdown += `- **Filename**: ${results.metadata.filename}\n`;
    markdown += `- **Type**: ${results.metadata.document_type}\n`;
    markdown += `- **Pages**: ${results.metadata.page_count}\n`;
    markdown += `- **File Size**: ${results.metadata.file_size} bytes\n\n`;
  }
  
  if (results.structured_data?.summary) {
    const summary = results.structured_data.summary;
    markdown += `## Summary\n\n`;
    markdown += `- **Total Elements**: ${summary.total_elements}\n`;
    markdown += `- **Text Elements**: ${summary.text_elements}\n`;
    markdown += `- **Table Elements**: ${summary.table_elements}\n`;
    markdown += `- **Validated Elements**: ${summary.validated_elements}\n\n`;
  }
  
  if (results.extracted_elements) {
    markdown += `## Extracted Content\n\n`;
    
    results.extracted_elements.forEach((element, index) => {
      if (element.type !== 'page') {
        markdown += `### Element ${index + 1} (${element.type})\n\n`;
        markdown += `**Content**: ${typeof element.content === 'string' ? element.content : JSON.stringify(element.content)}\n\n`;
        markdown += `**Confidence**: ${Math.round(element.confidence * 100)}%\n\n`;
        markdown += `**Page**: ${element.grounding?.page_number}\n\n`;
        markdown += `---\n\n`;
      }
    });
  }
  
  return markdown;
};

export default ResultsPanel;
