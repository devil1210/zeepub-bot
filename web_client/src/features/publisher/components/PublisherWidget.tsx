import React, { useState, useEffect, useRef } from 'react';
import {
    Send,
    Calendar,
    Clock,
    Sparkles,
    Search,
    ChevronRight,
    RefreshCw,
    Layers,
    FileText,
    CheckCircle2,
    XCircle,
    AlertCircle,
    Plus,
    X,
    ExternalLink
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { usePublisher } from '../hooks/usePublisher';
import { ScheduleModal } from './ScheduleModal';
import { api } from '@shared/services/api';
import { PublicationQueueItem } from '../services/publisherApi';

interface PublisherWidgetProps {
    onNavigate?: (tab: string) => void;
}

export const PublisherWidget: React.FC<PublisherWidgetProps> = ({ onNavigate }) => {
    const { settings } = useTheme();
    const {
        queue,
        channels,
        templates,
        loading,
        refresh,
        deleteQueueItem
    } = usePublisher();

    const [isScheduleOpen, setIsScheduleOpen] = useState(false);
    const [selectedBook, setSelectedBook] = useState<{ hash: string; title: string } | null>(null);
    const [editingItem, setEditingItem] = useState<PublicationQueueItem | null>(null);

    // Quick Book Search state
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);
    const [isSearchOpen, setIsSearchOpen] = useState(false);
    const searchRef = useRef<HTMLDivElement>(null);

    // Debounced search for books
    useEffect(() => {
        if (!searchQuery.trim() || searchQuery.length < 2) {
            setSearchResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsSearching(true);
            try {
                const res = await api.rpc('search_books', { query: searchQuery, limit: 6 });
                const books = res?.books || res || [];
                setSearchResults(Array.isArray(books) ? books.slice(0, 6) : []);
            } catch (err) {
                console.error("Error searching books for publisher", err);
            } finally {
                setIsSearching(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [searchQuery]);

    // Close search dropdown on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
                setIsSearchOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSelectBook = (book: any) => {
        const hash = book.book_hash || book.hash || book.id || '';
        const title = book.series_spanish || book.series || book.title || 'Libro sin título';
        setSelectedBook({ hash, title });
        setEditingItem(null);
        setIsSearchOpen(false);
        setSearchQuery('');
        setIsScheduleOpen(true);
    };

    const handleEditQueueItem = (item: PublicationQueueItem) => {
        setEditingItem(item);
        setSelectedBook({
            hash: item.book_hash,
            title: item.series_spanish || item.series || 'Publicación'
        });
        setIsScheduleOpen(true);
    };

    const pendingQueue = queue.filter(q => q.status === 'pending' || q.status === 'processing');

    return (
        <div className="glass-panel rounded-[3rem] p-8 relative overflow-hidden group hover:scale-[1.005] transition-all duration-700 shadow-premium border-white/10">
            {/* Background Glow */}
            <div
                className="absolute -top-24 -right-24 w-72 h-72 bg-gradient-to-br from-purple-600/20 to-blue-500/20 rounded-full blur-[100px] pointer-events-none group-hover:opacity-100 transition-opacity duration-700"
                style={{ opacity: settings.cardGlowIntensity || 0.6 }}
            ></div>

            {/* Header */}
            <div className="flex items-center justify-between gap-4 mb-6 relative z-10">
                <div className="flex items-center gap-3.5">
                    <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-500/20 to-blue-500/20 border border-purple-500/30 flex items-center justify-center text-purple-400 shadow-lg shadow-purple-500/10">
                        <Send className="w-6 h-6" />
                    </div>
                    <div>
                        <h3 className="text-white font-black text-xl tracking-tight leading-tight flex items-center gap-2">
                            Publicador
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-bold uppercase tracking-wider border border-purple-500/20">
                                Express
                            </span>
                        </h3>
                        <p className="text-xs text-gray-400 font-medium">
                            {channels.length} {channels.length === 1 ? 'canal conectado' : 'canales conectados'}
                        </p>
                    </div>
                </div>

                <button
                    onClick={() => refresh()}
                    title="Actualizar Cola"
                    className={`p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all duration-300 border border-white/5 ${loading ? 'animate-spin text-primary' : ''}`}
                >
                    <RefreshCw className="w-4 h-4" />
                </button>
            </div>

            {/* Quick Search to Publish */}
            <div className="mb-6 relative z-20" ref={searchRef}>
                <label className="block text-[10px] font-black text-gray-400 uppercase tracking-widest mb-2">
                    Publicación Inmediata / Programada
                </label>
                <div className="relative">
                    <Search className="w-4 h-4 text-gray-500 absolute left-4 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => {
                            setSearchQuery(e.target.value);
                            setIsSearchOpen(true);
                        }}
                        onFocus={() => setIsSearchOpen(true)}
                        placeholder="Buscar libro para publicar..."
                        className="w-full bg-white/[0.04] border border-white/10 rounded-2xl pl-11 pr-10 py-3 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-purple-500/50 focus:bg-white/[0.08] transition-all shadow-inner"
                    />
                    {searchQuery && (
                        <button
                            onClick={() => {
                                setSearchQuery('');
                                setSearchResults([]);
                            }}
                            className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                        >
                            <X className="w-4 h-4" />
                        </button>
                    )}
                </div>

                {/* Dropdown Results */}
                {isSearchOpen && searchQuery.length >= 2 && (
                    <div className="absolute left-0 right-0 top-full mt-2 bg-[#0e131f]/95 backdrop-blur-2xl border border-white/10 rounded-2xl p-2 shadow-2xl z-50 max-h-64 overflow-y-auto custom-scrollbar">
                        {isSearching ? (
                            <div className="p-4 text-center text-xs text-gray-400 flex items-center justify-center gap-2">
                                <div className="w-3.5 h-3.5 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
                                Buscando libros...
                            </div>
                        ) : searchResults.length > 0 ? (
                            <div className="space-y-1">
                                {searchResults.map((book, idx) => (
                                    <button
                                        key={book.book_hash || idx}
                                        onClick={() => handleSelectBook(book)}
                                        className="w-full flex items-center gap-3 p-2.5 rounded-xl hover:bg-purple-500/10 hover:border-purple-500/20 border border-transparent text-left transition-all group/item"
                                    >
                                        <div className="w-9 h-12 rounded-lg bg-black/40 overflow-hidden shrink-0 border border-white/5">
                                            {book.cover_url ? (
                                                <img src={book.cover_url} alt="" className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-[10px] text-gray-500 font-bold">
                                                    EPUB
                                                </div>
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-xs font-bold text-white truncate group-hover/item:text-purple-300 transition-colors">
                                                {book.series_spanish || book.series || book.title}
                                            </p>
                                            <p className="text-[10px] text-gray-500 truncate">
                                                Vol. {book.volume || '1'} • {book.author || 'Desconocido'}
                                            </p>
                                        </div>
                                        <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400 opacity-0 group-hover/item:opacity-100 transition-opacity">
                                            <Send className="w-3.5 h-3.5" />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        ) : (
                            <div className="p-4 text-center text-xs text-gray-500">
                                No se encontraron libros con ese término.
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Queue Preview Section */}
            <div className="space-y-3 mb-6 relative z-10">
                <div className="flex items-center justify-between">
                    <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5 text-purple-400" />
                        Próximas en Cola ({pendingQueue.length})
                    </span>
                    {onNavigate && (
                        <button
                            onClick={() => onNavigate('admin?view=publisher')}
                            className="text-[10px] font-bold text-purple-400 hover:text-purple-300 flex items-center gap-1 transition-colors"
                        >
                            Ver Todo <ChevronRight className="w-3 h-3" />
                        </button>
                    )}
                </div>

                {pendingQueue.length === 0 ? (
                    <div className="bg-white/[0.02] border border-white/5 rounded-2xl p-5 text-center">
                        <Calendar className="w-8 h-8 text-gray-600 mx-auto mb-2 opacity-50" />
                        <p className="text-xs font-bold text-gray-400">Sin publicaciones pendientes</p>
                        <p className="text-[10px] text-gray-600 mt-0.5">Usa el buscador superior para programar una difusión.</p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        {pendingQueue.slice(0, 3).map((item) => {
                            const date = new Date(item.scheduled_for);
                            const formattedTime = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            const formattedDate = date.toLocaleDateString([], { month: 'short', day: 'numeric' });

                            return (
                                <div
                                    key={item.id}
                                    className="flex items-center justify-between gap-3 p-3 rounded-2xl bg-white/[0.03] hover:bg-white/[0.06] border border-white/5 hover:border-white/10 transition-all duration-300 group/q"
                                >
                                    <div className="flex-1 min-w-0">
                                        <p className="text-xs font-bold text-white truncate">
                                            {item.series_spanish || item.series || item.title || 'Publicación'}
                                        </p>
                                        <div className="flex items-center gap-2 mt-0.5">
                                            <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/10">
                                                {formattedDate} {formattedTime}
                                            </span>
                                            <span className="text-[9px] text-gray-500 font-medium truncate">
                                                {item.channel_name || `@canal_${item.channel_id}`}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-1 opacity-80 group-hover/q:opacity-100">
                                        <button
                                            onClick={() => handleEditQueueItem(item)}
                                            title="Editar programación"
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-purple-500/20 text-gray-400 hover:text-purple-300 transition-colors"
                                        >
                                            <Clock className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            onClick={() => deleteQueueItem(item.id)}
                                            title="Cancelar publicación"
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                                        >
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {/* Quick Actions Footer */}
            <div className="grid grid-cols-2 gap-3 relative z-10">
                <button
                    onClick={() => {
                        setSelectedBook(null);
                        setEditingItem(null);
                        setIsScheduleOpen(true);
                    }}
                    className="flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-gradient-to-r from-purple-500/20 to-blue-500/20 hover:from-purple-500/30 hover:to-blue-500/30 border border-purple-500/30 text-white font-bold text-xs shadow-lg shadow-purple-500/10 transition-all hover:scale-[1.02]"
                >
                    <Plus className="w-4 h-4 text-purple-400" />
                    Programar
                </button>

                <button
                    onClick={() => onNavigate?.('admin?view=publisher')}
                    className="flex items-center justify-center gap-2 py-3 px-4 rounded-2xl bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 hover:border-white/20 text-gray-300 hover:text-white font-bold text-xs transition-all hover:scale-[1.02]"
                >
                    <Layers className="w-4 h-4 text-gray-400" />
                    Ajustes Admin
                </button>
            </div>

            {/* Modal for Scheduling */}
            <ScheduleModal
                isOpen={isScheduleOpen}
                onClose={() => {
                    setIsScheduleOpen(false);
                    setSelectedBook(null);
                    setEditingItem(null);
                }}
                bookHash={selectedBook?.hash || ''}
                bookTitle={selectedBook?.title || ''}
                editingItem={editingItem}
            />
        </div>
    );
};
