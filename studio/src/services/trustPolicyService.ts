/**
 * Trust Policy Service - V2 API Client
 */

import { v2ApiClient as apiClient } from '../api/v2Client';
import type {
  TrustPolicy,
  TrustPolicyCreateRequest,
  TrustPolicyUpdateRequest,
  DefaultPolicyConfig,
  SimulationResult,
} from '../types/trustPolicy';

const BASE_URL = '/trust-policies';

export const trustPolicyService = {
  /**
   * List all trust policies for the current user
   */
  async listPolicies(): Promise<TrustPolicy[]> {
    const response = await apiClient.get(BASE_URL);
    return response.data;
  },

  /**
   * Get default policy recommendations
   */
  async getDefaultPolicies(): Promise<Record<string, DefaultPolicyConfig>> {
    const response = await apiClient.get(`${BASE_URL}/defaults`);
    return response.data;
  },

  /**
   * Get a specific trust policy by layer
   */
  async getPolicy(layer: string): Promise<TrustPolicy> {
    const response = await apiClient.get(`${BASE_URL}/${layer}`);
    return response.data;
  },

  /**
   * Create a new trust policy
   */
  async createPolicy(request: TrustPolicyCreateRequest): Promise<TrustPolicy> {
    const response = await apiClient.post(BASE_URL, request);
    return response.data;
  },

  /**
   * Update a trust policy
   */
  async updatePolicy(layer: string, request: TrustPolicyUpdateRequest): Promise<TrustPolicy> {
    const response = await apiClient.patch(`${BASE_URL}/${layer}`, request);
    return response.data;
  },

  /**
   * Delete a trust policy
   */
  async deletePolicy(layer: string): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${layer}`);
  },

  /**
   * Simulate the impact of a policy change on a specific source
   */
  async simulatePolicyImpact(
    sourceId: string,
    layer: string,
    newThreshold: number
  ): Promise<SimulationResult> {
    const response = await apiClient.post(`${BASE_URL}/simulate`, null, {
      params: { source_id: sourceId, layer, new_threshold: newThreshold },
    });
    return response.data;
  },
};

export default trustPolicyService;
