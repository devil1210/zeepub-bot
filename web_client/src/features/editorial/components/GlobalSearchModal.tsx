import React, { useState, useEffect, useRef } from 'react';
import { Search, Book, Layers, FileText, X, ArrowRight, Loader2 } from 'lucide-react';
import { api } from '@shared/services/api';

interface GlobalSearchModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (type: 'epub' | 'series' | 'volume', id: string) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({ isOpen, onClose, onSelect }) => {
    const [query, setQuery] = useState('');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<{
        series: any[];
        books: any[];
    }>({ series: [], books: [] });
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isOpen) {
            setTimeout(() => inputRef.current?.focus(), 50);
        } else {
            setQuery('');
            setResults({ series: [], books: [] });
        }
    }, [isOpen]);

    useEffect(() => {
        if (!query.trim()) {
            setResults({ series: [], books: [] });
            return;
        }

        const timer = setTimeout(async () => {
            setLoading(true);
            try {
                const res = await api.searchBooks(query.trim(), 1, 'all', 'a-z');
                const seriesList = res?.results || [];

                // Extract books from series or grid search
                const gridRes = await api.getLibraryGrid({ query: query.trim(), limit: 10 });
                const books = gridRes?.books || [];

                setResults({
                    series: seriesList.slice(0, 6),
                    books: books.slice(0, 8),
                });
            } catch (err) {
                console.error('Error en búsqueda global:', err);
            } finally {
                setLoading(false);
            }
        }, 250);

        return () => clearTimeout(timer);
    }, [query]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="relative w-full max-w-2xl bg-slate-900 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
                {/* Search Header */}
                <div className="flex items-center px-4 py-3.5 border-b border-white/10 bg-slate-950/60">
                    <Search className="w-5 h-5 text-indigo-400 mr-3 shrink-0" />
                    <input
                        ref={inputRef}
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Buscar por serie, título de EPUB, autor o volumen..."
                        className="w-full bg-transparent text-white placeholder-gray-500 text-sm focus:outline-none"
                    />
                    {loading && <Loader2 className="w-4 h-4 text-indigo-400 animate-spin mr-2" />}
                    <button
                        onClick={onClose}
                        className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Results Viewport */}
                <div className="p-3 overflow-y-auto space-y-4 divide-y divide-white/5">
                    {query.trim() === '' ? (
                        <div className="py-12 text-center text-gray-500 text-xs">
                            Escribe cualquier palabra clave para buscar en toda la biblioteca editorial
                        </div>
                    ) : (
                        <>
                            {/* Series Group */}
                            {results.series.length > 0 && (
                                <div className="space-y-1">
                                    <div className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-indigo-400">
                                        <Layers className="w-3.5 h-3.5" /> Series ({results.series.length})
                                    </div>
                                    {results.series.map((s) => (
                                        <button
                                            key={s.id || s.series_hash}
                                            onClick={() => {
                                                onSelect('series', s.series_hash || s.id);
                                                onClose();
                                            }}
                                            className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-white/5 text-left transition-colors group"
                                        >
                                            <div className="flex items-center gap-3 min-w-0">
                                                <div className="w-8 h-10 rounded bg-slate-800 shrink-0 overflow-hidden border border-white/10">
                                                    {s.coverUrl && <img src={s.coverUrl} alt="" className="w-full h-full object-cover" />}
                                                </div>
                                                <div className="truncate">
                                                    <div className="text-sm font-semibold text-white group-hover:text-indigo-300 truncate">
                                                        {s.englishTitle || s.title || s.name}
                                                    </div>
                                                    <div className="text-xs text-gray-400 truncate">
                                                        {s.author || 'Autor desconocido'} • {s.volumesCount || 1} vols
                                                    </div>
                                                </div>
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-indigo-400 transition-colors shrink-0" />
                                        </button>
                                    ))}
                                </div>
                            )}

                            {/* Books / EPUBs Group */}
                            {results.books.length > 0 && (
                                <div className="space-y-1 pt-3">
                                    <div className="flex items-center gap-1.5 px-2 py-1 text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                                        <Book className="w-3.5 h-3.5" /> Volúmenes y EPUBs ({results.books.length})
                                    </div>
                                    {results.books.map((b) => (
                                        <button
                                            key={b.id || b.book_hash}
                                            onClick={() => {
                                                onSelect('epub', b.id || b.book_hash);
                                                onClose();
                                            }}
                                            className="w-full flex items-center justify-between p-2.5 rounded-xl hover:bg-white/5 text-left transition-colors group"
                                        >
                                            <div className="flex items-center gap-3 min-w-0">
                                                <FileText className="w-5 h-5 text-emerald-400 shrink-0" />
                                                <div className="truncate">
                                                    <div className="text-sm font-semibold text-white group-hover:text-emerald-300 truncate">
                                                        {b.title} {b.volume ? `(Vol. ${b.volume})` : ''}
                                                    </div>
                                                    <div className="text-xs text-gray-400 truncate">
                                                        {b.series_name || 'Sin serie asignada'}
                                                    </div>
                                                </div>
                                            </div>
                                            <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-emerald-400 transition-colors shrink-0" />
                                        </button>
                                    ))}
                                </div>
                            )}

                            {!loading && results.series.length === 0 && results.books.length === 0 && (
                                <div className="py-12 text-center text-gray-400 text-xs">
                                    No se encontraron coincidencias para &quot;{query}&quot;
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
};
