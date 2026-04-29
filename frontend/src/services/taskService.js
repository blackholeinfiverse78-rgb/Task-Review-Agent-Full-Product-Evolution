import apiClient from './apiClient';

export const taskService = {
    submitTask: async (data) => {
        const formData = new FormData();
        formData.append('task_title', data.task_title);
        formData.append('task_description', data.task_description);
        formData.append('submitted_by', data.submitted_by || 'Developer');
        formData.append('github_repo_link', data.github_repo_link || '');
        formData.append('module_id', data.module_id || 'task-review-agent');
        formData.append('schema_version', data.schema_version || 'v1.0');

        if (data.previous_task_id) {
            formData.append('previous_task_id', data.previous_task_id);
        }

        if (data.pdf_file) {
            formData.append('pdf_file', data.pdf_file);
        }

        const response = await apiClient.post('lifecycle/submit', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            }
        });
        return response.data;
    },
    getReview: async (taskId) => {
        const response = await apiClient.get(`lifecycle/review/${taskId}`);
        return response.data;
    },
    getNextTask: async (taskId) => {
        const response = await apiClient.get(`lifecycle/next/${taskId}`);
        return response.data;
    },
    getTaskHistory: async () => {
        const response = await apiClient.get('lifecycle/history');
        return response.data;
    },
    getTtsStream: (text, lang = 'en', tone = 'neutral') => {
        const params = new URLSearchParams({ text, lang, tone });
        let baseUrl = process.env.REACT_APP_API_BASE
            || process.env.REACT_APP_BACKEND_URL
            || 'http://localhost:8000/api/v1';
        baseUrl = baseUrl.replace(/\/+$/, '');
        if (!baseUrl.endsWith('/api/v1')) {
            baseUrl = `${baseUrl}/api/v1`;
        }
        return `${baseUrl}/tts/speak?${params.toString()}`;
    },
    getTtsLanguages: async () => {
        const response = await apiClient.get('tts/languages');
        return response.data;
    },
};
