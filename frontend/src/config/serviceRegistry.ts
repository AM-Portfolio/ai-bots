import { ServiceDefinition } from '../types/integrations';

export const SERVICE_REGISTRY: ServiceDefinition[] = [
  {
    id: 'github',
    name: 'GitHub',
    category: 'version_control',
    description: 'Connect to GitHub for repository access and code analysis',
    icon: 'Github',
    authType: 'token',
    isConfigured: true,
    isActive: true,
    status: 'connected',
    configFields: [
      {
        name: 'github_token',
        label: 'Personal Access Token',
        type: 'password',
        required: true,
        secret: true,
        description: 'GitHub PAT with repo and read permissions',
        placeholder: 'ghp_xxxxxxxxxxxx'
      },
      {
        name: 'default_repo',
        label: 'Default Repository',
        type: 'text',
        required: false,
        placeholder: 'owner/repo',
        description: 'Default repository for operations'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/github/test',
      method: 'POST',
      successMessage: 'GitHub connection successful!',
      errorMessage: 'Failed to connect to GitHub'
    },
    capabilities: ['Code Search', 'File Retrieval', 'Branch Management', 'PR Creation']
  },
  {
    id: 'jira',
    name: 'Jira',
    category: 'issue_tracking',
    description: 'Connect to Jira for issue tracking and project management',
    icon: 'FileText',
    authType: 'basic',
    isConfigured: true,
    isActive: true,
    status: 'connected',
    configFields: [
      {
        name: 'jira_url',
        label: 'Jira Instance URL',
        type: 'url',
        required: true,
        placeholder: 'https://your-domain.atlassian.net',
        description: 'Your Jira cloud instance URL'
      },
      {
        name: 'jira_email',
        label: 'Email',
        type: 'text',
        required: true,
        placeholder: 'user@example.com',
        description: 'Your Jira account email'
      },
      {
        name: 'jira_api_token',
        label: 'API Token',
        type: 'password',
        required: true,
        secret: true,
        description: 'Generate from Jira Account Settings',
        placeholder: 'Your Jira API token'
      },
      {
        name: 'default_project',
        label: 'Default Project Key',
        type: 'text',
        required: false,
        placeholder: 'PROJ',
        description: 'Default project for creating tickets'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/jira/test',
      method: 'POST',
      successMessage: 'Jira connection successful!',
      errorMessage: 'Failed to connect to Jira'
    },
    capabilities: ['Create Tickets', 'Fetch Issues', 'Update Status', 'Link Issues']
  },
  {
    id: 'confluence',
    name: 'Confluence',
    category: 'knowledge_base',
    description: 'Publish documentation to Confluence pages',
    icon: 'BookOpen',
    authType: 'basic',
    isConfigured: true,
    isActive: true,
    status: 'connected',
    configFields: [
      {
        name: 'confluence_url',
        label: 'Confluence URL',
        type: 'url',
        required: true,
        placeholder: 'https://your-domain.atlassian.net/wiki',
        description: 'Your Confluence instance URL'
      },
      {
        name: 'confluence_email',
        label: 'Email',
        type: 'text',
        required: true,
        placeholder: 'user@example.com',
        description: 'Your Confluence account email'
      },
      {
        name: 'confluence_api_token',
        label: 'API Token',
        type: 'password',
        required: true,
        secret: true,
        description: 'Generate from Atlassian Account Settings',
        placeholder: 'Your API token'
      },
      {
        name: 'default_space',
        label: 'Default Space Key',
        type: 'text',
        required: false,
        placeholder: 'DOCS',
        description: 'Default space for publishing docs'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/confluence/test',
      method: 'POST',
      successMessage: 'Confluence connection successful!',
      errorMessage: 'Failed to connect to Confluence'
    },
    capabilities: ['Create Pages', 'Update Pages', 'List Spaces', 'Search Content']
  },
  {
    id: 'grafana',
    name: 'Grafana',
    category: 'monitoring',
    description: 'Fetch metrics and dashboards from Grafana',
    icon: 'Activity',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'grafana_url',
        label: 'Grafana URL',
        type: 'url',
        required: true,
        placeholder: 'https://grafana.example.com',
        description: 'Your Grafana instance URL'
      },
      {
        name: 'grafana_api_key',
        label: 'API Key',
        type: 'password',
        required: true,
        secret: true,
        description: 'Generate from Grafana API Keys',
        placeholder: 'Your Grafana API key'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/grafana/test',
      method: 'POST',
      successMessage: 'Grafana connection successful!',
      errorMessage: 'Failed to connect to Grafana'
    },
    capabilities: ['Fetch Dashboards', 'Query Metrics', 'Get Alerts']
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    category: 'databases',
    description: 'Connect to PostgreSQL databases for data operations',
    icon: 'Database',
    authType: 'connection_string',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'db_host',
        label: 'Host',
        type: 'text',
        required: true,
        placeholder: 'localhost',
        description: 'Database host address'
      },
      {
        name: 'db_port',
        label: 'Port',
        type: 'number',
        required: true,
        defaultValue: 5432,
        description: 'Database port'
      },
      {
        name: 'db_name',
        label: 'Database Name',
        type: 'text',
        required: true,
        placeholder: 'mydb',
        description: 'Name of the database'
      },
      {
        name: 'db_user',
        label: 'Username',
        type: 'text',
        required: true,
        placeholder: 'postgres',
        description: 'Database user'
      },
      {
        name: 'db_password',
        label: 'Password',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'Your database password'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/database/test',
      method: 'POST',
      successMessage: 'Database connection successful!',
      errorMessage: 'Failed to connect to database'
    },
    capabilities: ['Query Data', 'Schema Introspection', 'Data Migration']
  },
  {
    id: 'openai',
    name: 'OpenAI',
    category: 'ai_providers',
    description: 'OpenAI GPT models for AI-powered features',
    icon: 'Sparkles',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'openai_api_key',
        label: 'API Key',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'sk-...',
        description: 'Your OpenAI API key'
      },
      {
        name: 'openai_model',
        label: 'Default Model',
        type: 'select',
        required: true,
        defaultValue: 'gpt-4',
        options: [
          { value: 'gpt-4', label: 'GPT-4' },
          { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' }
        ],
        description: 'Default model for AI operations'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/openai/test',
      method: 'POST',
      successMessage: 'OpenAI connection successful!',
      errorMessage: 'Failed to connect to OpenAI'
    },
    capabilities: ['Text Generation', 'Code Analysis', 'Embeddings']
  },
  {
    id: 'azure',
    name: 'Azure',
    category: 'cloud',
    description: 'Microsoft Azure cloud services and resources',
    icon: 'Cloud',
    authType: 'oauth',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'azure_tenant_id',
        label: 'Tenant ID',
        type: 'text',
        required: true,
        placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        description: 'Azure Active Directory tenant ID'
      },
      {
        name: 'azure_client_id',
        label: 'Client ID',
        type: 'text',
        required: true,
        placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        description: 'Application (client) ID'
      },
      {
        name: 'azure_client_secret',
        label: 'Client Secret',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'Your client secret',
        description: 'Application client secret'
      },
      {
        name: 'azure_subscription_id',
        label: 'Subscription ID',
        type: 'text',
        required: false,
        placeholder: 'xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
        description: 'Azure subscription ID (optional)'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/azure/test',
      method: 'POST',
      successMessage: 'Azure connection successful!',
      errorMessage: 'Failed to connect to Azure'
    },
    capabilities: ['AKS Management', 'Resource Deployment', 'Service Management']
  },
  {
    id: 'mongodb',
    name: 'MongoDB',
    category: 'databases',
    description: 'NoSQL document database for modern applications',
    icon: 'Database',
    authType: 'connection_string',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'mongo_uri',
        label: 'Connection String',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'mongodb://username:password@host:port/database',
        description: 'MongoDB connection URI'
      },
      {
        name: 'mongo_database',
        label: 'Database Name',
        type: 'text',
        required: true,
        placeholder: 'mydb',
        description: 'Default database to use'
      },
      {
        name: 'mongo_max_pool_size',
        label: 'Max Pool Size',
        type: 'number',
        required: false,
        defaultValue: 10,
        description: 'Maximum connection pool size'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/mongodb/test',
      method: 'POST',
      successMessage: 'MongoDB connection successful!',
      errorMessage: 'Failed to connect to MongoDB'
    },
    capabilities: ['Document Operations', 'Aggregation', 'Indexing', 'Collections Management']
  },
  {
    id: 'stripe',
    name: 'Stripe',
    category: 'apis',
    description: 'Payment processing and subscription management',
    icon: 'Zap',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'stripe_secret_key',
        label: 'Secret Key',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'sk_test_...',
        description: 'Stripe secret API key'
      },
      {
        name: 'stripe_publishable_key',
        label: 'Publishable Key',
        type: 'text',
        required: false,
        placeholder: 'pk_test_...',
        description: 'Stripe publishable key for frontend'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/stripe/test',
      method: 'POST',
      successMessage: 'Stripe connection successful!',
      errorMessage: 'Failed to connect to Stripe'
    },
    capabilities: ['Payment Processing', 'Subscriptions', 'Invoicing', 'Webhooks']
  },
  {
    id: 'twilio',
    name: 'Twilio',
    category: 'apis',
    description: 'SMS, voice, and messaging APIs',
    icon: 'Zap',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'twilio_account_sid',
        label: 'Account SID',
        type: 'text',
        required: true,
        placeholder: 'ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        description: 'Twilio Account SID'
      },
      {
        name: 'twilio_auth_token',
        label: 'Auth Token',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'Your auth token',
        description: 'Twilio authentication token'
      },
      {
        name: 'twilio_phone_number',
        label: 'Phone Number',
        type: 'text',
        required: false,
        placeholder: '+1234567890',
        description: 'Your Twilio phone number'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/twilio/test',
      method: 'POST',
      successMessage: 'Twilio connection successful!',
      errorMessage: 'Failed to connect to Twilio'
    },
    capabilities: ['SMS Messaging', 'Voice Calls', 'WhatsApp', 'Video']
  },
  {
    id: 'sendgrid',
    name: 'SendGrid',
    category: 'apis',
    description: 'Email delivery and marketing platform',
    icon: 'Zap',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'sendgrid_api_key',
        label: 'API Key',
        type: 'password',
        required: true,
        secret: true,
        placeholder: 'SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
        description: 'SendGrid API key'
      },
      {
        name: 'sendgrid_from_email',
        label: 'From Email',
        type: 'text',
        required: false,
        placeholder: 'noreply@example.com',
        description: 'Default sender email address'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/sendgrid/test',
      method: 'POST',
      successMessage: 'SendGrid connection successful!',
      errorMessage: 'Failed to connect to SendGrid'
    },
    capabilities: ['Email Sending', 'Templates', 'Analytics', 'Marketing Campaigns']
  },
  {
    id: 'rest_api',
    name: 'REST API',
    category: 'apis',
    description: 'Custom REST API integration',
    icon: 'Zap',
    authType: 'api_key',
    isConfigured: false,
    isActive: false,
    status: 'disconnected',
    configFields: [
      {
        name: 'api_name',
        label: 'API Name',
        type: 'text',
        required: true,
        placeholder: 'My API',
        description: 'Custom name for this API'
      },
      {
        name: 'api_base_url',
        label: 'Base URL',
        type: 'url',
        required: true,
        placeholder: 'https://api.example.com',
        description: 'API base endpoint URL'
      },
      {
        name: 'api_auth_type',
        label: 'Authentication Type',
        type: 'select',
        required: true,
        defaultValue: 'bearer',
        options: [
          { value: 'none', label: 'None' },
          { value: 'bearer', label: 'Bearer Token' },
          { value: 'api_key', label: 'API Key' },
          { value: 'basic', label: 'Basic Auth' }
        ],
        description: 'How to authenticate requests'
      },
      {
        name: 'api_key_value',
        label: 'API Key / Token',
        type: 'password',
        required: false,
        secret: true,
        placeholder: 'Your API key or token',
        description: 'Authentication credential'
      }
    ],
    testAction: {
      endpoint: '/api/integrations/custom-api/test',
      method: 'POST',
      successMessage: 'API connection successful!',
      errorMessage: 'Failed to connect to API'
    },
    capabilities: ['Custom Endpoints', 'Data Fetching', 'Webhooks']
  }
];

export function getServicesByCategory(category: string): ServiceDefinition[] {
  return SERVICE_REGISTRY.filter(service => service.category === category);
}

export function getServiceById(id: string): ServiceDefinition | undefined {
  return SERVICE_REGISTRY.find(service => service.id === id);
}

export function getActiveServices(): ServiceDefinition[] {
  return SERVICE_REGISTRY.filter(service => service.isActive);
}

export function getConfiguredServices(): ServiceDefinition[] {
  return SERVICE_REGISTRY.filter(service => service.isConfigured);
}
