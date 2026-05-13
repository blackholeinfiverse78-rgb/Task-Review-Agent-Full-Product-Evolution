import React, { useState, useEffect } from 'react';
import SubmissionTable from '../components/SubmissionTable';
import SubmissionDetail from '../components/SubmissionDetail';

const ReviewDashboard = () => {
    const [submissions, setSubmissions] = useState([]);
    const [selectedSubmission, setSelectedSubmission] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchSubmissions = async () => {
        try {
            setLoading(true);
            const response = await fetch('/api/v1/review/all');
            if (!response.ok) throw new Error('Failed to fetch submissions');
            const data = await response.json();
            setSubmissions(data);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSubmissions();
    }, []);

    const handleAction = async (action, submission, overrideTaskId = null) => {
        try {
            const response = await fetch(`/api/v1/review/${action}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    trace_id: submission.trace_id,
                    submission_id: submission.submission_id,
                    action: action,
                    override_task_id: overrideTaskId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `Failed to ${action} submission`);
            }

            // Refresh list
            await fetchSubmissions();
            setSelectedSubmission(null);
            alert(`Submission ${action}ed successfully!`);
        } catch (err) {
            alert(`Error: ${err.message}`);
        }
    };

    return (
        <div className="space-y-8 max-w-6xl mx-auto">
            <header className="flex justify-between items-end">
                <div>
                    <h1 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">Review Queue</h1>
                    <p className="text-slate-500 dark:text-slate-400 mt-2">Human Governance & Approval Layer</p>
                </div>
                <button 
                    onClick={fetchSubmissions}
                    className="px-4 py-2 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 rounded-lg text-sm font-semibold transition-colors"
                >
                    Refresh Data
                </button>
            </header>

            {loading ? (
                <div className="flex justify-center py-20">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                </div>
            ) : error ? (
                <div className="p-4 bg-rose-50 dark:bg-rose-900/20 text-rose-600 dark:text-rose-400 rounded-xl border border-rose-200 dark:border-rose-800">
                    Error: {error}
                </div>
            ) : (
                <SubmissionTable 
                    submissions={submissions} 
                    onRowClick={setSelectedSubmission} 
                />
            )}

            {selectedSubmission && (
                <SubmissionDetail 
                    submission={selectedSubmission}
                    onAction={handleAction}
                    onClose={() => setSelectedSubmission(null)}
                />
            )}
        </div>
    );
};

export default ReviewDashboard;
