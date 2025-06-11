import React from 'react';
import { CheckCircle, AlertCircle, Loader2, Clock } from 'lucide-react';

const ProcessingStatus = ({ 
  status, 
  progress, 
  isProcessing, 
  error,
  transactionId 
}) => {
  const getStatusIcon = () => {
    if (error) {
      return <AlertCircle className="w-6 h-6 text-red-500" />;
    }
    
    if (status === 'completed') {
      return <CheckCircle className="w-6 h-6 text-green-500" />;
    }
    
    if (isProcessing) {
      return <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />;
    }
    
    return <Clock className="w-6 h-6 text-gray-400" />;
  };

  const getStatusText = () => {
    if (error) return 'Processing Failed';
    
    const statusMap = {
      pending: 'Pending',
      parsing: 'Parsing Document',
      structuring: 'Structuring Data',
      validating: 'Validating Content',
      highlighting: 'Creating Highlights',
      storing: 'Storing Results',
      completed: 'Processing Complete',
      failed: 'Processing Failed'
    };
    
    return statusMap[status] || 'Unknown Status';
  };

  const getStatusColor = () => {
    if (error || status === 'failed') return 'text-red-600';
    if (status === 'completed') return 'text-green-600';
    if (isProcessing) return 'text-primary-600';
    return 'text-gray-600';
  };

  const getProgressColor = () => {
    if (error || status === 'failed') return 'bg-red-500';
    if (status === 'completed') return 'bg-green-500';
    return 'bg-primary-500';
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div className="card p-6">
        <div className="flex items-center space-x-4 mb-4">
          {getStatusIcon()}
          <div className="flex-1">
            <h3 className={`text-lg font-semibold ${getStatusColor()}`}>
              {getStatusText()}
            </h3>
            {transactionId && (
              <p className="text-sm text-gray-500 font-mono">
                ID: {transactionId}
              </p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Progress</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div
              className={`h-3 rounded-full transition-all duration-500 ${getProgressColor()}`}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Processing Steps */}
        <div className="space-y-2">
          <ProcessingStep 
            name="Parse" 
            status={getStepStatus('parsing', status, progress)} 
          />
          <ProcessingStep 
            name="Structure" 
            status={getStepStatus('structuring', status, progress)} 
          />
          <ProcessingStep 
            name="Validate" 
            status={getStepStatus('validating', status, progress)} 
          />
          <ProcessingStep 
            name="Highlight" 
            status={getStepStatus('highlighting', status, progress)} 
          />
          <ProcessingStep 
            name="Store" 
            status={getStepStatus('storing', status, progress)} 
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {status === 'completed' && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-700">
              Document processing completed successfully! You can now view the results below.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const ProcessingStep = ({ name, status }) => {
  const getStepIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'active':
        return <Loader2 className="w-4 h-4 text-primary-500 animate-spin" />;
      case 'pending':
        return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />;
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-300" />;
    }
  };

  const getStepTextColor = () => {
    switch (status) {
      case 'completed':
        return 'text-green-700';
      case 'active':
        return 'text-primary-700';
      case 'pending':
        return 'text-gray-500';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="flex items-center space-x-3">
      {getStepIcon()}
      <span className={`text-sm font-medium ${getStepTextColor()}`}>
        {name}
      </span>
    </div>
  );
};

// Helper function to determine step status
const getStepStatus = (stepName, currentStatus, progress) => {
  const stepOrder = ['parsing', 'structuring', 'validating', 'highlighting', 'storing'];
  const currentIndex = stepOrder.indexOf(currentStatus);
  const stepIndex = stepOrder.indexOf(stepName);

  if (currentStatus === 'completed') {
    return 'completed';
  }

  if (currentStatus === 'failed') {
    return stepIndex <= currentIndex ? 'failed' : 'pending';
  }

  if (stepIndex < currentIndex) {
    return 'completed';
  } else if (stepIndex === currentIndex) {
    return 'active';
  } else {
    return 'pending';
  }
};

export default ProcessingStatus;
