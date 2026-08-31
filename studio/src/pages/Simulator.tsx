import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { simulationApi } from '../services/simulationService';
import styles from './Simulator.module.css';

export const Simulator: React.FC = () => {
  const [domain, setDomain] = useState('security');
  const [multiplier, setMultiplier] = useState(1.0);

  const mutation = useMutation({
    mutationFn: () => simulationApi.runSimulation(
      domain,
      { confidence_multiplier: multiplier },
      '2026-01-01T00:00:00Z',
      '2026-08-31T23:59:59Z'
    )
  });

  const runSimulation = () => {
    mutation.mutate();
  };

  return (
    <div className={styles.container}>
      <h1>Policy Impact Simulator</h1>
      <div className={styles.controls}>
        <input value={domain} onChange={(e) => setDomain(e.target.value)} placeholder="Domain" />
        <input type="number" value={multiplier} onChange={(e) => setMultiplier(parseFloat(e.target.value))} />
        <button onClick={runSimulation} disabled={mutation.isPending}>
          {mutation.isPending ? 'Simulating...' : 'Run Simulation'}
        </button>
        </div>

        {mutation.data && mutation.data.metrics && (
          <div className={styles.results}>
            <h2>Results</h2>
            <p>Impact: {(mutation.data.metrics.impact * 100).toFixed(2)}%</p>
            <div className={styles.chart}>
               <div className={styles.bar} style={{ height: `${mutation.data.metrics.avg_original_confidence * 100}%` }}>Original</div>
               <div className={styles.bar} style={{ height: `${mutation.data.metrics.avg_simulated_confidence * 100}%` }}>Simulated</div>
            </div>
          </div>
        )}

    </div>
  );
};
