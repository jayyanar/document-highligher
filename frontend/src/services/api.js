import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API functions
export const documentAPI = {
  // Upload document
  uploadDocument: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    
    return response.data;
  },

  // Get processing status
  getStatus: async (transactionId) => {
    const response = await api.get(`/api/status/${transactionId}`);
    return response.data;
  },

  // Get processing result
  getResult: async (transactionId) => {
    const response = await api.get(`/api/result/${transactionId}`);
    return response.data;
  },

  // Get visual grounding
  getGrounding: async (chunkId, transactionId) => {
    const response = await api.get(`/api/grounding/${chunkId}`, {
      params: { transaction_id: transactionId }
    });
    return response.data;
  },

  // Submit corrections
  submitCorrections: async (transactionId, corrections) => {
    const response = await api.patch(`/api/correct/${transactionId}`, corrections);
    return response.data;
  },

  // Get page image
  getPageImage: async (transactionId, pageNumber = 1) => {
    const response = await api.get(`/api/page-image/${transactionId}`, {
      params: { page_number: pageNumber }
    });
    return response.data;
  },

  // Delete result
  deleteResult: async (transactionId) => {
    const response = await api.delete(`/api/result/${transactionId}`);
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/api/health');
    return response.data;
  },

  // Get API info
  getInfo: async () => {
    const response = await api.get('/api/info');
    return response.data;
  },
};

// Utility functions
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const getFileType = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const types = {
    pdf: 'PDF Document',
    png: 'PNG Image',
    jpg: 'JPEG Image',
    jpeg: 'JPEG Image',
  };
  return types[ext] || 'Unknown';
};

export const isValidFileType = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  return ['pdf', 'png', 'jpg', 'jpeg'].includes(ext);
};

export default api;
