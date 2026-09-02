import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    Search,
    Filter,
    Edit3,
    Send,
    BookOpen,
    Image,
    Layers,
    CheckCircle2,
    AlertCircle,
    Loader2,
    Sparkles,
    Eye
} from 'lucide-react';
import { api } from '@shared/services/api';
import { EditorialQuickEditDrawer } from '../components/EditorialQuickEditDrawer';
import { SchedulePostModal } from '../components/SchedulePostModal';

export const EditorialLibrary: React.FC = () => {
    const [searchParams, setSearchParams] = useSearchParams();
    const [books, setBooks] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [missingFilter, setMissingFilter] = useState(searchParams.get('missing') || 'all');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [totalItems, setTotalItems] = useState(0);

    // Drawer and Modal state
    const [selectedBookForEdit, setSelectedBookForEdit] = useState<any | null>(null);
    const [selectedBookForSchedule, setSelectedBookForSchedule] = useState<any | null>(null);

    const fetchBooks = async () => {
        setLoading(true);
        try {
            const res = await api.getLibraryGrid({
                query: searchQuery,
                missing_filter: missingFilter === 'all' ? undefined : missingFilter,
                page,
                limit: 15,
                sort_by: 'updated_desc',
            });

            const seriesList = res?.series || [];
            let allBooks = seriesList.flatMap((s: any) =>
                (s.books || []).map((b: any) => ({
                    ...b,
                    series_name: s.series_english || s.name,
                    series_spanish: s.series_spanish,
                    author: s.author,
                    demography: s.demographics?.[0] || s.book_type,
                    cover_image: b.cover_url || s.cover_url || `/api/library/covers/${b.id}.jpg`,
                }))
            );

            if (allBooks.length === 0) {
                const volRes = await api.searchVolumes(searchQuery, page, 20);
                const items = volRes?.results || volRes?.items || [];
                allBooks = items.map((b: any) => ({
                    ...b,
                    series_name: b.series_info?.series_name || b.series_name || b.title,
                    series_spanish: b.series_info?.series_spanish || b.series_spanish,
                    author: b.author || b.series_info?.author,
                    cover_image: b.cover_high || b.cover_medium || `/api/library/covers/${b.id || b.book_hash}.jpg`,
                }));
                setTotalPages(volRes?.totalPages || 1);
                setTotalItems(volRes?.totalItems || items.length);
            } else {
                setTotalPages(res?.pagination?.total_pages || 1);
                setTotalItems(res?.total_books || allBooks.length);
            }

            setBooks(allBooks);
        } catch (err) {
            console.error('Error cargando biblioteca editorial:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBooks();
    }, [page, missingFilter]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        fetchBooks();
    };

    const getStatusBadge = (book: any) => {
        if (!book.series_name) {
            return (
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/20">
                    Sin Serie
                </span>
            );
        }
        if (!book.volume) {
            return (
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/20">
                    Sin Volumen
                </span>
            );
        }
        if (!book.spanish_title && !book.title_spanish) {
            return (
                <span className="px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    Sin Español
                </span>
            );
        }
        return (
            <span className="px-2.5 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Listo
            </span>
        );
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <BookOpen className="w-6 h-6 text-indigo-400" /> Biblioteca de EPUBs
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Control exhaustivo de volúmenes, metadatos editoriales y estado de catalogación ({totalItems} archivos).
                    </p>
                </div>

                {/* Filter and Missing Selector */}
                <div className="flex items-center gap-3">
                    <select
                        value={missingFilter}
                        onChange={(e) => {
                            setMissingFilter(e.target.value);
                            setPage(1);
                        }}
                        className="px-3.5 py-2 rounded-xl bg-slate-900 border border-white/10 text-xs font-bold text-white focus:outline-none focus:border-indigo-500"
                    >
                        <option value="all">Todos los EPUBs</option>
                        <option value="missing_spanish">⚠️ Sin título en español</option>
                        <option value="missing_volume">⚠️ Sin número de volumen</option>
                        <option value="missing_cover">⚠️ Sin portada asignada</option>
                        <option value="missing_demography">⚠️ Sin demografía</option>
                    </select>
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
                        placeholder="Buscar por título, serie, autor o filename..."
                        className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                </div>
                <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold transition-all shadow-lg shadow-indigo-600/20"
                >
                    Filtrar
                </button>
            </form>

            {/* Table View */}
            <div className="bg-slate-900/40 border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {loading ? (
                    <div className="py-24 flex items-center justify-center">
                        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                ) : books.length === 0 ? (
                    <div className="py-24 text-center text-gray-500 text-xs">
                        No se encontraron EPUBs con los criterios seleccionados.
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr className="border-b border-white/10 bg-slate-950/60 text-gray-400 font-bold uppercase tracking-wider text-[10px]">
                                    <th className="p-4">Portada & Volumen</th>
                                    <th className="p-4">Serie & Título Canónico</th>
                                    <th className="p-4">Autor / Demografía</th>
                                    <th className="p-4">Estado Editorial</th>
                                    <th className="p-4 text-right">Acciones</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {books.map((b) => (
                                    <tr key={b.id || b.book_hash} className="hover:bg-white/[0.02] transition-colors group">
                                        <td className="p-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-14 rounded-lg bg-slate-800 border border-white/10 overflow-hidden shrink-0">
                                                    {b.cover_image || b.coverUrl ? (
                                                        <img
                                                            src={b.cover_image || b.coverUrl}
                                                            alt=""
                                                            className="w-full h-full object-cover"
                                                        />
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                            <Image className="w-4 h-4" />
                                                        </div>
                                                    )}
                                                </div>
                                                <div>
                                                    <span className="text-xs font-black text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                                                        Vol. {b.volume || '?'}
                                                    </span>
                                                    <div className="text-[10px] text-gray-500 mt-1 truncate max-w-[120px]">
                                                        {b.filename || b.id?.slice(0, 8)}
                                                    </div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="font-bold text-white group-hover:text-indigo-300 transition-colors">
                                                {b.series_name || 'Sin Serie'}
                                            </div>
                                            <div className="text-gray-400 text-[11px] truncate max-w-xs mt-0.5">
                                                {b.spanish_title || b.title}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <div className="text-gray-300">{b.author || 'Desconocido'}</div>
                                            <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-0.5">
                                                {b.demography || 'General'}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            {getStatusBadge(b)}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => setSelectedBookForSchedule(b)}
                                                    className="p-2 rounded-xl bg-white/5 hover:bg-indigo-600 text-gray-300 hover:text-white transition-all"
                                                    title="Programar Lanzamiento"
                                                >
                                                    <Send className="w-3.5 h-3.5" />
                                                </button>
                                                <button
                                                    onClick={() => setSelectedBookForEdit(b)}
                                                    className="p-2 rounded-xl bg-white/5 hover:bg-emerald-600 text-gray-300 hover:text-white transition-all"
                                                    title="Editar Metadatos"
                                                >
                                                    <Edit3 className="w-3.5 h-3.5" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination Bar */}
                {totalPages > 1 && (
                    <div className="p-4 border-t border-white/10 bg-slate-950/60 flex items-center justify-between">
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
            </div>

            {/* Quick Edit Drawer */}
            <EditorialQuickEditDrawer
                isOpen={!!selectedBookForEdit}
                itemType="epub"
                itemData={selectedBookForEdit}
                onClose={() => setSelectedBookForEdit(null)}
                onSaveSuccess={fetchBooks}
            />

            {/* Schedule Modal */}
            <SchedulePostModal
                isOpen={!!selectedBookForSchedule}
                book={selectedBookForSchedule}
                onClose={() => setSelectedBookForSchedule(null)}
                onSuccess={fetchBooks}
            />
        </div>
    );
};
