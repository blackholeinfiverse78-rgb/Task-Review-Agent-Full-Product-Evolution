import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, PlusCircle, History, Zap, ShieldCheck } from 'lucide-react';
import ThemeToggle from './ThemeToggle';

const Navbar = () => {
    const location = useLocation();

    const navLinks = [
        { name: 'Dashboard', path: '/', icon: <LayoutDashboard size={20} /> },
        { name: 'Submit Task', path: '/submit', icon: <PlusCircle size={20} /> },
        { name: 'Task History', path: '/history', icon: <History size={20} /> },
        { name: 'Review Queue', path: '/review-queue', icon: <ShieldCheck size={20} /> },
    ];

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="sticky top-0 z-50 glass-morphism border-b border-slate-200 dark:border-slate-800">
            <div className="container mx-auto px-4 h-16 flex items-center justify-between">
                <Link to="/" className="flex items-center gap-2 group">
                    <div className="p-2 bg-blue-600 rounded-xl group-hover:rotate-12 transition-transform duration-300">
                        <Zap className="text-white" size={24} />
                    </div>
                    <span className="text-xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 bg-clip-text text-transparent">
                        Parikshak
                    </span>
                </Link>

                <div className="hidden md:flex items-center gap-6">
                    {navLinks.map((link) => (
                        <Link
                            key={link.path}
                            to={link.path}
                            className={`flex items-center gap-2 px-3 py-2 rounded-lg font-medium transition-colors duration-200 ${isActive(link.path)
                                    ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/30'
                                    : 'text-slate-600 dark:text-slate-400 hover:text-blue-600 dark:hover:text-blue-400'
                                }`}
                        >
                            {link.icon}
                            {link.name}
                        </Link>
                    ))}
                    <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 mx-2" />
                    <ThemeToggle />
                </div>

                {/* Mobile Navigation Placeholder */}
                <div className="md:hidden flex items-center gap-4">
                    <ThemeToggle />
                </div>
            </div>
        </nav>
    );
};

export default Navbar;