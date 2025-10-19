/**
 * API client for service management with LLM wrapper
 */

import axios from 'axios';

const API_BASE = '/api/services';

export interface ServiceConnectionRequest {
  service_name: string;
  service_type: string;
  config: Record<string, any>;
}

export interface ServiceActionRequest {
  service_name: string;
  action: string;
  params?: Record<string, any>;
  use_llm?: boolean;
}

export interface ServiceStatus {
  service: string;
  status: 'connected' | 'disconnected' | 'error' | 'testing';
  last_error: string | null;
  last_connected: string | null;
}

export interface ServiceTestResult {
  success: boolean;
  error?: string;
  [key: string]: any;
}

/**
 * Connect to a service with configuration
 */
export async function connectService(request: ServiceConnectionRequest) {
  const response = await axios.post(`${API_BASE}/connect`, request);
  return response.data;
}

/**
 * Disconnect from a service
 */
export async function disconnectService(serviceName: string) {
  const response = await axios.post(`${API_BASE}/disconnect/${serviceName}`);
  return response.data;
}

/**
 * Execute a service action with optional LLM enhancement
 */
export async function executeServiceAction(request: ServiceActionRequest) {
  const response = await axios.post(`${API_BASE}/execute`, request);
  return response.data;
}

/**
 * Get status of all services
 */
export async function getAllServiceStatuses(): Promise<Record<string, ServiceStatus>> {
  const response = await axios.get(`${API_BASE}/status`);
  return response.data.services || {};
}

/**
 * Get status of a specific service
 */
export async function getServiceStatus(serviceName: string) {
  const response = await axios.get(`${API_BASE}/status/${serviceName}`);
  return response.data;
}

/**
 * List all registered services
 */
export async function listServices() {
  const response = await axios.get(`${API_BASE}/list`);
  return response.data.services || [];
}

/**
 * Test a service connection
 */
export async function testService(serviceName: string): Promise<ServiceTestResult> {
  const response = await axios.post(`${API_BASE}/test/${serviceName}`);
  return response.data;
}
