import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

// Global fetch interceptor to automatically authenticate with the backend
const originalFetch = window.fetch;
window.fetch = async function (resource, options = {}) {
    const url = typeof resource === 'string' ? resource : (resource.url || '');
    
    // Bypass health checks and token endpoint
    if (url.includes('/health') || url.includes('/auth/token')) {
        return originalFetch(resource, options);
    }
    
    if (url.includes('/api/v1/')) {
        options.headers = options.headers || {};
        let token = localStorage.getItem('parikshak_token');
        
        if (!token) {
            try {
                const baseUrlMatch = url.match(/^(https?:\/\/[^\/]+)/);
                const backendBase = baseUrlMatch ? baseUrlMatch[1] : '';
                
                const loginRes = await originalFetch(`${backendBase}/api/v1/production/auth/token`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        username: 'operator',
                        password: 'OperatorPass123!'
                    })
                });
                
                if (loginRes.ok) {
                    const authData = await loginRes.json();
                    token = authData.access_token;
                    localStorage.setItem('parikshak_token', token);
                }
            } catch (err) {
                console.error('Global auto login failed:', err);
            }
        }
        
        if (token) {
            if (options.headers instanceof Headers) {
                options.headers.set('Authorization', `Bearer ${token}`);
            } else {
                options.headers['Authorization'] = `Bearer ${token}`;
            }
        }
    }
    
    let response = await originalFetch(resource, options);
    
    if (response.status === 401 && url.includes('/api/v1/') && !options._retry) {
        options._retry = true;
        localStorage.removeItem('parikshak_token');
        
        try {
            const baseUrlMatch = url.match(/^(https?:\/\/[^\/]+)/);
            const backendBase = baseUrlMatch ? baseUrlMatch[1] : '';
            
            const loginRes = await originalFetch(`${backendBase}/api/v1/production/auth/token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: 'operator',
                    password: 'OperatorPass123!'
                })
            });
            
            if (loginRes.ok) {
                const authData = await loginRes.json();
                const token = authData.access_token;
                localStorage.setItem('parikshak_token', token);
                
                if (options.headers instanceof Headers) {
                    options.headers.set('Authorization', `Bearer ${token}`);
                } else {
                    options.headers['Authorization'] = `Bearer ${token}`;
                }
                
                response = await originalFetch(resource, options);
            }
        } catch (err) {
            console.error('Global token refresh failed:', err);
        }
    }
    
    return response;
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
