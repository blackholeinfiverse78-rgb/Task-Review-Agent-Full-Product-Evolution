import axios from 'axios';

const RAW_BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
let BACKEND_URL = RAW_BACKEND_URL.replace(/\/+$/, '');
if (BACKEND_URL.endsWith('/api/v1')) {
    BACKEND_URL = BACKEND_URL.replace(/\/api\/v1$/, '');
}
const LIFECYCLE_API = `${BACKEND_URL}/api/v1/lifecycle`;

const api = axios.create({
    baseURL: LIFECYCLE_API,
    timeout: 30000,
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