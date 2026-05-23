import React from 'react';
import { Plus } from 'lucide-react';

const SimpleApp = () => {
    return (
        <div className="min-h-screen bg-slate-50 flex items-center justify-center">
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-slate-900">
                    Parikshak
                </h1>
                <p className="text-slate-600">
                    Enterprise-grade autonomous evaluation system
                </p>
                <button className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2 mx-auto">
                    <Plus size={20} />
                    Get Started
                </button>
            </div>
        </div>
    );
};

export default SimpleApp;