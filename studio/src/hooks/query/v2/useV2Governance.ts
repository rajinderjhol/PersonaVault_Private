import { useQuery } from '@tanstack/react-query';
import { v2ApiClient } from '../../../api/v2Client';
import { useEnvironmentStore } from '../../../store/environmentStore';

export interface AuditLog {
  id: string;
  action: string;
  user: string;
  resource: string;
  details: Record<string, any>;
  status: 'success' | 'failure' | 'pending';
  timestamp: string;
  ip?: string;
  userAgent?: string;
}

export interface ComplianceStatus {
  standard: string;
  status: 'compliant' | 'non-compliant' | 'partial' | 'unknown';
  lastChecked: string;
  details: string;
  recommendations: string[];
}

export interface PolicyVerification {
  policyId: string;
  name: string;
  status: 'active' | 'inactive' | 'draft';
  hitRate: number;
  confidence: number;
  lastUsed: string;
  violations: number;
}

export const useV2AuditLogs = (params?: { limit?: number; offset?: number }) => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'governance', 'audit', currentEnvId, params],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<AuditLog[]>(
        `/environments/${currentEnvId}/governance/audit`,
        { params }
      );
    },
    enabled: !!currentEnvId,
    staleTime: 30000,
    refetchInterval: 30000,
  });
};

export const useV2ComplianceStatus = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'governance', 'compliance', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<ComplianceStatus[]>(
        `/environments/${currentEnvId}/governance/compliance`
      );
    },
    enabled: !!currentEnvId,
    staleTime: 60000,
    refetchInterval: 120000, // Every 2 minutes
  });
};

export const useV2PolicyVerification = () => {
  const { currentEnvId } = useEnvironmentStore();

  return useQuery({
    queryKey: ['v2', 'governance', 'policies', currentEnvId],
    queryFn: async () => {
      if (!currentEnvId) throw new Error('No environment selected');
      return v2ApiClient.get<PolicyVerification[]>(
        `/environments/${currentEnvId}/governance/policies`
      );
    },
    enabled: !!currentEnvId,
    staleTime: 60000,
  });
};
