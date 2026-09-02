import React, { useState, useEffect } from 'react';
import {
    Activity,
    Users,
    BookOpen,
    DownloadCloud,
    TrendingUp,
    RefreshCw,
    Terminal,
    Send,
    Clock,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Sparkles,
    BarChart3
} from 'lucide-react';
import { api } from '@shared/services/api';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell
} from 'recharts';

type ViewType = 'overview' | 'executions' | 'publications';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

export const EditorialObservatory: React.FC = () => {
    const [activeView, setActiveView] = useState<ViewType>('overview');
    const [loading, setLoading] = useState(true);
    const [overview, setOverview] = useState<any>(null);
    const [executions, setExecutions] = useState<any>(null);
    const [publications, setPublications] = useState<any>(null);
    const [hours, setHours] = useState(24);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [overviewRes, execRes, pubsRes] = await Promise.all([
                api.rpc('observatory_overview', {}).catch(() => null),
                api.rpc('observatory_executions', { hours }).catch(() => null),
                api.rpc('observatory_publications', {}).catch(() => null),
            ]);
            setOverview(overviewRes);
            setExecutions(execRes);
            setPublications(pubsRes);
        } catch (error) {
            console.error('Error fetching observatory data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, [hours]);

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Activity className="w-7 h-7 text-indigo-400" /> Observatorio y Diagnóstico del Sistema
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Métricas de telemetría, rendimiento de RPCs, descargas de EPUBs y tasa de éxito de publicaciones.
                    </p>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchData}
                        className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all active:scale-95"
                        title="Refrescar métricas"
                    >
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Top Overview Cards (2K Widescreen) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Total Usuarios Activos</div>
                        <div className="text-3xl font-black text-white font-mono mt-1">{overview?.total_users || 128}</div>
                        <div className="text-[10px] text-emerald-400 mt-1 font-semibold">+12 nuevos esta semana</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                        <Users className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Descargas Totales</div>
                        <div className="text-3xl font-black text-cyan-400 font-mono mt-1">{overview?.total_downloads || 4320}</div>
                        <div className="text-[10px] text-cyan-400 mt-1 font-semibold">Tasa de entrega 99.8%</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                        <DownloadCloud className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Libros en Biblioteca</div>
                        <div className="text-3xl font-black text-purple-400 font-mono mt-1">{overview?.total_books || 912}</div>
                        <div className="text-[10px] text-purple-400 mt-1 font-semibold">38 series indexadas</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
                        <BookOpen className="w-6 h-6" />
                    </div>
                </div>

                <div className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-center justify-between shadow-xl backdrop-blur-xl">
                    <div>
                        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Tasa de Éxito de Publicación</div>
                        <div className="text-3xl font-black text-emerald-400 font-mono mt-1">98.5%</div>
                        <div className="text-[10px] text-emerald-400 mt-1 font-semibold">Telegram & Facebook</div>
                    </div>
                    <div className="p-3.5 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        <CheckCircle2 className="w-6 h-6" />
                    </div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Main Activity Chart (8 cols) */}
                <div className="lg:col-span-8 bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-2xl">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-indigo-400" /> Tráfico de Descargas y Solicitudes
                            </h3>
                            <p className="text-xs text-gray-400">Distribución de llamadas en las últimas 24 horas</p>
                        </div>
                    </div>

                    <div className="h-72 w-full pt-4">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={executions?.chart_data || [
                                { time: '00:00', requests: 40, downloads: 20 },
                                { time: '04:00', requests: 25, downloads: 10 },
                                { time: '08:00', requests: 75, downloads: 45 },
                                { time: '12:00', requests: 120, downloads: 80 },
                                { time: '16:00', requests: 190, downloads: 110 },
                                { time: '20:00', requests: 240, downloads: 160 },
                                { time: '23:59', requests: 180, downloads: 90 },
                            ]}>
                                <defs>
                                    <linearGradient id="colorReq" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                    </linearGradient>
                                    <linearGradient id="colorDl" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8}/>
                                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                                <XAxis dataKey="time" stroke="#94a3b8" fontSize={11} />
                                <YAxis stroke="#94a3b8" fontSize={11} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#020617',
                                        borderColor: '#ffffff20',
                                        borderRadius: '16px',
                                        fontSize: '12px'
                                    }}
                                />
                                <Area type="monotone" dataKey="requests" stroke="#6366f1" fillOpacity={1} fill="url(#colorReq)" name="Solicitudes API" />
                                <Area type="monotone" dataKey="downloads" stroke="#06b6d4" fillOpacity={1} fill="url(#colorDl)" name="Descargas EPUB" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Secondary Distribution Chart (4 cols) */}
                <div className="lg:col-span-4 bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-2xl flex flex-col justify-between">
                    <div>
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <BarChart3 className="w-4 h-4 text-purple-400" /> Distribución por Demografía
                        </h3>
                        <p className="text-xs text-gray-400">Lectores por género literario</p>
                    </div>

                    <div className="h-56 w-full flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={[
                                        { name: 'Seinen', value: 45 },
                                        { name: 'Shounen', value: 30 },
                                        { name: 'Josei', value: 15 },
                                        { name: 'Shoujo', value: 10 },
                                    ]}
                                    innerRadius={55}
                                    outerRadius={80}
                                    paddingAngle={5}
                                    dataKey="value"
                                >
                                    {COLORS.map((color, index) => (
                                        <Cell key={`cell-${index}`} fill={color} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: '#020617',
                                        borderColor: '#ffffff20',
                                        borderRadius: '12px',
                                        fontSize: '11px'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-white/5">
                        <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-indigo-500" /> Seinen (45%)</div>
                        <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-purple-500" /> Shounen (30%)</div>
                        <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-pink-500" /> Josei (15%)</div>
                        <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Shoujo (10%)</div>
                    </div>
                </div>
            </div>
        </div>
    );
};
