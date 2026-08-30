import React, { useState, useCallback, useEffect } from 'react';
import { TimeFilter } from '../components/dashboard/TimeFilter';
import { temporalService, SearchResult } from '../services/temporalService';
import styles from './Search.module.css';

export const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [totalResults, setTotalResults] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState('30d');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [temporalMetadata, setTemporalMetadata] = useState<any>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const performSearch = useCallback(async () => {
    if (!query.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError(null);
    setHasSearched(true);

    try {
      const response = await temporalService.search({
        query: query.trim(),
        time_range: timeRange,
        start_date: startDate,
        end_date: endDate
      });
      
      setResults(response.items);
      setTotalResults(response.total);
      setTemporalMetadata(response.temporal_metadata);
    } catch (err: any) {
      console.error('Search failed:', err);
      setError(err.message || 'Search failed. Please try again.');
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query, timeRange, startDate, endDate]);

  const handleTimeFilterChange = (start: string, end: string, range: string) => {
    setTimeRange(range);
    setStartDate(start);
    setEndDate(end);
  };

  useEffect(() => {
    if (query.trim() && hasSearched) {
      performSearch();
    }
  }, [timeRange, startDate, endDate, performSearch, query, hasSearched]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      performSearch();
    }
  };

  const clearSearch = () => {
    setQuery('');
    setResults([]);
    setError(null);
    setTemporalMetadata(null);
    setHasSearched(false);
  };

  return (
    <div className={styles.searchPage}>
      <div className={styles.searchHeader}>
        <h2>🔍 Search Decisions</h2>
        <TimeFilter onFilterChange={handleTimeFilterChange} initialRange="30d" />
      </div>

      <div className={styles.searchBar}>
        <div className={styles.searchInputWrapper}>
          <span className={styles.searchIcon}>🔍</span>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Search decisions (e.g., 'security incidents last week')"
            className={styles.searchInput}
          />
          {query && (
            <button className={styles.clearButton} onClick={clearSearch}>
              ✕
            </button>
          )}
        </div>
        <button 
          onClick={performSearch} 
          className={styles.searchButton}
          disabled={loading}
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && (
        <div className={styles.errorMessage}>
          ⚠️ {error}
        </div>
      )}

      {temporalMetadata && results.length > 0 && (
        <div className={styles.temporalContext}>
          <div className={styles.contextHeader}>
            <span className={styles.contextLabel}>🕐 Temporal Context</span>
            <span className={`${styles.contextBadge} ${temporalMetadata.scoring_enabled ? styles.active : ''}`}>
              {temporalMetadata.scoring_enabled ? '✨ Temporal Scoring Active' : 'No Temporal Filter'}
            </span>
          </div>
          {temporalMetadata.context && (
            <div className={styles.contextDetails}>
              <span className={styles.contextRange}>
                {temporalMetadata.context.start_date && temporalMetadata.context.end_date ? (
                  <>
                    {new Date(temporalMetadata.context.start_date).toLocaleDateString()} → 
                    {new Date(temporalMetadata.context.end_date).toLocaleDateString()}
                  </>
                ) : 'All time'}
              </span>
              {temporalMetadata.context.original_expression && (
                <span className={styles.contextOriginal}>
                  Query: "{temporalMetadata.context.original_expression}"
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className={styles.loadingState}>
          <div className={styles.loadingSpinner}></div>
          <span>Searching for temporal patterns...</span>
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <div className={styles.resultsSummary}>
            <span>Found {totalResults} results</span>
            {temporalMetadata?.scoring_enabled && (
              <span className={styles.scoringInfo}>
                Sorted by relevance (confidence × temporal relevance)
              </span>
            )}
          </div>
          <div className={styles.resultsList}>
            {results.map((result) => (
              <div key={result.id} className={styles.resultItem}>
                <div className={styles.resultHeader}>
                  <h4 className={styles.resultTitle}>{result.title}</h4>
                  <div className={styles.resultScores}>
                    <span 
                      className={styles.confidenceScore}
                      style={{ 
                        color: result.confidence_score > 0.7 ? '#22c55e' : 
                               result.confidence_score > 0.4 ? '#eab308' : '#ef4444'
                      }}
                    >
                      {Math.round(result.confidence_score * 100)}% confidence
                    </span>
                    {result.temporal_relevance && (
                      <span 
                        className={styles.temporalScore}
                        style={{ 
                          backgroundColor: result.temporal_relevance.score > 0.7 ? '#22c55e' :
                                         result.temporal_relevance.score > 0.4 ? '#eab308' : '#ef4444',
                          color: 'white'
                        }}
                      >
                        {result.temporal_relevance.score > 0.7 ? '🔥' : 
                         result.temporal_relevance.score > 0.4 ? '📈' : '⏳'} 
                        {Math.round(result.temporal_relevance.score * 100)}% relevant
                      </span>
                    )}
                  </div>
                </div>
                <p className={styles.resultContent}>{result.content}</p>
                {result.temporal_relevance?.factors && (
                  <div className={styles.temporalFactors}>
                    <span className={styles.factorsLabel}>Why relevant:</span>
                    {result.temporal_relevance.factors.map((factor, index) => (
                      <span key={index} className={styles.factorTag}>
                        {factor}
                      </span>
                    ))}
                  </div>
                )}
                <div className={styles.resultFooter}>
                  <span className={styles.resultDomain}>📁 {result.domain}</span>
                  <span className={styles.resultDate}>
                    🗓️ {new Date(result.created_at).toLocaleDateString()}
                  </span>
                  {result.temporal_relevance && (
                    <span className={styles.temporalInfo}>
                      🕐 {result.temporal_relevance.context || 'Time-relevant'}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {!loading && query && results.length === 0 && !error && hasSearched && (
        <div className={styles.noResults}>
          <div className={styles.noResultsIcon}>🔍</div>
          <p>No results found for "{query}"</p>
          <p className={styles.noResultsHint}>
            Try adjusting your search terms or time range
          </p>
        </div>
      )}

      {!loading && !query && !hasSearched && (
        <div className={styles.searchPrompt}>
          <div className={styles.promptIcon}>🔍</div>
          <p>Enter a search query to find decisions</p>
          <p className={styles.promptHint}>
            Try: "security incidents last week" or "compliance reviews this month"
          </p>
        </div>
      )}
    </div>
  );
};
