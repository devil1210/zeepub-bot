import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    BookOpen,
    Search,
    Edit3,
    Send,
    Image,
    Layers,
    CheckCircle2,
    Calendar,
    Loader2,
    DownloadCloud,
    AlertCircle,
    Tag,
    User,
    Sparkles,
    Filter
} from 'lucide-react';
import { api } from '@shared/services/api';
import { EditorialQuickEditDrawer } from '../components/EditorialQuickEditDrawer';
import { SchedulePostModal } from '../components/SchedulePostModal';

export const EditorialVolumes: React.FC = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const seriesFilterParam = searchParams.get('series') || '';
    const initialMissing = searchParams.get('missing') || 'all';

    const [volumes, setVolumes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [missingFilter, setMissingFilter] = useState(initialMissing);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);

    const [selectedVolumeForEdit, setSelectedVolumeForEdit] = useState<any | null>(null);
    const [selectedVolumeForSchedule, setSelectedVolumeForSchedule] = useState<any | null>(null);

    const fetchVolumes = async () => {
        setLoading(true);
        try {
            const res = await api.getLibraryGrid({
                query: searchQuery || seriesFilterParam || undefined,
                missing_filter: missingFilter === 'all' ? undefined : missingFilter,
                page,
                limit: 24,
                sort_by: 'volume',
            });

            const seriesList = res?.series || [];
            let allVolumes = seriesList.flatMap((s: any) =>
                (s.books || []).map((b: any) => ({
                    ...b,
                    series_name: s.series_english || s.name,
                    series_spanish: s.series_spanish,
                    author: s.author,
                    demography: s.demographics?.[0] || s.demography,
                    cover_image: b.cover_url || s.cover_url || `/api/library/covers/${b.id || b.book_hash}.jpg`,
                }))
            );

            if (allVolumes.length === 0) {
                const volRes = await api.searchVolumes(searchQuery || seriesFilterParam, page, 24);
                const items = volRes?.results || volRes?.items || [];
                allVolumes = items.map((b: any) => ({
                    ...b,
                    series_name: b.series_info?.series_name || b.series_name || b.title,
                    series_spanish: b.series_info?.series_spanish || b.series_spanish,
                    author: b.author || b.series_info?.author,
                    demography: b.demography || b.series_info?.demography,
                    cover_image: b.cover_url || (b.book_hash ? `/api/library/covers/${b.book_hash}.jpg` : null),
                }));
            }

            setVolumes(allVolumes);
            setTotalPages(res?.pagination?.total_pages || res?.total_pages || 1);
            setTotalItems(res?.pagination?.total || allVolumes.length);
        } catch (err) {
            console.error('Error cargando volúmenes:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVolumes();
    }, [page, missingFilter]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        fetchVolumes();
    };

    const getMissingStatus = (vol: any) => {
        const issues: string[] = [];
        if (!vol.series_spanish && !vol.spanish_title) issues.push('Sin Español');
        if (!vol.volume) issues.push('Sin Volumen');
        if (!vol.cover_image && !vol.cover_url) issues.push('Sin Portada');
        if (!vol.author) issues.push('Sin Autor');
        return issues;
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Topbar Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <BookOpen className="w-7 h-7 text-indigo-400" /> Matriz de Volúmenes & Auditoría de EPUBs
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Control individual de tomos, metadatos en español, autoría y publicación a Telegram ({totalItems} volúmenes indexados).
                    </p>
                </div>

                {seriesFilterParam && (
                    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-300">
                        <span>Filtrando por serie: <strong>{seriesFilterParam}</strong></span>
                    </div>
                )}
            </div>

            {/* Metadata Quality Audit Filter Chips */}
            <div className="flex flex-wrap items-center gap-2 p-3 bg-slate-900/40 border border-white/10 rounded-2xl backdrop-blur-xl">
                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mr-2 flex items-center gap-1.5">
                    <Filter className="w-3.5 h-3.5 text-indigo-400" /> Auditoría de Metadatos:
                </span>
                {[
                    { id: 'all', label: '📚 Todos los Volúmenes' },
                    { id: 'missing_spanish', label: '🚨 Sin Título Español' },
                    { id: 'missing_volume', label: '⚠️ Sin Número de Tomo' },
                    { id: 'missing_cover', label: '🖼️ Sin Portada' },
                    { id: 'missing_author', label: '✍️ Sin Autor' },
                    { id: 'missing_demography', label: '👥 Sin Demografía' },
                ].map((chip) => (
                    <button
                        key={chip.id}
                        type="button"
                        onClick={() => {
                            setMissingFilter(chip.id);
                            setPage(1);
                        }}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                            missingFilter === chip.id
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'bg-white/5 text-gray-300 hover:text-white hover:bg-white/10 border border-white/5'
                        }`}
                    >
                        {chip.label}
                    </button>
                ))}
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
                <div className="relative flex-1">
                    <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Buscar por título de tomo, serie, autor o traductor..."
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                </div>
                <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/20 active:scale-95"
                >
                    Buscar
                </button>
            </form>

            {/* Widescreen 2K Card Grid: 1 col on mobile, 2 on sm, 3 on md, 4 on lg, 6 on 2K/ultrawide */}
            {loading ? (
                <div className="py-24 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
            ) : volumes.length === 0 ? (
                <div className="py-24 text-center text-gray-500 text-xs bg-slate-900/30 rounded-3xl border border-white/5">
                    No se encontraron volúmenes con los filtros seleccionados.
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6 gap-5">
                    {volumes.map((vol) => {
                        const issues = getMissingStatus(vol);
                        return (
                            <div
                                key={vol.id || vol.book_hash}
                                className="bg-slate-900/40 border border-white/10 hover:border-indigo-500/40 rounded-3xl overflow-hidden shadow-xl hover:shadow-2xl transition-all flex flex-col group backdrop-blur-xl"
                            >
                                {/* Cover Thumbnail Header */}
                                <div className="relative aspect-[2/3] max-h-56 bg-slate-950 overflow-hidden border-b border-white/5">
                                    <img
                                        src={vol.cover_image || `/api/library/covers/${vol.id || vol.book_hash}.jpg`}
                                        alt={vol.title}
                                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        onError={(e: any) => {
                                            e.target.src = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400';
                                        }}
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none" />

                                    {/* Volume Tag Badge */}
                                    <div className="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full bg-black/70 backdrop-blur-md text-[10px] font-black uppercase text-indigo-300 border border-white/10">
                                        Volumen {vol.volume || '?'}
                                    </div>

                                    {/* Missing Metadata Badges */}
                                    {issues.length > 0 && (
                                        <div className="absolute top-2.5 right-2.5 flex flex-col gap-1 items-end">
                                            {issues.slice(0, 2).map((iss) => (
                                                <span
                                                    key={iss}
                                                    className="px-2 py-0.5 rounded-md bg-red-500/80 backdrop-blur-md text-[9px] font-bold text-white shadow"
                                                >
                                                    {iss}
                                                </span>
                                            ))}
                                        </div>
                                    )}
                                </div>

                                {/* Body Information */}
                                <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                                    <div className="space-y-1">
                                        <h3 className="text-xs font-bold text-white line-clamp-1 group-hover:text-indigo-300 transition-colors">
                                            {vol.series_name || vol.title}
                                        </h3>
                                        <div className="text-[11px] text-gray-400 line-clamp-1 italic">
                                            {vol.series_spanish || vol.spanish_title || 'Sin título en español'}
                                        </div>
                                        <div className="text-[10px] text-gray-500 flex items-center gap-2 pt-1 font-mono">
                                            <span>✍️ {vol.author || 'Desconocido'}</span>
                                            {vol.demography && <span>• {vol.demography}</span>}
                                        </div>
                                    </div>

                                    {/* Action Buttons */}
                                    <div className="pt-2 border-t border-white/5 grid grid-cols-2 gap-2">
                                        <button
                                            type="button"
                                            onClick={() => setSelectedVolumeForEdit(vol)}
                                            className="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 border border-white/5 transition-all"
                                        >
                                            <Edit3 className="w-3 h-3 text-indigo-400" /> Editar
                                        </button>
                                        <button
                                            type="button"
                                            onClick={() => setSelectedVolumeForSchedule(vol)}
                                            className="px-2.5 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 hover:text-white text-[11px] font-bold flex items-center justify-center gap-1 border border-indigo-500/30 transition-all shadow-sm"
                                        >
                                            <Send className="w-3 h-3" /> Publicar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 pt-4">
                    <button
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-bold text-gray-300 hover:text-white disabled:opacity-30"
                    >
                        Anterior
                    </button>
                    <span className="text-xs text-gray-400 px-3 font-mono">
                        Página {page} de {totalPages}
                    </span>
                    <button
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="px-4 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-bold text-gray-300 hover:text-white disabled:opacity-30"
                    >
                        Siguiente
                    </button>
                </div>
            )}

            {/* Quick Edit Drawer */}
            <EditorialQuickEditDrawer
                isOpen={!!selectedVolumeForEdit}
                book={selectedVolumeForEdit}
                onClose={() => setSelectedVolumeForEdit(null)}
                onSuccess={() => {
                    setSelectedVolumeForEdit(null);
                    fetchVolumes();
                }}
            />

            {/* Schedule Post Modal */}
            <SchedulePostModal
                isOpen={!!selectedVolumeForSchedule}
                book={selectedVolumeForSchedule}
                onClose={() => setSelectedVolumeForSchedule(null)}
                onSuccess={() => {
                    setSelectedVolumeForSchedule(null);
                }}
            />
        </div>
    );
};
