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

export default apiClient;
