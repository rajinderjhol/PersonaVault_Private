/**
 * React Query hooks for Intelligence Source Control
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import intelligenceSourceService from '../../services/intelligenceSourceService';
import type {
  IntelligenceSource,
  RegisterSourceRequest,
  UpdateSourceRequest,
  LiveFeedEvent,
  TrustLevelConfig,
  SourceStats,
} from '../../types/intelligenceSource';

// ============================================================
// Query Keys
// ============================================================

export const intelligenceSourceKeys = {
  all: ['intelligence-sources'] as const,
  lists: () => [...intelligenceSourceKeys.all, 'list'] as const,
  list: (filters: any) => [...intelligenceSourceKeys.lists(), filters] as const,
  details: () => [...intelligenceSourceKeys.all, 'detail'] as const,
  detail: (id: string) => [...intelligenceSourceKeys.details(), id] as const,
  liveFeed: () => [...intelligenceSourceKeys.all, 'live-feed'] as const,
  trustLevels: () => [...intelligenceSourceKeys.all, 'trust-levels'] as const,
  stats: () => [...intelligenceSourceKeys.all, 'stats'] as const,
};

// ============================================================
// Queries
// ============================================================

/**
 * Hook to fetch all intelligence sources
 */
export function useIntelligenceSources(params?: {
  status?: string;
  type?: string;
  min_trust?: number;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: intelligenceSourceKeys.list(params || {}),
    queryFn: () => intelligenceSourceService.listSources(params),
    staleTime: 30 * 1000, // 30 seconds
    refetchInterval: 10 * 1000, // Auto-refresh every 10 seconds
  });
}

/**
 * Hook to fetch a single intelligence source
 */
export function useIntelligenceSource(sourceId: string | null) {
  return useQuery({
    queryKey: intelligenceSourceKeys.detail(sourceId || ''),
    queryFn: () => intelligenceSourceService.getSource(sourceId!),
    enabled: !!sourceId,
    staleTime: 30 * 1000,
  });
}

/**
 * Hook to fetch live feed events
 */
export function useLiveFeed(limit: number = 20) {
  return useQuery({
    queryKey: intelligenceSourceKeys.liveFeed(),
    queryFn: () => intelligenceSourceService.getLiveFeed(limit),
    staleTime: 5 * 1000,
    refetchInterval: 5 * 1000,
  });
}

/**
 * Hook to fetch trust levels configuration
 */
export function useTrustLevels() {
  return useQuery({
    queryKey: intelligenceSourceKeys.trustLevels(),
    queryFn: () => intelligenceSourceService.getTrustLevels(),
    staleTime: 60 * 60 * 1000, // 1 hour
  });
}

/**
 * Hook to fetch aggregated stats
 */
export function useSourceStats() {
  return useQuery({
    queryKey: intelligenceSourceKeys.stats(),
    queryFn: () => intelligenceSourceService.getStats(),
    staleTime: 30 * 1000,
    refetchInterval: 15 * 1000,
  });
}

// ============================================================
// Mutations
// ============================================================

/**
 * Hook to register a new intelligence source
 */
export function useRegisterSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: RegisterSourceRequest) =>
      intelligenceSourceService.registerSource(request),
    onSuccess: () => {
      // Invalidate and refetch queries
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.stats() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.liveFeed() });
    },
  });
}

/**
 * Hook to update an intelligence source
 */
export function useUpdateSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sourceId, request }: { sourceId: string; request: UpdateSourceRequest }) =>
      intelligenceSourceService.updateSource(sourceId, request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.stats() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.liveFeed() });
    },
  });
}

/**
 * Hook to delete an intelligence source
 */
export function useDeleteSource() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceId: string) =>
      intelligenceSourceService.deleteSource(sourceId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.stats() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.liveFeed() });
    },
  });
}

/**
 * Hook to recompute trust score
 */
export function useRecomputeTrust() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (sourceId: string) =>
      intelligenceSourceService.recomputeTrust(sourceId),
    onSuccess: (data, sourceId) => {
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.detail(sourceId) });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.stats() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.liveFeed() });
    },
  });
}

/**
 * Hook to simulate data ingestion
 */
export function useIngestData() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ sourceId, dataType, sizeBytes }: { sourceId: string; dataType: string; sizeBytes: number }) =>
      intelligenceSourceService.ingestData(sourceId, dataType, sizeBytes),
    onSuccess: (_, { sourceId }) => {
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.detail(sourceId) });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.lists() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.stats() });
      queryClient.invalidateQueries({ queryKey: intelligenceSourceKeys.liveFeed() });
    },
  });
}
