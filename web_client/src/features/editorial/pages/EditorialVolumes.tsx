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
    DownloadCloud
} from 'lucide-react';
import { api } from '@shared/services/api';
import { EditorialQuickEditDrawer } from '../components/EditorialQuickEditDrawer';
import { SchedulePostModal } from '../components/SchedulePostModal';

export const EditorialVolumes: React.FC = () => {
    const [searchParams] = useSearchParams();
    const seriesFilterParam = searchParams.get('series') || '';

    const [volumes, setVolumes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);

    const [selectedVolumeForEdit, setSelectedVolumeForEdit] = useState<any | null>(null);
    const [selectedVolumeForSchedule, setSelectedVolumeForSchedule] = useState<any | null>(null);

    const fetchVolumes = async () => {
        setLoading(true);
        try {
            const res = await api.getLibraryGrid({
                query: searchQuery || seriesFilterParam,
                page,
                limit: 18,
                sort_by: 'volume',
            });
            setVolumes(res?.books || []);
            setTotalPages(res?.pagination?.total_pages || 1);
        } catch (err) {
            console.error('Error cargando volúmenes:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchVolumes();
    }, [page, seriesFilterParam]);

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setPage(1);
        fetchVolumes();
    };

    return (
        <div className="max-w-7xl mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <BookOpen className="w-6 h-6 text-indigo-400" /> Matriz Editorial de Volúmenes
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Auditoría de volúmenes por serie, vinculación de archivos EPUB y plantillas sugeridas.
                    </p>
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
                        placeholder="Buscar por volumen, subtítulo, autor o serie..."
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

            {/* Grid of Volumes */}
            {loading ? (
                <div className="py-24 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
            ) : volumes.length === 0 ? (
                <div className="py-24 text-center text-gray-500 text-xs">
                    No se encontraron volúmenes registrados.
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {volumes.map((vol) => (
                        <div
                            key={vol.id || vol.book_hash}
                            className="p-4 rounded-2xl bg-slate-900/50 border border-white/10 flex flex-col justify-between hover:border-indigo-500/30 transition-all backdrop-blur-xl group"
                        >
                            <div className="flex gap-3.5">
                                <div className="w-14 h-20 rounded-xl bg-slate-800 border border-white/10 overflow-hidden shrink-0">
                                    {vol.cover_image || vol.coverUrl ? (
                                        <img src={vol.cover_image || vol.coverUrl} alt="" className="w-full h-full object-cover" />
                                    ) : (
                                        <div className="w-full h-full flex items-center justify-center text-gray-600">
                                            <Image className="w-4 h-4" />
                                        </div>
                                    )}
                                </div>

                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-1.5 mb-1">
                                        <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                            Vol. {vol.volume || 1}
                                        </span>
                                        {vol.download_count > 0 && (
                                            <span className="text-[10px] text-gray-400 flex items-center gap-1">
                                                <DownloadCloud className="w-3 h-3 text-emerald-400" /> {vol.download_count}
                                            </span>
                                        )}
                                    </div>

                                    <h4 className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors line-clamp-1">
                                        {vol.series_name || 'Sin Serie Asignada'}
                                    </h4>
                                    <p className="text-[11px] text-gray-400 line-clamp-2 mt-0.5 leading-tight">
                                        {vol.spanish_title || vol.title}
                                    </p>
                                    <p className="text-[10px] text-gray-500 mt-1 font-mono truncate">
                                        {vol.filename || vol.id?.slice(0, 12)}
                                    </p>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
                                <button
                                    onClick={() => setSelectedVolumeForSchedule(vol)}
                                    className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition-colors"
                                >
                                    <Send className="w-3.5 h-3.5" /> Programar Post
                                </button>
                                <button
                                    onClick={() => setSelectedVolumeForEdit(vol)}
                                    className="p-1.5 rounded-lg bg-white/5 hover:bg-emerald-600 text-gray-300 hover:text-white transition-all"
                                    title="Editar Volumen"
                                >
                                    <Edit3 className="w-3.5 h-3.5" />
                                </button>
                            </div>
                        </div>
                    ))}
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

            {/* Edit Drawer */}
            <EditorialQuickEditDrawer
                isOpen={!!selectedVolumeForEdit}
                itemType="volume"
                itemData={selectedVolumeForEdit}
                onClose={() => setSelectedVolumeForEdit(null)}
                onSaveSuccess={fetchVolumes}
            />

            {/* Schedule Modal */}
            <SchedulePostModal
                isOpen={!!selectedVolumeForSchedule}
                book={selectedVolumeForSchedule}
                onClose={() => setSelectedVolumeForSchedule(null)}
                onSuccess={fetchVolumes}
            />
        </div>
    );
};
