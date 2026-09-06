import React, { useState } from 'react';
import { useV2AuditLogs, useV2ComplianceStatus, useV2PolicyVerification } from '../hooks/query/v2/useV2Governance';
import styles from './Governance.module.css';

export const Governance: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'audit' | 'compliance' | 'policies'>('audit');
  const { data: auditLogs, isLoading: isLoadingAudit } = useV2AuditLogs({ limit: 50 });
  const { data: complianceStatus, isLoading: isLoadingCompliance } = useV2ComplianceStatus();
  const { data: policies, isLoading: isLoadingPolicies } = useV2PolicyVerification();

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🔒 Governance & Audit</h1>
        <p>Sovereign control, compliance monitoring, and policy verification</p>
      </div>

      {/* Tab Navigation */}
      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${activeTab === 'audit' ? styles.active : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          📋 Audit Logs
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'compliance' ? styles.active : ''}`}
          onClick={() => setActiveTab('compliance')}
        >
          ✅ Compliance Status
        </button>
        <button
          className={`${styles.tab} ${activeTab === 'policies' ? styles.active : ''}`}
          onClick={() => setActiveTab('policies')}
        >
          📜 Policy Verification
        </button>
      </div>

      {/* Audit Logs Tab */}
      {activeTab === 'audit' && (
        <div className={styles.tabContent}>
          <h2>📋 Audit Logs</h2>
          {isLoadingAudit ? (
            <div className={styles.loading}>Loading audit logs...</div>
          ) : (
            <div className={styles.auditTable}>
              <table>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>User</th>
                    <th>Action</th>
                    <th>Resource</th>
                    <th>Status</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs?.length === 0 ? (
                    <tr>
                      <td colSpan={6} className={styles.emptyState}>
                        <span>🔍</span>
                        <p>No audit logs available</p>
                        <p className={styles.emptySubtext}>Actions will appear here as they occur</p>
                      </td>
                    </tr>
                  ) : (
                    auditLogs?.map((log) => (
                      <tr key={log.id} className={styles.auditRow}>
                        <td>{new Date(log.timestamp).toLocaleString()}</td>
                        <td>{log.user}</td>
                        <td>
                          <span className={styles.actionBadge}>{log.action}</span>
                        </td>
                        <td>{log.resource}</td>
                        <td>
                          <span className={`${styles.statusBadge} ${styles[log.status]}`}>
                            {log.status}
                          </span>
                        </td>
                        <td>
                          <button className={styles.detailButton}>View</button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Compliance Status Tab */}
      {activeTab === 'compliance' && (
        <div className={styles.tabContent}>
          <h2>✅ Compliance Status</h2>
          {isLoadingCompliance ? (
            <div className={styles.loading}>Loading compliance status...</div>
          ) : (
            <div className={styles.complianceGrid}>
              {complianceStatus?.length === 0 ? (
                <div className={styles.emptyState}>
                  <span>✅</span>
                  <p>No compliance standards configured</p>
                  <p className={styles.emptySubtext}>Standards will appear here when configured</p>
                </div>
              ) : (
                complianceStatus?.map((standard) => (
                  <div key={standard.standard} className={styles.complianceCard}>
                    <div className={styles.complianceHeader}>
                      <span className={styles.complianceName}>{standard.standard}</span>
                      <span className={`${styles.complianceBadge} ${styles[standard.status]}`}>
                        {standard.status}
                      </span>
                    </div>
                    <div className={styles.complianceDetails}>
                      <p>{standard.details}</p>
                      <div className={styles.complianceMeta}>
                        <span>Last Checked: {new Date(standard.lastChecked).toLocaleString()}</span>
                      </div>
                      {standard.recommendations && standard.recommendations.length > 0 && (
                        <div className={styles.recommendations}>
                          <strong>Recommendations:</strong>
                          <ul>
                            {standard.recommendations.map((rec, index) => (
                              <li key={index}>{rec}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Policy Verification Tab */}
      {activeTab === 'policies' && (
        <div className={styles.tabContent}>
          <h2>📜 Policy Verification</h2>
          {isLoadingPolicies ? (
            <div className={styles.loading}>Loading policies...</div>
          ) : (
            <div className={styles.policyGrid}>
              {policies?.length === 0 ? (
                <div className={styles.emptyState}>
                  <span>📜</span>
                  <p>No policies available</p>
                  <p className={styles.emptySubtext}>Policies will appear here when created</p>
                </div>
              ) : (
                policies?.map((policy) => (
                  <div key={policy.policyId} className={styles.policyCard}>
                    <div className={styles.policyHeader}>
                      <span className={styles.policyName}>{policy.name}</span>
                      <span className={`${styles.statusBadge} ${styles[policy.status]}`}>
                        {policy.status}
                      </span>
                    </div>
                    <div className={styles.policyMetrics}>
                      <div className={styles.policyMetric}>
                        <span>Hit Rate</span>
                        <span>{policy.hitRate}%</span>
                      </div>
                      <div className={styles.policyMetric}>
                        <span>Confidence</span>
                        <span>{policy.confidence}%</span>
                      </div>
                      <div className={styles.policyMetric}>
                        <span>Violations</span>
                        <span>{policy.violations}</span>
                      </div>
                    </div>
                    <div className={styles.policyMeta}>
                      <span>Last Used: {new Date(policy.lastUsed).toLocaleString()}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
