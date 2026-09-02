import React, { useState, useEffect, useMemo } from 'react';
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
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [totalSeries, setTotalSeries] = useState(0);

    const fetchSeries = async () => {
        setLoading(true);
        try {
            const res = await api.getLibraryGrid({
                query: searchQuery.trim() || undefined,
                page,
                limit: 30,
            });
            if (res && res.series) {
                setSeriesList(res.series);
                setTotalSeries(res.total || res.series.length);
            }
        } catch (err) {
            console.error('Error cargando catálogo de series:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (viewMode === 'visual') {
            fetchSeries();
        }
    }, [page, viewMode]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        fetchSeries();
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

                                            {/* Footer Action */}
                                            <div className="pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-indigo-400 font-bold group-hover:text-indigo-300">
                                                <span>Ver Tomos & Volúmenes</span>
                                                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
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
