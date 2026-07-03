import axios from 'axios';

const RAW_BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;
let BACKEND_URL = RAW_BACKEND_URL.replace(/\/+$/, '');
if (BACKEND_URL.endsWith('/api/v1')) {
    BACKEND_URL = BACKEND_URL.replace(/\/api\/v1$/, '');
}
const LIFECYCLE_API = `${BACKEND_URL}/api/v1/lifecycle`;

const api = axios.create({
    baseURL: LIFECYCLE_API,
    timeout: 30000,
});

// Request interceptor to automatically add authorization token
api.interceptors.request.use(async (config) => {
    let token = localStorage.getItem('parikshak_token');
    if (!token) {
        try {
            const authUrl = `${BACKEND_URL}/api/v1/production/auth/token`;
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
api.interceptors.response.use((response) => response, async (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        localStorage.removeItem('parikshak_token');
        try {
            const authUrl = `${BACKEND_URL}/api/v1/production/auth/token`;
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

export const lifecycleAPI = {
    submitTask: async (taskData) => {
        const form = new FormData();
        form.append('task_title',       taskData.task_title);
        form.append('task_description', taskData.task_description);
        form.append('submitted_by',     taskData.submitted_by);
        form.append('github_repo_link', taskData.github_repo_link || '');
        form.append('module_id',        taskData.module_id || 'task-review-agent');
        form.append('schema_version',   taskData.schema_version || 'v1.0');
        if (taskData.pdf_file) form.append('pdf_file', taskData.pdf_file);
        const response = await api.post('submit', form, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    // Get task history
    getHistory: async () => {
        const response = await api.get('history');
        return response.data;
    },

    // Get review details by submission ID
    getReview: async (submissionId) => {
        const response = await api.get(`review/${submissionId}`);
        return response.data;
    },

    // Get next task details by submission ID
    getNextTask: async (submissionId) => {
        const response = await api.get(`next/${submissionId}`);
        return response.data;
    }
};

export const checkBackendHealth = async () => {
    try {
        const healthUrl = `${BACKEND_URL}/health`;
        const response = await axios.get(healthUrl, { timeout: 5000 });
        return response.status === 200;
    } catch {
        return false;
    }
};