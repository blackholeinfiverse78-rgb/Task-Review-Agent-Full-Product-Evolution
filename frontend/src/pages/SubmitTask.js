import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Upload, FileText, X, Settings, Code, AlertTriangle, Info } from 'lucide-react';
import ConnectionStatus from '../components/ConnectionStatus';

const SubmitTask = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        task_title: '',
        task_description: '',
        submitted_by: '',
        github_repo_link: '',
        module_id: 'task-review-agent',
        schema_version: 'v1.0'
    });
    const [pdfFile, setPdfFile] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [validationErrors, setValidationErrors] = useState({});
    const [showDeliverables, setShowDeliverables] = useState(false);

    // Available modules from the registry - schema_version must match registry
    const availableModules = [
        { id: 'task-review-agent',       name: 'Parikshak',        schema: 'v1.0', description: 'General task review and evaluation' },
        { id: 'core-development',        name: 'Core Development',         schema: 'v1.0', description: 'Core system development tasks' },
        { id: 'advanced-features',       name: 'Advanced Features',        schema: 'v1.0', description: 'Advanced feature implementation' },
        { id: 'system-integration',      name: 'System Integration',       schema: 'v1.0', description: 'System integration and connectivity' },
        { id: 'performance-optimization',name: 'Performance Optimization', schema: 'v1.0', description: 'Performance tuning and optimization' },
        { id: 'security-implementation', name: 'Security Implementation',  schema: 'v1.0', description: 'Security features and hardening' },
        { id: 'evaluation-engine',       name: 'Evaluation Engine',        schema: 'v3.0', description: 'Evaluation and scoring systems' },
        { id: 'lifecycle-orchestrator',  name: 'Lifecycle Orchestrator',   schema: 'v1.1', description: 'Lifecycle management and orchestration' }
    ];

    const availableSchemaVersions = [
        { version: 'v1.0', name: 'Version 1.0' },
        { version: 'v1.1', name: 'Version 1.1' },
        { version: 'v3.0', name: 'Version 3.0' }
    ];

    // Auto-sync schema_version when module changes
    const handleModuleChange = (e) => {
        const selectedMod = availableModules.find(m => m.id === e.target.value);
        setFormData(prev => ({
            ...prev,
            module_id: e.target.value,
            schema_version: selectedMod ? selectedMod.schema : 'v1.0'
        }));
    };

    // Strict input validation
    const validateInputs = () => {
        const errors = {};
        
        // GitHub URL validation - must be repository, not profile
        if (formData.github_repo_link) {
            const githubRepoPattern = /^https:\/\/github\.com\/[^/]+\/[^/]+\/?$/;
            if (!githubRepoPattern.test(formData.github_repo_link)) {
                errors.github_repo_link = 'Must be a valid GitHub repository URL (not profile)';
            }
        }
        
        // Module ID validation - must be selected
        if (!formData.module_id || formData.module_id === '') {
            errors.module_id = 'Module selection is required';
        }
        
        // Schema version validation
        if (!formData.schema_version || formData.schema_version === '') {
            errors.schema_version = 'Schema version selection is required';
        }
        
        return errors;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        // Strict validation before API call
        const errors = validateInputs();
        if (Object.keys(errors).length > 0) {
            setValidationErrors(errors);
            return;
        }
        
        setValidationErrors({});
        setIsSubmitting(true);
        
        try {
            const { taskService } = await import('../services/taskService');
            const result = await taskService.submitTask({
                ...formData,
                pdf_file: pdfFile || undefined
            });
            navigate(`/review/${result.submission_id}`);
        } catch (error) {
            const detail = error.response?.data?.detail || error.message;
            alert(`Submission failed: ${detail}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file && file.type === 'application/pdf') {
            setPdfFile(file);
        } else if (file) {
            alert('Please select a PDF file only.');
            e.target.value = '';
        }
    };

    const removePdfFile = () => {
        setPdfFile(null);
        const fileInput = document.getElementById('pdf_file');
        if (fileInput) fileInput.value = '';
    };

    const selectedModule = availableModules.find(m => m.id === formData.module_id);

    return (
        <div className="max-w-2xl mx-auto space-y-8">
            <header className="text-center">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">
                    Submit New Task
                </h1>
                <p className="text-slate-600 dark:text-slate-400">
                    Submit your project for comprehensive evaluation
                </p>
            </header>

            <div className="flex justify-center">
                <ConnectionStatus />
            </div>

            {/* Expected Deliverables Section */}
            <div className="card">
                <button
                    type="button"
                    onClick={() => setShowDeliverables(!showDeliverables)}
                    className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors"
                >
                    <div className="flex items-center gap-2">
                        <Info className="text-blue-500" size={20} />
                        <span className="font-medium text-slate-700 dark:text-slate-300">
                            Expected Deliverables & Requirements
                        </span>
                    </div>
                    <div className={`transform transition-transform ${showDeliverables ? 'rotate-180' : ''}`}>
                        ▼
                    </div>
                </button>
                
                {showDeliverables && (
                    <div className="px-4 pb-4 border-t border-slate-200 dark:border-slate-700">
                        <div className="mt-4 space-y-3 text-sm text-slate-600 dark:text-slate-400">
                            <div>
                                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">For High Scores (80-100):</h4>
                                <ul className="list-disc list-inside space-y-1 ml-2">
                                    <li>Technical title with specific keywords</li>
                                    <li>Detailed description with implementation specifics</li>
                                    <li>Active GitHub repository with recent commits</li>
                                    <li>Clear requirements and acceptance criteria</li>
                                    <li>Architecture documentation or README</li>
                                </ul>
                            </div>
                            <div>
                                <h4 className="font-medium text-slate-700 dark:text-slate-300 mb-2">Common Issues to Avoid:</h4>
                                <ul className="list-disc list-inside space-y-1 ml-2">
                                    <li>Vague or generic task titles</li>
                                    <li>Missing technical implementation details</li>
                                    <li>Empty or inactive repositories</li>
                                    <li>Unclear success criteria</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="card space-y-6">
                {/* Module Selection */}
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        <Settings className="inline w-4 h-4 mr-1" />
                        Module Selection *
                    </label>
                    <select
                        name="module_id"
                        value={formData.module_id}
                        onChange={handleModuleChange}
                        required
                        className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white"
                    >
                        {availableModules.map(module => (
                            <option key={module.id} value={module.id}>
                                {module.name} ({module.schema}) - {module.description}
                            </option>
                        ))}
                    </select>
                    {selectedModule && (
                        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                            Schema version auto-set to <strong>{selectedModule.schema}</strong> for this module
                        </p>
                    )}
                </div>

                {/* Schema Version - auto-set from module, read-only */}
                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        <Code className="inline w-4 h-4 mr-1" />
                        Schema Version (auto-set)
                    </label>
                    <input
                        type="text"
                        value={formData.schema_version}
                        readOnly
                        className="w-full px-4 py-3 border border-slate-200 dark:border-slate-700 rounded-lg bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400 cursor-not-allowed"
                    />
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Automatically set based on selected module
                    </p>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Task Title *
                    </label>
                    <input
                        type="text"
                        name="task_title"
                        value={formData.task_title}
                        onChange={handleChange}
                        required
                        minLength={5}
                        maxLength={100}
                        className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white"
                        placeholder="Enter your task title (5-100 characters)"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Task Description *
                    </label>
                    <textarea
                        name="task_description"
                        value={formData.task_description}
                        onChange={handleChange}
                        required
                        minLength={10}
                        maxLength={100000}
                        rows={6}
                        className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white"
                        placeholder="Describe your task in detail (10-100000 characters)"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        Submitted By *
                    </label>
                    <input
                        type="text"
                        name="submitted_by"
                        value={formData.submitted_by}
                        onChange={handleChange}
                        required
                        minLength={2}
                        maxLength={50}
                        className="w-full px-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white"
                        placeholder="Your name (2-50 characters)"
                    />
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        GitHub Repository Link
                    </label>
                    <input
                        type="url"
                        name="github_repo_link"
                        value={formData.github_repo_link}
                        onChange={handleChange}
                        className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-slate-800 dark:text-white ${
                            validationErrors.github_repo_link 
                                ? 'border-red-500 dark:border-red-400' 
                                : 'border-slate-300 dark:border-slate-600'
                        }`}
                        placeholder="https://github.com/username/repository"
                    />
                    {validationErrors.github_repo_link && (
                        <p className="text-red-500 text-sm mt-1 flex items-center gap-1">
                            <AlertTriangle size={14} />
                            {validationErrors.github_repo_link}
                        </p>
                    )}
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
                        Must be repository URL, not user profile
                    </p>
                </div>

                <div>
                    <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                        PDF Document (Optional)
                    </label>
                    <div className="space-y-3">
                        {!pdfFile ? (
                            <div className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                                <input
                                    type="file"
                                    id="pdf_file"
                                    accept=".pdf"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                                <label
                                    htmlFor="pdf_file"
                                    className="cursor-pointer flex flex-col items-center gap-2"
                                >
                                    <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
                                        <Upload className="text-blue-600 dark:text-blue-400" size={24} />
                                    </div>
                                    <div>
                                        <p className="font-medium text-slate-700 dark:text-slate-300">
                                            Click to upload PDF
                                        </p>
                                        <p className="text-sm text-slate-500 dark:text-slate-400">
                                            Upload project documentation, requirements, or specifications
                                        </p>
                                    </div>
                                </label>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                                <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded-lg">
                                    <FileText className="text-green-600 dark:text-green-400" size={20} />
                                </div>
                                <div className="flex-1">
                                    <p className="font-medium text-green-800 dark:text-green-200">
                                        {pdfFile.name}
                                    </p>
                                    <p className="text-sm text-green-600 dark:text-green-400">
                                        {(pdfFile.size / 1024 / 1024).toFixed(2)} MB
                                    </p>
                                </div>
                                <button
                                    type="button"
                                    onClick={removePdfFile}
                                    className="p-1 text-green-600 dark:text-green-400 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                                >
                                    <X size={20} />
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    {isSubmitting ? (
                        <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                            Submitting...
                        </>
                    ) : (
                        <>
                            <Send size={20} />
                            Submit Task
                        </>
                    )}
                </button>
            </form>
        </div>
    );
};

export default SubmitTask;