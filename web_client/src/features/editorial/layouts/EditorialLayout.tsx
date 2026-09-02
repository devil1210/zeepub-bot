import React, { useState } from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
    LayoutDashboard,
    BookOpen,
    Layers,
    Calendar,
    Send,
    FileCode2,
    Users,
    Settings,
    Wrench,
    Search,
    UploadCloud,
    ArrowLeft,
    Sparkles,
    Menu,
    X
} from 'lucide-react';
import { GlobalSearchModal } from '../components/GlobalSearchModal';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface EditorialLayoutProps {
    children: React.ReactNode;
}

export const EditorialLayout: React.FC<EditorialLayoutProps> = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, isAdmin } = useTelegram();
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    const navItems = [
        { path: '/app-v2', label: 'Dashboard', icon: LayoutDashboard, exact: true },
        { path: '/app-v2/library', label: 'Biblioteca EPUBs', icon: BookOpen },
        { path: '/app-v2/series', label: 'Series', icon: Layers },
        { path: '/app-v2/volumes', label: 'Volúmenes', icon: BookOpen },
        { path: '/app-v2/calendar', label: 'Calendario', icon: Calendar },
        { path: '/app-v2/posts', label: 'Publicaciones', icon: Send },
        { path: '/app-v2/templates', label: 'Plantillas', icon: FileCode2 },
        { path: '/app-v2/users', label: 'Usuarios', icon: Users, adminOnly: true },
        { path: '/app-v2/settings', label: 'Ajustes & Logs', icon: Settings },
        { path: '/app-v2/legacy', label: 'Herramientas Admin', icon: Wrench, adminOnly: true },
    ];

    const handleGlobalSearchSelect = (type: 'epub' | 'series' | 'volume', id: string) => {
        if (type === 'series') {
            navigate(`/app-v2/series?highlight=${id}`);
        } else if (type === 'volume' || type === 'epub') {
            navigate(`/app-v2/volumes?highlight=${id}`);
        }
    };

    return (
        <div className="flex h-screen bg-[#0a0d14] text-gray-100 overflow-hidden font-sans">
            {/* Desktop & Mobile Sidebar */}
            <aside
                className={`fixed inset-y-0 left-0 z-40 w-64 bg-slate-950/80 backdrop-blur-2xl border-r border-white/10 flex flex-col transition-transform duration-300 md:translate-x-0 ${
                    isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                {/* Brand Logo & Version Pill */}
                <div className="p-5 border-b border-white/10 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/30">
                            <Sparkles className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h1 className="text-base font-black tracking-wider text-white">ZEEPUB</h1>
                            <span className="text-[9px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                Consola Editorial v2
                            </span>
                        </div>
                    </div>
                    <button
                        onClick={() => setIsMobileSidebarOpen(false)}
                        className="p-1 md:hidden text-gray-400 hover:text-white"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Nav Links */}
                <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
                    {navItems.map((item) => {
                        if (item.adminOnly && !isAdmin) return null;
                        const Icon = item.icon;
                        const isActive = item.exact
                            ? location.pathname === item.path
                            : location.pathname.startsWith(item.path);

                        return (
                            <NavLink
                                key={item.path}
                                to={item.path}
                                onClick={() => setIsMobileSidebarOpen(false)}
                                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-bold transition-all ${
                                    isActive
                                        ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-extrabold'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                                <span>{item.label}</span>
                            </NavLink>
                        );
                    })}
                </nav>

                {/* Switch back to v1 & User profile */}
                <div className="p-4 border-t border-white/10 bg-slate-950/40 space-y-3">
                    <button
                        onClick={() => navigate('/')}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-white/[0.04] hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/5 transition-all"
                    >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        Vista Clásica (v1)
                    </button>

                    <div className="flex items-center gap-2.5 px-2 py-1">
                        <div className="w-7 h-7 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-xs font-bold text-indigo-400">
                            {user?.first_name?.[0] || 'A'}
                        </div>
                        <div className="min-w-0 flex-1">
                            <div className="text-xs font-bold text-white truncate">
                                {user?.first_name || 'Admin Editorial'}
                            </div>
                            <div className="text-[10px] text-gray-500 uppercase tracking-widest truncate">
                                {isAdmin ? '👑 Super Admin' : '📖 Editor Staff'}
                            </div>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main Content Area */}
            <div className="flex-1 flex flex-col md:pl-64 h-full overflow-hidden">
                {/* Topbar */}
                <header className="h-16 border-b border-white/10 bg-slate-950/60 backdrop-blur-xl px-4 sm:px-8 flex items-center justify-between shrink-0 z-30">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => setIsMobileSidebarOpen(true)}
                            className="p-2 md:hidden text-gray-400 hover:text-white rounded-lg hover:bg-white/5"
                        >
                            <Menu className="w-5 h-5" />
                        </button>

                        {/* Search Trigger */}
                        <button
                            onClick={() => setIsSearchOpen(true)}
                            className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-gray-400 text-xs font-medium transition-all group"
                        >
                            <Search className="w-4 h-4 text-gray-400 group-hover:text-white" />
                            <span className="hidden sm:inline">Buscar en la consola editorial...</span>
                            <span className="sm:hidden">Buscar...</span>
                            <kbd className="hidden sm:inline text-[10px] bg-black/40 px-2 py-0.5 rounded border border-white/10 text-gray-400">
                                ⌘K
                            </kbd>
                        </button>
                    </div>

                    {/* Quick Action Buttons */}
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => navigate('/upload')}
                            className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20 active:scale-95 transition-all"
                        >
                            <UploadCloud className="w-4 h-4" />
                            <span className="hidden sm:inline">Subir EPUB</span>
                        </button>
                    </div>
                </header>

                {/* Viewport Content */}
                <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#0f1422] to-[#0a0d14] p-4 sm:p-8">
                    {children}
                </main>
            </div>

            {/* Global Search Modal */}
            <GlobalSearchModal
                isOpen={isSearchOpen}
                onClose={() => setIsSearchOpen(false)}
                onSelect={handleGlobalSearchSelect}
            />
        </div>
    );
};
