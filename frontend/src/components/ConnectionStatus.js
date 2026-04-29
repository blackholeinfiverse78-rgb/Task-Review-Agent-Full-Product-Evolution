import React, { useState, useEffect } from 'react';
import { CheckCircle, XCircle, AlertCircle } from 'lucide-react';

const ConnectionStatus = () => {
    const [status, setStatus] = useState('checking');
    const [backendUrl, setBackendUrl] = useState('');

    useEffect(() => {
        checkConnection();
    }, []);

    const checkConnection = async () => {
        let url = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
        url = url.replace(/\/+$/, '');
        setBackendUrl(url);

        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 10000);

        try {
            const response = await fetch(`${url}/health`, {
                method: 'GET',
                signal: controller.signal,
                mode: 'cors'
            });
            clearTimeout(timer);
            if (response.ok) {
                setStatus('connected');
            } else {
                setStatus('error');
            }
        } catch (error) {
            clearTimeout(timer);
            console.error('Connection test failed:', error);
            setStatus(error.name === 'AbortError' ? 'error' : 'disconnected');
        }
    };

    const getStatusIcon = () => {
        switch (status) {
            case 'connected':
                return <CheckCircle className="text-green-500" size={20} />;
            case 'disconnected':
                return <XCircle className="text-red-500" size={20} />;
            case 'error':
                return <AlertCircle className="text-yellow-500" size={20} />;
            default:
                return <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />;
        }
    };

    const getStatusText = () => {
        switch (status) {
            case 'connected':
                return 'Backend Connected';
            case 'disconnected':
                return 'Backend Disconnected';
            case 'error':
                return 'Backend Starting (cold start)...';
            default:
                return 'Checking Connection...';
        }
    };

    const getStatusColor = () => {
        switch (status) {
            case 'connected':
                return 'text-green-700 bg-green-50 border-green-200';
            case 'disconnected':
                return 'text-red-700 bg-red-50 border-red-200';
            case 'error':
                return 'text-yellow-700 bg-yellow-50 border-yellow-200';
            default:
                return 'text-blue-700 bg-blue-50 border-blue-200';
        }
    };

    return (
        <div className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium ${getStatusColor()}`}>
            {getStatusIcon()}
            <span>{getStatusText()}</span>
            <span className="text-xs opacity-75">({backendUrl})</span>
            <button 
                onClick={checkConnection}
                className="ml-2 text-xs underline hover:no-underline"
            >
                Retry
            </button>
        </div>
    );
};

export default ConnectionStatus;