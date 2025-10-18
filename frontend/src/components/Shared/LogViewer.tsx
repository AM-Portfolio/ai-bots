import React, { useState, useEffect, useRef } from 'react';
import { useLogStore, LogEntry, LogLevel } from '../../utils/logger';
import { Terminal, X, Filter, Trash2, ChevronDown, ChevronRight } from 'lucide-react';

const LogViewer: React.FC = () => {
  const { logs, clearLogs } = useLogStore();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedLevel, setSelectedLevel] = useState<LogLevel | 'all'>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedLogs, setExpandedLogs] = useState<Set<string>>(new Set());
  const logContainerRef = useRef<HTMLDivElement>(null);

  const categories = Array.from(new Set(logs.map((log) => log.category)));
  const levels: (LogLevel | 'all')[] = ['all', 'debug', 'info', 'warn', 'error', 'success'];

  const filteredLogs = logs.filter((log) => {
    const levelMatch = selectedLevel === 'all' || log.level === selectedLevel;
    const categoryMatch = selectedCategory === 'all' || log.category === selectedCategory;
    return levelMatch && categoryMatch;
  });

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  const getLevelColor = (level: LogLevel): string => {
    switch (level) {
      case 'debug':
        return 'text-gray-500 bg-gray-50';
      case 'info':
        return 'text-blue-600 bg-blue-50';
      case 'warn':
        return 'text-yellow-600 bg-yellow-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'success':
        return 'text-green-600 bg-green-50';
    }
  };

  const getLevelIcon = (level: LogLevel): string => {
    switch (level) {
      case 'debug':
        return '🔍';
      case 'info':
        return 'ℹ️';
      case 'warn':
        return '⚠️';
      case 'error':
        return '❌';
      case 'success':
        return '✅';
    }
  };

  const toggleLogExpansion = (logId: string) => {
    setExpandedLogs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(logId)) {
        newSet.delete(logId);
      } else {
        newSet.add(logId);
      }
      return newSet;
    });
  };

  const formatTime = (date: Date): string => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
    });
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 p-3 bg-gray-800 text-white rounded-full shadow-lg hover:bg-gray-700 transition-colors z-50"
        title="Open Log Viewer"
      >
        <Terminal className="w-5 h-5" />
        {logs.length > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
            {logs.length > 99 ? '99+' : logs.length}
          </span>
        )}
      </button>
    );
  }

  return (
    <div className="fixed bottom-4 right-4 w-[600px] h-[500px] bg-white rounded-lg shadow-2xl border border-gray-300 flex flex-col z-50">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-2">
          <Terminal className="w-5 h-5 text-gray-700" />
          <h3 className="font-semibold text-gray-800">Activity Log</h3>
          <span className="text-xs text-gray-500">({filteredLogs.length} entries)</span>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={clearLogs}
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Clear logs"
          >
            <Trash2 className="w-4 h-4 text-gray-600" />
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 hover:bg-gray-200 rounded transition-colors"
            title="Close"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-2 p-2 border-b border-gray-200 bg-gray-50">
        <Filter className="w-4 h-4 text-gray-500" />
        <select
          value={selectedLevel}
          onChange={(e) => setSelectedLevel(e.target.value as LogLevel | 'all')}
          className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        >
          {levels.map((level) => (
            <option key={level} value={level}>
              {level.toUpperCase()}
            </option>
          ))}
        </select>
        <select
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="text-xs border border-gray-300 rounded px-2 py-1 bg-white"
        >
          <option value="all">ALL CATEGORIES</option>
          {categories.map((category) => (
            <option key={category} value={category}>
              {category}
            </option>
          ))}
        </select>
      </div>

      {/* Logs */}
      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto p-2 space-y-1 bg-gray-900 text-gray-100 font-mono text-xs"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center text-gray-500 mt-8">No logs to display</div>
        ) : (
          filteredLogs.map((log) => (
            <div key={log.id} className="border-b border-gray-700 pb-1">
              <div
                className="flex items-start space-x-2 cursor-pointer hover:bg-gray-800 p-1 rounded"
                onClick={() => log.data && toggleLogExpansion(log.id)}
              >
                {log.data && (
                  <span className="text-gray-500 mt-0.5">
                    {expandedLogs.has(log.id) ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                  </span>
                )}
                <span className="text-gray-500 whitespace-nowrap">{formatTime(log.timestamp)}</span>
                <span className="whitespace-nowrap">{getLevelIcon(log.level)}</span>
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium whitespace-nowrap ${getLevelColor(log.level)}`}>
                  {log.category}
                </span>
                <span className="flex-1 text-gray-200">{log.message}</span>
              </div>
              {log.data && expandedLogs.has(log.id) && (
                <div className="ml-8 mt-1 p-2 bg-gray-800 rounded text-gray-300 overflow-x-auto">
                  <pre>{JSON.stringify(log.data, null, 2)}</pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogViewer;
