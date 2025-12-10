import { useState } from 'react';
import axios from 'axios';
import { API } from '../App';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    try {
      const response = await axios.post(`${API}/search`, {
        query: query,
        limit: 10
      });
      setResults(response.data.results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="search-container" data-testid="search-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Semantic Search</h1>
        <p className="dashboard-subtitle">Find similar tenders using AI-powered search</p>
      </div>

      <div className="search-box">
        <form onSubmit={handleSearch}>
          <div className="search-input-wrapper">
            <input
              type="text"
              className="search-input"
              placeholder="Describe what you're looking for... (e.g., cloud infrastructure, healthcare analytics)"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              data-testid="search-input"
            />
            <button 
              type="submit" 
              className="search-button" 
              disabled={loading || !query.trim()}
              data-testid="search-button"
            >
              {loading ? 'Searching...' : 'Search'}
            </button>
          </div>
        </form>
      </div>

      {loading && (
        <div className="loading" data-testid="search-loading">
          <div className="spinner"></div>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="empty-state" data-testid="no-results">
          <div className="empty-icon">🔍</div>
          <div className="empty-text">No results found. Try a different search query.</div>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="results-grid">
          {results.map((result, index) => (
            <div key={result.id} className="result-card" data-testid={`search-result-${index}`}>
              <div className="result-header">
                <div>
                  <h3 className="result-title">{result.title}</h3>
                  <div className="result-meta">
                    <span>📍 {result.location}</span>
                    <span>🏢 {result.organization}</span>
                    <span>📂 {result.category}</span>
                  </div>
                </div>
                <div className="similarity-badge">
                  {Math.round(result.similarity * 100)}% match
                </div>
              </div>
              <p className="result-description">{result.description}</p>
              <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                <span style={{ fontWeight: '600', color: '#667eea' }}>
                  {result.currency} {result.value.toLocaleString()}
                </span>
                <span style={{ color: '#718096' }}>ID: {result.tender_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default SearchPage;