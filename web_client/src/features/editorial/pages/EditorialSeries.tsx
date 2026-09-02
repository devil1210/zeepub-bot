import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
    Layers,
    Search,
    Edit3,
    BookOpen,
    Image,
    Sparkles,
    GitMerge,
    Loader2,
    Star
} from 'lucide-react';
import { api } from '@shared/services/api';
import { EditorialQuickEditDrawer } from '../components/EditorialQuickEditDrawer';

export const EditorialSeries: React.FC = () => {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [seriesList, setSeriesList] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [selectedSeriesForEdit, setSelectedSeriesForEdit] = useState<any | null>(null);

    const fetchSeries = async () => {
        setLoading(true);
        try {
            const res = await api.searchBooks(searchQuery, page, 'all', 'a-z');
            const items = res?.results || [];
            setSeriesList(items);
            setTotalPages(res?.totalPages || 1);
        } catch (err) {
            console.error('Error cargando series:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSeries();
    }, [page]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        fetchSeries();
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <Layers className="w-6 h-6 text-indigo-400" /> Catálogo Editorial de Series
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Control de títulos canónicos, aliases de búsqueda, demografías y recálculo de slugs.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={() => navigate('/admin/series-manager')}
                        className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-white text-xs font-bold border border-white/10 flex items-center gap-2 transition-all"
                    >
                        <GitMerge className="w-4 h-4 text-purple-400" />
                        Fusión & DataGrid
                    </button>
                </div>
            </div>

            {/* Search Bar */}
            <form onSubmit={handleSearchSubmit} className="flex gap-2">
                <div className="relative flex-1">
                    <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Buscar serie por nombre oficial, romaji o español..."
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                </div>
                <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/20"
                >
                    Buscar
                </button>
            </form>

            {/* Grid of Series */}
            {loading ? (
                <div className="py-24 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
            ) : seriesList.length === 0 ? (
                <div className="py-24 text-center text-gray-500 text-xs">
                    No se encontraron series registradas.
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                    {seriesList.map((s) => {
                        const sId = s.series_hash || s.id;
                        const mainTitle = s.englishTitle || s.name_english || s.title || s.name;
                        const romajiTitle = s.romajiTitle || s.name;
                        const spanishTitle = s.spanishTitle || s.name_spanish;

                        return (
                            <div
                                key={sId}
                                className="bg-slate-900/50 border border-white/10 rounded-2xl p-4 flex flex-col justify-between hover:border-indigo-500/40 transition-all group backdrop-blur-xl hover:shadow-2xl hover:shadow-indigo-500/10"
                            >
                                <div className="flex gap-4">
                                    {/* Cover */}
                                    <div className="w-16 h-24 rounded-xl bg-slate-800 border border-white/10 overflow-hidden shrink-0 shadow-lg">
                                        {s.coverUrl || s.coverThumbUrl ? (
                                            <img
                                                src={s.coverUrl || s.coverThumbUrl}
                                                alt=""
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                <Image className="w-5 h-5" />
                                            </div>
                                        )}
                                    </div>

                                    {/* Details */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between gap-1 mb-1">
                                            <span className="text-[10px] font-black uppercase tracking-wider px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                                {s.volumesCount || 1} Vols
                                            </span>
                                            {s.rating > 0 && (
                                                <div className="flex items-center gap-1 text-[11px] font-bold text-amber-400">
                                                    <Star className="w-3 h-3 fill-current" />
                                                    {s.rating.toFixed(1)}
                                                </div>
                                            )}
                                        </div>

                                        <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-2 leading-tight">
                                            {mainTitle}
                                        </h3>

                                        {spanishTitle && spanishTitle !== mainTitle && (
                                            <p className="text-[11px] text-gray-400 italic line-clamp-1 mt-0.5">
                                                🇪🇸 {spanishTitle}
                                            </p>
                                        )}

                                        <p className="text-[10px] text-gray-500 uppercase tracking-widest font-bold mt-1 truncate">
                                            {s.author || 'Autor desconocido'}
                                        </p>
                                    </div>
                                </div>

                                {/* Footer Actions */}
                                <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between gap-2">
                                    <button
                                        onClick={() => navigate(`/app-v2/volumes?series=${sId}`)}
                                        className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition-colors"
                                    >
                                        <BookOpen className="w-3.5 h-3.5" /> Ver Volúmenes
                                    </button>

                                    <button
                                        onClick={() => setSelectedSeriesForEdit(s)}
                                        className="p-2 rounded-lg bg-white/5 hover:bg-emerald-600 text-gray-300 hover:text-white transition-all"
                                        title="Editar Serie"
                                    >
                                        <Edit3 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="p-4 border border-white/10 rounded-2xl bg-slate-900/60 flex items-center justify-between">
                    <span className="text-xs text-gray-400">
                        Página {page} de {totalPages}
                    </span>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage((p) => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-bold disabled:opacity-30"
                        >
                            Anterior
                        </button>
                        <button
                            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-bold disabled:opacity-30"
                        >
                            Siguiente
                        </button>
                    </div>
                </div>
            )}

            {/* Quick Edit Drawer for Series */}
            <EditorialQuickEditDrawer
                isOpen={!!selectedSeriesForEdit}
                itemType="series"
                itemData={selectedSeriesForEdit}
                onClose={() => setSelectedSeriesForEdit(null)}
                onSaveSuccess={fetchSeries}
            />
        </div>
    );
};
