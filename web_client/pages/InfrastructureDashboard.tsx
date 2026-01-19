import React, { useState, useEffect } from 'react';
import {
    Activity,
    Settings,
    Terminal,
    Database,
    RefreshCw,
    Plus,
    Shield,
    Users,
    Library,
    CloudDownload,
    Cpu,
    LogOut,
    Search,
    Bell,
    Menu,
    TrendingUp,
    LayoutDashboard,
    Box,
    Trash2,
    Lock,
    Archive,
    Zap,
    AlertTriangle,
    CheckCircle2,
    Loader2
} from 'lucide-react';
import { api } from '../src/services/api';

export const InfrastructureDashboard: React.FC = () => {
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [logs, setLogs] = useState<{ time: string, level: string, msg: string, color: string }[]>([]);

    const fetchStats = async () => {
        try {
            const data = await api.getAdminStats();
            setStats(data);
            addLog('INFO', 'System stats refreshed');
        } catch (error) {
            console.error('Error fetching stats:', error);
            addLog('ERROR', 'Failed to fetch system stats');
        } finally {
            setLoading(false);
        }
    };

    const addLog = (level: string, msg: string) => {
        const time = new Date().toLocaleTimeString([], { hour12: false });
        const color = level === 'ERROR' ? 'text-red-400' :
            level === 'WARN' ? 'text-yellow-400' :
                level === 'SUCCESS' ? 'text-green-400' : 'text-blue-400';

        setLogs(prev => [...prev.slice(-14), { time, level, msg, color }]);
    };

    useEffect(() => {
        fetchStats();

        // Initial dummy logs
        setLogs([
            { time: new Date().toLocaleTimeString([], { hour12: false }), level: 'INFO', msg: 'Admin Dashboard initialized', color: 'text-blue-400' },
            { time: new Date().toLocaleTimeString([], { hour12: false }), level: 'SUCCESS', msg: 'System connection healthy', color: 'text-green-400' }
        ]);

        const interval = setInterval(fetchStats, 60000); // Refresh every minute
        return () => clearInterval(interval);
    }, []);

    const handleAction = async (name: string, fn: () => Promise<any>) => {
        setActionLoading(name);
        addLog('INFO', `Executing ${name}...`);
        try {
            const res = await fn();
            if (res.success) {
                addLog('SUCCESS', res.message || `${name} completed successfully`);
                fetchStats();
            } else {
                addLog('ERROR', res.message || `${name} failed`);
            }
        } catch (error: any) {
            addLog('ERROR', error.message || `Error executing ${name}`);
        } finally {
            setActionLoading(null);
        }
    };

    const formatBytes = (bytes: number) => {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    return (
        <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-background-light dark:bg-[#101b22] text-slate-800 dark:text-slate-100 font-sans">
            {/* Background Glow */}
            <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-br from-[#0d93f2]/20 via-transparent to-transparent pointer-events-none opacity-50 dark:opacity-30"></div>

            {/* Header */}
            <header className="h-16 flex items-center justify-between px-6 z-10 glass-panel border-b-0 sticky top-0 backdrop-blur-md bg-white/70 dark:bg-[#1e293b]/60 border border-white/50 dark:border-white/10 shadow-sm">
                <div className="flex items-center md:hidden">
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                    >
                        <Menu className="w-6 h-6" />
                    </button>
                </div>

                <div className="flex items-center gap-4 text-sm font-medium text-slate-600 dark:text-slate-400">
                    <span className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse"></span>
                        Bot Status: Online
                    </span>
                    <span className="h-4 w-px bg-slate-300 dark:bg-slate-700"></span>
                    <span>Version: v7.1.1</span>
                </div>

                <div className="flex items-center gap-4">
                    <div className="relative hidden sm:block">
                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">
                            <Search className="w-4 h-4" />
                        </span>
                        <input
                            className="pl-10 pr-4 py-1.5 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0d93f2] focus:border-transparent w-64 text-slate-900 dark:text-slate-100 placeholder-slate-400 shadow-sm"
                            placeholder="Search logs, books..."
                            type="text"
                        />
                    </div>
                    <button className="relative p-2 text-slate-400 hover:text-slate-500 dark:hover:text-slate-300 transition-colors">
                        <Bell className="w-5 h-5" />
                        <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white dark:border-slate-900"></span>
                    </button>
                </div>
            </header>

            <main className="flex-1 overflow-y-auto p-6 z-10 scrollbar-hide">
                {/* Dashboard Header */}
                <div className="mb-8 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                    <div>
                        <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                            <Shield className="w-6 h-6 text-[#0d93f2]" />
                            System Health & Admin
                        </h2>
                        <p className="text-slate-500 dark:text-slate-400 mt-1">Real-time overview of the ZeepubBot ecosystem.</p>
                    </div>
                    <div className="flex gap-2">
                        <button
                            onClick={fetchStats}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-slate-900 dark:bg-slate-700 rounded-lg hover:bg-slate-800 dark:hover:bg-slate-600 transition-colors shadow-lg"
                        >
                            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                            Refresh Stats
                        </button>
                        <button
                            onClick={() => handleAction('Update System', api.adminUpdateSystem)}
                            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-[#0d93f2] rounded-lg hover:bg-blue-600 transition-colors shadow-lg shadow-blue-500/30"
                        >
                            {actionLoading === 'Update System' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                            Update System
                        </button>
                    </div>
                </div>

                {/* Metric Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    <div className="glass-panel p-5 rounded-xl border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md flex items-start justify-between relative overflow-hidden group shadow-sm">
                        <div className="relative z-10">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Active Users</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-1">
                                {loading ? '...' : stats?.totalUsers?.toLocaleString() || '0'}
                            </h3>
                            <div className="flex items-center mt-2 text-xs text-green-500 font-bold">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                +4.5% this week
                            </div>
                        </div>
                        <div className="p-3 bg-blue-100 dark:bg-blue-500/20 rounded-lg text-blue-600 dark:text-blue-400">
                            <Users className="w-6 h-6" />
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-blue-500/10 rounded-full blur-xl group-hover:bg-blue-500/20 transition-all duration-500"></div>
                    </div>

                    <div className="glass-panel p-5 rounded-xl border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md flex items-start justify-between relative overflow-hidden group shadow-sm">
                        <div className="relative z-10">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Library Index</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-1">
                                {loading ? '...' : stats?.totalBooks?.toLocaleString() || '0'}
                            </h3>
                            <div className="flex items-center mt-2 text-xs text-slate-500 dark:text-slate-400 font-bold">
                                <Archive className="w-3 h-3 mr-1" />
                                {stats?.storageUsedGB ? `${stats.storageUsedGB} GB storage` : 'Calculating...'}
                            </div>
                        </div>
                        <div className="p-3 bg-purple-100 dark:bg-purple-500/20 rounded-lg text-purple-600 dark:text-purple-400">
                            <Library className="w-6 h-6" />
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-purple-500/10 rounded-full blur-xl group-hover:bg-purple-500/20 transition-all duration-500"></div>
                    </div>

                    <div className="glass-panel p-5 rounded-xl border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md flex items-start justify-between relative overflow-hidden group shadow-sm">
                        <div className="relative z-10">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Downloads (24h)</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-1">
                                {loading ? '...' : stats?.downloads24h?.toLocaleString() || '0'}
                            </h3>
                            <div className="flex items-center mt-2 text-xs text-green-500 font-bold">
                                <TrendingUp className="w-3 h-3 mr-1" />
                                +12% vs yesterday
                            </div>
                        </div>
                        <div className="p-3 bg-emerald-100 dark:bg-emerald-500/20 rounded-lg text-emerald-600 dark:text-emerald-400">
                            <CloudDownload className="w-6 h-6" />
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-emerald-500/10 rounded-full blur-xl group-hover:bg-emerald-500/20 transition-all duration-500"></div>
                    </div>

                    <div className="glass-panel p-5 rounded-xl border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md flex items-start justify-between relative overflow-hidden group shadow-sm">
                        <div className="relative z-10">
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">System Uptime</p>
                            <h3 className="text-3xl font-black text-slate-900 dark:text-white mt-1">
                                {loading ? '...' : stats?.uptime || '99.9%'}
                            </h3>
                            <div className="flex items-center mt-2 text-xs text-slate-500 dark:text-slate-400 font-bold">
                                <Activity className="w-3 h-3 mr-1" />
                                {stats?.activeSessions || '0'} active sessions
                            </div>
                        </div>
                        <div className="p-3 bg-amber-100 dark:bg-amber-500/20 rounded-lg text-amber-600 dark:text-amber-400">
                            <Cpu className="w-6 h-6" />
                        </div>
                        <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-amber-500/10 rounded-full blur-xl group-hover:bg-amber-500/20 transition-all duration-500"></div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                    {/* Maintenance Section */}
                    <div className="lg:col-span-1 glass-panel border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md rounded-xl p-6 flex flex-col shadow-sm">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Settings className="text-[#0d93f2] w-5 h-5" />
                                Maintenance
                            </h3>
                            <span className="px-2 py-1 bg-green-500/10 text-green-500 text-[10px] rounded border border-green-500/20 font-black uppercase tracking-widest">Operational</span>
                        </div>
                        <div className="space-y-4 flex-1">
                            <div className="p-4 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-[#0d93f2]/50 transition-colors group cursor-default shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm">Scan Library</h4>
                                    <Activity className="w-4 h-4 text-slate-400 group-hover:text-[#0d93f2] transition-colors" />
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
                                    Trigger <code className="bg-slate-100 dark:bg-slate-900 px-1.5 py-0.5 rounded text-[#0d93f2] font-mono">/scan_library</code> to index new content.
                                </p>
                                <button
                                    disabled={!!actionLoading}
                                    onClick={() => handleAction('Scan Library', () => api.adminScanLibrary(true))}
                                    className="w-full py-2 text-xs font-black text-center bg-[#0d93f2] hover:bg-blue-600 disabled:bg-slate-500 text-white rounded-lg transition-colors shadow-sm uppercase tracking-widest flex items-center justify-center gap-2"
                                >
                                    {actionLoading === 'Scan Library' ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                                    Execute Scan
                                </button>
                            </div>

                            <div className="p-4 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-[#0d93f2]/50 transition-colors group cursor-default shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm">Backup Database</h4>
                                    <Database className="w-4 h-4 text-slate-400 group-hover:text-[#0d93f2] transition-colors" />
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
                                    Sync SQLite library data to Supabase for persistence.
                                </p>
                                <button
                                    disabled={!!actionLoading}
                                    onClick={() => handleAction('Backup', api.adminBackupLibrary)}
                                    className="w-full py-2 text-xs font-black text-center bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 disabled:bg-slate-500 text-slate-700 dark:text-slate-200 rounded-lg transition-colors uppercase tracking-widest flex items-center justify-center gap-2"
                                >
                                    {actionLoading === 'Backup' ? <Loader2 className="w-3 h-3 animate-spin" /> : <CloudDownload className="w-3 h-3" />}
                                    Start Backup
                                </button>
                            </div>

                            <div className="p-4 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 border-red-500/20 hover:border-red-500/50 transition-colors group cursor-default shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-red-600 dark:text-red-400 text-sm">Reset Library</h4>
                                    <Trash2 className="w-4 h-4 text-slate-400 group-hover:text-red-500 transition-colors" />
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
                                    Purge database and covers. <span className="text-red-500 font-bold">Irreversible!</span>
                                </p>
                                <button
                                    disabled={!!actionLoading}
                                    onClick={() => {
                                        if (confirm('¿ESTÁS SEGURO? Esta acción eliminará TODA la base de datos de libros y portadas local.')) {
                                            handleAction('Reset Library', () => api.adminResetLibrary(true));
                                        }
                                    }}
                                    className="w-full py-2 text-xs font-black text-center bg-red-500/10 hover:bg-red-500 text-red-600 hover:text-white border border-red-500/20 rounded-lg transition-colors uppercase tracking-widest flex items-center justify-center gap-2"
                                >
                                    {actionLoading === 'Reset Library' ? <Loader2 className="w-3 h-3 animate-spin" /> : <AlertTriangle className="w-3 h-3" />}
                                    Purge Data
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* System Logs Section */}
                    <div className="lg:col-span-2 glass-panel border border-white/50 dark:border-white/10 bg-white/30 dark:bg-[#1e293b]/60 backdrop-blur-md rounded-xl p-0 overflow-hidden flex flex-col h-[500px] lg:h-auto shadow-sm">
                        <div className="p-4 border-b border-gray-200 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-800/50 flex justify-between items-center">
                            <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-slate-400" />
                                Live System Logs
                            </h3>
                            <div className="flex gap-2">
                                <span className="w-2.5 h-2.5 rounded-full bg-red-500/50"></span>
                                <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></span>
                                <span className="w-2.5 h-2.5 rounded-full bg-green-500/50"></span>
                            </div>
                        </div>
                        <div className="flex-1 bg-slate-950 p-4 font-mono text-[11px] overflow-y-auto leading-relaxed scrollbar-thin scrollbar-thumb-slate-800 scrollbar-track-transparent">
                            <div className="space-y-1.5">
                                {logs.map((log, i) => (
                                    <div key={i} className="text-slate-500">
                                        [{log.time}] <span className={`${log.color} font-bold`}>{log.level}</span>: {log.msg}
                                    </div>
                                ))}
                                <div className="text-slate-300 animate-pulse">_</div>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};
