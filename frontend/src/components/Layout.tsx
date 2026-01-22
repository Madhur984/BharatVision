import type { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    Search,
    Upload,
    BarChart3,
    Settings,
    HelpCircle,
} from 'lucide-react';

interface LayoutProps {
    children: ReactNode;
}

const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/crawler', icon: Search, label: 'Web Crawler' },
    { path: '/upload', icon: Upload, label: 'OCR Upload' },
    { path: '/analytics', icon: BarChart3, label: 'Analytics' },
    { path: '/settings', icon: Settings, label: 'Settings' },
    { path: '/help', icon: HelpCircle, label: 'Help' },
];

export default function Layout({ children }: LayoutProps) {
    const location = useLocation();

    return (
        <div className="flex h-screen bg-gray-50">
            {/* Sidebar */}
            <aside className="w-64 bg-navy text-white flex flex-col">
                {/* Logo/Header */}
                <div className="p-6 border-b border-white/20">
                    <div className="text-xs font-bold mb-1">🇮🇳 Government of India</div>
                    <h1 className="text-xl font-extrabold leading-tight">
                        भारत Vision
                    </h1>
                    <p className="text-xs mt-1 opacity-90">Legal Metrology</p>
                    <p className="text-xs opacity-75">E-Commerce Compliance Console</p>
                </div>

                {/* Navigation */}
                <nav className="flex-1 p-4">
                    <ul className="space-y-2">
                        {navItems.map((item) => {
                            const Icon = item.icon;
                            const isActive = location.pathname === item.path;
                            return (
                                <li key={item.path}>
                                    <Link
                                        to={item.path}
                                        className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${isActive
                                            ? 'bg-white text-navy font-semibold'
                                            : 'hover:bg-white/10'
                                            }`}
                                    >
                                        <Icon size={20} />
                                        <span>{item.label}</span>
                                    </Link>
                                </li>
                            );
                        })}
                    </ul>
                </nav>

                {/* Footer */}
                <div className="p-4 border-t border-white/20 text-xs opacity-75">
                    <p>Ministry of Consumer Affairs</p>
                    <p>Legal Metrology Division</p>
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto">
                <div className="p-8">{children}</div>
            </main>
        </div>
    );
}
