import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    ArrowLeft, CheckCircle, XCircle, AlertTriangle, Target, Settings, 
    User, GitBranch, Calendar, Award, FileText, Sparkles, Clock, 
    Copy, Check, ExternalLink, Activity 
} from 'lucide-react';
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
    const [copiedRepo, setCopiedRepo] = useState(false);
    const [copiedTrace, setCopiedTrace] = useState(false);

    useEffect(() => { 
        fetchReviewData(); 
    }, [taskId]);

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

    const handleCopyRepo = (text) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        setCopiedRepo(true);
        setTimeout(() => setCopiedRepo(false), 2000);
    };

    const handleCopyTrace = (text) => {
        if (!text) return;
        navigator.clipboard.writeText(text);
        setCopiedTrace(true);
        setTimeout(() => setCopiedTrace(false), 2000);
    };

    if (loading) return <LoadingState message="Loading candidate review results..." />;

    if (error) return (
        <div className="max-w-6xl mx-auto card text-center py-12 bg-white dark:bg-slate-800 shadow-xl rounded-2xl border border-slate-100 dark:border-slate-700">
            <XCircle className="mx-auto text-rose-500 mb-4 animate-bounce" size={56} />
            <h3 className="text-2xl font-black mb-2 text-slate-800 dark:text-white">Error Loading Review</h3>
            <p className="text-slate-600 dark:text-slate-400 mb-6 max-w-md mx-auto">{error}</p>
            <button onClick={() => navigate('/')} className="px-6 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 transition-all">
                Back to Dashboard
            </button>
        </div>
    );

    if (!reviewData) return (
        <div className="max-w-6xl mx-auto card text-center py-12 bg-white dark:bg-slate-800 shadow-xl rounded-2xl border border-slate-100 dark:border-slate-700">
            <AlertTriangle className="mx-auto text-amber-500 mb-4 animate-pulse" size={56} />
            <h3 className="text-2xl font-black mb-2 text-slate-800 dark:text-white">Review Not Found</h3>
            <p className="text-slate-600 dark:text-slate-400">Task ID: {taskId}</p>
        </div>
    );

    const isPassed = reviewData.evaluation_result === 'PASS';
    const failureLabel = FAILURE_LABELS[reviewData.failure_type] || reviewData.failure_type;
    
    // Status color configurations
    const themeColorClass = isPassed 
        ? 'emerald' 
        : (reviewData.status === 'borderline' ? 'amber' : 'rose');
        
    const bgGradient = isPassed
        ? 'from-emerald-500 to-teal-600'
        : (reviewData.status === 'borderline' ? 'from-amber-500 to-orange-600' : 'from-rose-500 to-red-600');

    const cardBorderColor = isPassed 
        ? 'border-l-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/10' 
        : (reviewData.status === 'borderline' ? 'border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/10' : 'border-l-rose-500 bg-rose-50/50 dark:bg-rose-950/10');

    const scoreColorClass = isPassed 
        ? 'text-emerald-600 dark:text-emerald-400' 
        : (reviewData.status === 'borderline' ? 'text-amber-600 dark:text-amber-400' : 'text-rose-600 dark:text-rose-400');

    // Extract metrics from analysis
    const technicalQuality = reviewData.analysis?.technical_quality ?? reviewData.score;
    const clarity = reviewData.analysis?.clarity ?? reviewData.score;
    const disciplineSignals = reviewData.analysis?.discipline_signals ?? reviewData.score;
    const pac = reviewData.analysis?.pac || null;
    const rubric = reviewData.analysis?.rubric || null;

    return (
        <div className="max-w-6xl mx-auto space-y-8 fade-in">
            {/* Breadcrumb Navigation Header */}
            <div className="flex items-center gap-4">
                <button onClick={() => navigate('/')} className="p-2.5 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 transition-colors">
                    <ArrowLeft size={18} />
                </button>
                <div>
                    <h1 className="text-3xl font-black text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
                        Evaluation Results <span className="text-sm font-normal text-slate-400">/ Trace Details</span>
                    </h1>
                    <p className="text-sm font-mono text-slate-500">Submission ID: {taskId}</p>
                </div>
            </div>

            {/* Top Dashboard Hero Row (Score, Readiness, and Evidence) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                
                {/* 1. Score Gauge Card */}
                <div className="card relative bg-white dark:bg-slate-800 shadow-lg hover:shadow-xl transition-shadow rounded-2xl p-6 flex flex-col justify-between overflow-hidden border border-slate-100 dark:border-slate-700/80">
                    <div className="flex justify-between items-start">
                        <span className="text-xs font-black uppercase text-slate-400 tracking-widest">Grading Score</span>
                        <Award size={20} className={scoreColorClass} />
                    </div>
                    <div className="my-4 text-center">
                        <div className={`text-6xl font-black ${scoreColorClass} tracking-tighter`}>
                            {reviewData.score}
                            <span className="text-xl font-normal text-slate-400">/100</span>
                        </div>
                    </div>
                    <div className="text-xs text-slate-500 text-center">
                        Deterministic Content-Based Evaluation Metric
                    </div>
                </div>

                {/* 2. Readiness percentage gauge */}
                <div className="card relative bg-white dark:bg-slate-800 shadow-lg hover:shadow-xl transition-shadow rounded-2xl p-6 flex flex-col justify-between overflow-hidden border border-slate-100 dark:border-slate-700/80">
                    <div className="flex justify-between items-start">
                        <span className="text-xs font-black uppercase text-slate-400 tracking-widest">Production Readiness</span>
                        <Sparkles size={20} className="text-blue-500" />
                    </div>
                    <div className="my-4 text-center">
                        <div className="text-6xl font-black text-blue-600 dark:text-blue-400 tracking-tighter">
                            {reviewData.readiness_percent}%
                        </div>
                        {/* Beautiful Progress Bar */}
                        <div className="w-full bg-slate-100 dark:bg-slate-700 h-2.5 rounded-full mt-3 overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-1000" 
                                style={{ width: `${reviewData.readiness_percent}%` }}
                            />
                        </div>
                    </div>
                    <div className="text-xs text-slate-500 text-center">
                        Weighted checklist alignment across 12 dimensions
                    </div>
                </div>

                {/* 3. Overall Verdict & State Badge */}
                <div className={`card relative text-white bg-gradient-to-br ${bgGradient} shadow-lg rounded-2xl p-6 flex flex-col justify-between overflow-hidden border-none`}>
                    <div className="flex justify-between items-start">
                        <span className="text-xs font-black uppercase text-white/70 tracking-widest">Certification State</span>
                        {isPassed 
                            ? <CheckCircle size={20} className="text-white" />
                            : <XCircle size={20} className="text-white" />
                        }
                    </div>
                    <div className="my-4">
                        <div className="text-4xl font-black tracking-tight uppercase leading-none">
                            {isPassed ? 'READY' : (reviewData.status === 'borderline' ? 'NEEDS WORK' : 'NOT READY')}
                        </div>
                        {reviewData.failure_type && (
                            <div className="text-xs font-bold bg-white/20 px-2 py-1 rounded-md inline-block mt-2 font-mono">
                                {failureLabel}
                            </div>
                        )}
                    </div>
                    <div className="text-xs text-white/80">
                        {isPassed ? 'Approved for governed release.' : 'Corrective assignment release generated.'}
                    </div>
                </div>
            </div>

            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700/80 shadow-sm flex items-center gap-3">
                    <User size={18} className="text-slate-400" />
                    <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Candidate</div>
                        <div className="text-sm font-semibold">{reviewData.candidate_name}</div>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700/80 shadow-sm flex items-center gap-3">
                    <Calendar size={18} className="text-slate-400" />
                    <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Reviewed On</div>
                        <div className="text-sm font-semibold">{new Date(reviewData.reviewed_at).toLocaleString()}</div>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700/80 shadow-sm flex items-center gap-3 cursor-pointer group" onClick={() => handleCopyTrace(reviewData.trace_id)}>
                    <Settings size={18} className="text-slate-400" />
                    <div className="flex-1 min-w-0">
                        <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1.5 justify-between">
                            Trace ID
                            {copiedTrace 
                                ? <Check size={10} className="text-emerald-500" />
                                : <Copy size={10} className="text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                            }
                        </div>
                        <div className="text-xs font-mono font-semibold truncate">{reviewData.trace_id || 'N/A'}</div>
                    </div>
                </div>
                <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-100 dark:border-slate-700/80 shadow-sm flex items-center gap-3">
                    <Clock size={18} className="text-slate-400" />
                    <div>
                        <div className="text-[10px] uppercase font-bold text-slate-400">Review Version</div>
                        <div className="text-sm font-semibold">v{reviewData.version || 1}</div>
                    </div>
                </div>
            </div>

            {/* Details Section */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                
                {/* Left Columns - Repository, Assigned Task and Technical Analysis */}
                <div className="lg:col-span-2 space-y-6">
                    
                    {/* Repository Profile */}
                    {reviewData.repository_url && (
                        <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                            <h3 className="font-black text-lg text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                                <GitBranch size={18} className="text-blue-500" />
                                Repository Under Review
                            </h3>
                            <div className="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/50 p-3.5 rounded-xl border border-slate-100 dark:border-slate-800 font-mono text-sm group">
                                <span className="text-slate-600 dark:text-slate-300 truncate flex-1">{reviewData.repository_url}</span>
                                <div className="flex items-center gap-2">
                                    <button 
                                        onClick={() => handleCopyRepo(reviewData.repository_url)}
                                        className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg transition-colors"
                                        title="Copy Link"
                                    >
                                        {copiedRepo ? <Check size={14} className="text-emerald-500" /> : <Copy size={14} />}
                                    </button>
                                    <a 
                                        href={reviewData.repository_url} 
                                        target="_blank" 
                                        rel="noopener noreferrer" 
                                        className="p-1.5 hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg transition-colors"
                                    >
                                        <ExternalLink size={14} />
                                    </a>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Assigned Task block */}
                    <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                        <h3 className="font-black text-lg text-slate-800 dark:text-white mb-2.5 flex items-center gap-2">
                            <FileText size={18} className="text-indigo-500" />
                            Assigned Task
                        </h3>
                        <div className="text-xl font-extrabold text-slate-900 dark:text-white tracking-tight mb-2 uppercase">
                            {reviewData.task_title}
                        </div>
                        <div className="bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 max-h-60 overflow-y-auto text-sm text-slate-600 dark:text-slate-400 leading-relaxed font-sans whitespace-pre-wrap">
                            {reviewData.task_description || 'No task description available.'}
                        </div>
                    </div>

                    {/* Technical Analysis breakdown */}
                    <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                        <h3 className="font-black text-lg text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                            <Activity size={18} className="text-emerald-500" />
                            Technical Analysis Breakdown
                        </h3>
                        <div className="space-y-4">
                            {/* Technical Quality */}
                            <div>
                                <div className="flex justify-between text-xs font-bold text-slate-500 uppercase mb-1">
                                    <span>Technical Quality</span>
                                    <span>{technicalQuality}%</span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${technicalQuality}%` }} />
                                </div>
                            </div>
                            
                            {/* Clarity */}
                            <div>
                                <div className="flex justify-between text-xs font-bold text-slate-500 uppercase mb-1">
                                    <span>Clarity & Depth</span>
                                    <span>{clarity}%</span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: `${clarity}%` }} />
                                </div>
                            </div>
                            
                            {/* Discipline */}
                            <div>
                                <div className="flex justify-between text-xs font-bold text-slate-500 uppercase mb-1">
                                    <span>Discipline & Compliance</span>
                                    <span>{disciplineSignals}%</span>
                                </div>
                                <div className="w-full bg-slate-100 dark:bg-slate-700 h-2 rounded-full overflow-hidden">
                                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${disciplineSignals}%` }} />
                                </div>
                            </div>
                        </div>
                    </div>
                    {/* PAC Binary Signals */}
                    {pac && (
                        <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                            <h3 className="font-black text-lg text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                                <Target size={18} className="text-indigo-500" />
                                PAC Signal Detection
                            </h3>
                            <div className="grid grid-cols-3 gap-3">
                                {Object.entries(pac).map(([key, val]) => (
                                    <div key={key} className={`p-3 rounded-xl border text-center ${
                                        val === 1
                                            ? 'bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-900/40'
                                            : 'bg-rose-50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/40'
                                    }`}>
                                        <div className={`text-lg font-black ${ val === 1 ? 'text-emerald-600 dark:text-emerald-400' : 'text-rose-600 dark:text-rose-400'}`}>
                                            {val === 1 ? '✓' : '✗'}
                                        </div>
                                        <div className="text-[10px] uppercase font-bold text-slate-500 mt-1">{key}</div>
                                    </div>
                                ))}
                            </div>
                            {rubric && (
                                <div className="mt-4 grid grid-cols-3 gap-3">
                                    {Object.entries(rubric).map(([key, val]) => (
                                        <div key={key} className={`p-3 rounded-xl border text-center ${
                                            val === 1
                                                ? 'bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/40'
                                                : 'bg-amber-50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/40'
                                        }`}>
                                            <div className={`text-lg font-black ${ val === 1 ? 'text-blue-600 dark:text-blue-400' : 'text-amber-600 dark:text-amber-400'}`}>
                                                {val === 1 ? '✓' : '✗'}
                                            </div>
                                            <div className="text-[10px] uppercase font-bold text-slate-500 mt-1">{key.replace('has_', '')}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Evaluation Summary (markdown report) */}
                    {reviewData.evaluation_summary && reviewData.evaluation_summary.length > 30 && (
                        <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                            <h3 className="font-black text-lg text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                                <FileText size={18} className="text-purple-500" />
                                Evaluation Summary
                            </h3>
                            <pre className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap leading-relaxed font-sans bg-slate-50 dark:bg-slate-900/50 p-4 rounded-xl border border-slate-100 dark:border-slate-800 max-h-72 overflow-y-auto">
                                {reviewData.evaluation_summary}
                            </pre>
                        </div>
                    )}

                </div>{/* end lg:col-span-2 left column */}

                {/* Right Column - Review Details, Gaps, Recommendations, and Trace Documents */}
                <div className="space-y-6">
                    
                    {/* Issues / Recommendations / Missing Deliverables */}
                    <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md space-y-6">
                        <h3 className="font-black text-lg text-slate-800 dark:text-white pb-2 border-b border-slate-100 dark:border-slate-700 flex items-center gap-2">
                            <Settings size={18} className="text-slate-500" />
                            Deliverables Assessment
                        </h3>

                        {/* Whats Done Well */}
                        {reviewData.whats_done_well?.length > 0 && (
                            <div>
                                <span className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400 block mb-2 flex items-center gap-1">
                                    <CheckCircle size={12} /> What's Done Well
                                </span>
                                <ul className="space-y-2">
                                    {reviewData.whats_done_well.map((item, i) => (
                                        <li key={i} className="text-xs text-emerald-700 dark:text-emerald-400 bg-emerald-50/50 dark:bg-emerald-900/10 p-2.5 rounded-xl border border-emerald-100 dark:border-emerald-900/30 flex items-start gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 flex-shrink-0" />
                                            <span className="leading-normal">{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Missing Deliverables Badges */}
                        <div>
                            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-2">Missing Deliverables</span>
                            {reviewData.missing_features?.length > 0 ? (
                                <div className="flex flex-wrap gap-2">
                                    {reviewData.missing_features.map((feature, i) => (
                                        <span key={i} className="px-2.5 py-1 text-xs font-bold uppercase rounded-lg bg-rose-50 dark:bg-rose-900/25 text-rose-600 dark:text-rose-400 border border-rose-200/50 dark:border-rose-900/50">
                                            {feature}
                                        </span>
                                    ))}
                                </div>
                            ) : (
                                <span className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1">
                                    <CheckCircle size={14} /> 0 missing items
                                </span>
                            )}
                        </div>

                        {/* Failure Reasons list */}
                        {!isPassed && reviewData.failure_reasons?.length > 0 && (
                            <div>
                                <span className="text-[10px] uppercase font-bold text-rose-500 block mb-2 flex items-center gap-1">
                                    <XCircle size={12} /> Critical Failures
                                </span>
                                <ul className="space-y-2">
                                    {reviewData.failure_reasons.map((reason, i) => (
                                        <li key={i} className="text-xs text-rose-700 dark:text-rose-400 bg-rose-50/50 dark:bg-rose-900/10 p-2.5 rounded-xl border border-rose-100 dark:border-rose-900/30 flex items-start gap-2">
                                            <div className="w-1.5 h-1.5 rounded-full bg-rose-500 mt-1.5 flex-shrink-0" />
                                            <span className="leading-normal">{reason}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Recommendations */}
                        <div>
                            <span className="text-[10px] uppercase font-bold text-slate-400 block mb-2">Improvement Recommendations</span>
                            {reviewData.improvement_hints?.length > 0 ? (
                                <ul className="space-y-2">
                                    {reviewData.improvement_hints.map((hint, i) => (
                                        <li key={i} className="text-xs text-slate-700 dark:text-slate-400 flex items-start gap-2 bg-slate-50 dark:bg-slate-900/40 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800">
                                            <div className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 flex-shrink-0" />
                                            <span className="leading-normal">{hint}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <span className="text-sm text-slate-500">No suggestions recorded.</span>
                            )}
                        </div>
                    </div>

                    {/* Runtime Evidence list */}
                    <div className="card bg-white dark:bg-slate-800 p-6 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-md">
                        <h3 className="font-black text-lg text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                            <Settings size={18} className="text-blue-500" />
                            Runtime Evidence Logs
                        </h3>
                        {reviewData.runtime_evidence?.length > 0 ? (
                            <div className="space-y-2">
                                {reviewData.runtime_evidence.map((fileName, i) => (
                                    <div key={i} className="flex items-center justify-between text-xs font-mono bg-slate-50 dark:bg-slate-900/50 p-2.5 rounded-xl border border-slate-100 dark:border-slate-800">
                                        <span className="text-slate-700 dark:text-slate-300 truncate">{fileName}</span>
                                        <span className="text-[10px] uppercase font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/20 px-1.5 py-0.5 rounded">
                                            VERIFIED
                                        </span>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-xs text-slate-500 leading-relaxed">
                                No local trace directory evidence files detected. Ingestion staging only.
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Next Task Recommendation Card */}
            {reviewData.selected_task_id && (
                <div className={`card border-l-4 ${cardBorderColor} bg-white dark:bg-slate-800 shadow-md p-6 rounded-2xl flex flex-col justify-between overflow-hidden`}>
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="font-black text-lg text-slate-800 dark:text-white flex items-center gap-2">
                                <Target size={18} className="text-indigo-500 animate-pulse" />
                                Recommended Niyantran Corrective Task
                            </h3>
                            <p className="text-xs text-slate-400 mt-0.5">Automated graph routing dispatch suggestion</p>
                        </div>
                        <span className="text-xs font-bold uppercase bg-slate-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg">
                            {reviewData.next_task_difficulty || 'beginner'}
                        </span>
                    </div>

                    <div className="space-y-4">
                        <div className="bg-white dark:bg-slate-900 p-4 rounded-xl border border-slate-100 dark:border-slate-800">
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-mono text-sm font-bold text-indigo-600 dark:text-indigo-400">{reviewData.selected_task_id}</span>
                                <span className="text-xs px-2 py-0.5 bg-slate-100 dark:bg-slate-800 rounded font-semibold uppercase">{reviewData.next_task_focus_area || 'general'}</span>
                            </div>
                            <div className="font-bold text-slate-900 dark:text-white text-base mb-1">
                                {reviewData.next_task_title || `Corrective Assignment: ${reviewData.selected_task_id}`}
                            </div>
                            <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">
                                {reviewData.next_task_objective || 'Complete the corrective routing task in the project.'}
                            </p>
                        </div>

                        {reviewData.selection_reason && (
                            <div className="text-xs text-slate-500 bg-slate-50 dark:bg-slate-900/30 p-3 rounded-lg leading-relaxed">
                                <span className="font-bold text-slate-700 dark:text-slate-400 block mb-1">Routing Justification</span>
                                {reviewData.selection_reason}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Action Buttons Row */}
            <div className="flex flex-wrap gap-4 pt-4">
                <button
                    onClick={() => navigate(`/next/${taskId}`)}
                    className="px-6 py-3.5 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-lg shadow-blue-500/20 hover:scale-[1.01] active:scale-[0.99] transition-all flex items-center gap-2"
                >
                    <Target size={18} /> View Recommended Task Details
                </button>
                <button
                    onClick={() => navigate('/history')}
                    className="px-6 py-3.5 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 text-slate-900 dark:text-white font-bold rounded-xl transition-all"
                >
                    View Submission History
                </button>
                <button
                    onClick={() => navigate('/')}
                    className="px-6 py-3.5 bg-transparent border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-850 text-slate-700 dark:text-slate-300 font-bold rounded-xl transition-all"
                >
                    Go back to Dashboard
                </button>
            </div>
        </div>
    );
};

export default ReviewResult;
