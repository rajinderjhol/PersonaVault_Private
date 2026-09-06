import React, { useState } from 'react';
import { useV2RunSimulation, useV2SimulationHistory } from '../hooks/query/v2/useV2Simulation';
import styles from './PolicySimulator.module.css';

interface SimulationParams {
  policyId: string;
  scenario: string;
  parameters: Record<string, any>;
}

export const PolicySimulator: React.FC = () => {
  const [params, setParams] = useState<SimulationParams>({
    policyId: '',
    scenario: '',
    parameters: {},
  });
  const { mutate: runSimulation, data: result, isLoading } = useV2RunSimulation();
  const { data: history } = useV2SimulationHistory();

  const handleRunSimulation = () => {
    if (!params.policyId || !params.scenario) {
      alert('Please select a policy and enter a scenario.');
      return;
    }
    runSimulation(params);
  };

  const renderParameterInputs = () => {
    return (
      <div className={styles.parameterGrid}>
        <div className={styles.parameterField}>
          <label>Confidence Threshold</label>
          <input
            type="range"
            min="0"
            max="100"
            value={params.parameters.confidenceThreshold || 70}
            onChange={(e) => setParams({
              ...params,
              parameters: {
                ...params.parameters,
                confidenceThreshold: parseInt(e.target.value),
              },
            })}
          />
          <span>{params.parameters.confidenceThreshold || 70}%</span>
        </div>
        <div className={styles.parameterField}>
          <label>Risk Tolerance</label>
          <select
            value={params.parameters.riskTolerance || 'medium'}
            onChange={(e) => setParams({
              ...params,
              parameters: {
                ...params.parameters,
                riskTolerance: e.target.value,
              },
            })}
          >
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
      </div>
    );
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🎯 Policy Simulator</h1>
        <p>Run "What-If" scenarios to test policy changes before deployment</p>
      </div>

      <div className={styles.configSection}>
        <h2>⚙️ Simulation Configuration</h2>
        <div className={styles.configGrid}>
          <div className={styles.configField}>
            <label>Policy ID</label>
            <input
              type="text"
              value={params.policyId}
              onChange={(e) => setParams({ ...params, policyId: e.target.value })}
              placeholder="Enter policy ID (e.g., SEC-01)"
              className={styles.input}
            />
          </div>
          <div className={styles.configField}>
            <label>Scenario</label>
            <input
              type="text"
              value={params.scenario}
              onChange={(e) => setParams({ ...params, scenario: e.target.value })}
              placeholder="Describe the scenario (e.g., 'Vendor bank details changed')"
              className={styles.input}
            />
          </div>
        </div>
        {renderParameterInputs()}
        <button
          onClick={handleRunSimulation}
          disabled={isLoading}
          className={styles.runButton}
        >
          {isLoading ? '⏳ Running Simulation...' : '🚀 Run Simulation'}
        </button>
      </div>

      {result && (
        <div className={styles.resultsSection}>
          <h2>📊 Simulation Results</h2>
          <div className={styles.resultsSummary}>
            <div className={styles.resultStatus}>
              <span className={`${styles.statusBadge} ${styles[result.status]}`}>
                {result.status.toUpperCase()}
              </span>
            </div>
            <div className={styles.resultSummary}>{result.summary}</div>
          </div>

          <div className={styles.comparisonGrid}>
            <div className={styles.comparisonCard}>
              <h3>Before</h3>
              <div className={styles.metric}>
                <span>Confidence</span>
                <span>{result.before.confidence}%</span>
              </div>
              <div className={styles.metric}>
                <span>Risk</span>
                <span>{result.before.risk}%</span>
              </div>
              <div className={styles.metric}>
                <span>Cost</span>
                <span>${result.before.cost}</span>
              </div>
              <div className={styles.metric}>
                <span>Decisions</span>
                <span>{result.before.decisions}</span>
              </div>
            </div>
            <div className={`${styles.comparisonCard} ${styles.afterCard}`}>
              <h3>After</h3>
              <div className={styles.metric}>
                <span>Confidence</span>
                <span className={result.after.confidence > result.before.confidence ? styles.positive : styles.negative}>
                  {result.after.confidence}%
                </span>
              </div>
              <div className={styles.metric}>
                <span>Risk</span>
                <span className={result.after.risk < result.before.risk ? styles.positive : styles.negative}>
                  {result.after.risk}%
                </span>
              </div>
              <div className={styles.metric}>
                <span>Cost</span>
                <span className={result.after.cost < result.before.cost ? styles.positive : styles.negative}>
                  ${result.after.cost}
                </span>
              </div>
              <div className={styles.metric}>
                <span>Decisions</span>
                <span className={result.after.decisions > result.before.decisions ? styles.positive : styles.negative}>
                  {result.after.decisions}
                </span>
              </div>
            </div>
          </div>

          {result.recommendations && result.recommendations.length > 0 && (
            <div className={styles.recommendations}>
              <h3>💡 Recommendations</h3>
              <ul>
                {result.recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {history && history.length > 0 && (
        <div className={styles.historySection}>
          <h2>📜 Simulation History</h2>
          <div className={styles.historyTable}>
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Policy</th>
                  <th>Scenario</th>
                  <th>Status</th>
                  <th>Confidence Change</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {history.map((entry) => (
                  <tr key={entry.id}>
                    <td>{new Date(entry.timestamp).toLocaleString()}</td>
                    <td>{entry.policyId || 'N/A'}</td>
                    <td>{entry.scenario || 'N/A'}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${styles[entry.status]}`}>
                        {entry.status}
                      </span>
                    </td>
                    <td>
                      {entry.before && entry.after ? (
                        <span className={entry.after.confidence > entry.before.confidence ? styles.positive : styles.negative}>
                          {entry.after.confidence - entry.before.confidence > 0 ? '+' : ''}
                          {entry.after.confidence - entry.before.confidence}%
                        </span>
                      ) : 'N/A'}
                    </td>
                    <td>
                      <button className={styles.viewButton}>View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
