import axios from 'axios';

const getBaseUrl = () => {
    let url = process.env.REACT_APP_API_BASE
        || process.env.REACT_APP_BACKEND_URL
        || 'http://localhost:8000/api/v1';
    url = url.replace(/\/+$/, '');
    if (!url.endsWith('/api/v1')) {
        url = `${url}/api/v1`;
    }
    return url;
};

const apiClient = axios.create({
    baseURL: getBaseUrl(),
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor to automatically add authorization token
apiClient.interceptors.request.use(async (config) => {
    if (config.url.includes('/auth/token')) {
        return config;
    }
    
    let token = localStorage.getItem('parikshak_token');
    if (!token) {
        try {
            const authUrl = getBaseUrl().replace('/api/v1', '/api/v1/production/auth/token');
            const loginRes = await axios.post(authUrl, {
                username: 'operator',
                password: 'OperatorPass123!'
            });
            token = loginRes.data.access_token;
            localStorage.setItem('parikshak_token', token);
        } catch (err) {
            console.error('Auto login failed:', err);
        }
    }
    
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
}, (error) => {
    return Promise.reject(error);
});

// Response interceptor to handle token expiration (401)
apiClient.interceptors.response.use((response) => response, async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        localStorage.removeItem('parikshak_token');
        try {
            const authUrl = getBaseUrl().replace('/api/v1', '/api/v1/production/auth/token');
            const loginRes = await axios.post(authUrl, {
                username: 'operator',
                password: 'OperatorPass123!'
            });
            const token = loginRes.data.access_token;
            localStorage.setItem('parikshak_token', token);
            originalRequest.headers['Authorization'] = `Bearer ${token}`;
            return axios(originalRequest);
        } catch (err) {
            console.error('Refetch token failed:', err);
        }
    }
    return Promise.reject(error);
});

export default apiClient;
