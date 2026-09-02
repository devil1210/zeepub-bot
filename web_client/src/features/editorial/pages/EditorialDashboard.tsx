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
    Loader2,
    BookOpen,
    Table,
    BrainCircuit
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
                const queueRes = await api.pubGetQueue('pending', 6);
                const aiProposals = await api.getAiProposals().catch(() => ({ proposals: [] }));

                const totalBooks = gridRes?.pagination?.total || 0;
                const totalSeries = gridRes?.total_series || 0;

                // Count missing metadata books
                const missingGrid = await api
                    .getLibraryGrid({ missing_filter: 'missing_spanish', limit: 1 })
                    .catch(() => ({ pagination: { total: 0 } }));
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
        <div className="w-full max-w-[2100px] mx-auto space-y-8 animate-in fade-in duration-300">
            {/* Header Banner */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 bg-gradient-to-r from-indigo-950/70 via-purple-950/50 to-slate-900/80 p-6 sm:p-8 lg:p-10 rounded-3xl border border-indigo-500/20 backdrop-blur-2xl shadow-2xl">
                <div className="space-y-2">
                    <div className="flex items-center gap-2">
                        <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                            PANEL DE CONTROL PRINCIPAL
                        </span>
                        <span className="text-xs text-indigo-300/60 font-medium">ZeePubs v3.6.0</span>
                    </div>
                    <h2 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight">
                        Centro de Control Editorial
                    </h2>
                    <p className="text-xs sm:text-sm text-indigo-200/80 max-w-2xl leading-relaxed">
                        Gestiona la catalogación de EPUBs, enriquece metadatos con IA, organiza series y programa lanzamientos en Telegram y Facebook con máxima fidelidad visual.
                    </p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <button
                        onClick={() => navigate('/upload')}
                        className="px-5 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2.5 shadow-xl shadow-indigo-600/30 transition-all active:scale-95"
                    >
                        <UploadCloud className="w-4 h-4" />
                        Subir EPUBs
                    </button>
                    <button
                        onClick={() => navigate('/app-v2/calendar')}
                        className="px-5 py-3 rounded-2xl bg-white/5 hover:bg-white/10 text-white text-xs font-bold flex items-center gap-2.5 border border-white/10 transition-all active:scale-95"
                    >
                        <Calendar className="w-4 h-4" />
                        Agenda Editorial
                    </button>
                </div>
            </div>

            {/* Actionable Pending Work Cards */}
            <div className="space-y-4">
                <div className="flex items-center justify-between">
                    <h3 className="text-xs font-black uppercase tracking-wider text-gray-400 flex items-center gap-2">
                        ⚡ Métricas Clave y Tareas Pendientes
                    </h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 2xl:grid-cols-4 gap-5">
                    {/* Card 1: Missing Meta */}
                    <div
                        onClick={() => navigate('/app-v2/library?missing=missing_spanish')}
                        className="p-6 rounded-3xl bg-amber-500/[0.07] hover:bg-amber-500/[0.12] border border-amber-500/20 transition-all cursor-pointer group flex flex-col justify-between shadow-xl"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-3xl font-black text-amber-400 font-mono">
                                {stats.missingMetaCount}
                            </span>
                            <div className="p-3 rounded-2xl bg-amber-500/20 text-amber-300">
                                <AlertCircle className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="mt-5">
                            <div className="text-sm font-bold text-white group-hover:text-amber-300 transition-colors">
                                EPUBs sin metadatos en español
                            </div>
                            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1.5">
                                Revisar catálogo <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 2: AI Proposals */}
                    <div
                        onClick={() => navigate('/app-v2/ai')}
                        className="p-6 rounded-3xl bg-indigo-500/[0.07] hover:bg-indigo-500/[0.12] border border-indigo-500/20 transition-all cursor-pointer group flex flex-col justify-between shadow-xl"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-3xl font-black text-indigo-400 font-mono">
                                {stats.aiProposalsCount}
                            </span>
                            <div className="p-3 rounded-2xl bg-indigo-500/20 text-indigo-300">
                                <Sparkles className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="mt-5">
                            <div className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                                Sugerencias IA por revisar
                            </div>
                            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1.5">
                                Abrir Hub IA <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 3: Pending Queue */}
                    <div
                        onClick={() => navigate('/app-v2/calendar')}
                        className="p-6 rounded-3xl bg-emerald-500/[0.07] hover:bg-emerald-500/[0.12] border border-emerald-500/20 transition-all cursor-pointer group flex flex-col justify-between shadow-xl"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-3xl font-black text-emerald-400 font-mono">
                                {stats.pendingQueueCount}
                            </span>
                            <div className="p-3 rounded-2xl bg-emerald-500/20 text-emerald-300">
                                <Calendar className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="mt-5">
                            <div className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                                Publicaciones en agenda
                            </div>
                            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1.5">
                                Ver cronograma <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>

                    {/* Card 4: Total Series */}
                    <div
                        onClick={() => navigate('/app-v2/series')}
                        className="p-6 rounded-3xl bg-purple-500/[0.07] hover:bg-purple-500/[0.12] border border-purple-500/20 transition-all cursor-pointer group flex flex-col justify-between shadow-xl"
                    >
                        <div className="flex items-start justify-between">
                            <span className="text-3xl font-black text-purple-400 font-mono">
                                {stats.totalSeries}
                            </span>
                            <div className="p-3 rounded-2xl bg-purple-500/20 text-purple-300">
                                <Layers className="w-5 h-5" />
                            </div>
                        </div>
                        <div className="mt-5">
                            <div className="text-sm font-bold text-white group-hover:text-purple-300 transition-colors">
                                Total Series Indexadas ({stats.totalBooks} Tomos)
                            </div>
                            <div className="text-xs text-gray-400 mt-1 flex items-center gap-1.5">
                                Administrar series <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Main 2K Widescreen Pipeline Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Left (8 Columns on Widescreen): Quick Editorial Pipelines */}
                <div className="lg:col-span-8 space-y-4">
                    <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                        🚀 Flujos de Trabajo Editorial
                    </h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5">
                        <div
                            onClick={() => navigate('/app-v2/templates')}
                            className="p-6 rounded-3xl bg-slate-900/50 hover:bg-slate-900/80 border border-white/10 hover:border-indigo-500/40 transition-all cursor-pointer group space-y-3 shadow-xl backdrop-blur-xl"
                        >
                            <div className="p-3 w-fit rounded-2xl bg-indigo-500/20 text-indigo-400">
                                <FileText className="w-6 h-6" />
                            </div>
                            <h4 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                                Editor de Rich Messages y Copys
                            </h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Diseña mensajes enriquecidos con etiquetas dinámicas, simulador oficial de Telegram y adaptación a Facebook.
                            </p>
                        </div>

                        <div
                            onClick={() => navigate('/app-v2/volumes')}
                            className="p-6 rounded-3xl bg-slate-900/50 hover:bg-slate-900/80 border border-white/10 hover:border-emerald-500/40 transition-all cursor-pointer group space-y-3 shadow-xl backdrop-blur-xl"
                        >
                            <div className="p-3 w-fit rounded-2xl bg-emerald-500/20 text-emerald-400">
                                <TrendingUp className="w-6 h-6" />
                            </div>
                            <h4 className="text-base font-bold text-white group-hover:text-emerald-300 transition-colors">
                                Matriz de Volúmenes por Serie
                            </h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Reasigna volúmenes huérfanos, ajusta numeraciones de tomos y audita la resolución de portadas.
                            </p>
                        </div>

                        <div
                            onClick={() => navigate('/app-v2/datagrid')}
                            className="p-6 rounded-3xl bg-slate-900/50 hover:bg-slate-900/80 border border-white/10 hover:border-cyan-500/40 transition-all cursor-pointer group space-y-3 shadow-xl backdrop-blur-xl"
                        >
                            <div className="p-3 w-fit rounded-2xl bg-cyan-500/20 text-cyan-400">
                                <Table className="w-6 h-6" />
                            </div>
                            <h4 className="text-base font-bold text-white group-hover:text-cyan-300 transition-colors">
                                Editor Masivo DataGrid
                            </h4>
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Edición estilo hoja de cálculo para metadatos en lote, slugs, sinopsis y demografías.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right (4 Columns on Widescreen): Next Scheduled Publications */}
                <div className="lg:col-span-4 space-y-4">
                    <div className="flex items-center justify-between">
                        <h3 className="text-xs font-black uppercase tracking-wider text-gray-400">
                            📅 Próximos Lanzamientos
                        </h3>
                        <button
                            onClick={() => navigate('/app-v2/calendar')}
                            className="text-xs text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1"
                        >
                            Ver calendario <ArrowRight className="w-3 h-3" />
                        </button>
                    </div>

                    <div className="p-6 rounded-3xl bg-slate-900/60 border border-white/10 space-y-3 shadow-xl backdrop-blur-xl">
                        {recentQueue.length === 0 ? (
                            <div className="py-12 text-center text-gray-500 text-xs">
                                No hay publicaciones programadas en cola.
                            </div>
                        ) : (
                            recentQueue.map((item) => (
                                <div
                                    key={item.id}
                                    className="flex items-center justify-between p-3.5 rounded-2xl bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 transition-colors"
                                >
                                    <div className="min-w-0 flex-1 pr-3">
                                        <div className="text-xs font-bold text-white truncate">
                                            {item.series || 'Novela'}
                                        </div>
                                        <div className="text-[11px] text-gray-400 truncate flex items-center gap-2 mt-0.5">
                                            <span>Vol. {item.volume || 1}</span>
                                            <span>•</span>
                                            <span>{item.channel}</span>
                                        </div>
                                    </div>
                                    <span className="px-2.5 py-1 rounded-full text-[9px] font-black uppercase bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
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
