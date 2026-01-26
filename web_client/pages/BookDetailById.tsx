import React, { useState, useEffect } from 'react';
import { ArrowLeft, Download, Star, Book, User, Calendar, Hash, Loader2 } from 'lucide-react';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';
import { getCoverUrl } from '../src/utils/imageUtils';

interface BookDetailByIdProps {
    bookId: string;
    onBack: () => void;
    onNavigate?: (tab: string) => void;
}

export const BookDetailById: React.FC<BookDetailByIdProps> = ({ bookId, onBack, onNavigate }) => {
    const { settings } = useTheme();
    const [book, setBook] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        const fetchBook = async () => {
            try {
                setLoading(true);
                const res = await api.getBookDetail(bookId);
                if (res) {
                    // El backend puede devolver {book: {...}} o el libro directamente
                    const bookData = res.book || (res.id ? res : null);
                    if (bookData) {
                        setBook(bookData);
                    } else {
                        setError('No se encontró el libro');
                    }
                } else {
                    setError('No se encontró el libro');
                }
            } catch (err: any) {
                console.error('Error fetching book:', err);
                setError(err.message || 'Error al cargar el libro');
            } finally {
                setLoading(false);
            }
        };
        fetchBook();
    }, [bookId]);

    const handleDownload = async () => {
        if (!book) return;
        try {
            setDownloading(true);
            await api.requestDownload(bookId, 'private');
            // Show success feedback
            alert('✅ Libro enviado a tu chat privado');
        } catch (err: any) {
            alert('❌ Error: ' + (err.message || 'No se pudo descargar'));
        } finally {
            setDownloading(false);
        }
    };

    const formatDescription = (desc: string) => {
        if (!desc) return null;

        // Clean up <br/> tags first
        const cleanDesc = desc.replace(/<br\s*\/?>/gi, '\n');

        // Collapse double breaks and split by single breaks
        const paragraphs = cleanDesc
            .split(/\n\s*\n/)
            .join('\n')
            .split('\n')
            .filter(p => p.trim() !== '');

        return paragraphs.map((p, i) => (
            <p key={i} className={i !== paragraphs.length - 1 ? "mb-3" : ""}>
                {p}
            </p>
        ));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full min-h-[400px]">
                <div className="flex flex-col items-center gap-4">
                    <Loader2 className="w-10 h-10 text-primary animate-spin" />
                    <p className="text-gray-400 text-sm">Cargando detalles...</p>
                </div>
            </div>
        );
    }

    if (error || !book) {
        return (
            <div className="flex flex-col items-center justify-center h-full min-h-[400px] gap-4">
                <p className="text-red-400 text-lg">{error || 'Libro no encontrado'}</p>
                <button
                    onClick={onBack}
                    className="px-6 py-2 bg-primary text-white rounded-premium-sm font-bold"
                >
                    Volver
                </button>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto px-4 py-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Back Button */}
            <button
                onClick={onBack}
                className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
            >
                <ArrowLeft className="w-5 h-5" />
                <span className="text-sm font-bold uppercase tracking-wider">Volver</span>
            </button>

            {/* Book Header */}
            <div className="flex flex-col md:flex-row gap-8 mb-8">
                {/* Cover */}
                <div className="w-48 md:w-64 flex-shrink-0 mx-auto md:mx-0">
                    <div className="aspect-[2/3] rounded-premium-sm overflow-hidden border border-white/10 shadow-2xl">
                        <img
                            src={getCoverUrl(book, book.cover_thumb || book.cover, settings.coverQuality)}
                            alt={book.title}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                                (e.target as HTMLImageElement).src = 'https://via.placeholder.com/300x450?text=Sin+Portada';
                            }}
                        />
                    </div>
                </div>

                {/* Info */}
                <div className="flex-1 space-y-4">
                    <h1 className="text-2xl md:text-3xl font-black text-white leading-tight">
                        {book.clean_title || book.title}
                    </h1>

                    {book.author && (
                        <p className="text-lg text-primary font-bold flex items-center gap-2">
                            <User className="w-4 h-4" />
                            {book.author}
                        </p>
                    )}

                    {book.series && (
                        <p className="text-gray-400 text-sm flex items-center gap-2">
                            <Book className="w-4 h-4" />
                            {book.series} {book.seriesIndex ? `Vol. ${book.seriesIndex}` : ''}
                        </p>
                    )}

                    {book.rating_average > 0 && (
                        <div className="flex items-center gap-2">
                            <Star className="w-4 h-4 text-yellow-500 fill-current" />
                            <span className="text-white font-bold">{book.rating_average.toFixed(1)}</span>
                            {book.rating_count > 0 && (
                                <span className="text-gray-500 text-sm">({book.rating_count} votos)</span>
                            )}
                        </div>
                    )}

                    {/* Tags */}
                    {book.tags && book.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                            {book.tags.slice(0, 5).map((tag: string, i: number) => (
                                <span
                                    key={i}
                                    className="px-3 py-1 bg-white/10 text-gray-300 rounded-full text-xs font-bold"
                                >
                                    {tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Download Button */}
                    <button
                        onClick={handleDownload}
                        disabled={downloading}
                        className="w-full md:w-auto px-8 py-4 bg-primary hover:bg-primary-dark text-white font-black uppercase tracking-wider rounded-premium-sm flex items-center justify-center gap-3 transition-all shadow-lg shadow-primary/30 disabled:opacity-50"
                    >
                        {downloading ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Enviando...
                            </>
                        ) : (
                            <>
                                <Download className="w-5 h-5" />
                                Descargar EPUB
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Description */}
            {book.description && (
                <div className="glass-panel rounded-premium-sm p-6 border border-white/5">
                    <h3 className="text-sm font-black text-gray-500 uppercase tracking-wider mb-4">
                        Sinopsis
                    </h3>
                    <div className="text-gray-300 leading-relaxed font-medium">
                        {formatDescription(book.description)}
                    </div>
                </div>
            )}

            {/* Metadata Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                {book.translator && (
                    <div className="glass-panel p-4 rounded-premium-sm border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Traductor</p>
                        <p className="text-white font-bold text-sm truncate">{book.translator}</p>
                    </div>
                )}
                {book.publisher && (
                    <div className="glass-panel p-4 rounded-premium-sm border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Editorial</p>
                        <p className="text-white font-bold text-sm truncate">{book.publisher}</p>
                    </div>
                )}
                {book.publishedAt && (
                    <div className="glass-panel p-4 rounded-premium-sm border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Publicado</p>
                        <p className="text-white font-bold text-sm">{book.publishedAt}</p>
                    </div>
                )}
                {book.isbn && (
                    <div className="glass-panel p-4 rounded-premium-sm border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">ISBN</p>
                        <p className="text-white font-bold text-sm truncate">{book.isbn}</p>
                    </div>
                )}
                {(book.modifiedAtOpf || book.modifiedAt) && (
                    <div className="glass-panel p-4 rounded-premium-sm border border-white/5">
                        <p className="text-[10px] text-gray-500 uppercase font-bold mb-1">Actualizado</p>
                        <p className="text-white font-bold text-sm truncate">
                            {new Date(book.modifiedAtOpf || book.modifiedAt).toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })}
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

