import React, { useState } from 'react';
import { useV2Search } from '../hooks/query/v2/useV2Search';
import styles from './UniversalSearch.module.css';

export const UniversalSearch: React.FC = () => {
  const [query, setQuery] = useState('');
  const { mutate: search, data: results, isLoading } = useV2Search();

  const handleSearch = () => {
    if (!query.trim()) return;
    search({ query });
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>🔍 Universal Search</h1>
        <p>Semantic search across all your memories and patterns</p>
      </div>

      <div className={styles.searchBox}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search for memories, concepts, or patterns..."
          className={styles.searchInput}
        />
        <button onClick={handleSearch} disabled={isLoading} className={styles.searchButton}>
          {isLoading ? '⏳ Searching...' : 'Search'}
        </button>
      </div>

      {results && (
        <div className={styles.resultsSection}>
          <h2>Results ({results.length})</h2>
          <div className={styles.resultsList}>
            {results.length === 0 ? (
              <p className={styles.noResults}>No memories found matching your query.</p>
            ) : (
              results.map((result) => (
                <div key={result.id} className={styles.resultCard}>
                  <div className={styles.resultHeader}>
                    <span className={styles.resultScore}>Score: {result.score.toFixed(4)}</span>
                  </div>
                  <div className={styles.resultContent}>{result.content}</div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};
