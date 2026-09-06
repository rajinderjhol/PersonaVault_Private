import React from 'react';
import styles from './ProviderTable.module.css';

interface Provider {
  id: string;
  name: string;
  type: string;
  model: string;
  status: string;
}

interface ProviderTableProps {
  providers: Provider[];
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
}

export const ProviderTable: React.FC<ProviderTableProps> = ({ providers, onEdit, onDelete }) => {
  return (
    <div className={styles.container}>
      <h3 className={styles.title}>🔌 AI Providers</h3>
      <table className={styles.table}>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Type</th>
            <th>Model</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {providers?.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>{p.type}</td>
              <td>{p.model}</td>
              <td><span className={styles.statusActive}>✅ {p.status}</span></td>
              <td>
                <button className={styles.actionBtn} onClick={() => onEdit(p.id)}>✏️ Edit</button>
                <button className={styles.deleteBtn} onClick={() => onDelete(p.id)}>🗑️ Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <button className={styles.addBtn}>+ Add Provider</button>
    </div>
  );
};
