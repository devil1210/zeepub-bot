import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Layers,
    Search,
    BookOpen,
    Edit3,
    Table,
    Grid,
    Loader2,
    Sparkles,
    User,
    Tag,
    ChevronLeft,
    ChevronRight,
    Filter,
    Plus
} from 'lucide-react';
import { api } from '@shared/services/api';
import { DataGridEditor } from '@features/admin/pages/DataGridEditor';

export const EditorialSeries: React.FC = () => {
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'visual' | 'datagrid'>('visual');
    const [seriesList, setSeriesList] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalSeries, setTotalSeries] = useState(0);

    // Refs to avoid stale closures in scroll callbacks
    const pageRef = useRef(1);
    const totalPagesRef = useRef(1);
    const loadingRef = useRef(false);
    const loadingMoreRef = useRef(false);

    useEffect(() => {
        pageRef.current = page;
        totalPagesRef.current = totalPages;
        loadingRef.current = loading;
        loadingMoreRef.current = loadingMore;
    }, [page, totalPages, loading, loadingMore]);

    const fetchSeries = async (pageToFetch = 1, append = false) => {
        if (append) setLoadingMore(true);
        else setLoading(true);

        try {
            const res = await api.getLibraryGrid({
                query: searchQuery.trim() || undefined,
                page: pageToFetch,
                limit: 30,
            });
            if (res && res.series) {
                if (append) {
                    setSeriesList((prev) => [...prev, ...res.series]);
                } else {
                    setSeriesList(res.series);
                }
                const computedPages = res?.pagination?.total_pages || res?.total_pages || res?.pages || 1;
                const computedTotal = res?.pagination?.total || res?.total_series || res?.total || res.series.length;
                setTotalPages(computedPages);
                setTotalSeries(computedTotal);
                totalPagesRef.current = computedPages;
            }
        } catch (err) {
            console.error('Error cargando catálogo de series:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    useEffect(() => {
        if (viewMode === 'visual') {
            setPage(1);
            pageRef.current = 1;
            fetchSeries(1, false);
        }
    }, [viewMode]);

    // Infinite scroll listener for visual mode
    useEffect(() => {
        if (viewMode !== 'visual') return;
        const mainEl = document.querySelector('main');

        const handleScroll = () => {
            if (loadingRef.current || loadingMoreRef.current) return;
            if (pageRef.current >= totalPagesRef.current) return;

            const target = mainEl || document.documentElement;
            const scrollTop = target.scrollTop;
            const scrollHeight = target.scrollHeight;
            const clientHeight = target.clientHeight;

            if (scrollTop + clientHeight >= scrollHeight - 350) {
                const nextPage = pageRef.current + 1;
                pageRef.current = nextPage;
                setPage(nextPage);
                fetchSeries(nextPage, true);
            }
        };

        mainEl?.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('scroll', handleScroll, { passive: true });

        return () => {
            mainEl?.removeEventListener('scroll', handleScroll);
            window.removeEventListener('scroll', handleScroll);
        };
    }, [viewMode]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        pageRef.current = 1;
        fetchSeries(1, false);
    };

    const handlePageChange = (newPage: number) => {
        if (newPage < 1 || newPage > totalPages) return;
        setPage(newPage);
        pageRef.current = newPage;
        fetchSeries(newPage, false);
        document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' });
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const getSeriesCover = (s: any) => {
        if (s.coverUrl && (s.coverUrl.startsWith('http') || s.coverUrl.startsWith('/'))) return s.coverUrl;
        if (s.cover_url && (s.cover_url.startsWith('http') || s.cover_url.startsWith('/'))) return s.cover_url;
        const sId = s.series_hash || s.id;
        if (sId) return `/api/library/covers/${sId}.jpg`;
        return null;
    };

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header with View Toggle (Visual vs DataGrid) */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/40 border border-white/10 p-5 rounded-3xl backdrop-blur-xl shadow-xl">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Layers className="w-7 h-7 text-indigo-400" /> Catálogo Editorial & Gestor de Series
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Control global de franquicias, edición masiva en hoja de cálculo y unificación de duplicados ({totalSeries} series).
                    </p>
                </div>

                {/* View Mode Toggle Switcher */}
                <div className="flex items-center gap-1.5 p-1 bg-black/40 border border-white/10 rounded-2xl">
                    <button
                        type="button"
                        onClick={() => setViewMode('visual')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            viewMode === 'visual'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        <Grid className="w-4 h-4" /> Tarjetas Visuales
                    </button>
                    <button
                        type="button"
                        onClick={() => setViewMode('datagrid')}
                        className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                            viewMode === 'datagrid'
                                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white'
                        }`}
                    >
                        <Table className="w-4 h-4" /> Modo DataGrid (Excel)
                    </button>
                </div>
            </div>

            {/* VIEW 1: Visual Cards View */}
            {viewMode === 'visual' ? (
                <div className="space-y-6">
                    {/* Search Bar */}
                    <form onSubmit={handleSearchSubmit} className="flex gap-2">
                        <div className="relative flex-1">
                            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Buscar serie por nombre canónico, título en español, autor o alias..."
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

                    {/* Widescreen Series Grid */}
                    {loading ? (
                        <div className="py-24 flex items-center justify-center">
                            <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                        </div>
                    ) : seriesList.length === 0 ? (
                        <div className="py-24 text-center text-gray-500 text-xs bg-slate-900/30 rounded-3xl border border-white/5">
                            No se encontraron series registradas.
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-6 gap-5">
                            {seriesList.map((s) => {
                                const cover = getSeriesCover(s);
                                const count = s.book_count || s.books?.length || 0;
                                return (
                                    <div
                                        key={s.id || s.series_hash}
                                        onClick={() => navigate(`/app-v2/volumes?series=${encodeURIComponent(s.name || s.series_english || '')}`)}
                                        className="bg-slate-900/40 border border-white/10 hover:border-indigo-500/50 rounded-3xl overflow-hidden shadow-xl hover:shadow-2xl transition-all flex flex-col group cursor-pointer backdrop-blur-xl"
                                    >
                                        {/* Cover Banner */}
                                        <div className="relative aspect-[2/3] max-h-56 bg-slate-950 overflow-hidden border-b border-white/5">
                                            <img
                                                src={cover || 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400'}
                                                alt={s.name}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                                onError={(e: any) => {
                                                    e.target.src = 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=400';
                                                }}
                                            />
                                            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none" />

                                            {/* Volume Count Pill */}
                                            <div className="absolute top-2.5 left-2.5 px-2.5 py-0.5 rounded-full bg-black/70 backdrop-blur-md text-[10px] font-black uppercase text-indigo-300 border border-white/10">
                                                {count} {count === 1 ? 'Tomo' : 'Tomos'}
                                            </div>

                                            {/* Category Tag */}
                                            <div className="absolute bottom-2.5 left-2.5 px-2 py-0.5 rounded-md bg-indigo-500/80 backdrop-blur-md text-[9px] font-black uppercase text-white shadow">
                                                {s.book_type || 'Novela Ligera'}
                                            </div>
                                        </div>

                                        {/* Series Data */}
                                        <div className="p-4 flex-1 flex flex-col justify-between space-y-3">
                                            <div className="space-y-1">
                                                <h3 className="text-xs font-bold text-white line-clamp-1 group-hover:text-indigo-300 transition-colors">
                                                    {s.series_english || s.name}
                                                </h3>
                                                <div className="text-[11px] text-gray-400 line-clamp-1 italic">
                                                    {s.series_spanish || 'Sin título en español'}
                                                </div>
                                                <div className="text-[10px] text-gray-500 flex items-center gap-1 pt-1 font-mono">
                                                    <User className="w-3 h-3 text-indigo-400" />
                                                    <span className="truncate">{s.author || 'Autor desconocido'}</span>
                                                </div>
                                            </div>

                                            {/* Footer Actions */}
                                            <div className="pt-2 border-t border-white/5 flex items-center gap-2">
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/app-v2/series/${s.series_hash || s.id}`);
                                                    }}
                                                    className="flex-1 py-1.5 px-2 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 hover:text-white text-[11px] font-bold border border-indigo-500/30 transition-all flex items-center justify-center gap-1"
                                                >
                                                    <Edit3 className="w-3 h-3" /> Editar Serie
                                                </button>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/app-v2/volumes?series=${encodeURIComponent(s.name || s.series_english || '')}`);
                                                    }}
                                                    className="py-1.5 px-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white text-[11px] font-bold border border-white/5 transition-all flex items-center justify-center gap-1"
                                                    title="Ver volúmenes"
                                                >
                                                    <BookOpen className="w-3 h-3" />
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Infinite Scroll Spinner */}
                    {loadingMore && (
                        <div className="py-6 flex justify-center">
                            <div className="flex items-center gap-2 text-xs text-indigo-400 font-mono">
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Cargando más series...</span>
                            </div>
                        </div>
                    )}

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-between p-4 rounded-3xl bg-slate-900/40 border border-white/10 backdrop-blur-xl shadow-xl mt-6">
                            <button
                                type="button"
                                onClick={() => handlePageChange(page - 1)}
                                disabled={page <= 1 || loading}
                                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-bold flex items-center gap-1.5 transition-all disabled:opacity-30"
                            >
                                <ChevronLeft className="w-4 h-4" /> Anterior
                            </button>

                            <div className="flex items-center gap-2">
                                <span className="text-xs text-gray-400">
                                    Página <span className="font-bold text-white">{page}</span> de <span className="font-bold text-white">{totalPages}</span> ({totalSeries} series)
                                </span>
                            </div>

                            <button
                                type="button"
                                onClick={() => handlePageChange(page + 1)}
                                disabled={page >= totalPages || loading}
                                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 text-xs font-bold flex items-center gap-1.5 transition-all disabled:opacity-30"
                            >
                                Siguiente <ChevronRight className="w-4 h-4" />
                            </button>
                        </div>
                    )}
                </div>
            ) : (
                /* VIEW 2: DataGrid Spreadsheet Mode */
                <div className="bg-slate-950 border border-white/10 rounded-3xl overflow-hidden shadow-2xl p-2 sm:p-4 backdrop-blur-2xl">
                    <DataGridEditor />
                </div>
            )}
        </div>
    );
};
