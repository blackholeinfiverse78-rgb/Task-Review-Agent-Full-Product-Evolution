import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { History, Eye, ArrowRight, Calendar, User, FileText, RefreshCw } from 'lucide-react';
import LoadingState from '../components/LoadingState';
import StatusBadge from '../components/StatusBadge';

const TaskHistory = () => {
    const navigate = useNavigate();
    const [historyData, setHistoryData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchHistoryData();
    }, []);

    const fetchHistoryData = async () => {
        try {
            setLoading(true);
            let backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
            backendUrl = backendUrl.replace(/\/+$/, '');
            const response = await fetch(`${backendUrl}/api/v1/lifecycle/history`);
            
            if (response.ok) {
                const data = await response.json();
                setHistoryData(data);
                setError(null);
            } else {
                setError(`Failed to load history: ${response.status}`);
            }
        } catch (err) {
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    const getResultColor = (result) => {
        return result === 'PASS' ? 'text-green-600' : 'text-red-600';
    };

    const getResultBgColor = (result) => {
        return result === 'PASS'
            ? 'bg-green-100 dark:bg-green-900/30'
            : 'bg-red-100 dark:bg-red-900/30';
    };

    if (loading) return <LoadingState message="Loading task history..." />;
    
    if (error) {
        return (
            <div className="max-w-6xl mx-auto space-y-8">
                <header className="text-center">
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                        Task History
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400">
                        View all your previous task submissions
                    </p>
                </header>
                
                <div className="card text-center py-12">
                    <div className="text-red-500 mb-4">
                        <History size={48} className="mx-auto" />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Error Loading History</h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
                    <button 
                        onClick={fetchHistoryData}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 mx-auto"
                    >
                        <RefreshCw size={16} />
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            {/* Header */}
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                        Task History
                    </h1>
                    <p className="text-slate-600 dark:text-slate-400">
                        {historyData.length} task{historyData.length !== 1 ? 's' : ''} submitted
                    </p>
                </div>
                <button 
                    onClick={fetchHistoryData}
                    className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
                >
                    <RefreshCw size={16} />
                    Refresh
                </button>
            </header>

            {historyData.length === 0 ? (
                <div className="card text-center py-12">
                    <div className="text-6xl mb-4">📚</div>
                    <h3 className="text-xl font-bold mb-2">No History Yet</h3>
                    <p className="text-slate-600 dark:text-slate-400 mb-6">
                        Your task history will appear here once you submit tasks.
                    </p>
                    <button 
                        onClick={() => navigate('/submit')}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                    >
                        Submit Your First Task
                    </button>
                </div>
            ) : (
                <div className="space-y-4">
                    {historyData.map((task) => (
                        <div 
                            key={task.submission_id}
                            className="card hover:shadow-lg transition-all duration-200 cursor-pointer group"
                            onClick={() => navigate(`/review/${task.submission_id}`)}
                        >
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-6 flex-1">
                                    {/* Result Badge */}
                                    <div className={`w-16 h-16 rounded-2xl ${getResultBgColor(task.evaluation_result)} flex items-center justify-center`}>
                                        <div className={`text-sm font-black ${getResultColor(task.evaluation_result)}`}>
                                            {task.evaluation_result || 'FAIL'}
                                        </div>
                                    </div>

                                    {/* Task Info */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors truncate">
                                                {task.task_title}
                                            </h3>
                                            <StatusBadge status={task.evaluation_result === 'PASS' ? 'pass' : 'fail'} />
                                            {task.has_pdf && (
                                                <div className="flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 rounded text-xs">
                                                    <FileText size={12} />
                                                    PDF
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                                            <div className="flex items-center gap-1">
                                                <User size={14} />
                                                <span>{task.submitted_by}</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <Calendar size={14} />
                                                <span>{new Date(task.submitted_at).toLocaleDateString()}</span>
                                            </div>
                                            <div className="text-xs font-mono bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded">
                                                {task.submission_id}
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-3">
                                    <button 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/review/${task.submission_id}`);
                                        }}
                                        className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                                        title="View Review"
                                    >
                                        <Eye size={18} />
                                    </button>
                                    <button 
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/next/${task.submission_id}`);
                                        }}
                                        className="p-2 text-slate-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-lg transition-colors"
                                        title="View Next Task"
                                    >
                                        <ArrowRight size={18} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Summary Stats */}
            {historyData.length > 0 && (
                <div className="grid md:grid-cols-4 gap-4">
                    <div className="card text-center">
                        <div className="text-2xl font-black text-blue-600 mb-1">
                            {historyData.length}
                        </div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                            Total Submissions
                        </div>
                    </div>
                    <div className="card text-center">
                        <div className="text-2xl font-black text-green-600 mb-1">
                            {historyData.filter(t => t.evaluation_result === 'PASS').length}
                        </div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                            Passed
                        </div>
                    </div>
                    <div className="card text-center">
                        <div className="text-2xl font-black text-red-600 mb-1">
                            {historyData.filter(t => t.evaluation_result === 'FAIL').length}
                        </div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                            Failed
                        </div>
                    </div>
                    <div className="card text-center">
                        <div className="text-2xl font-black text-slate-600 dark:text-slate-400 mb-1">
                            {historyData.length}
                        </div>
                        <div className="text-sm text-slate-600 dark:text-slate-400">
                            Total
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TaskHistory;