import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, Target, Settings } from 'lucide-react';
import LoadingState from '../components/LoadingState';

const FAILURE_LABELS = {
    schema_violation: 'Schema Violation',
    incomplete:       'Incomplete Submission',
    incorrect_logic:  'Incorrect Logic',
    integration_fail: 'Integration Failure',
};

const ReviewResult = () => {
    const { taskId } = useParams();
    const navigate   = useNavigate();
    const [reviewData, setReviewData] = useState(null);
    const [loading, setLoading]       = useState(true);
    const [error, setError]           = useState(null);

    useEffect(() => { fetchReviewData(); }, [taskId]);

    const fetchReviewData = async () => {
        try {
            const { taskService } = await import('../services/taskService');
            const data = await taskService.getReview(taskId);
            setReviewData(data);
        } catch (err) {
            setError(`Failed to load review: ${err.response?.status || err.message}`);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <LoadingState message="Loading review results..." />;

    if (error) return (
        <div className="max-w-4xl mx-auto card text-center py-12">
            <XCircle className="mx-auto text-red-500 mb-4" size={48} />
            <h3 className="text-xl font-bold mb-2">Error Loading Review</h3>
            <p className="text-slate-600 dark:text-slate-400 mb-4">{error}</p>
            <button onClick={() => navigate('/')} className="px-4 py-2 bg-blue-600 text-white rounded-lg">
                Back to Dashboard
            </button>
        </div>
    );

    if (!reviewData) return (
        <div className="max-w-4xl mx-auto card text-center py-12">
            <AlertTriangle className="mx-auto text-yellow-500 mb-4" size={48} />
            <h3 className="text-xl font-bold mb-2">Review Not Found</h3>
            <p className="text-slate-600 dark:text-slate-400">Task ID: {taskId}</p>
        </div>
    );

    const isPassed       = reviewData.evaluation_result === 'PASS';
    const failureLabel   = FAILURE_LABELS[reviewData.failure_type] || reviewData.failure_type;

    return (
        <div className="max-w-4xl mx-auto space-y-8">

            {/* Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => navigate('/')} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg">
                    <ArrowLeft size={20} />
                </button>
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Review Results</h1>
                    <p className="text-slate-600 dark:text-slate-400">Task ID: {taskId}</p>
                </div>
            </div>

            {/* Result Card */}
            <div className={`card border-l-4 ${isPassed ? 'border-l-green-500 bg-green-50 dark:bg-green-900/20' : 'border-l-red-500 bg-red-50 dark:bg-red-900/20'}`}>
                <div className="flex items-center gap-6">
                    {isPassed
                        ? <CheckCircle className="text-green-600" size={48} />
                        : <XCircle    className="text-red-600"   size={48} />
                    }
                    <div>
                        <div className={`text-3xl font-black ${isPassed ? 'text-green-600' : 'text-red-600'}`}>
                            {reviewData.evaluation_result}
                        </div>
                        {!isPassed && reviewData.failure_type && (
                            <div className="text-sm font-medium text-slate-600 dark:text-slate-400 mt-1">
                                Failure Type: <span className="font-bold">{failureLabel}</span>
                            </div>
                        )}
                        <div className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                            Reviewed on {new Date(reviewData.reviewed_at).toLocaleDateString()}
                        </div>
                    </div>
                </div>
            </div>

            {/* Selected Task */}
            {reviewData.selected_task_id && (
                <div className="card">
                    <h3 className="font-bold mb-3 flex items-center gap-2">
                        <Target size={20} />
                        Next Task Assigned
                    </h3>
                    <div className="font-mono text-sm bg-slate-100 dark:bg-slate-800 px-4 py-3 rounded-lg">
                        {reviewData.selected_task_id}
                    </div>
                    {reviewData.selection_reason && (
                        <p className="text-sm text-slate-500 dark:text-slate-400 mt-2">
                            {reviewData.selection_reason}
                        </p>
                    )}
                </div>
            )}

            {/* Failure Reasons */}
            {!isPassed && reviewData.failure_reasons?.length > 0 && (
                <div className="card">
                    <h3 className="font-bold text-red-600 dark:text-red-400 mb-3 flex items-center gap-2">
                        <XCircle size={20} /> Issues Found
                    </h3>
                    <ul className="space-y-2">
                        {reviewData.failure_reasons.map((r, i) => (
                            <li key={i} className="flex items-start gap-2 text-sm">
                                <div className="w-1.5 h-1.5 bg-red-500 rounded-full mt-2 flex-shrink-0" />
                                <span>{r}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}

            {/* Evaluation Summary */}
            {reviewData.evaluation_summary && (
                <div className="card">
                    <h3 className="font-bold mb-3">Evaluation Summary</h3>
                    <p className="text-slate-700 dark:text-slate-300">{reviewData.evaluation_summary}</p>
                </div>
            )}

            {/* Registry Validation */}
            {reviewData.registry_validation && (
                <div className="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                    <h3 className="font-bold text-blue-800 dark:text-blue-400 mb-3 flex items-center gap-2">
                        <Settings size={20} /> Registry Validation
                    </h3>
                    <div className="grid md:grid-cols-3 gap-4 text-sm">
                        <div>
                            <div className="font-medium text-blue-600">Module ID</div>
                            <div className="font-mono">{reviewData.registry_validation.module_id}</div>
                        </div>
                        <div>
                            <div className="font-medium text-blue-600">Schema Version</div>
                            <div className="font-mono">{reviewData.registry_validation.schema_version}</div>
                        </div>
                        <div>
                            <div className="font-medium text-blue-600">Validation Status</div>
                            <div className={reviewData.registry_validation.validation_passed ? 'text-green-600' : 'text-red-600'}>
                                {reviewData.registry_validation.validation_passed ? '✅ Passed' : '❌ Failed'}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Actions */}
            <div className="flex gap-4">
                <button
                    onClick={() => navigate(`/next/${taskId}`)}
                    className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center gap-2"
                >
                    <Target size={20} /> View Next Task
                </button>
                <button
                    onClick={() => navigate('/history')}
                    className="px-6 py-3 bg-slate-200 dark:bg-slate-700 text-slate-900 dark:text-white rounded-lg font-medium hover:bg-slate-300"
                >
                    View All History
                </button>
            </div>
        </div>
    );
};

export default ReviewResult;
