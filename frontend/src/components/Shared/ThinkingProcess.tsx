import { CheckCircle, XCircle, Loader2, Clock, ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface ThinkingStep {
  id: string;
  title: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'skipped';
  start_time: string | null;
  end_time: string | null;
  metadata: Record<string, any>;
  error: string | null;
  duration_ms: number | null;
}

interface ThinkingProcessData {
  workflow_id: string;
  workflow_type: string;
  steps: ThinkingStep[];
  start_time: string;
  end_time: string | null;
  total_duration_ms: number | null;
  status: string;
}

interface ThinkingProcessProps {
  data: ThinkingProcessData | null;
  title?: string;
}

const ThinkingProcess = ({ data, title = "Backend Processing Steps" }: ThinkingProcessProps) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState<Set<string>>(new Set());

  if (!data) {
    return null;
  }

  const toggleStep = (stepId: string) => {
    const newExpanded = new Set(expandedSteps);
    if (newExpanded.has(stepId)) {
      newExpanded.delete(stepId);
    } else {
      newExpanded.add(stepId);
    }
    setExpandedSteps(newExpanded);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'in_progress':
        return <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />;
      case 'skipped':
        return <div className="w-5 h-5 text-gray-400">⊘</div>;
      default:
        return <div className="w-5 h-5 border-2 border-gray-300 rounded-full" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-50 border-green-200';
      case 'failed':
        return 'bg-red-50 border-red-200';
      case 'in_progress':
        return 'bg-blue-50 border-blue-200';
      case 'skipped':
        return 'bg-gray-50 border-gray-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  return (
    <div className="card bg-gray-50">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-3">
          {isExpanded ? (
            <ChevronDown className="w-5 h-5 text-gray-500" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-500" />
          )}
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <span className="text-sm text-gray-500">
            ({data.steps.filter(s => s.status === 'completed').length}/{data.steps.length} completed)
          </span>
        </div>
        {data.total_duration_ms && (
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>{formatDuration(data.total_duration_ms)}</span>
          </div>
        )}
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-2">
          {data.steps.map((step, index) => (
            <div key={step.id} className="relative">
              {/* Connecting line */}
              {index < data.steps.length - 1 && (
                <div className="absolute left-2.5 top-8 bottom-0 w-0.5 bg-gray-300" />
              )}

              <div className={`relative border rounded-lg p-3 ${getStatusColor(step.status)}`}>
                <div 
                  className="flex items-start space-x-3 cursor-pointer"
                  onClick={() => toggleStep(step.id)}
                >
                  <div className="flex-shrink-0 mt-0.5">
                    {getStatusIcon(step.status)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-gray-900">{step.title}</p>
                      {step.duration_ms !== null && (
                        <span className="text-xs text-gray-500 ml-2">
                          {formatDuration(step.duration_ms)}
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{step.description}</p>

                    {/* Expanded details */}
                    {expandedSteps.has(step.id) && (
                      <div className="mt-3 pt-3 border-t border-gray-300 space-y-2">
                        {step.error && (
                          <div className="bg-red-100 border border-red-300 rounded p-2">
                            <p className="text-sm text-red-800 font-medium">Error:</p>
                            <p className="text-sm text-red-700">{step.error}</p>
                          </div>
                        )}

                        {Object.keys(step.metadata).length > 0 && (
                          <div className="bg-white border border-gray-300 rounded p-2">
                            <p className="text-xs font-medium text-gray-700 mb-1">Metadata:</p>
                            <div className="text-xs text-gray-600 space-y-1">
                              {Object.entries(step.metadata).map(([key, value]) => (
                                <div key={key} className="flex items-start">
                                  <span className="font-medium mr-2">{key}:</span>
                                  <span className="flex-1">{JSON.stringify(value)}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="text-xs text-gray-500">
                          {step.start_time && <p>Started: {new Date(step.start_time).toLocaleTimeString()}</p>}
                          {step.end_time && <p>Ended: {new Date(step.end_time).toLocaleTimeString()}</p>}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThinkingProcess;
