import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, History, Activity, TrendingUp, RefreshCw } from 'lucide-react';
import LoadingState from '../components/LoadingState';
import StatusBadge from '../components/StatusBadge';

const Dashboard = () => {
    const navigate = useNavigate();
    const [historyData, setHistoryData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            let backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
            backendUrl = backendUrl.replace(/\/+$/, '');
            const response = await fetch(`${backendUrl}/api/v1/lifecycle/history`);
            
            if (response.ok) {
                const data = await response.json();
                setHistoryData(data);
                setError(null);
            } else {
                setError(`Failed to load data: ${response.status}`);
            }
        } catch (err) {
            setError(`Network error: ${err.message}`);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingState message="Loading dashboard..." />;
    
    const recentTasks = historyData.slice(-3).reverse();
    const passedTasks = historyData.filter(t => t.evaluation_result === 'PASS').length;
    const totalTasks = historyData.length;

    return (
        <div className="space-y-10 fade-in">
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div className="space-y-1">
                    <h1 className="text-4xl font-black tracking-tight text-slate-900 dark:text-white">
                        Task Review <span className="text-blue-600">Agent</span>
                    </h1>
                    <p className="text-slate-500 font-medium">Enterprise-grade autonomous evaluation system</p>
                </div>
                <div className="flex items-center gap-3">
                    <button 
                        onClick={fetchDashboardData}
                        className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg font-medium hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
                    >
                        <RefreshCw size={16} />
                        Refresh
                    </button>
                    <button 
                        onClick={() => navigate('/history')}
                        className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg font-medium hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors flex items-center gap-2"
                    >
                        <History size={18} />
                        History
                    </button>
                    <button 
                        onClick={() => navigate('/submit')}
                        className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
                    >
                        <Plus size={18} />
                        New Task
                    </button>
                </div>
            </header>

            {/* Stats Cards */}
            <section className="grid md:grid-cols-4 gap-6">
                <div className="card border-b-4 border-b-blue-500 flex items-center gap-4">
                    <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-600">
                        <Activity size={32} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Total Tasks</div>
                        <div className="text-3xl font-black">{totalTasks}</div>
                    </div>
                </div>
                <div className="card border-b-4 border-b-emerald-500 flex items-center gap-4">
                    <div className="p-4 bg-emerald-500/10 rounded-2xl text-emerald-600">
                        <TrendingUp size={32} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Passed</div>
                        <div className="text-3xl font-black">{passedTasks}</div>
                    </div>
                </div>
                <div className="card border-b-4 border-b-green-500 flex items-center gap-4">
                    <div className="p-4 bg-green-500/10 rounded-2xl text-green-600">
                        <Activity size={32} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Passed</div>
                        <div className="text-3xl font-black">{passedTasks}</div>
                    </div>
                </div>
                <div className="card border-b-4 border-b-indigo-500 flex items-center gap-4">
                    <div className="p-4 bg-indigo-500/10 rounded-2xl text-indigo-600">
                        <History size={32} />
                    </div>
                    <div>
                        <div className="text-sm font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Status</div>
                        <div className="text-lg font-black uppercase text-indigo-600">
                            {error ? 'Error' : 'Ready'}
                        </div>
                    </div>
                </div>
            </section>

            {error && (
                <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-center py-8">
                    <h3 className="text-lg font-bold text-red-800 dark:text-red-400 mb-2">Connection Issue</h3>
                    <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
                    <p className="text-sm text-red-500 dark:text-red-400 mb-4">
                        Make sure the backend is running on http://localhost:8000
                    </p>
                    <button 
                        onClick={() => navigate('/submit')}
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2 mx-auto"
                    >
                        <Plus size={18} />
                        Submit Task Anyway
                    </button>
                </div>
            )}

            <section className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-4">
                    <div className="flex items-center justify-between px-2">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Activity className="text-blue-600" size={20} />
                            Recent Activity
                        </h2>
                        {totalTasks > 3 && (
                            <button
                                onClick={() => navigate('/history')}
                                className="text-sm font-bold text-blue-600 hover:underline"
                            >
                                View Full History
                            </button>
                        )}
                    </div>

                    <div className="space-y-3">
                        {recentTasks.length > 0 ? (
                            recentTasks.map((task) => (
                                <div
                                    key={task.submission_id}
                                    onClick={() => navigate(`/review/${task.submission_id}`)}
                                    className="card !p-4 flex items-center justify-between hover:scale-[1.01] transition-all cursor-pointer group"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className={`w-12 h-12 rounded-xl flex items-center justify-center font-bold text-white text-xs ${
                                            task.evaluation_result === 'PASS' ? 'bg-green-500' : 'bg-red-500'
                                        }`}>
                                            {task.evaluation_result || 'FAIL'}
                                        </div>
                                        <div>
                                            <div className="font-bold group-hover:text-blue-600 transition-colors uppercase tracking-tight">
                                                {task.task_title}
                                            </div>
                                            <div className="text-xs text-slate-500 flex items-center gap-2">
                                                <span>{new Date(task.submitted_at).toLocaleDateString()}</span>
                                                <span>•</span>
                                                <span>{task.submitted_by}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <StatusBadge status={task.evaluation_result === 'PASS' ? 'pass' : 'fail'} />
                                </div>
                            ))
                        ) : (
                            <div className="card py-10 text-center border-dashed border-2">
                                <p className="text-slate-500 font-medium">No tasks found. Start by submitting your first task.</p>
                                <button 
                                    onClick={() => navigate('/submit')}
                                    className="mt-4 px-4 py-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                                >
                                    Submit First Task
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                <div className="rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 border-none text-white relative overflow-hidden group shadow-xl shadow-blue-500/20 p-6">
                    <div className="relative z-10 space-y-6">
                        <div className="space-y-2">
                            <h3 className="text-2xl font-black text-white">Ready to Start?</h3>
                            <p className="text-blue-100 text-sm leading-relaxed">
                                Submit your project for registry-aware evaluation. Get dynamic scoring across title, description, and repository analysis.
                            </p>
                        </div>
                        <button 
                            onClick={() => navigate('/submit')}
                            className="w-full bg-white text-blue-700 hover:bg-blue-50 font-bold shadow-none border-none px-6 py-3 rounded-lg transition-colors"
                        >
                            Start New Evaluation
                        </button>
                    </div>
                    <div className="absolute top-[-20%] right-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:bg-white/20 transition-colors" />
                    <div className="absolute bottom-[-10%] left-[-10%] w-32 h-32 bg-indigo-400/20 rounded-full blur-2xl" />
                </div>
            </section>
        </div>
    );
};

export default Dashboard;