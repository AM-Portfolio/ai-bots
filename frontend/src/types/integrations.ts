export type ServiceCategory = 
  | 'version_control'
  | 'issue_tracking'
  | 'knowledge_base'
  | 'monitoring'
  | 'databases'
  | 'apis'
  | 'cloud'
  | 'ai_providers';

export type FieldType = 'text' | 'password' | 'url' | 'select' | 'number' | 'toggle';

export type AuthType = 'basic' | 'token' | 'oauth' | 'api_key' | 'connection_string';

export interface ConfigField {
  name: string;
  label: string;
  type: FieldType;
  required: boolean;
  placeholder?: string;
  description?: string;
  options?: { value: string; label: string }[];
  defaultValue?: any;
  secret?: boolean;
}

export interface TestAction {
  endpoint: string;
  method: 'GET' | 'POST';
  successMessage: string;
  errorMessage: string;
}

export interface ServiceDefinition {
  id: string;
  name: string;
  type: string;
  category: ServiceCategory;
  description: string;
  icon: string;
  authType: AuthType;
  configFields: ConfigField[];
  testAction?: TestAction;
  capabilities?: string[];
  status?: 'connected' | 'disconnected' | 'error' | 'testing';
  isConfigured?: boolean;
  isActive?: boolean;
}

export interface ServiceConfig {
  [key: string]: any;
}

export interface CategoryInfo {
  id: ServiceCategory;
  name: string;
  description: string;
  icon: string;
}

export const CATEGORIES: Record<ServiceCategory, CategoryInfo> = {
  version_control: {
    id: 'version_control',
    name: 'Version Control',
    description: 'Source code repositories and version control systems',
    icon: 'GitBranch'
  },
  issue_tracking: {
    id: 'issue_tracking',
    name: 'Issue Tracking',
    description: 'Project management and issue tracking tools',
    icon: 'CheckSquare'
  },
  knowledge_base: {
    id: 'knowledge_base',
    name: 'Knowledge Base',
    description: 'Documentation and knowledge management platforms',
    icon: 'BookOpen'
  },
  monitoring: {
    id: 'monitoring',
    name: 'Monitoring',
    description: 'Application monitoring and observability',
    icon: 'Activity'
  },
  databases: {
    id: 'databases',
    name: 'Databases',
    description: 'Database connections and data storage',
    icon: 'Database'
  },
  apis: {
    id: 'apis',
    name: 'APIs & Services',
    description: 'External APIs and web services',
    icon: 'Zap'
  },
  cloud: {
    id: 'cloud',
    name: 'Cloud Platforms',
    description: 'Cloud infrastructure and services',
    icon: 'Cloud'
  },
  ai_providers: {
    id: 'ai_providers',
    name: 'AI Providers',
    description: 'AI and machine learning services',
    icon: 'Brain'
  }
};
