import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from './contexts/ThemeContext';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import SubmitTask from './pages/SubmitTask';
import ReviewResult from './pages/ReviewResult';
import NextTask from './pages/NextTask';
import TaskHistory from './pages/TaskHistory';
import ReviewDashboard from './pages/ReviewDashboard';
import './index.css';

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            refetchOnWindowFocus: false,
            retry: 1,
            staleTime: 30000,
        },
    },
});

function App() {
    return (
        <ErrorBoundary>
            <QueryClientProvider client={queryClient}>
                <ThemeProvider>
                    <Router>
                        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 transition-colors duration-200">
                            <Navbar />
                            <main className="container mx-auto px-4 py-8">
                                <Routes>
                                    <Route path="/" element={<Dashboard />} />
                                    <Route path="/submit" element={<SubmitTask />} />
                                    <Route path="/review/:taskId" element={<ReviewResult />} />
                                    <Route path="/next/:taskId" element={<NextTask />} />
                                    <Route path="/history" element={<TaskHistory />} />
                                    <Route path="/review-queue" element={<ReviewDashboard />} />
                                </Routes>
                            </main>
                        </div>
                    </Router>
                </ThemeProvider>
            </QueryClientProvider>
        </ErrorBoundary>
    );
}

export default App;