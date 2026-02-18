import React, { useState, useEffect } from 'react';
import { Loader2, Home, Download } from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { SeriesDetail } from './SeriesDetail';
import { BookDetail } from './BookDetail';
import { Series, Volume } from '@shared/types';

interface BookDetailByIdProps {
    bookId: string;
    onBack: () => void;
    onNavigate?: (tab: string, series?: Series | null, volume?: Volume | null) => void;
}

export const BookDetailById: React.FC<BookDetailByIdProps> = ({ bookId, onBack, onNavigate }) => {
    const { settings } = useTheme();
    const { webApp } = useTelegram();
    const { setContextType, registerCallbacks, setVisible, setCustomActions, setSearchTerm } = useNavigation();
    const [book, setBook] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        setContextType('book');
        setVisible(true);

        const buttons: any[] = [
            {
                id: 'home',
                label: 'Inicio',
                icon: Home,
                onClick: () => onNavigate && onNavigate('dashboard')
            }
        ];

        setCustomActions({
            buttons
        });

        const unregister = registerCallbacks({
            onBack: onBack
        });
        return () => {
            unregister();
            setContextType('main');
        };
    }, [onBack, setContextType, setVisible, registerCallbacks, downloading, onNavigate, setCustomActions]);

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
            webApp?.HapticFeedback?.impactOccurred('medium');
            setDownloading(true);
            await api.requestDownload(bookId, 'private');
            webApp?.HapticFeedback?.notificationOccurred('success');
            webApp?.showAlert?.('✅ Libro enviado a tu chat privado');
        } catch (err: any) {
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.('❌ Error: ' + (err.message || 'No se pudo descargar'));
        } finally {
            setDownloading(false);
        }
    };

    const handleSelectVolume = (vol: Volume, selSeries: Series) => {
        if (onNavigate) {
            onNavigate('search', selSeries, vol);
        }
    };

    const handleSearch = (term: string, scope?: string) => {
        if (setSearchTerm && onNavigate) {
            // If it's a specific field like translator, maybe add prefix? 
            // For now, let's stick to the term as the user expects.
            setSearchTerm(term);
            onNavigate('search');
        }
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

    // Logic: If it's a series or has multiple volumes, show SeriesDetail
    // The backend provides 'is_series' flag in our new implementation
    if (book.is_series && book.volumes && book.volumes.length > 0) {
        return (
            <SeriesDetail
                series={book as Series}
                onBack={onBack}
                onSelectVolume={handleSelectVolume}
                onSearch={handleSearch}
            />
        );
    }

    // Otherwise, show individual BookDetail
    return (
        <BookDetail
            series={book.series_data || book}
            volume={book as Volume}
            bookId={bookId}
            onBack={onBack}
            onNavigate={onNavigate}
            onSearch={handleSearch}
        />
    );
};

