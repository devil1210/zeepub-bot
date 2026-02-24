import React, { useState, useEffect } from 'react';
import {
    Activity,
    Users,
    Library,
    CloudDownload,
    TrendingUp,
    RefreshCw,
    Terminal,
    Send,
    Clock,
    CheckCircle,
    XCircle,
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
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
    Cell,
} from 'recharts';

type ViewType = 'overview' | 'executions' | 'publications' | 'metrics';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

export const ObservatoryPage: React.FC = () => {
    const { settings } = useTheme();
    const [activeView, setActiveView] = useState<ViewType>('overview');
    const [loading, setLoading] = useState(true);
    const [overview, setOverview] = useState<any>(null);
    const [executions, setExecutions] = useState<any>(null);
    const [publications, setPublications] = useState<any>(null);
    const [metrics, setMetrics] = useState<any>(null);
    const [hours, setHours] = useState(24);

    const fetchData = async () => {
        setLoading(true);
        try {
            const [overviewRes, execRes, pubsRes, metricsRes] = await Promise.all([
                api.rpc('observatory_overview', {}),
                api.rpc('observatory_executions', { hours }),
                api.rpc('observatory_publications', {}),
                api.rpc('observatory_metrics', {}),
            ]);
            setOverview(overviewRes);
            setExecutions(execRes);
            setPublications(pubsRes);
            setMetrics(metricsRes);
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

    const renderOverview = () => (
        <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-panel p-5 rounded-premium relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Libros</p>
                        <h3 className="text-3xl font-bold text-white mt-1">{overview?.totalBooks?.toLocaleString() || 0}</h3>
                    </div>
                    <div className="p-3 bg-indigo-500/20 rounded-premium-sm text-indigo-400 border border-indigo-500/20 absolute right-4 top-4">
                        <Library className="w-5 h-5" />
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-premium relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Usuarios</p>
                        <h3 className="text-3xl font-bold text-white mt-1">{overview?.totalUsers?.toLocaleString() || 0}</h3>
                    </div>
                    <div className="p-3 bg-purple-500/20 rounded-premium-sm text-purple-400 border border-purple-500/20 absolute right-4 top-4">
                        <Users className="w-5 h-5" />
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-premium relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Descargas Hoy</p>
                        <h3 className="text-3xl font-bold text-white mt-1">{overview?.downloadsToday?.toLocaleString() || 0}</h3>
                    </div>
                    <div className="p-3 bg-emerald-500/20 rounded-premium-sm text-emerald-400 border border-emerald-500/20 absolute right-4 top-4">
                        <CloudDownload className="w-5 h-5" />
                    </div>
                </div>
                <div className="glass-panel p-5 rounded-premium relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Publicaciones</p>
                        <h3 className="text-3xl font-bold text-white mt-1">{overview?.pendingPublications?.toLocaleString() || 0}</h3>
                    </div>
                    <div className="p-3 bg-amber-500/20 rounded-premium-sm text-amber-400 border border-amber-500/20 absolute right-4 top-4">
                        <Send className="w-5 h-5" />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-panel p-6 rounded-premium border border-white/5">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-indigo-400" />
                        Actividad (7 días)
                    </h3>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={overview?.activityLast7Days || []}>
                                <defs>
                                    <linearGradient id="colorDownloads" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                                <XAxis dataKey="date" stroke="#6b7280" fontSize={10} />
                                <YAxis stroke="#6b7280" fontSize={10} />
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                />
                                <Area type="monotone" dataKey="downloads" stroke="#6366f1" fillOpacity={1} fill="url(#colorDownloads)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="glass-panel p-6 rounded-premium border border-white/5">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                        <Users className="w-4 h-4 text-purple-400" />
                        Usuarios por Nivel
                    </h3>
                    <div className="h-48">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={overview?.usersByLevel || []}
                                    cx="50%"
                                    cy="50%"
                                    innerRadius={50}
                                    outerRadius={70}
                                    paddingAngle={5}
                                    dataKey="count"
                                    nameKey="level"
                                >
                                    {(overview?.usersByLevel || []).map((_: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip
                                    contentStyle={{
                                        backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                        border: '1px solid rgba(255,255,255,0.1)',
                                        borderRadius: '8px',
                                        color: '#fff'
                                    }}
                                />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    );

    const renderExecutions = () => (
        <div className="space-y-6">
            <div className="flex items-center gap-4">
                <select
                    value={hours}
                    onChange={(e) => setHours(Number(e.target.value))}
                    className="bg-black/40 border border-white/10 rounded-lg text-sm font-bold text-gray-400 px-3 py-2 focus:outline-none focus:border-primary transition-colors"
                >
                    <option value={1}>1 hora</option>
                    <option value={6}>6 horas</option>
                    <option value={12}>12 horas</option>
                    <option value={24}>24 horas</option>
                    <option value={48}>48 horas</option>
                    <option value={72}>72 horas</option>
                </select>
            </div>

            <div className="grid grid-cols-3 gap-4">
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <CheckCircle className="w-6 h-6 text-green-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">{executions?.stats?.success || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Exitosas</p>
                </div>
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <XCircle className="w-6 h-6 text-red-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">{executions?.stats?.error || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Errores</p>
                </div>
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <Clock className="w-6 h-6 text-blue-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">{executions?.stats?.avgDuration || 0}s</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Promedio</p>
                </div>
            </div>

            <div className="glass-panel rounded-premium border border-white/5 overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 font-black uppercase tracking-wider">
                                <th className="p-4">Hora</th>
                                <th className="p-4">Función</th>
                                <th className="p-4">Estado</th>
                                <th className="p-4">Duración</th>
                                <th className="p-4">Error</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {(executions?.executions || []).slice(0, 20).map((exec: any, i: number) => (
                                <tr key={i} className="hover:bg-white/[0.02] transition-colors">
                                    <td className="p-4 text-gray-400 font-mono text-[10px]">
                                        {exec.timestamp ? new Date(exec.timestamp).toLocaleTimeString() : '-'}
                                    </td>
                                    <td className="p-4 text-gray-200 font-medium">{exec.funcName}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-[9px] font-black uppercase ${
                                            exec.status === 'success' ? 'bg-green-500/20 text-green-400' :
                                            exec.status === 'error' ? 'bg-red-500/20 text-red-400' :
                                            'bg-gray-500/20 text-gray-400'
                                        }`}>
                                            {exec.status}
                                        </span>
                                    </td>
                                    <td className="p-4 text-gray-400 font-mono">{exec.duration?.toFixed(2) || '-'}s</td>
                                    <td className="p-4 text-red-400 max-w-[200px] truncate">{exec.error || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );

    const renderPublications = () => (
        <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <p className="text-2xl font-bold text-yellow-400">{publications?.queue?.pending || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Pendientes</p>
                </div>
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <p className="text-2xl font-bold text-blue-400">{publications?.queue?.publishing || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Publicando</p>
                </div>
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <p className="text-2xl font-bold text-green-400">{publications?.queue?.sent || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Enviados</p>
                </div>
                <div className="glass-panel p-4 rounded-premium border border-white/5 text-center">
                    <p className="text-2xl font-bold text-red-400">{publications?.queue?.failed || 0}</p>
                    <p className="text-[10px] font-black text-gray-500 uppercase">Fallidos</p>
                </div>
            </div>

            <div className="glass-panel p-6 rounded-premium border border-white/5">
                <h3 className="text-sm font-black text-white uppercase tracking-widest mb-4">Canales Configurados</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {(publications?.channels || []).map((ch: any, i: number) => (
                        <div key={i} className="flex items-center justify-between p-3 bg-black/20 rounded-lg border border-white/5">
                            <div>
                                <p className="font-bold text-gray-200">{ch.name}</p>
                                <p className="text-[10px] text-gray-500">{ch.platform}</p>
                            </div>
                            <span className={`px-2 py-1 rounded text-[9px] font-black ${
                                ch.isActive ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'
                            }`}>
                                {ch.isActive ? 'Activo' : 'Inactivo'}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );

    const renderMetrics = () => (
        <div className="space-y-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-panel p-5 rounded-premium border border-white/5">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Total Libros</p>
                    <p className="text-2xl font-bold text-white mt-1">{metrics?.library?.totalBooks?.toLocaleString() || 0}</p>
                </div>
                <div className="glass-panel p-5 rounded-premium border border-white/5">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Total Series</p>
                    <p className="text-2xl font-bold text-white mt-1">{metrics?.library?.totalSeries?.toLocaleString() || 0}</p>
                </div>
                <div className="glass-panel p-5 rounded-premium border border-white/5">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Valoraciones</p>
                    <p className="text-2xl font-bold text-white mt-1">{metrics?.library?.totalRatings?.toLocaleString() || 0}</p>
                </div>
                <div className="glass-panel p-5 rounded-premium border border-white/5">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Rating Promedio</p>
                    <p className="text-2xl font-bold text-white mt-1">{metrics?.library?.avgRating || 0}</p>
                </div>
            </div>

            <div className="glass-panel p-6 rounded-premium border border-white/5">
                <h3 className="text-sm font-black text-white uppercase tracking-widest mb-4">Top 10 Libros Más Descargados</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={metrics?.topBooks || []} layout="vertical">
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                            <XAxis type="number" stroke="#6b7280" fontSize={10} />
                            <YAxis dataKey="title" type="category" stroke="#6b7280" fontSize={10} width={120} />
                            <Tooltip
                                contentStyle={{
                                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                    border: '1px solid rgba(255,255,255,0.1)',
                                    borderRadius: '8px',
                                    color: '#fff'
                                }}
                            />
                            <Bar dataKey="downloads" fill="#8b5cf6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500 pt-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-black text-white">Observatorio</h1>
                    <p className="text-sm text-gray-500">Dashboard de Observabilidad - Capa 4</p>
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="p-2 glass-panel rounded-lg hover:bg-white/5 transition-colors"
                >
                    <RefreshCw className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            <div className="flex gap-2 overflow-x-auto pb-2">
                {(['overview', 'executions', 'publications', 'metrics'] as ViewType[]).map((view) => (
                    <button
                        key={view}
                        onClick={() => setActiveView(view)}
                        className={`px-4 py-2 rounded-lg text-sm font-bold transition-all whitespace-nowrap ${
                            activeView === view
                                ? 'bg-primary text-white'
                                : 'glass-panel text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                    >
                        {view === 'overview' && 'Resumen'}
                        {view === 'executions' && 'Ejecuciones'}
                        {view === 'publications' && 'Publicaciones'}
                        {view === 'metrics' && 'Métricas'}
                    </button>
                ))}
            </div>

            {loading && !overview ? (
                <div className="flex items-center justify-center py-20">
                    <RefreshCw className="w-8 h-8 text-gray-500 animate-spin" />
                </div>
            ) : (
                <>
                    {activeView === 'overview' && renderOverview()}
                    {activeView === 'executions' && renderExecutions()}
                    {activeView === 'publications' && renderPublications()}
                    {activeView === 'metrics' && renderMetrics()}
                </>
            )}
        </div>
    );
};
