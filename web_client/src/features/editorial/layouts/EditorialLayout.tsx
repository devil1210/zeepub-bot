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
    Search,
    UploadCloud,
    ArrowLeft,
    Sparkles,
    Menu,
    X,
    Table,
    BrainCircuit,
    Building2,
    GitMerge,
    Tags,
    Activity,
    Sliders
} from 'lucide-react';
import { GlobalSearchModal } from '../components/GlobalSearchModal';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface EditorialLayoutProps {
    children: React.ReactNode;
}

export const EditorialLayout: React.FC<EditorialLayoutProps> = ({ children }) => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, isAdmin, isStaff } = useTelegram();
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

    const navSections = [
        {
            title: 'GENERAL',
            items: [
                { path: '/app-v2', label: 'Centro de Control', icon: LayoutDashboard, exact: true },
            ],
        },
        {
            title: 'BIBLIOTECA & CATÁLOGO',
            items: [
                { path: '/app-v2/volumes', label: 'Matriz de Volúmenes & EPUBs', icon: BookOpen },
                { path: '/app-v2/series', label: 'Catálogo & DataGrid de Series', icon: Layers },
            ],
        },
        {
            title: 'PUBLICACIÓN & REDES',
            items: [
                { path: '/app-v2/calendar', label: 'Agenda & Calendario', icon: Calendar },
                { path: '/app-v2/posts', label: 'Historial de Posts', icon: Send },
                { path: '/app-v2/templates', label: 'Plantillas & Rich Messages', icon: FileCode2 },
                { path: '/app-v2/fansubs', label: 'Directorio de Fansubs', icon: Building2, adminOnly: true },
            ],
        },
        {
            title: 'HERRAMIENTAS & SISTEMA',
            items: [
                { path: '/app-v2/ai', label: 'Hub de IA (Gemini)', icon: BrainCircuit, adminOnly: true },
                { path: '/app-v2/duplicates', label: 'Gestor de Duplicados & Hash', icon: GitMerge, adminOnly: true },
                { path: '/app-v2/observatory', label: 'Observatorio del Sistema', icon: Activity, adminOnly: true },
                { path: '/app-v2/users', label: 'Usuarios y Permisos', icon: Users, adminOnly: true },
                { path: '/app-v2/settings', label: 'Configuración & Logs', icon: Settings },
            ],
        },
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
            {/* Desktop & Mobile Sidebar (Widescreen optimized: 280px / 320px on 2K) */}
            <aside
                className={`fixed inset-y-0 left-0 z-40 w-64 xl:w-72 2xl:w-80 bg-slate-950/90 backdrop-blur-2xl border-r border-white/10 flex flex-col transition-transform duration-300 md:translate-x-0 ${
                    isMobileSidebarOpen ? 'translate-x-0' : '-translate-x-full'
                }`}
            >
                {/* Brand Logo & Version Pill */}
                <div className="p-5 xl:p-6 border-b border-white/10 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-600/30 shrink-0">
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

                {/* Categorized Navigation Links */}
                <nav className="flex-1 overflow-y-auto px-3 xl:px-4 py-4 space-y-6 scrollbar-thin">
                    {navSections.map((section) => (
                        <div key={section.title} className="space-y-1">
                            <div className="px-3 text-[10px] font-black tracking-widest text-gray-500 uppercase mb-2">
                                {section.title}
                            </div>
                            {section.items.map((item) => {
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
                                        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-white' : 'text-gray-400'}`} />
                                        <span className="truncate">{item.label}</span>
                                    </NavLink>
                                );
                            })}
                        </div>
                    ))}
                </nav>

                {/* Switch back to v1 & User profile */}
                <div className="p-4 xl:p-5 border-t border-white/10 bg-slate-950/60 space-y-3 shrink-0">
                    <button
                        onClick={() => navigate('/')}
                        className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-white/[0.04] hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/5 transition-all"
                    >
                        <ArrowLeft className="w-3.5 h-3.5" />
                        Vista Clásica (v1)
                    </button>

                    <div className="flex items-center gap-3 px-2 py-1">
                        <div className="w-8 h-8 rounded-full bg-slate-800 border border-white/10 flex items-center justify-center text-xs font-bold text-indigo-400 shrink-0">
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

            {/* Main Content Area (Fluid 2K / 4K widescreen responsive layout) */}
            <div className="flex-1 flex flex-col md:pl-64 xl:pl-72 2xl:pl-80 h-full overflow-hidden">
                {/* Topbar Header */}
                <header className="h-16 border-b border-white/10 bg-slate-950/60 backdrop-blur-xl px-4 sm:px-8 xl:px-10 flex items-center justify-between shrink-0 z-30">
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
                            className="flex items-center gap-3 px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 text-gray-400 text-xs font-medium transition-all group w-64 sm:w-80 lg:w-96"
                        >
                            <Search className="w-4 h-4 text-gray-400 group-hover:text-white" />
                            <span className="hidden sm:inline truncate">Buscar en la consola editorial...</span>
                            <span className="sm:hidden">Buscar...</span>
                            <kbd className="hidden sm:inline ml-auto text-[10px] bg-black/40 px-2 py-0.5 rounded border border-white/10 text-gray-400 font-mono">
                                ⌘K
                            </kbd>
                        </button>
                    </div>

                    {/* Quick Actions */}
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => navigate('/upload')}
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/20 active:scale-95 transition-all"
                        >
                            <UploadCloud className="w-4 h-4" />
                            <span className="hidden sm:inline">Subir EPUB</span>
                        </button>
                    </div>
                </header>

                {/* Viewport Content with full 2K utilization */}
                <main className="flex-1 overflow-y-auto bg-gradient-to-b from-[#0f1422] to-[#0a0d14] p-4 sm:p-6 lg:p-8 2xl:p-10 scrollbar-thin">
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
