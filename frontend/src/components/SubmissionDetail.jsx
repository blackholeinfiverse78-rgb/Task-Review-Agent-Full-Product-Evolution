import React, { useState } from 'react';

const SubmissionDetail = ({ submission, onAction, onClose }) => {
    const [overrideTaskId, setOverrideTaskId] = useState('');

    if (!submission) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm">
            <div className="bg-white dark:bg-slate-800 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden border border-slate-200 dark:border-slate-700 animate-in fade-in zoom-in duration-200">
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-900/50">
                    <h2 className="text-xl font-bold">Submission Detail</h2>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-2xl">&times;</button>
                </div>
                
                <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Candidate</p>
                            <p className="font-medium">{submission.candidate_name}</p>
                        </div>
                        <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Trace ID</p>
                            <p className="font-mono text-sm">{submission.trace_id}</p>
                        </div>
                        <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Deterministic Recommendation</p>
                            <p className="font-mono text-sm text-indigo-600 dark:text-indigo-400">{submission.selected_task_id}</p>
                        </div>
                        <div>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Result</p>
                            <p className={`font-bold ${submission.evaluation_result === 'PASS' ? 'text-emerald-500' : 'text-rose-500'}`}>
                                {submission.evaluation_result}
                            </p>
                        </div>
                    </div>

                    <div>
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Selection Reason</p>
                        <div className="p-3 bg-slate-50 dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-700 text-sm">
                            {submission.selection_reason}
                        </div>
                    </div>

                    <div>
                        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1">Full Response JSON</p>
                        <pre className="p-3 bg-slate-900 text-slate-300 rounded-lg text-xs overflow-x-auto">
                            {JSON.stringify(submission.full_response, null, 2)}
                        </pre>
                    </div>

                    {submission.review_state === 'PENDING_REVIEW' && (
                        <div className="pt-4 border-t border-slate-200 dark:border-slate-700 space-y-4">
                            <div className="flex gap-3">
                                <button 
                                    onClick={() => onAction('approve', submission)}
                                    className="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-emerald-600/20"
                                >
                                    APPROVE
                                </button>
                                <button 
                                    onClick={() => onAction('reject', submission)}
                                    className="flex-1 bg-rose-600 hover:bg-rose-700 text-white font-bold py-3 rounded-xl transition-all shadow-lg shadow-rose-600/20"
                                >
                                    REJECT
                                </button>
                            </div>

                            <div className="p-4 bg-slate-100 dark:bg-slate-900/80 rounded-xl space-y-3">
                                <p className="text-xs font-bold text-slate-500">MODIFY ASSIGNMENT</p>
                                <div className="flex gap-2">
                                    <input 
                                        type="text" 
                                        placeholder="Enter Override Task ID (e.g. T-GOV-101)"
                                        value={overrideTaskId}
                                        onChange={(e) => setOverrideTaskId(e.target.value)}
                                        className="flex-1 px-4 py-2 rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                                    />
                                    <button 
                                        onClick={() => onAction('modify', submission, overrideTaskId)}
                                        disabled={!overrideTaskId}
                                        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white px-6 py-2 rounded-lg font-bold text-sm transition-all"
                                    >
                                        MODIFY
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default SubmissionDetail;
