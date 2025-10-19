import { useState, useEffect } from 'react';
import { 
  Github, FileText, BookOpen, Activity, Database, Zap, Cloud, Brain,
  GitBranch, CheckSquare, CheckCircle, XCircle, Loader2,
  AlertCircle, Eye, EyeOff, X, Check, Settings, History, Plug, RefreshCw
} from 'lucide-react';
import { getServicesByCategory, SERVICE_REGISTRY } from '../../config/serviceRegistry';
import { CATEGORIES, ServiceCategory, ServiceDefinition } from '../../types/integrations';
import { getAllServiceStatuses, ServiceStatus } from '../../api/servicesClient';

const ICON_MAP: Record<string, any> = {
  Github, FileText, BookOpen, Activity, Database, Zap, Cloud, Brain,
  GitBranch, CheckSquare, Sparkles: Brain
};

interface ConnectionHistory {
  id: string;
  serviceName: string;
  action: 'connected' | 'disconnected' | 'tested' | 'error';
  timestamp: Date;
  message?: string;
}

const IntegrationsHub = () => {
  const [selectedCategory, setSelectedCategory] = useState<ServiceCategory>('version_control');
  const [selectedService, setSelectedService] = useState<ServiceDefinition | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [configData, setConfigData] = useState<Record<string, any>>({});
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [history, setHistory] = useState<ConnectionHistory[]>([]);
  const [serviceStatuses, setServiceStatuses] = useState<Record<string, ServiceStatus>>({});
  const [isLoadingStatuses, setIsLoadingStatuses] = useState(false);

  // Fetch live service statuses
  const fetchStatuses = async () => {
    setIsLoadingStatuses(true);
    try {
      const statuses = await getAllServiceStatuses();
      setServiceStatuses(statuses);
    } catch (error) {
      console.error('Failed to fetch service statuses:', error);
    } finally {
      setIsLoadingStatuses(false);
    }
  };

  // Load statuses on mount
  useEffect(() => {
    fetchStatuses();
  }, []);

  const services = getServicesByCategory(selectedCategory).map(service => ({
    ...service,
    status: serviceStatuses[service.id]?.status || service.status || 'disconnected'
  }));

  const categories = Object.values(CATEGORIES);

  // Get all connected services using live status
  const allServicesWithStatus = SERVICE_REGISTRY.map(service => ({
    ...service,
    status: serviceStatuses[service.id]?.status || service.status || 'disconnected'
  }));
  const connectedServices = allServicesWithStatus.filter(s => s.status === 'connected');
  const totalServices = SERVICE_REGISTRY.length;

  const addToHistory = (serviceName: string, action: ConnectionHistory['action'], message?: string) => {
    const newEntry: ConnectionHistory = {
      id: Date.now().toString(),
      serviceName,
      action,
      timestamp: new Date(),
      message
    };
    setHistory(prev => [newEntry, ...prev].slice(0, 50)); // Keep last 50 entries
  };

  const handleServiceClick = (service: ServiceDefinition) => {
    setSelectedService(service);
    setTestResult(null);
    
    const initialConfig: Record<string, any> = {};
    service.configFields.forEach(field => {
      if (field.defaultValue !== undefined) {
        initialConfig[field.name] = field.defaultValue;
      }
    });
    setConfigData(initialConfig);
  };

  const handleConfigChange = (fieldName: string, value: any) => {
    setConfigData(prev => ({ ...prev, [fieldName]: value }));
  };

  const toggleSecretVisibility = (fieldName: string) => {
    setShowSecrets(prev => ({ ...prev, [fieldName]: !prev[fieldName] }));
  };

  const handleTest = async () => {
    if (!selectedService) return;
    
    setIsTesting(true);
    setTestResult(null);

    try {
      const { connectService } = await import('../../api/servicesClient');
      await connectService({
        service_name: selectedService.id,
        service_type: selectedService.type,
        config: configData
      });
      
      const { testService } = await import('../../api/servicesClient');
      const result = await testService(selectedService.id);
      
      const success = result.success;
      const message = success 
        ? selectedService.testAction?.successMessage || 'Connection successful'
        : result.error || 'Connection failed';
      
      setTestResult({ success, message });
      addToHistory(selectedService.name, success ? 'tested' : 'error', message);
      
      // Refresh statuses after test
      await fetchStatuses();
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Connection failed';
      setTestResult({ success: false, message });
      addToHistory(selectedService.name, 'error', message);
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = async () => {
    if (!selectedService) return;
    
    try {
      const { connectService } = await import('../../api/servicesClient');
      await connectService({
        service_name: selectedService.id,
        service_type: selectedService.type,
        config: configData
      });
      addToHistory(selectedService.name, 'connected', 'Configuration saved successfully');
      
      // Refresh statuses after save
      await fetchStatuses();
      setSelectedService(null);
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Save failed';
      setTestResult({ success: false, message });
      addToHistory(selectedService.name, 'error', message);
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-50 border-green-200';
      case 'error': return 'text-red-600 bg-red-50 border-red-200';
      case 'testing': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'connected': return <CheckCircle className="w-4 h-4" />;
      case 'error': return <XCircle className="w-4 h-4" />;
      case 'testing': return <Loader2 className="w-4 h-4 animate-spin" />;
      default: return <AlertCircle className="w-4 h-4" />;
    }
  };

  const getActionIcon = (action: ConnectionHistory['action']) => {
    switch (action) {
      case 'connected': return <Plug className="w-4 h-4 text-green-600" />;
      case 'disconnected': return <X className="w-4 h-4 text-gray-600" />;
      case 'tested': return <Activity className="w-4 h-4 text-blue-600" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-600" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Top Status Bar */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-700">
                {connectedServices.length} / {totalServices} Connected
              </span>
            </div>
            
            {/* Refresh Button */}
            <button
              onClick={fetchStatuses}
              disabled={isLoadingStatuses}
              className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded transition-colors"
              title="Refresh connection status"
            >
              <RefreshCw className={`w-3 h-3 ${isLoadingStatuses ? 'animate-spin' : ''}`} />
              <span>Refresh</span>
            </button>
            
            {/* Quick Status */}
            <div className="flex items-center space-x-2 overflow-x-auto">
              {connectedServices.slice(0, 5).map(service => {
                const Icon = ICON_MAP[service.icon];
                return (
                  <div
                    key={service.id}
                    className="flex items-center space-x-1 px-2 py-1 bg-green-50 border border-green-200 rounded-lg"
                    title={service.name}
                  >
                    <Icon className="w-3 h-3 text-green-600" />
                    <span className="text-xs font-medium text-green-700">{service.name}</span>
                  </div>
                );
              })}
              {connectedServices.length > 5 && (
                <span className="text-xs text-gray-500 px-2">
                  +{connectedServices.length - 5} more
                </span>
              )}
              {connectedServices.length === 0 && (
                <span className="text-xs text-gray-500">No services connected yet</span>
              )}
            </div>
          </div>

          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center space-x-2 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <History className="w-4 h-4" />
            <span>History</span>
            {history.length > 0 && (
              <span className="px-1.5 py-0.5 text-xs bg-primary-100 text-primary-700 rounded-full">
                {history.length}
              </span>
            )}
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Category Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-3 space-y-1">
            {categories.map(category => {
              const Icon = ICON_MAP[category.icon];
              const categoryServices = getServicesByCategory(category.id);
              const connectedCount = categoryServices.filter(s => s.status === 'connected').length;
              
              return (
                <button
                  key={category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg transition-all ${
                    selectedCategory === category.id
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-5 h-5" />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">{category.name}</div>
                      <div className="text-xs text-gray-500">
                        {connectedCount}/{categoryServices.length} connected
                      </div>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Service Grid */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="mb-6">
            <h3 className="text-2xl font-bold text-gray-900">
              {CATEGORIES[selectedCategory].name}
            </h3>
            <p className="text-gray-600 mt-1">
              {CATEGORIES[selectedCategory].description}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {services.map(service => {
              const Icon = ICON_MAP[service.icon];
              const configuredFieldsCount = service.configFields.filter(f => f.required).length;
              
              return (
                <div
                  key={service.id}
                  onClick={() => handleServiceClick(service)}
                  className="card hover:shadow-lg transition-all cursor-pointer group"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-gray-100 rounded-lg group-hover:bg-primary-50 transition-colors">
                        <Icon className="w-6 h-6 text-gray-700 group-hover:text-primary-600" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-gray-900">{service.name}</h4>
                        <div className={`inline-flex items-center space-x-1 px-2 py-0.5 rounded-full text-xs border mt-1 ${getStatusColor(service.status)}`}>
                          {getStatusIcon(service.status)}
                          <span className="capitalize">{service.status || 'disconnected'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <p className="text-sm text-gray-600 mb-3 line-clamp-2">{service.description}</p>

                  {/* Configuration Summary */}
                  {service.isConfigured && (
                    <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded-lg">
                      <div className="flex items-center space-x-2">
                        <Settings className="w-3 h-3 text-blue-600" />
                        <span className="text-xs text-blue-700 font-medium">
                          {configuredFieldsCount} required fields configured
                        </span>
                      </div>
                    </div>
                  )}

                  {service.capabilities && service.capabilities.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {service.capabilities.slice(0, 3).map((cap, idx) => (
                        <span key={idx} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          {cap}
                        </span>
                      ))}
                      {service.capabilities.length > 3 && (
                        <span className="text-xs text-gray-500">
                          +{service.capabilities.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {services.length === 0 && (
            <div className="text-center py-12">
              <Database className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-600">No services in this category yet</p>
              <p className="text-sm text-gray-500 mt-1">Check back soon for more integrations</p>
            </div>
          )}
        </div>

        {/* History Sidebar */}
        {showHistory && (
          <div className="w-96 bg-white border-l border-gray-200 overflow-y-auto">
            <div className="p-4 border-b border-gray-200 sticky top-0 bg-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <History className="w-5 h-5 text-gray-700" />
                  <h3 className="font-semibold text-gray-900">Connection History</h3>
                </div>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-1 hover:bg-gray-100 rounded"
                >
                  <X className="w-4 h-4 text-gray-600" />
                </button>
              </div>
            </div>

            <div className="p-4 space-y-3">
              {history.length === 0 ? (
                <div className="text-center py-8">
                  <History className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">No connection history yet</p>
                  <p className="text-xs text-gray-500 mt-1">
                    Connect or test services to see activity
                  </p>
                </div>
              ) : (
                history.map(entry => (
                  <div key={entry.id} className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start space-x-2">
                      {getActionIcon(entry.action)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm text-gray-900">
                            {entry.serviceName}
                          </span>
                          <span className="text-xs text-gray-500">
                            {new Date(entry.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <span className="text-xs text-gray-600 capitalize">{entry.action}</span>
                        {entry.message && (
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                            {entry.message}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>

      {/* Service Detail Modal */}
      {selectedService && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {(() => {
                    const Icon = ICON_MAP[selectedService.icon];
                    return <Icon className="w-8 h-8 text-gray-700" />;
                  })()}
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">{selectedService.name}</h3>
                    <p className="text-sm text-gray-600">{selectedService.description}</p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedService(null)}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-gray-600" />
                </button>
              </div>
            </div>

            {/* Configuration Form */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-semibold text-gray-900">Configuration</h4>
                  <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded">
                    {selectedService.authType.toUpperCase()}
                  </span>
                </div>

                {selectedService.configFields.map(field => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    
                    {field.type === 'select' ? (
                      <select
                        value={configData[field.name] || field.defaultValue || ''}
                        onChange={(e) => handleConfigChange(field.name, e.target.value)}
                        className="input-field"
                      >
                        {field.options?.map(opt => (
                          <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                      </select>
                    ) : field.type === 'password' ? (
                      <div className="relative">
                        <input
                          type={showSecrets[field.name] ? 'text' : 'password'}
                          value={configData[field.name] || ''}
                          onChange={(e) => handleConfigChange(field.name, e.target.value)}
                          placeholder={field.placeholder}
                          className="input-field pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => toggleSecretVisibility(field.name)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                        >
                          {showSecrets[field.name] ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    ) : field.type === 'number' ? (
                      <input
                        type="number"
                        value={configData[field.name] || field.defaultValue || ''}
                        onChange={(e) => handleConfigChange(field.name, parseInt(e.target.value))}
                        placeholder={field.placeholder}
                        className="input-field"
                      />
                    ) : (
                      <input
                        type="text"
                        value={configData[field.name] || ''}
                        onChange={(e) => handleConfigChange(field.name, e.target.value)}
                        placeholder={field.placeholder}
                        className="input-field"
                      />
                    )}
                    
                    {field.description && (
                      <p className="text-xs text-gray-500 mt-1">{field.description}</p>
                    )}
                  </div>
                ))}

                {/* Test Connection */}
                {selectedService.testAction && (
                  <div className="pt-4 border-t border-gray-200">
                    <button
                      onClick={handleTest}
                      disabled={isTesting}
                      className="btn-secondary w-full flex items-center justify-center space-x-2"
                    >
                      {isTesting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          <span>Testing Connection...</span>
                        </>
                      ) : (
                        <>
                          <Activity className="w-4 h-4" />
                          <span>Test Connection</span>
                        </>
                      )}
                    </button>

                    {testResult && (
                      <div className={`mt-3 p-3 rounded-lg flex items-center space-x-2 ${
                        testResult.success 
                          ? 'bg-green-50 text-green-700 border border-green-200'
                          : 'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {testResult.success ? (
                          <CheckCircle className="w-5 h-5" />
                        ) : (
                          <XCircle className="w-5 h-5" />
                        )}
                        <span className="text-sm font-medium">{testResult.message}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Capabilities */}
                {selectedService.capabilities && selectedService.capabilities.length > 0 && (
                  <div className="pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-700 mb-2">Capabilities</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedService.capabilities.map((cap, idx) => (
                        <span key={idx} className="inline-flex items-center space-x-1 text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                          <Check className="w-3 h-3" />
                          <span>{cap}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Footer Actions */}
            <div className="p-6 border-t border-gray-200 bg-gray-50">
              <div className="flex items-center justify-end space-x-3">
                <button
                  onClick={() => setSelectedService(null)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  className="btn-primary"
                >
                  Save Configuration
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsHub;
