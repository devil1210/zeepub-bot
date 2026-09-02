import React, { useState, useEffect } from 'react';
import {
    Calendar as CalendarIcon,
    Clock,
    Send,
    AlertCircle,
    CheckCircle2,
    RefreshCw,
    XCircle,
    Loader2,
    ChevronLeft,
    ChevronRight,
    Sparkles,
    Edit3
} from 'lucide-react';
import { api } from '@shared/services/api';
import { SchedulePostModal } from '../components/SchedulePostModal';

export const EditorialCalendar: React.FC = () => {
    const [queue, setQueue] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [editingItem, setEditingItem] = useState<any | null>(null);

    const fetchQueue = async () => {
        setLoading(true);
        try {
            const filter = statusFilter === 'all' ? undefined : statusFilter;
            const res = await api.pubGetQueue(filter, 100);
            setQueue(res?.items || []);
        } catch (err) {
            console.error('Error cargando cola de publicaciones:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQueue();
    }, [statusFilter]);

    const handleRetry = async (id: number) => {
        try {
            await api.pubRetry(id);
            setActionMsg({ type: 'success', text: 'Publicación reintentada' });
            fetchQueue();
        } catch (err: any) {
            setActionMsg({ type: 'error', text: err.message || 'Error al reintentar' });
        }
    };

    const handleCancel = async (id: number) => {
        if (!confirm('¿Deseas cancelar esta publicación programada?')) return;
        try {
            await api.pubCancel(id);
            setActionMsg({ type: 'success', text: 'Publicación cancelada' });
            fetchQueue();
        } catch (err: any) {
            setActionMsg({ type: 'error', text: err.message || 'Error al cancelar' });
        }
    };

    const handleEditPost = (item: any) => {
        setEditingItem({
            id: item.book_hash,
            book_hash: item.book_hash,
            title: item.series || 'Novela',
            volume: item.volume || 1,
            channel_id: item.channel_id,
            template_id: item.template_id,
            scheduled_for: item.scheduled_for,
        });
    };

    const getStatusPill = (status: string) => {
        const st = (status || '').toLowerCase();
        switch (st) {
            case 'pending':
            case 'scheduled':
            case 'programado':
                return (
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Programado
                    </span>
                );
            case 'sent':
            case 'published':
            case 'completado':
                return (
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" /> Publicado
                    </span>
                );
            case 'failed':
            case 'fallido':
                return (
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/20 flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" /> Fallido
                    </span>
                );
            default:
                return (
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-gray-500/10 text-gray-400 border border-gray-500/20">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <CalendarIcon className="w-6 h-6 text-indigo-400" /> Agenda y Cronograma Editorial
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Calendario de publicaciones programadas para canales de Telegram y páginas de Facebook.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-3.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-bold text-white focus:outline-none focus:border-indigo-500"
                    >
                        <option value="all">Todos los Estados</option>
                        <option value="pending">⏳ Programadas (Pendientes)</option>
                        <option value="sent">✅ Publicadas (Sent)</option>
                        <option value="failed">❌ Fallidas</option>
                    </select>

                    <button
                        onClick={fetchQueue}
                        className="p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white border border-white/10 transition-all active:scale-95"
                        title="Actualizar Cola"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {actionMsg && (
                <div
                    className={`p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${
                        actionMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {actionMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{actionMsg.text}</span>
                </div>
            )}

            {/* List / Timeline View */}
            <div className="bg-slate-900/40 border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {loading ? (
                    <div className="py-24 flex items-center justify-center">
                        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                ) : queue.length === 0 ? (
                    <div className="py-24 text-center text-gray-500 text-xs">
                        No hay publicaciones en cola con el filtro seleccionado.
                    </div>
                ) : (
                    <div className="divide-y divide-white/5">
                        {queue.map((item) => (
                            <div
                                key={item.id}
                                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors"
                            >
                                <div className="flex items-start sm:items-center gap-4 min-w-0">
                                    <div className="p-3 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                                        <Send className="w-5 h-5" />
                                    </div>

                                    <div className="min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span className="text-xs font-bold text-white truncate">
                                                {item.series || 'Novela'}
                                            </span>
                                            <span className="text-[10px] font-black px-1.5 py-0.5 rounded bg-white/10 text-gray-300">
                                                Vol. {item.volume || 1}
                                            </span>
                                            {getStatusPill(item.status)}
                                        </div>

                                        <div className="text-[11px] text-gray-400 flex flex-wrap items-center gap-3">
                                            <span>Destino: <strong className="text-gray-200">{item.channel}</strong> ({item.platform})</span>
                                            <span>•</span>
                                            <span className="flex items-center gap-1">
                                                <Clock className="w-3 h-3 text-indigo-400" />
                                                {new Date(item.scheduled_for).toLocaleString()}
                                            </span>
                                        </div>

                                        {item.error && (
                                            <p className="text-[11px] text-red-400 mt-1 font-mono">
                                                Error: {item.error}
                                            </p>
                                        )}
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex items-center gap-2 self-end sm:self-center">
                                    {(item.status === 'pending' || item.status === 'scheduled') && (
                                        <button
                                            onClick={() => handleEditPost(item)}
                                            className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-bold flex items-center gap-1 transition-all border border-indigo-500/30"
                                        >
                                            <Edit3 className="w-3.5 h-3.5" /> Editar
                                        </button>
                                    )}
                                    {item.status === 'failed' && (
                                        <button
                                            onClick={() => handleRetry(item.id)}
                                            className="px-3 py-1.5 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold transition-all"
                                        >
                                            Reintentar
                                        </button>
                                    )}
                                    {(item.status === 'pending' || item.status === 'scheduled') && (
                                        <button
                                            onClick={() => handleCancel(item.id)}
                                            className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold transition-all"
                                        >
                                            Cancelar
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Edit / Reschedule Modal */}
            <SchedulePostModal
                isOpen={!!editingItem}
                book={editingItem}
                onClose={() => setEditingItem(null)}
                onSuccess={fetchQueue}
            />
        </div>
    );
};

