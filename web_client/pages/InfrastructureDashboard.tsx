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
    const [logs, setLogs] = useState<{ time: string, level: string, msg: string, color: string, timestamp?: number }[]>([]);
    const [auditLogs, setAuditLogs] = useState<any[]>([]);
    const [auditLoading, setAuditLoading] = useState(false);
    const [logLevel, setLogLevel] = useState('INFO');
    const [isExporting, setIsExporting] = useState(false);
    const [sendingTelegram, setSendingTelegram] = useState(false);
    const [copied, setCopied] = useState(false);

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

    const fetchAuditLogs = async () => {
        setAuditLoading(true);
        try {
            const res = await api.getRecentAuditLogs(20);
            if (res.success) {
                setAuditLogs(res.logs || []);
            }
        } catch (error) {
            console.error('Error fetching audit logs:', error);
        } finally {
            setAuditLoading(false);
        }
    };

    const fetchSystemLogs = async () => {
        try {
            const res = await api.getSystemLogs(logLevel);
            if (res.success && res.logs) {
                setLogs(res.logs);
            }
        } catch (error) {
            console.error('Error fetching system logs:', error);
        }
    };

    const handleExportLogs = async (hours?: number) => {
        setIsExporting(true);
        try {
            const res = await api.getSystemLogs('DEBUG', hours);
            if (res.success && res.logs && res.logs.length > 0) {
                const logEntries = res.logs.map((l: any) => `[${l.time}] ${l.level}: ${l.msg}`);
                const logText = logEntries.join('\n');

                const timestamps = res.logs.map((l: any) => l.timestamp).filter(Boolean);
                let dateSuffix = 'export';
                if (timestamps.length > 0) {
                    const first = new Date(Math.min(...timestamps) * 1000);
                    const last = new Date(Math.max(...timestamps) * 1000);
                    const pad = (n: number) => n.toString().padStart(2, '0');
                    const fmt = (d: Date) => `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}_${pad(d.getHours())}${pad(d.getMinutes())}`;
                    dateSuffix = `${fmt(first)}_${fmt(last)}`;
                }

                const filename = `logs_${dateSuffix}.txt`;
                const blob = new Blob([logText], { type: 'application/octet-stream' });
                const url = URL.createObjectURL(blob);

                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();

                setTimeout(() => {
                    document.body.removeChild(link);
                    URL.revokeObjectURL(url);
                }, 1000);
            }
        } catch (error) {
            console.error('Error exporting logs:', error);
        } finally {
            setIsExporting(false);
        }
    };

    const handleCopyLogs = () => {
        const text = logs.map(l => `[${l.time}] ${l.level}: ${l.msg}`).join('\n');
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleSendTelegram = async (hours?: number) => {
        setSendingTelegram(true);
        try {
            const res = await api.sendLogsToTelegram('DEBUG', hours);
            if (res.success) {
                alert('Logs enviados a tu Telegram!');
            } else {
                alert('Error: ' + res.message);
            }
        } catch (error) {
            console.error('Error sending logs to telegram:', error);
            alert('Error al enviar logs.');
        } finally {
            setSendingTelegram(false);
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
        fetchSystemLogs();
        fetchAuditLogs();

        const statsInterval = setInterval(fetchStats, 60000); // 1 min
        const logsInterval = setInterval(fetchSystemLogs, 10000); // 10 sec

        return () => {
            clearInterval(statsInterval);
            clearInterval(logsInterval);
        };
    }, [logLevel]);

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

                {/* Synchronization Summary Table */}
                <div className="glass-panel mb-8 p-6 rounded-xl border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md shadow-sm">
                    <div className="flex items-center gap-2 mb-4">
                        <Database className="w-5 h-5 text-blue-500" />
                        <h3 className="font-bold text-slate-900 dark:text-white">Synchronization Strategy</h3>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs">
                            <thead>
                                <tr className="border-b border-slate-200 dark:border-slate-700 text-slate-400 font-bold uppercase tracking-wider">
                                    <th className="pb-3 px-2">Table / Record</th>
                                    <th className="pb-3 px-2">Primary Storage</th>
                                    <th className="pb-3 px-2">Sync Status</th>
                                    <th className="pb-3 px-2">Cloud Backup Trigger</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                                <tr>
                                    <td className="py-3 px-2 font-bold">Books & Metadata</td>
                                    <td className="py-3 px-2">SQLite (Local)</td>
                                    <td className="py-3 px-2 text-amber-500">Manual Only</td>
                                    <td className="py-3 px-2 italic text-slate-500 font-mono text-[10px]">Cloud Sync → Library</td>
                                </tr>
                                <tr>
                                    <td className="py-3 px-2 font-bold">Library Sources</td>
                                    <td className="py-3 px-2">SQLite (Local)</td>
                                    <td className="py-3 px-2 text-amber-500">Manual Only</td>
                                    <td className="py-3 px-2 italic text-slate-500 font-mono text-[10px]">Cloud Sync → Library</td>
                                </tr>
                                <tr>
                                    <td className="py-3 px-2 font-bold">Users & Roles</td>
                                    <td className="py-3 px-2">SQLite (Local)</td>
                                    <td className="py-3 px-2 text-amber-500">Manual Only</td>
                                    <td className="py-3 px-2 italic text-slate-500 font-mono text-[10px]">Cloud Sync → Users</td>
                                </tr>
                                <tr>
                                    <td className="py-3 px-2 font-bold">User Levels (Tiers)</td>
                                    <td className="py-3 px-2">SQLite (Local)</td>
                                    <td className="py-3 px-2 text-amber-500">Manual Only</td>
                                    <td className="py-3 px-2 italic text-slate-500 font-mono text-[10px]">Cloud Sync → Users</td>
                                </tr>
                                <tr>
                                    <td className="py-3 px-2 font-bold">System Logs</td>
                                    <td className="py-3 px-2">Volatile (Memory)</td>
                                    <td className="py-3 px-2 text-slate-400">None</td>
                                    <td className="py-3 px-2 text-slate-400 italic">N/A</td>
                                </tr>
                                <tr>
                                    <td className="py-3 px-2 font-bold">Audit Logs</td>
                                    <td className="py-3 px-2">Supabase (Remote)</td>
                                    <td className="py-3 px-2 text-green-500">Automatic / Real-time</td>
                                    <td className="py-3 px-2 text-green-500 font-bold uppercase text-[9px]">Live Push</td>
                                </tr>
                            </tbody>
                        </table>
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

                            <div className="p-4 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-amber-500/50 transition-colors group cursor-default shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm">Enrich Metadata</h4>
                                    <Zap className="w-4 h-4 text-slate-400 group-hover:text-amber-500 transition-colors" />
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
                                    Fetch missing descriptions and covers from online sources.
                                </p>
                                <button
                                    disabled={!!actionLoading}
                                    onClick={() => handleAction('Enrich Metadata', api.adminEnrichMetadata)}
                                    className="w-full py-2 text-xs font-black text-center bg-amber-500/10 hover:bg-amber-500 text-amber-600 hover:text-white border border-amber-500/20 rounded-lg transition-all uppercase tracking-widest flex items-center justify-center gap-2"
                                >
                                    {actionLoading === 'Enrich Metadata' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Zap className="w-3 h-3" />}
                                    Run Enrichment
                                </button>
                            </div>

                            <div className="p-4 rounded-lg bg-white/50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700 hover:border-[#0d93f2]/50 transition-colors group cursor-default shadow-sm">
                                <div className="flex justify-between items-start mb-2">
                                    <h4 className="font-bold text-slate-800 dark:text-slate-200 text-sm">Cloud Sync</h4>
                                    <Shield className="w-4 h-4 text-slate-400 group-hover:text-blue-500 transition-colors" />
                                </div>
                                <p className="text-xs text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
                                    Sync local database and users to Supabase for double persistence.
                                </p>
                                <div className="grid grid-cols-2 gap-2">
                                    <button
                                        disabled={!!actionLoading}
                                        onClick={() => handleAction('Sync Users', api.adminSyncUsersCloud)}
                                        className="py-2 text-[10px] font-black text-center bg-blue-500/10 hover:bg-blue-500 text-blue-600 hover:text-white border border-blue-500/20 rounded-lg transition-all uppercase tracking-widest flex items-center justify-center gap-1.5"
                                    >
                                        {actionLoading === 'Sync Users' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Users className="w-3 h-3" />}
                                        Users
                                    </button>
                                    <button
                                        disabled={!!actionLoading}
                                        onClick={() => handleAction('Backup', api.adminBackupLibrary)}
                                        className="py-2 text-[10px] font-black text-center bg-purple-500/10 hover:bg-purple-500 text-purple-600 hover:text-white border border-purple-500/20 rounded-lg transition-all uppercase tracking-widest flex items-center justify-center gap-1.5"
                                    >
                                        {actionLoading === 'Backup' ? <Loader2 className="w-3 h-3 animate-spin" /> : <Library className="w-3 h-3" />}
                                        Library
                                    </button>
                                </div>
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

                    {/* Recent Activity Section */}
                    <div className="lg:col-span-2 glass-panel border border-white/50 dark:border-white/10 bg-white/70 dark:bg-[#1e293b]/60 backdrop-blur-md rounded-xl p-6 shadow-sm flex flex-col min-h-[400px]">
                        <div className="flex items-center justify-between mb-6">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
                                <Activity className="text-purple-500 w-5 h-5" />
                                Recent Activity
                            </h3>
                            <button
                                onClick={fetchAuditLogs}
                                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                            >
                                <RefreshCw className={`w-4 h-4 text-slate-400 ${auditLoading ? 'animate-spin' : ''}`} />
                            </button>
                        </div>
                        <div className="flex-1 overflow-x-auto">
                            <table className="w-full text-left text-xs">
                                <thead>
                                    <tr className="border-b border-slate-100 dark:border-slate-800 text-slate-400 font-bold uppercase tracking-wider">
                                        <th className="pb-3 px-2">Time</th>
                                        <th className="pb-3 px-2">Admin</th>
                                        <th className="pb-3 px-2">Action</th>
                                        <th className="pb-3 px-2">Target User</th>
                                        <th className="pb-3 px-2">Detail</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-50 dark:divide-slate-800/50">
                                    {auditLogs.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="py-10 text-center text-slate-400 italic">No activity logs found.</td>
                                        </tr>
                                    ) : (
                                        auditLogs.map((log) => (
                                            <tr key={log.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                                                <td className="py-3 px-2 text-slate-400">{new Date(log.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
                                                <td className="py-3 px-2">
                                                    <div className="flex items-center gap-2">
                                                        <div className="w-6 h-6 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center text-[10px] font-bold">
                                                            {log.changed_by_username?.charAt(0).toUpperCase()}
                                                        </div>
                                                        <span className="font-medium">{log.changed_by_username}</span>
                                                    </div>
                                                </td>
                                                <td className="py-3 px-2">
                                                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${log.action === 'update_permissions' ? 'bg-blue-100 text-blue-600' :
                                                        log.action === 'update_level' ? 'bg-purple-100 text-purple-600' :
                                                            'bg-slate-100 text-slate-600'
                                                        }`}>
                                                        {log.action.replace('update_', '')}
                                                    </span>
                                                </td>
                                                <td className="py-3 px-2 font-medium">{log.username || log.user_id}</td>
                                                <td className="py-3 px-2">
                                                    <div className="max-w-[200px] truncate">
                                                        {log.changes_summary ? (
                                                            Object.entries(log.changes_summary).map(([key, val]: [string, any]) => (
                                                                <span key={key} className="inline-block mr-2 px-1.5 py-0.5 bg-slate-100 dark:bg-slate-800 rounded border border-slate-200 dark:border-slate-700 text-[9px]">
                                                                    <span className="text-slate-400">{key}:</span> {typeof val === 'object' ? (val.new || val.to) : val}
                                                                </span>
                                                            ))
                                                        ) : 'No summary'}
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* System Logs Section */}
                    <div className="lg:col-span-1 glass-panel border border-white/50 dark:border-white/10 bg-white/30 dark:bg-[#1e293b]/60 backdrop-blur-md rounded-xl p-0 overflow-hidden flex flex-col h-[600px] lg:h-auto shadow-sm">
                        <div className="p-4 border-b border-gray-200 dark:border-slate-700 bg-gray-50/50 dark:bg-slate-800/50 flex flex-col gap-3">
                            <div className="flex justify-between items-center">
                                <h3 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                                    <Terminal className="w-4 h-4 text-slate-400" />
                                    Live System Logs
                                </h3>
                                <div className="flex gap-1">
                                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/50"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/50"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-green-500/50"></span>
                                </div>
                            </div>

                            <div className="flex items-center justify-between gap-2">
                                <select
                                    value={logLevel}
                                    onChange={(e) => setLogLevel(e.target.value)}
                                    className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md text-[10px] font-bold py-1 px-2 focus:outline-none focus:ring-1 focus:ring-primary"
                                >
                                    <option value="DEBUG">DEBUG (+ALL)</option>
                                    <option value="INFO">INFO ONLY</option>
                                    <option value="WARNING">WARNING+</option>
                                    <option value="ERROR">ERROR ONLY</option>
                                </select>

                                <div className="flex gap-1">
                                    <button
                                        onClick={() => handleExportLogs(1)}
                                        className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-[9px] font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                    >
                                        1H
                                    </button>
                                    <button
                                        onClick={() => handleExportLogs(24)}
                                        className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-[9px] font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                    >
                                        TEXT
                                    </button>
                                    <button
                                        onClick={handleCopyLogs}
                                        className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-[9px] font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                    >
                                        {copied ? 'COPIED' : 'COPY'}
                                    </button>
                                    <button
                                        onClick={() => handleSendTelegram()}
                                        disabled={sendingTelegram}
                                        className="px-2 py-1 bg-slate-100 dark:bg-slate-800 rounded text-[9px] font-bold hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                                    >
                                        {sendingTelegram ? '...' : 'TG BOT'}
                                    </button>
                                    <button
                                        onClick={() => handleExportLogs()}
                                        className="px-2 py-1 bg-blue-500 text-white rounded text-[9px] font-bold hover:bg-blue-600 transition-colors"
                                    >
                                        {isExporting ? '...' : 'EXPORT ALL'}
                                    </button>
                                </div>
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
