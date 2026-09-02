import React, { useState, useEffect } from 'react';
import {
    GitMerge,
    Copy,
    HardDrive,
    Trash2,
    RefreshCw,
    Search,
    AlertTriangle,
    AlertCircle,
    CheckCircle2,
    Sparkles,
    Loader2,
    Info,
    ArrowRight
} from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialDuplicates: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'hash' | 'ai-series'>('hash');
    const [duplicates, setDuplicates] = useState<any[]>([]);
    const [aiSuggestions, setAiSuggestions] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const loadData = async () => {
        setLoading(true);
        try {
            const hashRes = await api.getDuplicates().catch(() => ({ duplicates: [] }));
            setDuplicates(hashRes?.duplicates || hashRes?.items || []);

            const aiRes = await api.getAiDuplicates().catch(() => ({ suggestions: [] }));
            setAiSuggestions(aiRes?.suggestions || []);
        } catch (err) {
            console.error('Error cargando duplicados:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleClearHashHistory = async () => {
        if (!confirm('¿Limpiar el historial de conflictos de bitstream?')) return;
        try {
            await api.clearDuplicateHistory();
            setStatusMsg({ type: 'success', text: 'Historial de conflictos purgado correctamente' });
            loadData();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al purgar historial' });
        }
    };

    const handleMergeSeries = async (sug: any) => {
        if (!confirm(`¿Fusionar "${sug.series_b?.name}" dentro de "${sug.series_a?.name}"?`)) return;
        try {
            await api.mergeSeries(sug.series_a?.hash, sug.series_b?.hash, sug.suggested_name);
            setStatusMsg({ type: 'success', text: 'Series fusionadas con éxito' });
            loadData();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al fusionar' });
        }
    };

    const filteredDuplicates = duplicates.filter((d) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return (
            d.title?.toLowerCase().includes(q) ||
            d.original?.toLowerCase().includes(q) ||
            d.duplicate?.toLowerCase().includes(q) ||
            d.hash?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <GitMerge className="w-7 h-7 text-indigo-400" /> Centro de Resolución & Duplicados
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Detección y resolución de conflictos de bitstream por hash SHA-256 / MD5 y sugerencias de fusión por IA.
                    </p>
                </div>

                {/* Tab Switcher */}
                <div className="flex items-center gap-1.5 p-1 bg-slate-900 border border-white/10 rounded-2xl">
                    <button
                        type="button"
                        onClick={() => setActiveTab('hash')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            activeTab === 'hash'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        <HardDrive className="w-4 h-4" /> Duplicados por Hash ({duplicates.length})
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab('ai-series')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            activeTab === 'ai-series'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        <Sparkles className="w-4 h-4" /> Fusión de Series IA ({aiSuggestions.length})
                    </button>
                </div>
            </div>

            {statusMsg && (
                <div
                    className={`p-3.5 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* TAB 1: Hash Bitstream Duplicates */}
            {activeTab === 'hash' && (
                <div className="space-y-6">
                    {/* Top Overview Cards (2K Widescreen) */}
                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                        <div className="lg:col-span-8 p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex items-start gap-4 shadow-xl backdrop-blur-xl">
                            <div className="p-3.5 rounded-2xl bg-amber-500/10 text-amber-400 shrink-0">
                                <Info className="w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-sm font-bold text-white">Duplicados Físicos por Hash</h3>
                                <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                                    Archivos EPUB con contenido binario 100% idéntico. Fueron omitidos para evitar registros redundantes en la base de datos. Se recomienda borrar los duplicados físicamente del disco.
                                </p>
                            </div>
                        </div>

                        <div className="lg:col-span-4 p-6 rounded-3xl bg-slate-900/50 border border-white/10 flex flex-col justify-between shadow-xl backdrop-blur-xl">
                            <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Conflictos de Bitstream</span>
                                <span className="text-3xl font-black text-amber-400 font-mono">{duplicates.length}</span>
                            </div>
                            <button
                                type="button"
                                onClick={handleClearHashHistory}
                                className="w-full mt-4 py-2.5 px-4 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs font-bold flex items-center justify-center gap-2 border border-red-500/20 transition-all"
                            >
                                <Trash2 className="w-4 h-4" /> Limpiar Historial de Conflictos
                            </button>
                        </div>
                    </div>

                    {/* Search & Actions Bar */}
                    <div className="flex flex-col sm:flex-row gap-3">
                        <div className="relative flex-1">
                            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Filtrar por título, autor, ruta de archivo o hash..."
                                className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                            />
                        </div>
                        <button
                            onClick={loadData}
                            className="px-4 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-bold border border-white/10 flex items-center gap-2 transition-all shrink-0"
                        >
                            <RefreshCw className="w-4 h-4" /> Refrescar
                        </button>
                    </div>

                    {/* Duplicates List */}
                    <div className="bg-slate-900/40 border border-white/10 rounded-3xl overflow-hidden shadow-2xl backdrop-blur-xl">
                        {loading ? (
                            <div className="py-24 flex items-center justify-center">
                                <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                            </div>
                        ) : filteredDuplicates.length === 0 ? (
                            <div className="py-24 text-center text-gray-500 text-xs">
                                No se registran conflictos de bitstream o duplicados por hash.
                            </div>
                        ) : (
                            <div className="divide-y divide-white/5">
                                {filteredDuplicates.map((item, idx) => (
                                    <div
                                        key={idx}
                                        className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors"
                                    >
                                        <div className="space-y-1 min-w-0 flex-1">
                                            <div className="text-xs font-bold text-white truncate">{item.title}</div>
                                            <div className="text-[11px] text-gray-400">{item.author || 'Autor desconocido'}</div>
                                            <div className="text-[10px] font-mono text-gray-500 truncate pt-1">
                                                <span>Hash: {item.hash}</span>
                                            </div>
                                        </div>

                                        <div className="text-[11px] font-mono space-y-1 text-right shrink-0">
                                            <div className="text-emerald-400 flex items-center justify-end gap-1">
                                                <span>● Conservado: {item.original}</span>
                                            </div>
                                            <div className="text-red-400 flex items-center justify-end gap-1">
                                                <span>▲ Duplicado: {item.duplicate}</span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* TAB 2: AI Series Merge Suggestions */}
            {activeTab === 'ai-series' && (
                <div className="space-y-4">
                    {loading ? (
                        <div className="py-24 flex items-center justify-center">
                            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                        </div>
                    ) : aiSuggestions.length === 0 ? (
                        <div className="py-24 text-center text-gray-500 text-xs bg-slate-900/30 rounded-3xl border border-white/5">
                            No hay propuestas de fusión de series pendientes.
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
                            {aiSuggestions.map((sug, idx) => (
                                <div
                                    key={idx}
                                    className="p-6 rounded-3xl bg-slate-900/50 border border-white/10 space-y-4 shadow-xl backdrop-blur-xl"
                                >
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-bold text-indigo-400">Propuesta #{idx + 1}</span>
                                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase bg-purple-500/20 text-purple-300 border border-purple-500/30">
                                            {Math.round((sug.confidence || 0.9) * 100)}% Confianza
                                        </span>
                                    </div>

                                    <div className="grid grid-cols-2 gap-3 text-xs bg-black/40 p-3.5 rounded-2xl border border-white/5">
                                        <div>
                                            <div className="text-[10px] text-gray-400 font-bold uppercase">Serie A (Destino)</div>
                                            <div className="font-bold text-white mt-0.5">{sug.series_a?.name}</div>
                                            <div className="text-[10px] text-gray-500">{sug.series_a?.count} tomos</div>
                                        </div>
                                        <div>
                                            <div className="text-[10px] text-gray-400 font-bold uppercase">Serie B (Origen)</div>
                                            <div className="font-bold text-slate-300 mt-0.5">{sug.series_b?.name}</div>
                                            <div className="text-[10px] text-gray-500">{sug.series_b?.count} tomos</div>
                                        </div>
                                    </div>

                                    <div className="text-xs text-gray-400 leading-relaxed italic">
                                        Motivo: {sug.reason || 'Nombres canónicos coincidentes en inglés y romaji.'}
                                    </div>

                                    <button
                                        type="button"
                                        onClick={() => handleMergeSeries(sug)}
                                        className="w-full py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all"
                                    >
                                        <GitMerge className="w-4 h-4" /> Fusionar Series Ahora
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
