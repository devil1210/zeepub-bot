import React, { useState, useEffect } from 'react';
import {
    Clock,
    CheckCircle,
    XCircle,
    FileText,
    AlertTriangle,
    RefreshCw,
    Hash
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';

export const UploadHistoryDashboard: React.FC = () => {
    const { settings } = useTheme();
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const data = await api.getUploadHistory(100, 0);
            setHistory(data);
        } catch (error) {
            console.error('Error fetching upload history:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
        const interval = setInterval(fetchHistory, 30000); // Auto-refresh every 30s
        return () => clearInterval(interval);
    }, []);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'success':
                return (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-green-500/10 text-green-400 border border-green-500/10 text-[10px] font-black uppercase tracking-widest">
                        <CheckCircle className="w-3.5 h-3.5" /> Success
                    </span>
                );
            case 'error':
                return (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-red-500/10 text-red-400 border border-red-500/10 text-[10px] font-black uppercase tracking-widest">
                        <XCircle className="w-3.5 h-3.5" /> Error
                    </span>
                );
            case 'duplicate_rejected':
            case 'rejected':
                return (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-yellow-500/10 text-yellow-400 border border-yellow-500/10 text-[10px] font-black uppercase tracking-widest">
                        <AlertTriangle className="w-3.5 h-3.5" /> Duplicate
                    </span>
                );
            default:
                return (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-500/10 text-gray-400 border border-gray-500/10 text-[10px] font-black uppercase tracking-widest">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="flex flex-col gap-6 animate-in fade-in duration-500 pt-4">

            {/* Header / Stats could go here later */}

            {/* History Table */}
            <div className="glass-panel border border-white/5 rounded-premium p-8 shadow-sm flex flex-col">
                <div className="flex items-center justify-between mb-8">
                    <h3 className="text-sm font-black text-white uppercase tracking-widest flex items-center gap-3">
                        <Clock className="text-blue-500 w-5 h-5" />
                        Recent Uploads
                    </h3>
                    <button
                        onClick={fetchHistory}
                        className="p-2 hover:bg-white/5 rounded-full transition-colors"
                    >
                        <RefreshCw className={`w-4 h-4 text-gray-500 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 font-black uppercase tracking-wider">
                                <th className="pb-4 px-2">Time</th>
                                <th className="pb-4 px-2">File</th>
                                <th className="pb-4 px-2">Status</th>
                                <th className="pb-4 px-2">Details</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {history.length === 0 ? (
                                <tr>
                                    <td colSpan={4} className="py-16 text-center text-gray-500 font-medium italic">
                                        No uploads recorded yet.
                                    </td>
                                </tr>
                            ) : (
                                history.map((item) => (
                                    <tr key={item.id} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="py-4 px-2 text-gray-500 tabular-nums whitespace-nowrap">
                                            {item.created_at ? new Date(item.created_at).toLocaleString([], {
                                                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
                                            }) : '-'}
                                        </td>
                                        <td className="py-4 px-2">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2 text-gray-200 font-bold">
                                                    <FileText className="w-3.5 h-3.5 opacity-50" />
                                                    {item.filename}
                                                </div>
                                                {item.book_hash && (
                                                    <div className="flex items-center gap-1 text-[9px] text-gray-600 font-mono">
                                                        <Hash className="w-2.5 h-2.5" />
                                                        {item.book_hash.substring(0, 16)}...
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="py-4 px-2">
                                            {getStatusBadge(item.status)}
                                        </td>
                                        <td className="py-4 px-2">
                                            <div className="max-w-[300px] text-gray-500 text-[10px]">
                                                {item.error_message ? (
                                                    <span className="text-red-400 font-medium">{item.error_message}</span>
                                                ) : item.final_path ? (
                                                    <span className="text-gray-500 font-mono opacity-70 break-all">{item.final_path}</span>
                                                ) : (
                                                    <span className="opacity-30">-</span>
                                                )}
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
