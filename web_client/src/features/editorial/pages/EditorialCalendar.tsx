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
    Edit3,
    Globe,
    X,
    Save
} from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialCalendar: React.FC = () => {
    const [queue, setQueue] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('all');
    const [actionMsg, setActionMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    // Reschedule Modal State
    const [editingItem, setEditingItem] = useState<any | null>(null);
    const [editDate, setEditDate] = useState('');
    const [editTime, setEditTime] = useState('');
    const [savingEdit, setSavingEdit] = useState(false);

    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'Horario Local';

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

    const handleOpenEdit = (item: any) => {
        setEditingItem(item);
        if (item.scheduled_for) {
            const normalized = item.scheduled_for.endsWith('Z') || item.scheduled_for.includes('+')
                ? item.scheduled_for
                : `${item.scheduled_for}Z`;
            const d = new Date(normalized);
            if (!isNaN(d.getTime())) {
                const year = d.getFullYear();
                const month = String(d.getMonth() + 1).padStart(2, '0');
                const day = String(d.getDate()).padStart(2, '0');
                const hours = String(d.getHours()).padStart(2, '0');
                const mins = String(d.getMinutes()).padStart(2, '0');
                setEditDate(`${year}-${month}-${day}`);
                setEditTime(`${hours}:${mins}`);
            }
        }
    };

    const handleSaveReschedule = async () => {
        if (!editingItem || !editDate || !editTime) return;
        setSavingEdit(true);
        try {
            const localDateTime = new Date(`${editDate}T${editTime}:00`);
            const isoUtc = localDateTime.toISOString();

            await api.pubUpdateQueueItem({
                id: editingItem.id,
                scheduled_for: isoUtc,
            });

            setActionMsg({ type: 'success', text: 'Horario de publicación actualizado con éxito' });
            setEditingItem(null);
            fetchQueue();
        } catch (err: any) {
            setActionMsg({ type: 'error', text: err.message || 'Error al actualizar horario' });
        } finally {
            setSavingEdit(false);
        }
    };

    const renderLocalDateTime = (dateStr: string) => {
        if (!dateStr) return 'Fecha no definida';
        const normalized = dateStr.endsWith('Z') || dateStr.includes('+') ? dateStr : `${dateStr}Z`;
        const d = new Date(normalized);
        if (isNaN(d.getTime())) return dateStr;
        return d.toLocaleString('es-ES', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true,
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
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-slate-800 text-gray-400">
                        {status}
                    </span>
                );
        }
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <CalendarIcon className="w-7 h-7 text-indigo-400" /> Agenda y Cola de Publicación
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Programación automática de lanzamientos en canales de Telegram y páginas oficiales.
                    </p>
                </div>

                {/* Status Filter and Refresh */}
                <div className="flex items-center gap-3">
                    <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/5 text-xs text-gray-400 font-mono">
                        <Globe className="w-3.5 h-3.5 text-indigo-400" />
                        <span>Hora Local: {userTimeZone}</span>
                    </div>

                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="px-3.5 py-2.5 bg-slate-900 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
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
                        <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
                    </button>
                </div>
            </div>

            {actionMsg && (
                <div
                    className={`p-3.5 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
                        actionMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {actionMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{actionMsg.text}</span>
                </div>
            )}

            {/* List / Timeline View */}
            <div className="bg-slate-900/40 border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl">
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
                                            <span className="flex items-center gap-1.5 font-mono text-indigo-300">
                                                <Clock className="w-3.5 h-3.5 text-indigo-400" />
                                                {renderLocalDateTime(item.scheduled_for)}
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
                                            onClick={() => handleOpenEdit(item)}
                                            className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-bold flex items-center gap-1 transition-all border border-indigo-500/30"
                                        >
                                            <Edit3 className="w-3.5 h-3.5" /> Editar Horario
                                        </button>
                                    )}
                                    {item.status === 'failed' && (
                                        <button
                                            onClick={() => handleRetry(item.id)}
                                            className="px-3 py-1.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 text-xs font-bold transition-all"
                                        >
                                            Reintentar
                                        </button>
                                    )}
                                    {(item.status === 'pending' || item.status === 'scheduled') && (
                                        <button
                                            onClick={() => handleCancel(item.id)}
                                            className="px-3 py-1.5 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold transition-all"
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

            {/* Reschedule Quick Modal */}
            {editingItem && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="relative w-full max-w-md bg-slate-900 border border-white/10 rounded-3xl shadow-2xl overflow-hidden p-6 space-y-5">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <div>
                                <h3 className="text-sm font-bold text-white">Editar Horario de Publicación</h3>
                                <p className="text-xs text-gray-400 mt-0.5">
                                    {editingItem.series} • Vol. {editingItem.volume}
                                </p>
                            </div>
                            <button onClick={() => setEditingItem(null)} className="p-1 text-gray-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-4 text-xs">
                            <div className="text-gray-400 bg-white/[0.02] p-3 rounded-xl border border-white/5 flex items-center justify-between">
                                <span>Zona Horaria:</span>
                                <strong className="text-indigo-300">{userTimeZone}</strong>
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Fecha</label>
                                <input
                                    type="date"
                                    value={editDate}
                                    onChange={(e) => setEditDate(e.target.value)}
                                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Hora Local</label>
                                <input
                                    type="time"
                                    value={editTime}
                                    onChange={(e) => setEditTime(e.target.value)}
                                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div className="pt-2 border-t border-white/10 flex items-center justify-end gap-2">
                            <button
                                onClick={() => setEditingItem(null)}
                                className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleSaveReschedule}
                                disabled={savingEdit}
                                className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                            >
                                {savingEdit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                                <span>Guardar Nuevo Horario</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
