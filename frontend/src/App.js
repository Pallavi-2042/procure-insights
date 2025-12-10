import { useState, useEffect } from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import Dashboard from './pages/Dashboard';
import SearchPage from './pages/SearchPage';
import TendersPage from './pages/TendersPage';
import UploadPage from './pages/UploadPage';
import Navigation from './components/Navigation';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Navigation />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/tenders" element={<TendersPage />} />
          <Route path="/upload" element={<UploadPage />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;