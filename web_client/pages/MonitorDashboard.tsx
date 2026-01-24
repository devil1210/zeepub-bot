import React, { useState, useEffect } from 'react';
import {
    Activity,
    Users,
    Library,
    CloudDownload,
    Cpu,
    TrendingUp,
    RefreshCw,
    Terminal,
    Search,
    Bell
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

export const MonitorDashboard: React.FC = () => {
    const { settings } = useTheme();
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [auditLogs, setAuditLogs] = useState<any[]>([]);
    const [auditLoading, setAuditLoading] = useState(false);
    const [logs, setLogs] = useState<{ time: string, level: string, msg: string, color: string, timestamp?: number }[]>([]);
    const [logLevel, setLogLevel] = useState('INFO');
    const [isExporting, setIsExporting] = useState(false);
    const [sendingTelegram, setSendingTelegram] = useState(false);
    const [copied, setCopied] = useState(false);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await api.getAdminStats();
            setStats(data);
        } catch (error) {
            console.error('Error fetching stats:', error);
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
                }, 1000); // Wait longer
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
        fetchAuditLogs();
        fetchSystemLogs();

        const statsInterval = setInterval(fetchStats, 60000);
        const logsInterval = setInterval(fetchSystemLogs, 5000); // 5 sec for monitor

        return () => {
            clearInterval(statsInterval);
            clearInterval(logsInterval);
        };
    }, [logLevel]);

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">

            {/* Metric Cards - Enhanced style */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="glass-panel p-6 rounded-3xl flex items-start justify-between relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Active Users</p>
                        <h3 className="text-4xl font-bold text-white mt-1 tracking-tight">
                            {loading ? '...' : (stats?.totalUsers || 0).toLocaleString()}
                        </h3>
                        <div className={`flex items-center mt-3 text-[10px] font-bold uppercase tracking-tight ${stats?.users7d > 0 ? 'text-green-500' : 'text-gray-400'}`}>
                            {stats?.users7d > 0 ? <TrendingUp className="w-3.5 h-3.5 mr-1" /> : <Activity className="w-3.5 h-3.5 mr-1" />}
                            {loading ? '...' : `+${stats?.users7d || 0} nuevos esta semana`}
                        </div>
                    </div>
                    <div className="p-4 bg-blue-500/20 rounded-2xl text-blue-400 border border-blue-500/20 shadow-[0_0_20px_rgba(59,130,246,0.1)] relative z-10">
                        <Users className="w-6 h-6" />
                    </div>
                    {/* Background Glow */}
                    <div
                        className="absolute -right-6 -bottom-6 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:bg-blue-500/20 group-hover:scale-110 transition-all duration-700 pointer-events-none"
                        style={{ opacity: settings.cardGlowIntensity }}
                    ></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl flex items-start justify-between relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Library Index</p>
                        <h3 className="text-4xl font-bold text-white mt-1 tracking-tight">
                            {loading ? '...' : (stats?.totalBooks || 0).toLocaleString()}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-gray-400 font-bold uppercase tracking-tight">
                            <Library className="w-3.5 h-3.5 mr-1" />
                            {loading ? '...' : `${stats?.storageUsedGB || 0} GB en uso`}
                        </div>
                    </div>
                    <div className="p-4 bg-purple-500/20 rounded-2xl text-purple-400 border border-purple-500/20 shadow-[0_0_20px_rgba(168,85,247,0.1)] relative z-10">
                        <Library className="w-6 h-6" />
                    </div>
                    {/* Background Glow */}
                    <div
                        className="absolute -right-6 -bottom-6 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl group-hover:bg-purple-500/20 group-hover:scale-110 transition-all duration-700 pointer-events-none"
                        style={{ opacity: settings.cardGlowIntensity }}
                    ></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl flex items-start justify-between relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Downloads (24h)</p>
                        <h3 className="text-4xl font-bold text-white mt-1 tracking-tight">
                            {loading ? '...' : (stats?.downloads24h || 0).toLocaleString()}
                        </h3>
                        <div className={`flex items-center mt-3 text-[10px] font-bold uppercase tracking-tight ${(stats?.downloads24h || 0) >= (stats?.downloadsPrev24h || 0) ? 'text-green-500' : 'text-red-400'}`}>
                            <TrendingUp className={`w-3.5 h-3.5 mr-1 ${(stats?.downloads24h || 0) < (stats?.downloadsPrev24h || 0) ? 'rotate-180' : ''}`} />
                            {loading ? '...' : `${stats?.downloads24h || 0} vs ${stats?.downloadsPrev24h || 0} ayer`}
                        </div>
                    </div>
                    <div className="p-4 bg-emerald-500/20 rounded-2xl text-emerald-400 border border-emerald-500/20 shadow-[0_0_20px_rgba(16,185,129,0.1)] relative z-10">
                        <CloudDownload className="w-6 h-6" />
                    </div>
                    {/* Background Glow */}
                    <div
                        className="absolute -right-6 -bottom-6 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:bg-emerald-500/20 group-hover:scale-110 transition-all duration-700 pointer-events-none"
                        style={{ opacity: settings.cardGlowIntensity }}
                    ></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl flex items-start justify-between relative overflow-hidden group hover:scale-[1.02] transition-all duration-300">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">System Uptime</p>
                        <h3 className="text-4xl font-bold text-white mt-1 tracking-tight">
                            {loading ? '...' : stats?.uptime || '0h 0m'}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-green-500 font-bold uppercase tracking-tight">
                            <Activity className="w-3.5 h-3.5 mr-1" />
                            {loading ? '...' : `${stats?.activeSessions || 0} sesiones activas`}
                        </div>
                    </div>
                    <div className="p-4 bg-amber-500/20 rounded-2xl text-amber-400 border border-amber-500/20 shadow-[0_0_20px_rgba(245,158,11,0.1)] relative z-10">
                        <Cpu className="w-6 h-6" />
                    </div>
                    {/* Background Glow */}
                    <div className="absolute -right-6 -bottom-6 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl group-hover:bg-amber-500/20 group-hover:scale-110 transition-all duration-700"></div>
                </div>
            </div>

            {/* Recent Activity Table - Image 3 style */}
            <div className="glass-panel border border-white/5 rounded-3xl p-8 shadow-sm flex flex-col">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Activity className="text-purple-500 w-5 h-5" />
                        Recent Activity
                    </h3>
                    <button
                        onClick={fetchAuditLogs}
                        className="p-2 hover:bg-white/5 rounded-full transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 text-gray-500 ${auditLoading ? 'animate-spin' : ''}`} />
                    </button>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 font-black uppercase tracking-wider">
                                <th className="pb-4 px-2">Time</th>
                                <th className="pb-4 px-2">Admin</th>
                                <th className="pb-4 px-2">Action</th>
                                <th className="pb-4 px-2">Target User</th>
                                <th className="pb-4 px-2">Detail</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {auditLogs.length === 0 ? (
                                <tr>
                                    <td colSpan={5} className="py-16 text-center text-gray-500 font-medium italic">No activity logs found.</td>
                                </tr>
                            ) : (
                                auditLogs.map((log) => (
                                    <tr key={log.id} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="py-4 px-2 text-gray-500 tabular-nums">{new Date(log.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td>
                                        <td className="py-4 px-2">
                                            <div className="flex items-center gap-3">
                                                <div className="w-7 h-7 rounded-lg bg-white/5 flex items-center justify-center text-[10px] font-black border border-white/5">
                                                    {log.changed_by_username?.charAt(0).toUpperCase()}
                                                </div>
                                                <span className="font-bold text-gray-200">{log.changed_by_username}</span>
                                            </div>
                                        </td>
                                        <td className="py-4 px-2">
                                            <span className={`px-2.5 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${log.action === 'update_permissions' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/10' :
                                                log.action === 'update_level' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/10' :
                                                    'bg-gray-500/10 text-gray-400 border border-white/5'
                                                }`}>
                                                {log.action.replace('update_', '')}
                                            </span>
                                        </td>
                                        <td className="py-4 px-2 font-bold text-gray-300">{log.username || log.user_id}</td>
                                        <td className="py-4 px-2">
                                            <div className="max-w-[300px] truncate text-gray-500">
                                                {log.changes_summary ? (
                                                    Object.entries(log.changes_summary).map(([key, val]: [string, any]) => {
                                                        // Safe rendering for values to avoid Error #31 (Objects are not valid as a React child)
                                                        const renderSafeValue = (v: any) => {
                                                            if (v === null || v === undefined) return 'N/A';
                                                            if (typeof v === 'object') {
                                                                // Handle {id, name} objects or simple from/to wrappers
                                                                const inner = v.new !== undefined ? v.new : (v.to !== undefined ? v.to : v);
                                                                if (inner === null || inner === undefined) return 'N/A';
                                                                if (typeof inner === 'object') {
                                                                    return inner.name || inner.username || JSON.stringify(inner);
                                                                }
                                                                return String(inner);
                                                            }
                                                            return String(v);
                                                        };

                                                        return (
                                                            <span key={key} className="inline-block mr-3 px-2 py-0.5 bg-black/20 rounded-md border border-white/5 text-[9px]">
                                                                <span className="text-gray-600 font-bold lowercase">{key}:</span> <span className="text-primary">{renderSafeValue(val)}</span>
                                                            </span>
                                                        );
                                                    })
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

            {/* Live System Logs - Bottom section */}
            <div className="glass-panel rounded-3xl p-0 overflow-hidden flex flex-col h-[600px] border border-white/5 bg-black/20">
                <div className="px-6 py-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center flex-wrap gap-4">
                    <div className="flex items-center gap-4">
                        <h3 className="text-[10px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                            <Terminal className="w-4 h-4 text-gray-500" /> Live System Logs
                        </h3>
                        <div className="h-4 w-px bg-white/10 hidden sm:block"></div>
                        <select
                            value={logLevel}
                            onChange={(e) => setLogLevel(e.target.value)}
                            className="bg-black/40 border border-white/10 rounded-lg text-[10px] font-bold text-gray-400 px-2 py-1 focus:outline-none focus:border-primary transition-colors cursor-pointer"
                        >
                            <option value="DEBUG">DEBUG (+ALL)</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                        </select>
                    </div>

                    <div className="flex items-center gap-3">
                        {/* Download presets */}
                        <div className="flex items-center bg-black/40 border border-white/10 rounded-lg p-0.5">
                            <button
                                onClick={() => handleExportLogs(1)}
                                disabled={isExporting}
                                className="px-2 py-1 text-[9px] font-bold text-gray-400 hover:text-white transition-colors border-r border-white/5"
                                title="Download last hour"
                            >
                                1H
                            </button>
                            <button
                                onClick={() => handleExportLogs(24)}
                                disabled={isExporting}
                                className="px-2 py-1 text-[9px] font-bold text-gray-400 hover:text-white transition-colors border-r border-white/5"
                                title="Download last 24h"
                            >
                                24H
                            </button>
                            <button
                                onClick={() => handleExportLogs()}
                                disabled={isExporting}
                                className="px-2 py-1 text-[9px] font-bold text-gray-400 hover:text-white transition-colors"
                                title="Download all buffered logs"
                            >
                                ALL
                            </button>
                        </div>

                        {/* Telegram presets */}
                        <div className="flex items-center bg-blue-500/10 border border-blue-500/20 rounded-lg p-0.5">
                            <button
                                onClick={() => handleSendTelegram(1)}
                                disabled={sendingTelegram}
                                className="px-2 py-1 text-[9px] font-black text-blue-400 hover:text-blue-300 transition-colors border-r border-blue-500/10 flex items-center gap-1"
                                title="Send last hour to Telegram"
                            >
                                🤖 1H
                            </button>
                            <button
                                onClick={() => handleSendTelegram()}
                                disabled={sendingTelegram}
                                className="px-2 py-1 text-[9px] font-black text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
                                title="Send all to Telegram"
                            >
                                🤖 ALL
                            </button>
                        </div>

                        <div className="h-4 w-px bg-white/10"></div>

                        <button
                            onClick={handleCopyLogs}
                            className="px-3 py-1 text-[9px] font-black text-gray-400 hover:text-white transition-colors border border-white/10 rounded-lg bg-black/40"
                        >
                            {copied ? 'COPIED!' : 'COPY'}
                        </button>
                    </div>
                    <div className="flex gap-1.5 px-2 hidden sm:flex">
                        <span className="w-2.5 h-2.5 rounded-full bg-red-500/20"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/20"></span>
                        <span className="w-2.5 h-2.5 rounded-full bg-green-500/20"></span>
                    </div>
                </div>
                <div className="flex-1 p-6 font-mono text-[11px] overflow-y-auto leading-relaxed scrollbar-hide">
                    <div className="space-y-1.5">
                        {logs.map((log, i) => (
                            <div key={i} className="text-gray-500 flex gap-4">
                                <span className="opacity-40 shrink-0">[{log.time}]</span>
                                <div className="flex gap-2">
                                    <span className={`${log.color} font-black uppercase w-12 tracking-tighter`}>{log.level}</span>
                                    <span className="text-gray-400">: {log.msg}</span>
                                </div>
                            </div>
                        ))}
                        <div className="text-primary animate-pulse ml-16">_</div>
                    </div>
                </div>
            </div>
        </div>
    );
};
