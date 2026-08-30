import React, { useState, useCallback } from 'react';
import { TimeFilter } from '../components/dashboard/TimeFilter';
import { temporalService } from '../services/temporalService';
import styles from './Search.module.css';

export const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [temporalContext, setTemporalContext] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const response = await temporalService.search({ query, ...temporalContext });
      setResults(response.data.items);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  }, [query, temporalContext]);

  const handleTimeFilterChange = (start: string, end: string, range: string) => {
    setTemporalContext({ startDate: start, endDate: end, timeRange: range });
    if (query) handleSearch(); // Auto-search on filter change
  };

  return (
    <div className={styles.searchPage}>
      <div className={styles.searchHeader}>
        <h2>Search Decisions</h2>
        <TimeFilter onFilterChange={handleTimeFilterChange} initialRange="30d" />
      </div>
      <div className={styles.searchBar}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by keyword or phrase..."
          className={styles.searchInput}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button onClick={handleSearch} className={styles.searchButton}>Search</button>
      </div>
      {/* Result rendering logic would go here */}
      {loading && <div>Searching...</div>}
    </div>
  );
};
