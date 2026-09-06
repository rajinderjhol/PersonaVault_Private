export interface VerdictConfig {
  label: string;
  icon: string;
  color: string;
  bgColor: string;
  borderColor: string;
}

export const VERDICT_CONFIG: Record<string, VerdictConfig> = {
  'APPROVED': {
    label: 'Approved',
    icon: '✅',
    color: '#155724',
    bgColor: '#d4edda',
    borderColor: '#28a745',
  },
  'CONTAINED': {
    label: 'Contained',
    icon: '🛑',
    color: '#856404',
    bgColor: '#fff3cd',
    borderColor: '#ffc107',
  },
  'ESCALATED': {
    label: 'Escalated',
    icon: '🔍',
    color: '#0c5460',
    bgColor: '#d1ecf1',
    borderColor: '#17a2b8',
  },
  'REFUSED': {
    label: 'Refused',
    icon: '❌',
    color: '#721c24',
    bgColor: '#f8d7da',
    borderColor: '#dc3545',
  },
};
