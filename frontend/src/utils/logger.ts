import { create } from 'zustand';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'success';

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: LogLevel;
  category: string;
  message: string;
  data?: any;
}

interface LogStore {
  logs: LogEntry[];
  maxLogs: number;
  addLog: (level: LogLevel, category: string, message: string, data?: any) => void;
  clearLogs: () => void;
  getLogsByCategory: (category: string) => LogEntry[];
  getLogsByLevel: (level: LogLevel) => LogEntry[];
}

export const useLogStore = create<LogStore>((set, get) => ({
  logs: [],
  maxLogs: 1000,

  addLog: (level, category, message, data) => {
    const entry: LogEntry = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      level,
      category,
      message,
      data,
    };

    set((state) => {
      const newLogs = [...state.logs, entry];
      if (newLogs.length > state.maxLogs) {
        newLogs.shift();
      }
      return { logs: newLogs };
    });

    const prefix = `[${category}]`;
    const formattedMessage = `${prefix} ${message}`;

    switch (level) {
      case 'debug':
        console.debug(formattedMessage, data || '');
        break;
      case 'info':
        console.info(formattedMessage, data || '');
        break;
      case 'warn':
        console.warn(formattedMessage, data || '');
        break;
      case 'error':
        console.error(formattedMessage, data || '');
        break;
      case 'success':
        console.log(`✅ ${formattedMessage}`, data || '');
        break;
    }
  },

  clearLogs: () => set({ logs: [] }),

  getLogsByCategory: (category) => {
    return get().logs.filter((log) => log.category === category);
  },

  getLogsByLevel: (level) => {
    return get().logs.filter((log) => log.level === level);
  },
}));

class Logger {
  private category: string;

  constructor(category: string) {
    this.category = category;
  }

  debug(message: string, data?: any) {
    useLogStore.getState().addLog('debug', this.category, message, data);
  }

  info(message: string, data?: any) {
    useLogStore.getState().addLog('info', this.category, message, data);
  }

  warn(message: string, data?: any) {
    useLogStore.getState().addLog('warn', this.category, message, data);
  }

  error(message: string, data?: any) {
    useLogStore.getState().addLog('error', this.category, message, data);
  }

  success(message: string, data?: any) {
    useLogStore.getState().addLog('success', this.category, message, data);
  }

  async track<T>(operation: string, fn: () => Promise<T>): Promise<T> {
    const startTime = Date.now();
    this.info(`Starting: ${operation}`);

    try {
      const result = await fn();
      const duration = Date.now() - startTime;
      this.success(`Completed: ${operation}`, { duration: `${duration}ms` });
      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      this.error(`Failed: ${operation}`, { 
        error: error instanceof Error ? error.message : String(error),
        duration: `${duration}ms` 
      });
      throw error;
    }
  }
}

export const createLogger = (category: string): Logger => {
  return new Logger(category);
};

export const logger = {
  chat: createLogger('Chat'),
  voice: createLogger('Voice'),
  integrations: createLogger('Integrations'),
  api: createLogger('API'),
  orchestrator: createLogger('Orchestrator'),
  llm: createLogger('LLM'),
  ui: createLogger('UI'),
};
