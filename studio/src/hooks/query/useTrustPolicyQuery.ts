/**
 * React Query hooks for Trust Policy Configuration
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import trustPolicyService from '../../services/trustPolicyService';
import type {
  TrustPolicy,
  TrustPolicyCreateRequest,
  TrustPolicyUpdateRequest,
} from '../../types/trustPolicy';

// ============================================================
// Query Keys
// ============================================================

export const trustPolicyKeys = {
  all: ['trust-policies'] as const,
  list: () => [...trustPolicyKeys.all, 'list'] as const,
  detail: (layer: string) => [...trustPolicyKeys.all, 'detail', layer] as const,
  defaults: () => [...trustPolicyKeys.all, 'defaults'] as const,
  simulation: () => [...trustPolicyKeys.all, 'simulation'] as const,
};

// ============================================================
// Queries
// ============================================================

/**
 * Hook to fetch all trust policies
 */
export function useTrustPolicies() {
  return useQuery({
    queryKey: trustPolicyKeys.list(),
    queryFn: () => trustPolicyService.listPolicies(),
    staleTime: 60 * 1000, // 1 minute
  });
}

/**
 * Hook to fetch a single trust policy by layer
 */
export function useTrustPolicy(layer: string | null) {
  return useQuery({
    queryKey: trustPolicyKeys.detail(layer || ''),
    queryFn: () => trustPolicyService.getPolicy(layer!),
    enabled: !!layer,
    staleTime: 60 * 1000,
  });
}

/**
 * Hook to fetch default policy recommendations
 */
export function useDefaultPolicies() {
  return useQuery({
    queryKey: trustPolicyKeys.defaults(),
    queryFn: () => trustPolicyService.getDefaultPolicies(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

// ============================================================
// Mutations
// ============================================================

/**
 * Hook to create a new trust policy
 */
export function useCreateTrustPolicy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: TrustPolicyCreateRequest) =>
      trustPolicyService.createPolicy(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trustPolicyKeys.list() });
    },
  });
}

/**
 * Hook to update a trust policy
 */
export function useUpdateTrustPolicy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ layer, request }: { layer: string; request: TrustPolicyUpdateRequest }) =>
      trustPolicyService.updatePolicy(layer, request),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: trustPolicyKeys.list() });
      queryClient.invalidateQueries({ queryKey: trustPolicyKeys.detail(data.layer) });
    },
  });
}

/**
 * Hook to delete a trust policy
 */
export function useDeleteTrustPolicy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (layer: string) =>
      trustPolicyService.deletePolicy(layer),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: trustPolicyKeys.list() });
    },
  });
}

/**
 * Hook to simulate policy impact
 */
export function useSimulatePolicyImpact() {
  return useMutation({
    mutationFn: ({
      sourceId,
      layer,
      newThreshold,
    }: {
      sourceId: string;
      layer: string;
      newThreshold: number;
    }) => trustPolicyService.simulatePolicyImpact(sourceId, layer, newThreshold),
  });
}
