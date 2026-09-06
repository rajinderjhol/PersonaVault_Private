import React from 'react';
import styles from './ModelBOM.module.css';

interface ModelBOMProps {
  models: any[];
  activeModel: string;
}

export const ModelBOM: React.FC<ModelBOMProps> = ({ models, activeModel }) => {
  const providers = Array.from(new Set(models.map(m => m.provider)));
  
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>📋 AI Bill of Materials</h3>
      <div className={styles.stats}>
        <div className={styles.stat}><span>Total Providers:</span> <strong>{providers.length}</strong></div>
        <div className={styles.stat}><span>Installed Models:</span> <strong>{models.length}</strong></div>
        <div className={styles.stat}><span>Active Provider:</span> <strong>{activeModel}</strong></div>
      </div>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Model</th>
            <th>Provider</th>
          </tr>
        </thead>
        <tbody>
          {models.map(model => (
            <tr key={model.id}>
              <td>{model.name}</td>
              <td>{model.provider}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
