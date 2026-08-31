import React, { useState } from 'react';
import { simulationApi } from '../services/simulationService';
import styles from './Simulator.module.css';

export const Simulator: React.FC = () => {
  const [domain, setDomain] = useState('security');
  const [multiplier, setMultiplier] = useState(1.0);
  const [results, setResults] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async () => {
    setLoading(true);
    try {
      const response = await simulationApi.runSimulation(
        domain,
        { confidence_multiplier: multiplier },
        '2026-01-01T00:00:00Z',
        '2026-08-31T23:59:59Z'
      );
      setResults(response);
    } catch (error) {
      console.error('Simulation error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1>Policy Impact Simulator</h1>
      <div className={styles.controls}>
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain" />
        <input type="number" value={multiplier} onChange={(e) => setMultiplier(parseFloat(e.target.value))} />
        <button onClick={runSimulation} disabled={loading}>
          {loading ? 'Simulating...' : 'Run Simulation'}
        </button>
      </div>
      
      {results && results.metrics && (
        <div className={styles.results}>
          <h2>Results</h2>
          <p>Impact: {(results.metrics.impact * 100).toFixed(2)}%</p>
          <div className={styles.chart}>
             <div className={styles.bar} style={{ height: `${results.metrics.avg_original_confidence * 100}%` }}>Original</div>
             <div className={styles.bar} style={{ height: `${results.metrics.avg_simulated_confidence * 100}%` }}>Simulated</div>
          </div>
        </div>
      )}
    </div>
  );
};
