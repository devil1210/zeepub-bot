import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    BookOpen, Search, Filter, Plus, Edit3, Tag, GitMerge, Layers, 
    User, Sparkles, Check, AlertCircle, RefreshCw, ChevronRight, Image as ImageIcon
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { api } from '@shared/services/api';

interface SeriesItem {
    id: string;
    series_hash?: string;
    name: string;
    series_spanish?: string;
    series_english?: string;
    slug?: string;
    author?: string;
    illustrator?: string;
    book_type?: string;
    cover_url?: string;
    book_count: number;
    aliases?: Array<{ id: number; alias: string }>;
}

export const SeriesManagerPage: React.FC = () => {
    const navigate = useNavigate();
    const { settings } = useTheme();
    const { webApp } = useTelegram();

    const [seriesList, setSeriesList] = useState<SeriesItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedType, setSelectedType] = useState<string>('all');
    const [page, setPage] = useState(1);
    const [totalSeries, setTotalSeries] = useState(0);

    const loadSeries = async () => {
        try {
            setLoading(true);
            const res = await api.getLibraryGrid({
                query: searchQuery.trim() || undefined,
                book_type: selectedType !== 'all' ? selectedType : undefined,
                page,
                limit: 30
            });
            if (res && res.series) {
                setSeriesList(res.series);
                setTotalSeries(res.total || res.series.length);
            }
        } catch (err) {
            console.error("Error cargando lista de series:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSeries();
    }, [searchQuery, selectedType, page]);

    const filteredSeries = useMemo(() => {
        if (!searchQuery.trim()) return seriesList;
        const q = searchQuery.toLowerCase();
        return seriesList.filter(s => 
            (s.name && s.name.toLowerCase().includes(q)) ||
            (s.series_spanish && s.series_spanish.toLowerCase().includes(q)) ||
            (s.series_english && s.series_english.toLowerCase().includes(q)) ||
            (s.author && s.author.toLowerCase().includes(q)) ||
            (s.aliases && s.aliases.some(a => a.alias.toLowerCase().includes(q)))
        );
    }, [seriesList, searchQuery]);

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 md:p-8 space-y-6 animate-in fade-in duration-300">
            {/* Header Area */}
            <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-start md:items-center justify-between gap-4 bg-slate-900/80 border border-white/10 rounded-2xl p-6 backdrop-blur-xl shadow-2xl">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase tracking-wider">
                            Gestión de Catálogo
                        </span>
                        <span className="text-xs text-slate-400 font-mono">
                            {totalSeries} Series Registradas
                        </span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
                        <BookOpen className="w-7 h-7 text-indigo-400" />
                        Editor de Series
                    </h1>
                    <p className="text-xs text-slate-400 mt-1">
                        Edición individual de portadas, títulos en español/inglés, alias de maquetación y fusión de duplicados.
                    </p>
                </div>

                <button
                    onClick={() => loadSeries()}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold flex items-center gap-2 transition-all active:scale-95 border border-white/10"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                    Actualizar Lista
                </button>
            </div>

            {/* Controls: Search and Filters */}
            <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
                <div className="relative w-full sm:w-96">
                    <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                    <input
                        type="text"
                        placeholder="Buscar por serie, autor o alias..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 text-xs rounded-xl bg-slate-900 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors shadow-md"
                    />
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                    <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                        className="px-3.5 py-2.5 text-xs rounded-xl bg-slate-900 border border-white/10 text-white focus:outline-none focus:border-indigo-500 shadow-md cursor-pointer"
                    >
                        <option value="all">Todos los tipos</option>
                        <option value="Novela Ligera">Novela Ligera</option>
                        <option value="Web Novel">Web Novel</option>
                        <option value="Novela Visual">Novela Visual</option>
                        <option value="Manga">Manga</option>
                    </select>
                </div>
            </div>

            {/* Series Cards Grid */}
            <div className="max-w-7xl mx-auto">
                {loading ? (
                    <div className="py-20 text-center space-y-3">
                        <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
                        <p className="text-xs text-slate-400 font-mono uppercase tracking-widest">Cargando catálogo de series...</p>
                    </div>
                ) : filteredSeries.length === 0 ? (
                    <div className="py-20 text-center space-y-3 bg-slate-900/40 border border-white/5 rounded-2xl p-8">
                        <BookOpen className="w-12 h-12 text-slate-600 mx-auto" />
                        <h3 className="text-sm font-bold text-white">No se encontraron series</h3>
                        <p className="text-xs text-slate-400">Prueba ajustando el término de búsqueda o filtro.</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                        {filteredSeries.map((series) => (
                            <div 
                                key={series.id}
                                className="bg-slate-900/80 border border-white/10 hover:border-indigo-500/40 rounded-2xl p-4 backdrop-blur-xl shadow-xl transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/10 flex flex-col justify-between group"
                            >
                                <div className="space-y-3">
                                    <div className="flex items-start gap-3.5">
                                        {/* Cover */}
                                        {series.cover_url ? (
                                            <img
                                                src={series.cover_url}
                                                alt={series.name}
                                                className="w-16 h-24 object-cover rounded-xl border border-white/10 shadow-md group-hover:scale-105 transition-transform flex-shrink-0"
                                                onError={(e) => {
                                                    (e.target as any).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="64" height="96" viewBox="0 0 64 96"><rect width="64" height="96" fill="%231e293b"/><text x="50%" y="50%" fill="%2364748b" dominant-baseline="middle" text-anchor="middle" font-size="9">Sin Portada</text></svg>';
                                                }}
                                            />
                                        ) : (
                                            <div className="w-16 h-24 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-500 text-[10px] flex-shrink-0">
                                                <ImageIcon className="w-5 h-5 opacity-40" />
                                            </div>
                                        )}

                                        <div className="flex-1 min-w-0 space-y-1">
                                            <div className="flex items-center justify-between gap-1">
                                                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-bold">
                                                    {series.book_count} vol.
                                                </span>
                                                <span className="text-[10px] text-slate-400 font-mono">
                                                    {series.book_type || 'LN'}
                                                </span>
                                            </div>

                                            <h3 className="text-sm font-bold text-white truncate leading-tight group-hover:text-indigo-300 transition-colors" title={series.name}>
                                                {series.name}
                                            </h3>

                                            {series.series_spanish && (
                                                <p className="text-[11px] text-slate-400 truncate">
                                                    🇪🇸 {series.series_spanish}
                                                </p>
                                            )}

                                            {series.author && (
                                                <p className="text-[10px] text-slate-400 flex items-center gap-1">
                                                    <User className="w-3 h-3 text-indigo-400" />
                                                    <span className="truncate">{series.author}</span>
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Aliases Tags */}
                                    {series.aliases && series.aliases.length > 0 && (
                                        <div className="flex flex-wrap gap-1 pt-1">
                                            {series.aliases.slice(0, 3).map(al => (
                                                <span key={al.id} className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[9px] font-semibold border border-white/5">
                                                    {al.alias}
                                                </span>
                                            ))}
                                            {series.aliases.length > 3 && (
                                                <span className="text-[9px] text-slate-500 font-bold self-center">
                                                    +{series.aliases.length - 3} más
                                                </span>
                                            )}
                                        </div>
                                    )}
                                </div>

                                {/* Action Buttons */}
                                <div className="pt-4 border-t border-white/10 flex items-center gap-2 mt-3">
                                    <button
                                        onClick={() => navigate(`/admin/series/${series.id}`)}
                                        className="flex-1 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-1.5 transition-all active:scale-95 shadow-lg shadow-indigo-600/20"
                                    >
                                        <Edit3 className="w-3.5 h-3.5" />
                                        Editar Serie
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
