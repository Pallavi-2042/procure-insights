import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';

const Dashboard = () => {
  const [health, setHealth] = useState(null);
  const [qualityLogs, setQualityLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [healthRes, qualityRes] = await Promise.all([
        axios.get(`${API}/pipeline-health`),
        axios.get(`${API}/data-quality`)
      ]);
      setHealth(healthRes.data);
      setQualityLogs(qualityRes.data.logs);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerValidation = async () => {
    try {
      await axios.post(`${API}/validate`);
      fetchData();
    } catch (error) {
      console.error('Error triggering validation:', error);
    }
  };

  if (loading) {
    return (
      <div className="loading" data-testid="dashboard-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="dashboard-container" data-testid="dashboard-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title" data-testid="dashboard-title">Data Quality & Pipeline Intelligence</h1>
        <p className="dashboard-subtitle">Real-time monitoring of procurement data pipeline</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card" data-testid="stat-total-records">
          <div className="stat-label">Total Records</div>
          <div className="stat-value">{health?.total_records || 0}</div>
          <div className="stat-trend">Raw ingested data</div>
        </div>
        <div className="stat-card" data-testid="stat-clean-records">
          <div className="stat-label">Clean Records</div>
          <div className="stat-value">{health?.clean_records || 0}</div>
          <div className="stat-trend">Processed & normalized</div>
        </div>
        <div className="stat-card" data-testid="stat-quality-score">
          <div className="stat-label">Quality Score</div>
          <div className="stat-value">{health?.quality_score || 0}%</div>
          <div className="stat-trend">
            {health?.status === 'healthy' ? '✓ Healthy' : '⚠ Needs attention'}
          </div>
        </div>
        <div className="stat-card" data-testid="stat-pipeline-status">
          <div className="stat-label">Pipeline Status</div>
          <div className="stat-value" style={{ fontSize: '1.5rem', textTransform: 'capitalize' }}>
            {health?.status || 'Unknown'}
          </div>
          <div className="stat-trend">
            {health?.last_ingestion ? new Date(health.last_ingestion).toLocaleString() : 'No ingestion yet'}
          </div>
        </div>
      </div>

      <div className="quality-section">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 className="section-title">Data Quality Checks</h2>
          <button 
            onClick={triggerValidation} 
            className="search-button"
            data-testid="trigger-validation-btn"
          >
            Run Validation
          </button>
        </div>
        
        {qualityLogs.length === 0 ? (
          <div className="empty-state" data-testid="no-quality-logs">
            <div className="empty-icon">✓</div>
            <div className="empty-text">No quality issues detected</div>
          </div>
        ) : (
          <div className="quality-logs">
            {qualityLogs.map((log, index) => (
              <div key={index} className={`log-item ${log.severity}`} data-testid={`quality-log-${index}`}>
                <div className="log-header">
                  <span className="log-type">{log.check_type.replace('_', ' ')}</span>
                  <span className={`log-severity severity-${log.severity}`}>{log.severity}</span>
                </div>
                <div className="log-message">{log.message}</div>
                <div className="log-details">
                  {JSON.stringify(log.details)} | Records affected: {log.record_count}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;