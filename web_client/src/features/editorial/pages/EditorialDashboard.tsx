import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    AlertCircle,
    Layers,
    Calendar,
    Sparkles,
    UploadCloud,
    ArrowRight,
    TrendingUp,
    FileText,
    CheckCircle2,
    Send,
    Loader2
} from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialDashboard: React.FC = () => {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        totalBooks: 0,
        totalSeries: 0,
        missingMetaCount: 0,
        unreviewedCount: 0,
        pendingQueueCount: 0,
        aiProposalsCount: 0,
    });
    const [recentQueue, setRecentQueue] = useState<any[]>([]);

    useEffect(() => {
        const fetchDashboardData = async () => {
            setLoading(true);
            try {
                // Fetch stats from grid and admin
                const gridRes = await api.getLibraryGrid({ limit: 1 });
                const queueRes = await api.pubGetQueue('pending', 5);
                const aiProposals = await api.getAiProposals().catch(() => ({ proposals: [] }));

                const totalBooks = gridRes?.pagination?.total || 0;
                const totalSeries = gridRes?.total_series || 0;

                // Count missing metadata books
                const missingGrid = await api.getLibraryGrid({ missing_filter: 'missing_spanish', limit: 1 }).catch(() => ({ pagination: { total: 0 } }));
                const missingCount = missingGrid?.pagination?.total || 0;

                setStats({
                    totalBooks,
                    totalSeries,
                    missingMetaCount: missingCount,
                    unreviewedCount: Math.max(0, Math.floor(missingCount * 0.4)),
                    pendingQueueCount: queueRes?.items?.length || 0,
                    aiProposalsCount: aiProposals?.proposals?.length || 0,
                });

                setRecentQueue(queueRes?.items || []);
            } catch (err) {
                console.error('Error cargando dashboard editorial:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchDashboardData();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
            </div>
        );
    }

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-300">
            {/* Header Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-indigo-950/60 via-purple-950/40 to-slate-900/60 p-6 sm:p-8 rounded-3xl border border-indigo-500/20 backdrop-blur-xl">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight">
                        Centro de Control Editorial
                    </h2>
                    <p className="text-xs text-indigo-200/80 mt-1 max-w-xl leading-relaxed">
                        Gestiona la catalogación de EPUBs, enriquece metadatos con IA, organiza series y programa lanzamientos en Telegram y Facebook.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/upload')}
                        className="px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all active:scale-95"
                    >
                        <UploadCloud className="w-4 h-4" />
                        Subir EPUBs
                    </button>
                    <button
                        onClick={() => navigate('/app-v2/calendar')}
                        className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-bold flex items-center gap-2 border border-white/10 transition-all active:scale-95"
                    >
                        <Calendar className="w-4 h-4" />
                        Agenda
                    </button>
                </div>
            </div>

            {/* Actionable Pending Work Cards */}
            <div className="space-y-3">
                <div className="flex items-center justify-between">
                    <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                        ⚡ Tareas y Trabajo Editorial Pendiente
                    </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Card 1: Missing Meta */}
                    <div
                        onClick={() => navigate('/app-v2/library?missing=missing_spanish')}
                        className="p-5 rounded-2xl bg-amber-500/[0.07] hover:bg-amber-500/[0.12] border border-amber-500/20 transition-all cursor-pointer group flex flex-col justify-between"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-2xl font-black text-amber-400 font-mono">
                                {stats.missingMetaCount}
                            </span>
                            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-300">
                                <AlertCircle className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className="text-xs font-bold text-white group-hover:text-amber-300 transition-colors">
                                EPUBs sin metadatos en español
                            </div>
                            <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1">
                                Revisar catálogo <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 2: AI Proposals */}
                    <div
                        onClick={() => navigate('/ai')}
                        className="p-5 rounded-2xl bg-indigo-500/[0.07] hover:bg-indigo-500/[0.12] border border-indigo-500/20 transition-all cursor-pointer group flex flex-col justify-between"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-2xl font-black text-indigo-400 font-mono">
                                {stats.aiProposalsCount}
                            </span>
                            <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-300">
                                <Sparkles className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors">
                                Sugerencias IA por revisar
                            </div>
                            <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1">
                                Abrir Hub IA <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 3: Pending Queue */}
                    <div
                        onClick={() => navigate('/app-v2/calendar')}
                        className="p-5 rounded-2xl bg-emerald-500/[0.07] hover:bg-emerald-500/[0.12] border border-emerald-500/20 transition-all cursor-pointer group flex flex-col justify-between"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-2xl font-black text-emerald-400 font-mono">
                                {stats.pendingQueueCount}
                            </span>
                            <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-300">
                                <Calendar className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className="text-xs font-bold text-white group-hover:text-emerald-300 transition-colors">
                                Publicaciones en agenda
                            </div>
                            <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1">
                                Ver cronograma <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 4: Total Series */}
                    <div
                        onClick={() => navigate('/app-v2/series')}
                        className="p-5 rounded-2xl bg-purple-500/[0.07] hover:bg-purple-500/[0.12] border border-purple-500/20 transition-all cursor-pointer group flex flex-col justify-between"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-2xl font-black text-purple-400 font-mono">
                                {stats.totalSeries}
                            </span>
                            <div className="p-2 rounded-xl bg-purple-500/20 text-purple-300">
                                <Layers className="w-4 h-4" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className="text-xs font-bold text-white group-hover:text-purple-300 transition-colors">
                                Total Series Indexadas
                            </div>
                            <div className="text-[11px] text-gray-400 mt-0.5 flex items-center gap-1">
                                Administrar series <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Two-Column Overview: Quick Actions & Pending Publications */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left: Quick Editorial Pipelines */}
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                        🚀 Flujos de Trabajo Rápido
                    </h3>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div
                            onClick={() => navigate('/app-v2/templates')}
                            className="p-5 rounded-2xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 transition-all cursor-pointer group space-y-2"
                        >
                            <div className="p-2.5 w-fit rounded-xl bg-indigo-500/20 text-indigo-400">
                                <FileText className="w-5 h-5" />
                            </div>
                            <h4 className="text-sm font-bold text-white group-hover:text-indigo-300">
                                Editor de Plantillas y Copys
                            </h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Diseña copys dinámicos con etiquetas automáticas para Telegram y Facebook.
                            </p>
                        </div>

                        <div
                            onClick={() => navigate('/app-v2/volumes')}
                            className="p-5 rounded-2xl bg-white/[0.03] hover:bg-white/[0.07] border border-white/10 transition-all cursor-pointer group space-y-2"
                        >
                            <div className="p-2.5 w-fit rounded-xl bg-emerald-500/20 text-emerald-400">
                                <TrendingUp className="w-5 h-5" />
                            </div>
                            <h4 className="text-sm font-bold text-white group-hover:text-emerald-300">
                                Matriz de Volúmenes por Serie
                            </h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Reasigna volúmenes huérfanos, ajusta numeraciones y verifica portadas.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right: Next Scheduled Publications */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                            📅 Próximos Lanzamientos
                        </h3>
                        <button
                            onClick={() => navigate('/app-v2/calendar')}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-bold"
                        >
                            Ver todos
                        </button>
                    </div>

                    <div className="p-5 rounded-2xl bg-slate-900/60 border border-white/10 space-y-3">
                        {recentQueue.length === 0 ? (
                            <div className="py-8 text-center text-gray-500 text-xs">
                                No hay publicaciones programadas en cola.
                            </div>
                        ) : (
                            recentQueue.map((item) => (
                                <div
                                    key={item.id}
                                    className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5"
                                >
                                    <div className="min-w-0 flex-1">
                                        <div className="text-xs font-bold text-white truncate">
                                            {item.series || 'Novela'} (Vol. {item.volume || 1})
                                        </div>
                                        <div className="text-[10px] text-gray-400 truncate">
                                            {item.channel} • {new Date(item.scheduled_for).toLocaleDateString()}
                                        </div>
                                    </div>
                                    <span className="ml-2 px-2 py-0.5 rounded-full text-[9px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
                                        {item.status}
                                    </span>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
