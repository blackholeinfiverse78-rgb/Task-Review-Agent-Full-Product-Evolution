import React from 'react';

const SubmissionTable = ({ submissions, onRowClick }) => {
    return (
        <div className="overflow-x-auto bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700">
            <table className="w-full text-left border-collapse">
                <thead>
                    <tr className="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Candidate Name</th>
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Task Title</th>
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Result</th>
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Failure Type</th>
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">State</th>
                        <th className="px-6 py-4 font-semibold text-slate-700 dark:text-slate-300">Trace ID</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {submissions.length === 0 ? (
                        <tr>
                            <td colSpan="6" className="px-6 py-10 text-center text-slate-500">
                                No submissions in queue.
                            </td>
                        </tr>
                    ) : (
                        submissions.map((sub) => (
                            <tr 
                                key={sub.submission_id} 
                                onClick={() => onRowClick(sub)}
                                className="hover:bg-slate-50 dark:hover:bg-slate-700/50 cursor-pointer transition-colors duration-150"
                            >
                                <td className="px-6 py-4 font-medium">{sub.candidate_name}</td>
                                <td className="px-6 py-4 text-sm truncate max-w-xs">{sub.task_title}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                        sub.evaluation_result === 'PASS' 
                                        ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' 
                                        : 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400'
                                    }`}>
                                        {sub.evaluation_result}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-sm text-slate-500">{sub.failure_type || '-'}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${
                                        sub.review_state === 'PENDING_REVIEW' ? 'bg-amber-100 text-amber-700' :
                                        sub.review_state === 'APPROVED' ? 'bg-emerald-100 text-emerald-700' :
                                        sub.review_state === 'REJECTED' ? 'bg-rose-100 text-rose-700' :
                                        'bg-blue-100 text-blue-700'
                                    }`}>
                                        {sub.review_state}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-xs font-mono text-slate-400">{sub.trace_id}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default SubmissionTable;
