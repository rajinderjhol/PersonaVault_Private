import { SuggestedAction } from '../../api/chat';

interface ActionConfig {
  primaryActions: Omit<SuggestedAction, 'id' | 'action'>[];
  secondaryActions: Omit<SuggestedAction, 'id' | 'action'>[];
  tertiaryActions: Omit<SuggestedAction, 'id' | 'action'>[];
}

export const ACTION_CONFIG: Record<string, ActionConfig> = {
  'APPROVED': {
    primaryActions: [
      {
        label: 'Execute Decision',
        description: 'Proceed with approved action',
        icon: '⚡',
        primary: true,
      },
    ],
    secondaryActions: [
      {
        label: 'Add Note',
        description: 'Attach a note to the decision record',
        icon: '📝',
      },
      {
        label: 'Download Receipt',
        description: 'Download the full decision receipt',
        icon: '📥',
      },
    ],
    tertiaryActions: [
      {
        label: 'Override & Escalate',
        description: 'Override the decision and escalate',
        icon: '🔄',
      },
    ],
  },
  'CONTAINED': {
    primaryActions: [
      {
        label: 'Escalate for Review',
        description: 'Send to designated approver',
        icon: '👤',
        primary: true,
      },
    ],
    secondaryActions: [
      {
        label: 'Create Exception Report',
        description: 'Document override reason for audit',
        icon: '📝',
      },
      {
        label: 'Modify Request',
        description: 'Adjust parameters and resubmit',
        icon: '✏️',
      },
    ],
    tertiaryActions: [
      {
        label: 'Force Approve',
        description: 'Override containment (requires reason)',
        icon: '⚠️',
      },
    ],
  },
  'ESCALATED': {
    primaryActions: [
      {
        label: 'View Escalation Status',
        description: 'Check progress of escalation',
        icon: '🔍',
        primary: true,
      },
    ],
    secondaryActions: [
      {
        label: 'Add Supporting Evidence',
        description: 'Attach additional evidence for reviewers',
        icon: '📎',
      },
      {
        label: 'Notify Stakeholders',
        description: 'Send update to relevant parties',
        icon: '📢',
      },
    ],
    tertiaryActions: [
      {
        label: 'Cancel Escalation',
        description: 'Withdraw the escalation request',
        icon: '🚫',
      },
    ],
  },
  'REFUSED': {
    primaryActions: [
      {
        label: 'Appeal Decision',
        description: 'Request review of refusal',
        icon: '⚖️',
        primary: true,
      },
    ],
    secondaryActions: [
      {
        label: 'Modify Request',
        description: 'Adjust to meet policy requirements',
        icon: '✏️',
      },
      {
        label: 'View Policy Details',
        description: 'Review specific policy that caused refusal',
        icon: '📋',
      },
    ],
    tertiaryActions: [
      {
        label: 'Force Override',
        description: 'Override refusal (requires justification)',
        icon: '⚠️',
      },
    ],
  },
};
