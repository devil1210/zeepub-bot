import React, { useState, useEffect } from 'react';
import {
    ArrowLeft,
    Trash2,
    Download,
    Clock,
    ExternalLink,
    Search,
    BookOpen
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
import { Book } from '@shared/types';

interface DownloadsProps {
    onNavigate?: (tab: string) => void;
    onBookClick?: (book: Book) => void;
}

export const Downloads: React.FC<DownloadsProps> = ({ onNavigate, onBookClick }) => {
    const { settings } = useTheme();
    const [downloadHistory, setDownloadHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await api.getDownloadHistory();
                // Extract downloads array from the response object
                const history = Array.isArray(res) ? res : (res?.downloads || []);
                setDownloadHistory(history);
            } catch (error) {
                console.error("Error fetching download history:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="max-w-6xl mx-auto p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-100 pb-32">
            <header className="flex items-center gap-4 mb-8">
                <button
                    onClick={() => onNavigate && onNavigate('settings')}
                    className="p-2 -ml-2 rounded-full hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                >
                    <ArrowLeft className="w-6 h-6" />
                </button>
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Mis Descargas</h1>
                    <p className="text-gray-400 text-sm">Contenido recién descargado en este dispositivo.</p>
                </div>
            </header>

            {loading ? (
                <div className="flex flex-col items-center justify-center py-20 gap-4">
                    <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                    <p className="text-gray-500 font-medium">Cargando historial...</p>
                </div>
            ) : downloadHistory.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {downloadHistory.map((item) => (
                        <div
                            key={item.id}
                            className="glass-panel group rounded-premium overflow-hidden border border-white/5 hover:border-primary/30 transition-all duration-300 flex flex-col"
                            style={{
                                background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
                                backdropFilter: `blur(${settings.glassBlur}px)`,
                                WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                            }}
                        >
                            <div className="relative aspect-[16/9] overflow-hidden">
                                <img
                                    src={item.book?.coverUrl || item.volume?.coverUrl || '/api/library/covers/default.jpg'}
                                    alt={item.title}
                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-60 group-hover:opacity-80"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent"></div>
                                <div className="absolute top-4 left-4">
                                    <span className="px-2.5 py-1 rounded-lg bg-black/60 backdrop-blur-md text-[10px] font-black uppercase tracking-widest text-white border border-white/10 flex items-center gap-1.5 shadow-xl">
                                        <Download className="w-3 h-3 text-primary" />
                                        Descargado
                                    </span>
                                </div>
                                <div className="absolute bottom-4 left-4 right-4 text-left">
                                    <h3 className="text-white font-bold leading-tight line-clamp-2 drop-shadow-md text-lg">
                                        {item.title}
                                    </h3>
                                </div>
                            </div>

                            <div className="p-5 flex flex-col flex-1 gap-4">
                                <div className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-2 text-gray-400">
                                        <Clock className="w-4 h-4" />
                                        <span>Hace {item.timeAgo || 'un momento'}</span>
                                    </div>
                                    <span className="font-mono text-primary font-bold">{item.size || '2.4MB'}</span>
                                </div>

                                <div className="mt-auto pt-4 border-t border-white/5 flex gap-2">
                                    <button
                                        onClick={() => onBookClick && onBookClick(item.book)}
                                        className="flex-1 py-2.5 rounded-premium-sm bg-primary hover:bg-primary-dark text-white text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                                    >
                                        <BookOpen className="w-4 h-4" />
                                        Leer
                                    </button>
                                    <button className="p-2.5 rounded-premium-sm bg-white/5 hover:bg-red-500/20 text-gray-400 hover:text-red-400 border border-white/5 transition-all">
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="glass-panel rounded-premium p-12 text-center border border-white/5 flex flex-col items-center justify-center gap-6">
                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center text-gray-500">
                        <Download className="w-10 h-10" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white mb-2">No hay descargas recientes</h2>
                        <p className="text-gray-400 max-w-xs mx-auto text-sm">Los libros que descargues aparecerán aquí para un acceso rápido.</p>
                    </div>
                    <button
                        onClick={() => onNavigate && onNavigate('search')}
                        className="px-8 py-3 bg-primary hover:bg-primary-dark text-white rounded-premium-sm text-xs font-black uppercase tracking-widest transition-all flex items-center gap-2"
                    >
                        <Search className="w-4 h-4" />
                        Explorar Catálogo
                    </button>
                </div>
            )}
        </div>
    );
};
