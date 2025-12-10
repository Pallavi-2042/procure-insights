import { Link, useLocation } from 'react-router-dom';
import './Navigation.css';

const Navigation = () => {
  const location = useLocation();

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="navigation" data-testid="main-navigation">
      <div className="nav-container">
        <Link to="/" className="nav-logo" data-testid="nav-logo">
          <span className="logo-icon">📊</span>
          <span className="logo-text">Procurement Intelligence</span>
        </Link>
        <div className="nav-links">
          <Link 
            to="/" 
            className={`nav-link ${isActive('/') ? 'active' : ''}`}
            data-testid="nav-dashboard"
          >
            Dashboard
          </Link>
          <Link 
            to="/search" 
            className={`nav-link ${isActive('/search') ? 'active' : ''}`}
            data-testid="nav-search"
          >
            Search
          </Link>
          <Link 
            to="/tenders" 
            className={`nav-link ${isActive('/tenders') ? 'active' : ''}`}
            data-testid="nav-tenders"
          >
            Tenders
          </Link>
          <Link 
            to="/upload" 
            className={`nav-link ${isActive('/upload') ? 'active' : ''}`}
            data-testid="nav-upload"
          >
            Upload
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;