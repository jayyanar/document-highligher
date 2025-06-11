import { useState, useEffect, useCallback } from 'react';
import { documentAPI } from '../services/api';

export const useDocumentProcessing = () => {
  const [processing, setProcessing] = useState({
    isUploading: false,
    isProcessing: false,
    uploadProgress: 0,
    processingProgress: 0,
    status: null,
    error: null,
  });

  const [results, setResults] = useState({
    transactionId: null,
    data: null,
    pageImages: {},
    selectedElement: null,
  });

  // Upload document
  const uploadDocument = useCallback(async (file) => {
    try {
      setProcessing(prev => ({
        ...prev,
        isUploading: true,
        uploadProgress: 0,
        error: null,
      }));

      const response = await documentAPI.uploadDocument(file, (progressEvent) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setProcessing(prev => ({ ...prev, uploadProgress: progress }));
      });

      setResults(prev => ({
        ...prev,
        transactionId: response.transaction_id,
      }));

      setProcessing(prev => ({
        ...prev,
        isUploading: false,
        isProcessing: true,
        status: response.status,
      }));

      // Start polling for status
      pollProcessingStatus(response.transaction_id);

      return response;
    } catch (error) {
      setProcessing(prev => ({
        ...prev,
        isUploading: false,
        error: error.response?.data?.detail || error.message,
      }));
      throw error;
    }
  }, []);

  // Poll processing status
  const pollProcessingStatus = useCallback(async (transactionId) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await documentAPI.getStatus(transactionId);
        
        setProcessing(prev => ({
          ...prev,
          processingProgress: status.progress,
          status: status.status,
          error: status.error,
        }));

        // If completed or failed, stop polling and get results
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setProcessing(prev => ({ ...prev, isProcessing: false }));
          await fetchResults(transactionId);
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          setProcessing(prev => ({
            ...prev,
            isProcessing: false,
            error: status.error || 'Processing failed',
          }));
        }
      } catch (error) {
        console.error('Status polling error:', error);
        clearInterval(pollInterval);
        setProcessing(prev => ({
          ...prev,
          isProcessing: false,
          error: 'Failed to check processing status',
        }));
      }
    }, 2000); // Poll every 2 seconds

    // Cleanup after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
  }, []);

  // Fetch processing results
  const fetchResults = useCallback(async (transactionId) => {
    try {
      const data = await documentAPI.getResult(transactionId);
      setResults(prev => ({
        ...prev,
        data,
      }));

      // Fetch page images
      if (data.metadata?.page_count) {
        const pageImages = {};
        for (let i = 1; i <= data.metadata.page_count; i++) {
          try {
            const imageData = await documentAPI.getPageImage(transactionId, i);
            pageImages[i] = imageData.image_base64;
          } catch (error) {
            console.warn(`Failed to load page ${i} image:`, error);
          }
        }
        setResults(prev => ({
          ...prev,
          pageImages,
        }));
      }
    } catch (error) {
      console.error('Failed to fetch results:', error);
      setProcessing(prev => ({
        ...prev,
        error: 'Failed to fetch processing results',
      }));
    }
  }, []);

  // Select element
  const selectElement = useCallback((element) => {
    setResults(prev => ({
      ...prev,
      selectedElement: element,
    }));
  }, []);

  // Submit corrections
  const submitCorrections = useCallback(async (corrections) => {
    if (!results.transactionId) return;

    try {
      await documentAPI.submitCorrections(results.transactionId, corrections);
      
      // Refresh results
      await fetchResults(results.transactionId);
      
      return true;
    } catch (error) {
      console.error('Failed to submit corrections:', error);
      throw error;
    }
  }, [results.transactionId, fetchResults]);

  // Get visual grounding
  const getGrounding = useCallback(async (chunkId) => {
    if (!results.transactionId) return null;

    try {
      const grounding = await documentAPI.getGrounding(chunkId, results.transactionId);
      return grounding;
    } catch (error) {
      console.error('Failed to get grounding:', error);
      return null;
    }
  }, [results.transactionId]);

  // Reset state
  const reset = useCallback(() => {
    setProcessing({
      isUploading: false,
      isProcessing: false,
      uploadProgress: 0,
      processingProgress: 0,
      status: null,
      error: null,
    });
    setResults({
      transactionId: null,
      data: null,
      pageImages: {},
      selectedElement: null,
    });
  }, []);

  return {
    processing,
    results,
    uploadDocument,
    selectElement,
    submitCorrections,
    getGrounding,
    reset,
  };
};

export default useDocumentProcessing;
