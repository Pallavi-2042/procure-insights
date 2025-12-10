import { useState, useRef } from 'react';
import axios from 'axios';
import { API } from '../App';

const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'text/csv') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid CSV file');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile && droppedFile.type === 'text/csv') {
      setFile(droppedFile);
      setError(null);
    } else {
      setError('Please drop a valid CSV file');
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API}/ingest`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setResult(response.data);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const downloadSample = () => {
    window.location.href = '/sample_data.csv';
  };

  return (
    <div className="upload-container" data-testid="upload-container">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Upload Data</h1>
        <p className="dashboard-subtitle">Upload CSV files to ingest procurement data</p>
      </div>

      <div className="upload-box">
        <div
          className={`upload-area ${dragOver ? 'dragover' : ''}`}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          data-testid="upload-area"
        >
          <div className="upload-icon">📤</div>
          <div className="upload-text">
            {file ? file.name : 'Drag and drop your CSV file here'}
          </div>
          <div className="upload-hint">or click to browse</div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            style={{ display: 'none' }}
            data-testid="file-input"
          />
        </div>

        <button
          className="upload-button"
          onClick={handleUpload}
          disabled={!file || uploading}
          data-testid="upload-button"
        >
          {uploading ? 'Processing...' : 'Upload & Process'}
        </button>

        <div style={{ marginTop: '1rem' }}>
          <button
            onClick={downloadSample}
            style={{
              background: 'transparent',
              border: '2px solid #667eea',
              color: '#667eea',
              padding: '0.75rem 1.5rem',
              borderRadius: '8px',
              fontWeight: '600',
              cursor: 'pointer',
            }}
            data-testid="download-sample-btn"
          >
            Download Sample CSV
          </button>
        </div>

        {result && (
          <div className="success-message" data-testid="upload-success">
            ✓ Success! {result.records_ingested} records ingested, {result.records_cleaned} cleaned.
          </div>
        )}

        {error && (
          <div className="error-message" data-testid="upload-error">
            ✗ {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default UploadPage;