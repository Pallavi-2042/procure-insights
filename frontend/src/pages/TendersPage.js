import { useState, useEffect } from 'react';
import axios from 'axios';
import { API } from '../App';

const TendersPage = () => {
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTenders();
  }, []);

  const fetchTenders = async () => {
    try {
      const response = await axios.get(`${API}/tenders?limit=50`);
      setTenders(response.data);
    } catch (error) {
      console.error('Error fetching tenders:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading" data-testid="tenders-loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="tenders-container" data-testid="tenders-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">All Tenders</h1>
        <p className="dashboard-subtitle">Browse all procurement opportunities</p>
      </div>

      {tenders.length === 0 ? (
        <div className="empty-state" data-testid="no-tenders">
          <div className="empty-icon">📋</div>
          <div className="empty-text">No tenders available. Upload data to get started.</div>
        </div>
      ) : (
        <div className="tenders-grid">
          {tenders.map((tender, index) => (
            <div key={tender.id} className="tender-card" data-testid={`tender-card-${index}`}>
              <h3 className="tender-title">{tender.title}</h3>
              <div className="tender-meta">
                <div>🏢 {tender.organization}</div>
                <div>📂 {tender.category}</div>
                <div>📍 {tender.location}</div>
                <div>📅 Deadline: {tender.deadline || 'Not specified'}</div>
              </div>
              <div className="tender-value">
                {tender.currency} {tender.value.toLocaleString()}
              </div>
              <p style={{ color: '#718096', fontSize: '0.875rem', lineHeight: '1.5' }}>
                {tender.description.substring(0, 150)}...
              </p>
              <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: '#a0aec0' }}>
                ID: {tender.tender_id}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TendersPage;