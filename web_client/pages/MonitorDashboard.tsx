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

export const MonitorDashboard: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [auditLogs, setAuditLogs] = useState<any[]>([]);
    const [auditLoading, setAuditLoading] = useState(false);
    const [logs, setLogs] = useState<{ time: string, level: string, msg: string, color: string }[]>([]);

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

        // Initial simulated logs for visualization
        setLogs([
            { time: '10:42:01', level: 'INFO', msg: 'Worker process started with PID 8821', color: 'text-blue-400' },
            { time: '10:42:05', level: 'INFO', msg: 'Connecting to Telegram API... OK', color: 'text-blue-400' },
            { time: '10:42:06', level: 'WARN', msg: 'High latency detected on webhook (450ms)', color: 'text-yellow-400' },
            { time: '10:43:45', level: 'SUCCESS', msg: 'Library index updated. +12 items.', color: 'text-green-400' }
        ]);

        const interval = setInterval(fetchStats, 60000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">

            {/* Metric Cards - Image 2 style */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="glass-panel p-6 rounded-3xl flex items-start justify-between relative overflow-hidden group">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Active Users</p>
                        <h3 className="text-4xl font-bold text-white mt-2">
                            {loading ? '...' : stats?.totalUsers || '0'}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-green-400 font-bold uppercase tracking-tight">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            +4.5% this week
                        </div>
                    </div>
                    <div className="p-3 bg-blue-500/10 rounded-2xl text-blue-400">
                        <Users className="w-6 h-6" />
                    </div>
                    <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl group-hover:bg-blue-500/10 transition-all duration-500"></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Library Index</p>
                        <h3 className="text-4xl font-bold text-white mt-2">
                            {loading ? '...' : stats?.totalBooks || '0'}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-gray-500 font-bold uppercase tracking-tight">
                            <Library className="w-3 h-3 mr-1" />
                            {stats?.storageUsedGB ? `${stats.storageUsedGB} GB storage` : '0 GB'}
                        </div>
                    </div>
                    <div className="p-3 bg-purple-500/10 rounded-2xl text-purple-400">
                        <Library className="w-6 h-6" />
                    </div>
                    <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-purple-500/5 rounded-full blur-3xl group-hover:bg-purple-500/10 transition-all duration-500"></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Downloads (24h)</p>
                        <h3 className="text-4xl font-bold text-white mt-2">
                            {loading ? '...' : stats?.downloads24h || '0'}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-green-400 font-bold uppercase tracking-tight">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            +12% vs yesterday
                        </div>
                    </div>
                    <div className="p-3 bg-emerald-500/10 rounded-2xl text-emerald-400">
                        <CloudDownload className="w-6 h-6" />
                    </div>
                    <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-emerald-500/5 rounded-full blur-3xl group-hover:bg-emerald-500/10 transition-all duration-500"></div>
                </div>

                <div className="glass-panel p-6 rounded-3xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                    <div className="relative z-10">
                        <p className="text-[10px] font-black text-gray-400 uppercase tracking-widest">System Uptime</p>
                        <h3 className="text-4xl font-bold text-white mt-2">
                            {loading ? '...' : stats?.uptime || '0h 0m'}
                        </h3>
                        <div className="flex items-center mt-3 text-[10px] text-gray-500 font-bold uppercase tracking-tight">
                            <Activity className="w-3 h-3 mr-1" />
                            {stats?.activeSessions || '0'} active sessions
                        </div>
                    </div>
                    <div className="p-3 bg-amber-500/10 rounded-2xl text-amber-400">
                        <Cpu className="w-6 h-6" />
                    </div>
                    <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-amber-500/5 rounded-full blur-3xl group-hover:bg-amber-500/10 transition-all duration-500"></div>
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
                                                    Object.entries(log.changes_summary).map(([key, val]: [string, any]) => (
                                                        <span key={key} className="inline-block mr-3 px-2 py-0.5 bg-black/20 rounded-md border border-white/5 text-[9px]">
                                                            <span className="text-gray-600 font-bold lowercase">{key}:</span> <span className="text-primary">{typeof val === 'object' ? (val.new || val.to) : val}</span>
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

            {/* Live System Logs - Bottom section */}
            <div className="glass-panel rounded-3xl p-0 overflow-hidden flex flex-col h-[500px] border border-white/5 bg-black/20">
                <div className="px-6 py-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                        <Terminal className="w-4 h-4 text-gray-500" /> Live System Logs
                    </h3>
                    <div className="flex gap-1.5 px-2">
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
