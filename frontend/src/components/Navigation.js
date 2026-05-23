import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { checkBackendHealth } from '../api';

const Navigation = () => {
    const location = useLocation();
    const [backendStatus, setBackendStatus] = useState('checking');

    useEffect(() => {
        const checkHealth = async () => {
            const isHealthy = await checkBackendHealth();
            setBackendStatus(isHealthy ? 'online' : 'offline');
        };
        
        checkHealth();
        const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
        return () => clearInterval(interval);
    }, []);

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="navigation">
            <div className="nav-brand">
                <Link to="/" className="brand-link">
                    <h1>🛡️ Parikshak</h1>
                    <span className="subtitle">Autonomous Lifecycle System</span>
                </Link>
            </div>

            <div className="nav-links">
                <Link 
                    to="/" 
                    className={`nav-link ${isActive('/') ? 'active' : ''}`}
                >
                    Submit Task
                </Link>
                <Link 
                    to="/history" 
                    className={`nav-link ${isActive('/history') ? 'active' : ''}`}
                >
                    Task History
                </Link>
            </div>

            <div className="nav-status">
                <div className={`status-indicator ${backendStatus}`}>
                    <span className="status-dot"></span>
                    <span className="status-text">
                        {backendStatus === 'online' ? 'Online' : 
                         backendStatus === 'offline' ? 'Offline' : 'Checking...'}
                    </span>
                </div>
            </div>
        </nav>
    );
};

export default Navigation;