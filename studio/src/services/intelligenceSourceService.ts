/**
 * Intelligence Source Service - V2 API Client
 */

import { v2ApiClient as apiClient } from '../api/v2Client';
import type {
  IntelligenceSource,
  RegisterSourceRequest,
  UpdateSourceRequest,
  LiveFeedEvent,
  TrustLevelConfig,
  SourceStats,
} from '../types/intelligenceSource';

const BASE_URL = '/intelligence-sources';

export const intelligenceSourceService = {
  /**
   * List all intelligence sources for the current user
   */
  async listSources(params?: {
    status?: string;
    type?: string;
    min_trust?: number;
    limit?: number;
    offset?: number;
  }): Promise<IntelligenceSource[]> {
    const response = await apiClient.get(BASE_URL, { params });
    return response.data;
  },

  /**
   * Get a single intelligence source by ID
   */
  async getSource(sourceId: string): Promise<IntelligenceSource> {
    const response = await apiClient.get(`${BASE_URL}/${sourceId}`);
    return response.data;
  },

  /**
   * Register a new intelligence source
   */
  async registerSource(request: RegisterSourceRequest): Promise<IntelligenceSource> {
    const response = await apiClient.post(BASE_URL, request);
    return response.data;
  },

  /**
   * Update an existing intelligence source
   */
  async updateSource(sourceId: string, request: UpdateSourceRequest): Promise<IntelligenceSource> {
    const response = await apiClient.patch(`${BASE_URL}/${sourceId}`, request);
    return response.data;
  },

  /**
   * Delete an intelligence source
   */
  async deleteSource(sourceId: string): Promise<void> {
    await apiClient.delete(`${BASE_URL}/${sourceId}`);
  },

  /**
   * Recompute trust score for a source
   */
  async recomputeTrust(sourceId: string): Promise<{ source_id: string; old_score: number; new_score: number }> {
    const response = await apiClient.post(`${BASE_URL}/${sourceId}/recompute-trust`);
    return response.data;
  },

  /**
   * Simulate data ingestion from a source
   */
  async ingestData(sourceId: string, dataType: string, sizeBytes: number): Promise<any> {
    const response = await apiClient.post(`${BASE_URL}/${sourceId}/ingest`, null, {
      params: { data_type: dataType, size_bytes: sizeBytes },
    });
    return response.data;
  },

  /**
   * Get live feed events
   */
  async getLiveFeed(limit: number = 20): Promise<LiveFeedEvent[]> {
    const response = await apiClient.get(`${BASE_URL}/live-feed`, {
      params: { limit },
    });
    return response.data;
  },

  /**
   * Get available trust levels configuration
   */
  async getTrustLevels(): Promise<Record<string, TrustLevelConfig>> {
    const response = await apiClient.get(`${BASE_URL}/trust-levels`);
    return response.data;
  },

  /**
   * Get aggregated statistics
   */
  async getStats(): Promise<SourceStats> {
    const response = await apiClient.get(`${BASE_URL}/stats`);
    return response.data;
  },
};

export default intelligenceSourceService;
