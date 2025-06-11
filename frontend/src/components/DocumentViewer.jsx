import React, { useState, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, RotateCw, Download, Eye, EyeOff } from 'lucide-react';

const DocumentViewer = ({ 
  pageImages, 
  extractedElements, 
  selectedElement, 
  onElementSelect,
  currentPage = 1,
  onPageChange 
}) => {
  const [zoom, setZoom] = useState(1);
  const [showHighlights, setShowHighlights] = useState(true);
  const [hoveredElement, setHoveredElement] = useState(null);

  const pageCount = Object.keys(pageImages).length;
  const currentPageImage = pageImages[currentPage];

  // Get elements for current page
  const pageElements = extractedElements?.filter(
    element => element.grounding?.page_number === currentPage && element.type !== 'page'
  ) || [];

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev + 0.25, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev - 0.25, 0.5));
  }, []);

  const handleElementClick = useCallback((element, event) => {
    event.stopPropagation();
    onElementSelect?.(element);
  }, [onElementSelect]);

  const handleElementHover = useCallback((element) => {
    setHoveredElement(element);
  }, []);

  const handleElementLeave = useCallback(() => {
    setHoveredElement(null);
  }, []);

  const getHighlightStyle = useCallback((element) => {
    const bbox = element.grounding?.bounding_box;
    if (!bbox) return {};

    const isSelected = selectedElement?.id === element.id;
    const isHovered = hoveredElement?.id === element.id;

    return {
      position: 'absolute',
      left: `${bbox.x * 100}%`,
      top: `${bbox.y * 100}%`,
      width: `${bbox.width * 100}%`,
      height: `${bbox.height * 100}%`,
      border: `2px solid ${getElementColor(element.type)}`,
      backgroundColor: `${getElementColor(element.type)}20`,
      borderRadius: '2px',
      cursor: 'pointer',
      transition: 'all 0.2s ease',
      zIndex: isSelected ? 20 : isHovered ? 15 : 10,
      transform: isHovered ? 'scale(1.02)' : 'scale(1)',
      boxShadow: isSelected 
        ? `0 0 0 2px ${getElementColor(element.type)}80` 
        : isHovered 
        ? `0 2px 8px ${getElementColor(element.type)}40`
        : 'none',
    };
  }, [selectedElement, hoveredElement]);

  const getElementColor = useCallback((type) => {
    const colors = {
      text: '#3B82F6',
      table: '#10B981',
      form_field: '#F59E0B',
      image: '#8B5CF6',
      header: '#EF4444',
    };
    return colors[type] || '#6B7280';
  }, []);

  if (!currentPageImage) {
    return (
      <div className="flex items-center justify-center h-96 bg-gray-100 rounded-lg">
        <p className="text-gray-500">No document to display</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 bg-white border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <button
            onClick={handleZoomOut}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          
          <span className="text-sm font-medium text-gray-700 min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          
          <button
            onClick={handleZoomIn}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowHighlights(!showHighlights)}
            className={`p-2 rounded-lg transition-colors ${
              showHighlights 
                ? 'text-primary-600 bg-primary-100' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
            }`}
            title={showHighlights ? 'Hide Highlights' : 'Show Highlights'}
          >
            {showHighlights ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
        </div>

        {/* Page Navigation */}
        {pageCount > 1 && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onPageChange?.(Math.max(1, currentPage - 1))}
              disabled={currentPage <= 1}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            >
              Previous
            </button>
            
            <span className="text-sm text-gray-600">
              Page {currentPage} of {pageCount}
            </span>
            
            <button
              onClick={() => onPageChange?.(Math.min(pageCount, currentPage + 1))}
              disabled={currentPage >= pageCount}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed rounded"
            >
              Next
            </button>
          </div>
        )}
      </div>

      {/* Document Display */}
      <div className="flex-1 overflow-auto bg-gray-100 p-4">
        <div className="flex justify-center">
          <div 
            className="relative bg-white shadow-lg"
            style={{ 
              transform: `scale(${zoom})`,
              transformOrigin: 'top center',
              transition: 'transform 0.2s ease'
            }}
          >
            {/* Document Image */}
            <img
              src={`data:image/png;base64,${currentPageImage}`}
              alt={`Page ${currentPage}`}
              className="block max-w-none"
              style={{ width: 'auto', height: 'auto' }}
            />

            {/* Highlight Overlays */}
            {showHighlights && pageElements.map((element) => (
              <div
                key={element.id}
                style={getHighlightStyle(element)}
                onClick={(e) => handleElementClick(element, e)}
                onMouseEnter={() => handleElementHover(element)}
                onMouseLeave={handleElementLeave}
                title={`${element.type}: ${
                  typeof element.content === 'string' 
                    ? element.content.substring(0, 100) 
                    : 'Complex content'
                }`}
              />
            ))}

            {/* Element Labels (on hover) */}
            {showHighlights && hoveredElement && (
              <div
                className="absolute bg-gray-900 text-white text-xs px-2 py-1 rounded shadow-lg pointer-events-none z-30"
                style={{
                  left: `${hoveredElement.grounding.bounding_box.x * 100}%`,
                  top: `${(hoveredElement.grounding.bounding_box.y - 0.05) * 100}%`,
                  transform: 'translateY(-100%)',
                }}
              >
                {hoveredElement.type} ({Math.round(hoveredElement.confidence * 100)}%)
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Legend */}
      {showHighlights && (
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex flex-wrap gap-4 text-sm">
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-blue-500 bg-blue-100 rounded"></div>
              <span>Text</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-green-500 bg-green-100 rounded"></div>
              <span>Table</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-yellow-500 bg-yellow-100 rounded"></div>
              <span>Form Field</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="w-4 h-4 border-2 border-purple-500 bg-purple-100 rounded"></div>
              <span>Image</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentViewer;
