import { useState } from 'react';
import { 
  Github, FileText, BookOpen, Activity, Database, Zap, Cloud, Brain,
  GitBranch, CheckSquare, CheckCircle, XCircle, Loader2,
  AlertCircle, Eye, EyeOff, X, Check
} from 'lucide-react';
import { getServicesByCategory } from '../../config/serviceRegistry';
import { CATEGORIES, ServiceCategory, ServiceDefinition } from '../../types/integrations';

const ICON_MAP: Record<string, any> = {
  Github, FileText, BookOpen, Activity, Database, Zap, Cloud, Brain,
  GitBranch, CheckSquare, Sparkles: Brain
};

const IntegrationsHub = () => {
  const [selectedCategory, setSelectedCategory] = useState<ServiceCategory>('version_control');
  const [selectedService, setSelectedService] = useState<ServiceDefinition | null>(null);
  const [showSecrets, setShowSecrets] = useState<Record<string, boolean>>({});
  const [configData, setConfigData] = useState<Record<string, any>>({});
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  const services = getServicesByCategory(selectedCategory);
  const categories = Object.values(CATEGORIES);

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
    if (!selectedService?.testAction) return;
    
    setIsTesting(true);
    setTestResult(null);

    try {
      await new Promise(resolve => setTimeout(resolve, 1500));
      setTestResult({
        success: true,
        message: selectedService.testAction.successMessage
      });
    } catch (error) {
      setTestResult({
        success: false,
        message: selectedService.testAction?.errorMessage || 'Connection failed'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = () => {
    console.log('Saving configuration:', configData);
    setSelectedService(null);
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

  return (
    <div className="flex h-full bg-gray-50">
      {/* Category Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Integrations Hub</h2>
          <p className="text-sm text-gray-600 mt-1">Connect & Configure Services</p>
        </div>
        
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

                <p className="text-sm text-gray-600 mb-3">{service.description}</p>

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

      {/* Service Detail Drawer */}
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
