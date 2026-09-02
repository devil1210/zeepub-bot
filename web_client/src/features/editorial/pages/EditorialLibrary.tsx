import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    Search,
    Grid,
    List,
    BookOpen,
    Layers,
    Loader2,
    Sparkles,
    User,
    Star,
    Download,
    Eye,
    SlidersHorizontal,
    ChevronLeft,
    ChevronRight,
    ArrowUpDown,
    CheckCircle2
} from 'lucide-react';
import { api } from '@shared/services/api';

const CATEGORIES = [
    { id: 'all', label: 'Todas las Categorías' },
    { id: 'Novela Ligera', label: 'Novelas Ligeras' },
    { id: 'Manga', label: 'Manga' },
    { id: 'Web Novel', label: 'Web Novel' },
    { id: 'Seinen', label: 'Seinen' },
    { id: 'Shounen', label: 'Shounen' },
    { id: 'Josei', label: 'Josei' },
    { id: 'Shoujo', label: 'Shoujo' },
];

const SORT_OPTIONS = [
    { id: 'name_asc', label: 'Título (A - Z)' },
    { id: 'name_desc', label: 'Título (Z - A)' },
    { id: 'updated_desc', label: 'Más Recientes' },
    { id: 'downloads_desc', label: 'Más Descargados' },
    { id: 'rating_desc', label: 'Mejor Valorados' },
    { id: 'books_desc', label: 'Más Volúmenes' },
];

export const EditorialLibrary: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams, setSearchParams] = useSearchParams();

    // Query states
    const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
    const [selectedCategory, setSelectedCategory] = useState(searchParams.get('category') || 'all');
    const [sortBy, setSortBy] = useState(searchParams.get('sort') || 'name_asc');

    // UI View states
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [paginationMode, setPaginationMode] = useState<'infinite' | 'paged'>('infinite');

    // Data states
    const [seriesList, setSeriesList] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [loadingMore, setLoadingMore] = useState(false);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalSeries, setTotalSeries] = useState(0);

    // Refs to avoid stale closures in scroll/observer callbacks
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

    // Infinite scroll observer
    const observerRef = useRef<IntersectionObserver | null>(null);
    const loadMoreTriggerRef = useRef<HTMLDivElement | null>(null);

    const fetchCatalog = async (pageToFetch = 1, append = false) => {
        if (append) {
            setLoadingMore(true);
        } else {
            setLoading(true);
        }

        try {
            const queryParams: any = {
                query: searchQuery.trim() || undefined,
                page: pageToFetch,
                limit: 24,
                sort_by: sortBy,
            };

            if (selectedCategory !== 'all') {
                if (['Novela Ligera', 'Manga', 'Web Novel'].includes(selectedCategory)) {
                    queryParams.book_type = selectedCategory;
                } else {
                    queryParams.demography = selectedCategory;
                }
            }

            const res = await api.getLibraryGrid(queryParams);
            const incomingSeries = res?.series || [];
            const pagination = res?.pagination;

            if (append) {
                setSeriesList((prev) => [...prev, ...incomingSeries]);
            } else {
                setSeriesList(incomingSeries);
            }

            const computedTotalPages = pagination?.total_pages || res?.total_pages || res?.pages || 1;
            const computedTotalSeries = pagination?.total || res?.total_series || res?.total || incomingSeries.length;

            setTotalPages(computedTotalPages);
            setTotalSeries(computedTotalSeries);
            totalPagesRef.current = computedTotalPages;
        } catch (err) {
            console.error('Error cargando catálogo editorial:', err);
        } finally {
            setLoading(false);
            setLoadingMore(false);
        }
    };

    // Refetch on filters or sort change
    useEffect(() => {
        setPage(1);
        pageRef.current = 1;
        fetchCatalog(1, false);
    }, [searchQuery, selectedCategory, sortBy]);

    // Handle Infinite Scroll Intersection
    const handleObserver = useCallback(
        (entries: IntersectionObserverEntry[]) => {
            const target = entries[0];
            if (target.isIntersecting && paginationMode === 'infinite') {
                if (!loadingRef.current && !loadingMoreRef.current && pageRef.current < totalPagesRef.current) {
                    const nextPage = pageRef.current + 1;
                    pageRef.current = nextPage;
                    setPage(nextPage);
                    fetchCatalog(nextPage, true);
                }
            }
        },
        [paginationMode]
    );

    useEffect(() => {
        if (paginationMode !== 'infinite') return;
        const mainEl = document.querySelector('main');
        const option = { root: mainEl || null, rootMargin: '300px', threshold: 0.01 };
        observerRef.current = new IntersectionObserver(handleObserver, option);
        if (loadMoreTriggerRef.current) {
            observerRef.current.observe(loadMoreTriggerRef.current);
        }

        // Secondary fallback scroll listener for virtual scrolling or deep viewports
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
                fetchCatalog(nextPage, true);
            }
        };

        mainEl?.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('scroll', handleScroll, { passive: true });

        return () => {
            if (observerRef.current) observerRef.current.disconnect();
            mainEl?.removeEventListener('scroll', handleScroll);
            window.removeEventListener('scroll', handleScroll);
        };
    }, [handleObserver, paginationMode]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        pageRef.current = 1;
        fetchCatalog(1, false);
    };

    const handlePageChange = (newPage: number) => {
        if (newPage < 1 || newPage > totalPages) return;
        setPage(newPage);
        pageRef.current = newPage;
        fetchCatalog(newPage, false);
        document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' });
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const getSeriesCover = (s: any) => {
        if (s.cover_url && (s.cover_url.startsWith('http') || s.cover_url.startsWith('/'))) return s.cover_url;
        if (s.coverUrl && (s.coverUrl.startsWith('http') || s.coverUrl.startsWith('/'))) return s.coverUrl;
        const sId = s.series_hash || s.id;
        if (sId) return `/api/library/covers/${sId}.jpg`;
        return null;
    };

    return (
        <div className="w-full max-w-[2400px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Top Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-900/40 border border-white/10 p-6 rounded-[2.5rem] backdrop-blur-2xl shadow-2xl">
                <div>
                    <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Layers className="w-7 h-7 text-indigo-400" /> Catálogo Editorial ZeePub
                    </h1>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Exploración completa de la biblioteca con navegación tipo árbol ({totalSeries} series indexadas).
                    </p>
                </div>

                {/* View & Pagination Mode Controls */}
                <div className="flex items-center gap-3 flex-wrap">
                    {/* Grid vs List Switcher */}
                    <div className="flex items-center gap-1 p-1 bg-slate-950/80 border border-white/10 rounded-2xl">
                        <button
                            type="button"
                            onClick={() => setViewMode('grid')}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                viewMode === 'grid'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            <Grid className="w-3.5 h-3.5" />
                            <span>Cuadrícula</span>
                        </button>
                        <button
                            type="button"
                            onClick={() => setViewMode('list')}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                viewMode === 'list'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            <List className="w-3.5 h-3.5" />
                            <span>Lista</span>
                        </button>
                    </div>

                    {/* Infinite Scroll vs Paged Mode Switcher */}
                    <div className="flex items-center gap-1 p-1 bg-slate-950/80 border border-white/10 rounded-2xl">
                        <button
                            type="button"
                            onClick={() => setPaginationMode('infinite')}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                                paginationMode === 'infinite'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Scroll Infinito
                        </button>
                        <button
                            type="button"
                            onClick={() => setPaginationMode('paged')}
                            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                                paginationMode === 'paged'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            Paginado
                        </button>
                    </div>
                </div>
            </div>

            {/* Filter & Search Bar */}
            <div className="space-y-4">
                {/* Search & Sort Row */}
                <div className="flex flex-col sm:flex-row gap-3">
                    {/* Search Input */}
                    <form onSubmit={handleSearchSubmit} className="relative flex-1">
                        <Search className="w-4 h-4 text-gray-400 absolute left-4 top-1/2 -translate-y-1/2" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Buscar series por título inglés, español, autor o slug..."
                            className="w-full pl-11 pr-4 py-3 bg-slate-900/60 border border-white/10 rounded-2xl text-xs sm:text-sm text-white focus:outline-none focus:border-indigo-500 backdrop-blur-xl shadow-lg"
                        />
                    </form>

                    {/* Sort Dropdown */}
                    <div className="relative min-w-[200px]">
                        <ArrowUpDown className="w-4 h-4 text-indigo-400 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                        <select
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 bg-slate-900/60 border border-white/10 rounded-2xl text-xs font-bold text-white focus:outline-none focus:border-indigo-500 appearance-none cursor-pointer backdrop-blur-xl shadow-lg"
                        >
                            {SORT_OPTIONS.map((opt) => (
                                <option key={opt.id} value={opt.id} className="bg-slate-950 text-white">
                                    {opt.label}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                {/* Category Pills Bar */}
                <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
                    {CATEGORIES.map((cat) => (
                        <button
                            key={cat.id}
                            type="button"
                            onClick={() => setSelectedCategory(cat.id)}
                            className={`px-4 py-2 rounded-2xl text-xs font-black uppercase tracking-wider shrink-0 transition-all border ${
                                selectedCategory === cat.id
                                    ? 'bg-indigo-600 text-white border-indigo-500 shadow-lg shadow-indigo-600/30'
                                    : 'bg-white/[0.03] text-gray-400 hover:text-white border-white/5 hover:bg-white/[0.06]'
                            }`}
                        >
                            {cat.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Catalog Series Grid / List */}
            {loading && page === 1 ? (
                <div className="py-32 flex flex-col items-center justify-center gap-4">
                    <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                    <span className="text-xs text-gray-400 font-mono">Cargando catálogo editorial...</span>
                </div>
            ) : seriesList.length === 0 ? (
                <div className="py-24 text-center bg-slate-900/40 border border-white/10 rounded-3xl p-8 space-y-3">
                    <BookOpen className="w-12 h-12 text-gray-600 mx-auto" />
                    <h3 className="text-base font-bold text-white">No se encontraron series</h3>
                    <p className="text-xs text-gray-400">
                        Intenta ajustar los filtros de búsqueda o categoría.
                    </p>
                </div>
            ) : viewMode === 'grid' ? (
                /* 1. GRID VIEW MODE */
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-8 gap-5">
                    {seriesList.map((s) => {
                        const cover = getSeriesCover(s);
                        const sTitle = s.series_english || s.name;
                        const sId = s.series_hash || s.id;
                        const bookCount = s.book_count || (s.books ? s.books.length : 0);

                        return (
                            <div
                                key={sId}
                                onClick={() => navigate(`/app-v2/series/${sId}`)}
                                className="group relative rounded-3xl bg-slate-900/40 border border-white/10 hover:border-indigo-500/50 p-3.5 flex flex-col justify-between backdrop-blur-xl shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 cursor-pointer"
                            >
                                {/* Cover Frame */}
                                <div className="relative aspect-[2/3] rounded-2xl overflow-hidden bg-slate-950 border border-white/5 shadow-md">
                                    {cover ? (
                                        <img
                                            src={cover}
                                            alt={sTitle}
                                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                        />
                                    ) : (
                                        <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                                            <BookOpen className="w-8 h-8" />
                                            <span className="text-[10px]">Sin Portada</span>
                                        </div>
                                    )}

                                    {/* Book Count Badge */}
                                    <div className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded-lg bg-indigo-600/90 backdrop-blur-md text-white text-[10px] font-black shadow-lg font-mono flex items-center gap-1">
                                        <BookOpen className="w-3 h-3" />
                                        <span>{bookCount} Vol.</span>
                                    </div>
                                </div>

                                {/* Series Info */}
                                <div className="pt-3 space-y-1.5 min-w-0">
                                    <h3 className="text-xs sm:text-sm font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                                        {sTitle}
                                    </h3>
                                    {s.series_spanish && s.series_spanish !== sTitle && (
                                        <h4 className="text-[11px] text-amber-300/80 truncate font-medium">
                                            {s.series_spanish}
                                        </h4>
                                    )}
                                    <div className="flex items-center justify-between text-[10px] text-gray-400 pt-0.5">
                                        <span className="truncate flex items-center gap-1">
                                            <User className="w-3 h-3 text-indigo-400" />
                                            <span>{s.author || 'Sin autor'}</span>
                                        </span>
                                    </div>
                                </div>

                                {/* Card Footer */}
                                <div className="pt-2 mt-2 border-t border-white/5 flex items-center justify-between text-[10px] font-medium text-gray-400">
                                    <span className="px-2 py-0.5 rounded-md bg-white/5 uppercase font-bold text-[9px] text-gray-300">
                                        {s.demographics?.[0] || s.demography || s.book_type || 'General'}
                                    </span>
                                    <span className="text-indigo-400 font-bold group-hover:underline flex items-center gap-0.5">
                                        Explorar ›
                                    </span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            ) : (
                /* 2. LIST VIEW MODE */
                <div className="rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl overflow-hidden divide-y divide-white/5">
                    {seriesList.map((s) => {
                        const cover = getSeriesCover(s);
                        const sTitle = s.series_english || s.name;
                        const sId = s.series_hash || s.id;
                        const bookCount = s.book_count || (s.books ? s.books.length : 0);

                        return (
                            <div
                                key={sId}
                                onClick={() => navigate(`/app-v2/series/${sId}`)}
                                className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-white/[0.03] transition-colors cursor-pointer group"
                            >
                                <div className="flex items-center gap-4 min-w-0">
                                    <div className="w-14 h-20 rounded-2xl overflow-hidden bg-slate-950 border border-white/10 shrink-0">
                                        {cover ? (
                                            <img src={cover} alt={sTitle} className="w-full h-full object-cover" />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                <BookOpen className="w-5 h-5" />
                                            </div>
                                        )}
                                    </div>

                                    <div className="min-w-0 space-y-1">
                                        <div className="flex items-center gap-2 flex-wrap">
                                            <h3 className="text-sm sm:text-base font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                                                {sTitle}
                                            </h3>
                                            <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-mono text-xs font-black">
                                                {bookCount} Volúmenes
                                            </span>
                                            {s.demographics?.[0] && (
                                                <span className="px-2 py-0.5 rounded-md bg-white/5 text-gray-400 text-[10px] uppercase font-bold">
                                                    {s.demographics[0]}
                                                </span>
                                            )}
                                        </div>

                                        {s.series_spanish && s.series_spanish !== sTitle && (
                                            <div className="text-xs text-amber-300/80 truncate">
                                                🇪🇸 {s.series_spanish}
                                            </div>
                                        )}

                                        <div className="text-xs text-gray-400 flex items-center gap-3">
                                            <span>👤 {s.author || 'Sin autor'}</span>
                                            {s.illustrator && <span>🎨 {s.illustrator}</span>}
                                        </div>
                                    </div>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => navigate(`/app-v2/series/${sId}`)}
                                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black flex items-center gap-1.5 transition-all shadow-lg shrink-0"
                                >
                                    <Eye className="w-3.5 h-3.5" />
                                    <span>Ver Serie</span>
                                </button>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Infinite Scroll Trigger & Spinner */}
            {paginationMode === 'infinite' && (
                <div ref={loadMoreTriggerRef} className="py-8 flex justify-center">
                    {loadingMore && (
                        <div className="flex items-center gap-2 text-xs text-indigo-400 font-mono">
                            <Loader2 className="w-5 h-5 animate-spin" />
                            <span>Cargando más series...</span>
                        </div>
                    )}
                </div>
            )}

            {/* Paged Navigation Bar */}
            {paginationMode === 'paged' && totalPages > 1 && (
                <div className="flex items-center justify-between p-4 rounded-3xl bg-slate-900/40 border border-white/10 backdrop-blur-xl shadow-xl">
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
                            Página <span className="font-bold text-white">{page}</span> de <span className="font-bold text-white">{totalPages}</span>
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
    );
};
