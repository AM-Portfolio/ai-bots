import { useEffect, useState } from 'react';
import { Loader2, CheckCircle2, XCircle, Clock, Play, AlertCircle } from 'lucide-react';

interface ActivityLog {
  timestamp: string;
  step: string;
  status: string;
  details: Record<string, any>;
}

interface BackendActivityStreamProps {
  message: string;
  templateName?: string;
  executeTasks?: boolean;
  onComplete?: (result: any) => void;
  onError?: (error: string) => void;
}

const BackendActivityStream = ({ 
  message, 
  templateName = 'default',
  executeTasks = true,
  onComplete,
  onError 
}: BackendActivityStreamProps) => {
  const [activities, setActivities] = useState<ActivityLog[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!message) return;

    const streamActivity = async () => {
      setIsStreaming(true);
      setActivities([]);
      setError(null);

      try {
        const response = await fetch('/api/orchestration/stream', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message,
            template_name: templateName,
            execute_tasks: executeTasks
          })
        });

        if (!response.ok || !response.body) {
          throw new Error('Failed to connect to streaming endpoint');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              try {
                const parsed = JSON.parse(data);
                
                if (parsed.type === 'final_result') {
                  onComplete?.(parsed.result);
                } else {
                  setActivities(prev => [...prev, parsed]);
                }
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }

        setIsStreaming(false);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(errorMessage);
        onError?.(errorMessage);
        setIsStreaming(false);
      }
    };

    streamActivity();
  }, [message, templateName, executeTasks]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'started':
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'skipped':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatStepName = (step: string) => {
    return step
      .replace(/_/g, ' ')
      .replace(/([A-Z])/g, ' $1')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
      .trim();
  };

  const formatDetails = (details: Record<string, any>) => {
    const important = [];
    
    if (details.action) important.push(details.action);
    if (details.references_found !== undefined) important.push(`Found ${details.references_found} references`);
    if (details.github_refs) important.push(`GitHub: ${details.github_refs}`);
    if (details.jira_refs) important.push(`Jira: ${details.jira_refs}`);
    if (details.confluence_refs) important.push(`Confluence: ${details.confluence_refs}`);
    if (details.context_items !== undefined) important.push(`Fetched ${details.context_items} items`);
    if (details.cache_hits !== undefined) important.push(`Cache hits: ${details.cache_hits}`);
    if (details.tasks_planned !== undefined) important.push(`Planned ${details.tasks_planned} tasks`);
    if (details.task_types) important.push(`Types: ${details.task_types.join(', ')}`);
    if (details.task_type) important.push(`Task: ${details.task_type}`);
    if (details.successful_tasks !== undefined) important.push(`✓ ${details.successful_tasks} successful`);
    if (details.error) important.push(`❌ ${details.error}`);
    if (details.reason) important.push(details.reason);
    
    return important.join(' • ');
  };

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <div className="flex items-center gap-2 text-red-700">
          <XCircle className="w-5 h-5" />
          <span className="font-medium">Streaming Error</span>
        </div>
        <p className="mt-2 text-sm text-red-600">{error}</p>
      </div>
    );
  }

  if (activities.length === 0 && !isStreaming) {
    return null;
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white">
      <div className="border-b border-gray-200 px-4 py-3 bg-gray-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-primary-600" />
            <h3 className="font-semibold text-gray-900">Backend Activity</h3>
          </div>
          {isStreaming && (
            <div className="flex items-center gap-2 text-sm text-blue-600">
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Processing...</span>
            </div>
          )}
        </div>
      </div>

      <div className="max-h-96 overflow-y-auto p-4 space-y-3">
        {activities.map((activity, index) => (
          <div
            key={index}
            className={`flex items-start gap-3 p-3 rounded-lg transition-all ${
              activity.status === 'running' || activity.status === 'started'
                ? 'bg-blue-50 border border-blue-200'
                : activity.status === 'completed'
                ? 'bg-green-50 border border-green-200'
                : activity.status === 'failed'
                ? 'bg-red-50 border border-red-200'
                : 'bg-gray-50 border border-gray-200'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getStatusIcon(activity.status)}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between gap-2">
                <h4 className="font-medium text-sm text-gray-900">
                  {formatStepName(activity.step)}
                </h4>
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  {new Date(activity.timestamp).toLocaleTimeString()}
                </span>
              </div>
              
              {activity.details && Object.keys(activity.details).length > 0 && (
                <p className="mt-1 text-sm text-gray-600">
                  {formatDetails(activity.details)}
                </p>
              )}
              
              {activity.status === 'failed' && activity.details.error && (
                <div className="mt-2 text-xs text-red-600 bg-red-100 rounded px-2 py-1">
                  {activity.details.error}
                </div>
              )}
            </div>
          </div>
        ))}
        
        {activities.length === 0 && isStreaming && (
          <div className="text-center py-8 text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
            <p className="text-sm">Connecting to backend...</p>
          </div>
        )}
      </div>
      
      {activities.length > 0 && (
        <div className="border-t border-gray-200 px-4 py-2 bg-gray-50">
          <div className="flex items-center justify-between text-xs text-gray-600">
            <span>{activities.length} steps</span>
            <span>
              {activities.filter(a => a.status === 'completed').length} completed •{' '}
              {activities.filter(a => a.status === 'failed').length} failed
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

export default BackendActivityStream;
