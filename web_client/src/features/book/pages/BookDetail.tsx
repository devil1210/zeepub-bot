import React, { useState, useEffect } from 'react';
import { api } from '@shared/services/api';
import {
  FileText,
  Home,
  Star,
  Download,
  Check,
  Loader2
} from 'lucide-react';
import { Volume, Series } from '@shared/types';
import { ReportIssueModal } from '@components/ReportIssueModal';
import { RatingModal } from '../components/RatingModal';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { BookCover } from '../components/BookCover';
import { BookActions } from '../components/BookActions';
import { BookHeader } from '../components/BookHeader';
import { BookSpecs } from '../components/BookSpecs';
import { ScheduleModal } from '@features/publisher/components/ScheduleModal';

interface BookDetailProps {
  volume?: Volume;
  series?: Series;
  bookId?: string;
  onBack: () => void;
  onSearch?: (term: string, type?: string) => void;
  onNavigate?: (tab: string) => void;
}

export const BookDetail: React.FC<BookDetailProps> = ({
  volume: initialVolume,
  series: initialSeries,
  bookId,
  onBack,
  onSearch,
  onNavigate
}) => {
  const { settings } = useTheme();
  const { webApp } = useTelegram();
  const { setContextType, registerCallbacks, setVisible, setCustomActions } = useNavigation();

  // Data State
  const [curVolume, setCurVolume] = useState<Volume | null>(initialVolume || null);
  const [curSeries, setCurSeries] = useState<Series | null>(initialSeries || null);
  const [loading, setLoading] = useState(!initialVolume);

  // UI State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);
  const [isScheduleModalOpen, setIsScheduleModalOpen] = useState(false);
  const [hasDownloaded, setHasDownloaded] = useState(false);
  const [localRating, setLocalRating] = useState(initialVolume?.rating || 0);
  const [localDownloadCount, setLocalDownloadCount] = useState(initialVolume?.downloadCount || 0);

  // Fetch Data if needed
  useEffect(() => {
    const fetchData = async () => {
      if (initialVolume && initialSeries && (initialVolume.wordCount || initialVolume.word_count)) {
        // Robust normalization for coverUrl if it's missing the expected object structure
        if (typeof initialVolume.coverUrl === 'string' && (initialVolume as any).cover_original) {
          setCurVolume({
            ...initialVolume,
            coverUrl: {
              cover_low: (initialVolume as any).cover_low,
              cover_medium: (initialVolume as any).cover_medium,
              cover_high: (initialVolume as any).cover_high,
              cover_original: (initialVolume as any).cover_original,
              cover: initialVolume.coverUrl
            }
          });
        }
        setLoading(false);
        return;
      }

      const idToFetch = bookId || initialVolume?.id;
      if (!idToFetch) return;

      try {
        setLoading(true);
        const res = await api.getBookDetail(idToFetch);
        const bookData = res.book || (res.id ? res : null);

        if (bookData) {
          const mappedVolume: Volume = {
            id: bookData.id,
            seriesId: bookData.seriesHash || 'unknown',
            title: bookData.title,
            volume: (bookData.volume !== undefined && bookData.volume !== null) ? bookData.volume : (bookData.volumeNumber !== undefined ? bookData.volumeNumber : 0),
            volumeNumber: (bookData.volume !== undefined && bookData.volume !== null) ? bookData.volume : (bookData.volumeNumber !== undefined ? bookData.volumeNumber : 0),
            coverUrl: {
              cover_low: bookData.cover_low,
              cover_medium: bookData.cover_medium,
              cover_high: bookData.cover_high,
              cover_original: bookData.cover_original,
              cover: bookData.cover || ''
            },
            coverThumbUrl: bookData.cover_thumb || bookData.cover_low || bookData.cover || '',
            published_at: bookData.published_at || bookData.publishedAt,
            publishedAt: bookData.publishedAt || bookData.published_at,
            pageCount: bookData.page_count || bookData.pageCount || 0,
            pages: bookData.page_count || bookData.pageCount || 0,
            format: (bookData.book_type || bookData.bookType || 'EPUB') as any,
            rating: bookData.rating_average || 0,
            description: bookData.description || bookData.summary,
            language: bookData.language || 'Español',
            size: bookData.size || (bookData.file_size ? `${(bookData.file_size / 1024 / 1024).toFixed(2)} MB` : 'N/A'),
            uploader: 'ZeePub',
            wordCount: bookData.word_count || bookData.wordCount || 0,
            word_count: bookData.word_count || bookData.wordCount || 0,
            readingTime: bookData.reading_time || bookData.readingTime,
            reading_time: bookData.reading_time || bookData.readingTime,
            tags: bookData.tags || [],
            demographics: bookData.demographics || bookData.demography || [],
            downloadCount: bookData.download_count || 0,
            download_count: bookData.download_count || 0,
            ratingCount: bookData.rating_count || bookData.ratingCount || 0,
            rating_count: bookData.rating_count || bookData.ratingCount || 0,
            illustrator: bookData.illustrator,
            translator: bookData.translator,
            layout_by: bookData.layout_by || bookData.layoutBy,
            layoutBy: bookData.layoutBy || bookData.layout_by,
            group: bookData.group,
            publisher: bookData.publisher,
            isbn: bookData.isbn,
            asin: bookData.asin,
            epubVersion: bookData.epub_version || bookData.epubVersion,
            epub_version: bookData.epub_version || bookData.epubVersion,
            modifiedAt: bookData.modifiedAt || bookData.modified_at,
            modified_at: bookData.modified_at || bookData.modifiedAt,
            modifiedAtOpf: bookData.modified_at_opf || bookData.modifiedAtOpf,
            modified_at_opf: bookData.modified_at_opf || bookData.modifiedAtOpf,
            english_title: bookData.english_title,
            spanish_title: bookData.spanish_title,
            romaji_title: bookData.romaji_title || bookData.romaji,
            book_type: bookData.book_type || bookData.bookType,
            is_uncensored: bookData.is_uncensored === 1 || bookData.is_uncensored === true,
            color_mode: bookData.color_mode,
            book_hash: bookData.book_hash
          };

          const mappedSeries: Series = {
            id: bookData.seriesHash || 'unknown',
            series_hash: bookData.series_hash || bookData.seriesHash || 'unknown',
            book_hash: bookData.book_hash,
            title: bookData.series || bookData.title,
            author: bookData.author || 'Desconocido',
            coverUrl: {
              cover_low: bookData.cover_low,
              cover_medium: bookData.cover_medium,
              cover_high: bookData.cover_high,
              cover_original: bookData.cover_original,
              cover: bookData.cover || ''
            },
            description: bookData.description || '',
            genre: bookData.tags ? bookData.tags.join(', ') : '',
            rating: bookData.rating_average || 0,
            volumesCount: 1,
            status: 'Completed',
            lastUpdated: bookData.modifiedAt_opf || bookData.modifiedAt || 'N/A',
            englishTitle: bookData.english_title,
            spanishTitle: bookData.spanish_title,
            seriesName: bookData.series_name,
            romajiTitle: bookData.romaji_title || bookData.romaji,
            is_uncensored: bookData.is_uncensored,
            color_mode: bookData.color_mode,
            volumes: []
          };

          setCurVolume(mappedVolume);
          setCurSeries(mappedSeries);
          setLocalRating(mappedVolume.rating);
          setLocalDownloadCount(mappedVolume.downloadCount || 0);

          if (bookData.is_downloaded) {
            setHasDownloaded(true);
          }
        }
      } catch (err) {
        console.error("Failed to fetch book detail", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [bookId, initialVolume?.id]);

  useEffect(() => {
    setContextType('book');
    setVisible(true);

    const buttons: any[] = [
      {
        id: 'home',
        label: 'Inicio',
        icon: Home,
        onClick: () => {
          webApp?.HapticFeedback?.notificationOccurred('success');
          onNavigate && onNavigate('dashboard');
        }
      }
    ];

    // We removed the floating/sticky Download and Rate buttons
    // to rely on the on-page "Liquid" UI controls which are now visible on mobile.
    // This addresses the user's feedback about the "stuck" button.

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
  }, [onBack, setContextType, setVisible, registerCallbacks, hasDownloaded, onNavigate, setCustomActions]);



  const handleSearch = (term?: string, type?: string) => {
    if (term && onSearch) {
      onSearch(term, type);
    }
  };

  const handleDownload = async () => {
    if (!curVolume) return;
    try {
      webApp?.HapticFeedback?.impactOccurred('medium');
      await api.requestDownload(curVolume.id);
      setHasDownloaded(true);
      setLocalDownloadCount(prev => prev + 1);
      webApp?.HapticFeedback?.notificationOccurred('success');
      webApp?.showAlert?.("📚 ¡Libro enviado! Revisa tu chat privado con el bot.");
    } catch (err) {
      console.error("Error downloading book", err);
      webApp?.HapticFeedback?.notificationOccurred('error');
      webApp?.showAlert?.("❌ Error: " + (err as Error).message);
    }
  };

  const handleRateSubmit = async (rating: number) => {
    if (!curVolume) return;
    try {
      const res = await api.rateBook(curVolume.id, rating);
      if (res && res.new_average !== undefined) {
        setLocalRating(res.new_average);
        setCurVolume(prev => prev ? { ...prev, rating: res.new_average } : null);
      } else {
        setLocalRating(rating);
      }
      webApp?.HapticFeedback?.notificationOccurred('success');
      setIsRatingModalOpen(false);
    } catch (err) {
      console.error("Error rating book", err);
      webApp?.HapticFeedback?.notificationOccurred('error');
      webApp?.showAlert?.("Error al enviar valoración: " + (err as Error).message);
    }
  };

  const handleRateDelete = async () => {
    if (!curVolume) return;
    try {
      const res = await api.removeRating(curVolume.id);
      if (res && res.new_average !== undefined) {
        setLocalRating(res.new_average);
        setCurVolume(prev => prev ? { ...prev, rating: res.new_average } : null);
      } else {
        setLocalRating(0);
      }
      setIsRatingModalOpen(false);
    } catch (err) {
      console.error("Error deleting rating", err);
      alert("Error al eliminar valoración: " + (err as Error).message);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr || dateStr === 'N/A' || dateStr === 'Reciente' || dateStr === 'undefined') return 'N/A';

    // Clean string from known noise
    let cleanStr = dateStr.trim();
    if (cleanStr.includes('T00:00:00')) {
      cleanStr = cleanStr.split('T')[0];
    }

    // Try standard parsing
    let d = new Date(cleanStr);

    // If invalid, try to check if DD and MM are swapped (e.g. 1998-18-09)
    if (isNaN(d.getTime())) {
      const parts = cleanStr.split(/[-/]/);
      if (parts.length === 3) {
        const year = parts[0].length === 4 ? parts[0] : parts[2];
        const p1 = parseInt(parts[1]);
        const p2 = parseInt(parts[2].length === 4 ? parts[1] : parts[2]);

        // If year is first (YYYY-DD-MM)
        if (parts[0].length === 4) {
          if (p1 > 12 && p2 <= 12) {
            // Likely YYYY-DD-MM
            d = new Date(`${year}-${parts[2]}-${parts[1]}`);
          }
        }
      }
    }

    if (isNaN(d.getTime())) return cleanStr; // Return as is if still invalid

    return d.toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatReadingTime = (minutes?: number) => {
    if (!minutes || minutes <= 0) return 'N/A';
    const hours = minutes / 60;
    const hoursStr = hours % 1 === 0 ? hours.toString() : hours.toFixed(1);
    return `${minutes} min/ ${hoursStr} horas`;
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
        <Loader2 className="w-12 h-12 text-primary animate-spin mb-4" />
        <p className="text-gray-400 font-bold uppercase tracking-widest text-xs">Cargando detalles...</p>
      </div>
    );
  }

  if (!curVolume || !curSeries) return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[400px]">
      <p className="text-red-400 font-bold mb-4">No se pudo cargar la información del libro</p>
      <button onClick={onBack} className="px-6 py-2 bg-primary text-white rounded-premium-sm">Volver</button>
    </div>
  );

  // Función para limpiar y validar que el texto sea romaji (solo caracteres latinos)
  const cleanRomajiText = (text: string): string => {
    if (!text) return '';

    // Si contiene caracteres japoneses (hiragana, katakana, kanji), no es romaji válido
    const hasJapaneseChars = /[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]/.test(text);

    if (hasJapaneseChars) {
      console.warn('Texto japonés detectado en romajiTitle:', text);
      return ''; // No mostrar si no es romaji válido
    }

    return text.trim();
  };

  // Función para intentar extraer romaji del título si no hay romajiTitle válido
  const extractRomajiFromTitle = (title: string): string => {
    if (!title) return '';

    // Patrones comunes de títulos japoneses con romaji
    // Ej: "Kagurabachi: Yuugen no Ma" -> "Kagurabachi: Yuugen no Ma"
    const romajiPatterns = [
      /([a-zA-Z\s\-\:]+)/,  // Extraer caracteres latinos
      /([^\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf]+)/  // Extraer lo que no es japonés
    ];

    for (const pattern of romajiPatterns) {
      const match = title.match(pattern);
      if (match) {
        const extracted = match[1].trim();
        if (extracted && extracted.length > 2) { // Mínimo 3 caracteres para ser válido
          console.log('Romaji extraído del título:', extracted);
          return extracted;
        }
      }
    }

    return '';
  };

  // Intentar obtener romaji de múltiples fuentes
  const getRomajiTitle = (): string => {
    // 1. Usar romaji_title del volumen (LocalBook) - PRIORIDAD MÁXIMA
    const volumeRomaji = cleanRomajiText(String(curVolume.romaji_title || ''));
    if (volumeRomaji) return volumeRomaji;

    // 2. Usar romajiTitle de la serie (fallback)
    const seriesRomaji = cleanRomajiText(String(curSeries?.romajiTitle || ''));
    if (seriesRomaji) return seriesRomaji;

    // 3. Intentar extraer del título principal
    const mainTitle = String(curSeries?.title || curVolume.series || '');
    const extractedRomaji = extractRomajiFromTitle(mainTitle);
    if (extractedRomaji) return extractedRomaji;

    return ''; // No se encontró romaji válido
  };

  const displayData = {
    ...curVolume,
    rating: localRating,
    ratingCount: curVolume.rating_count || curVolume.ratingCount || 0,
    downloadCount: localDownloadCount,
    title: String(curVolume.title || ''),
    language: String(curVolume.language || 'Español'),
    size: String(curVolume.size || (curVolume.file_size ? `${(curVolume.file_size / (1024 * 1024)).toFixed(2)} MB` : '0 MB')),
    format: 'EPUB',
    bookType: String(curVolume.book_type || curVolume.bookType || 'Novela Ligera'),
    epubVersion: String(curVolume.epub_version || curVolume.epubVersion || '3.0'),
    uploader: 'ZeePub',
    wordCount: curVolume.word_count || curVolume.wordCount || 0,
    pages: curVolume.page_count || curVolume.pageCount || curVolume.pages || 0,
    readTime: formatReadingTime(curVolume.reading_time || curVolume.readingTime || ((curVolume.word_count || curVolume.wordCount) ? Math.ceil((curVolume.word_count || curVolume.wordCount) / 200) : undefined)),
    lastUpdated: curVolume.modified_at_opf || curVolume.modifiedAtOpf ? formatDate(String(curVolume.modified_at_opf || curVolume.modifiedAtOpf)) : (curVolume.modified_at || curVolume.modifiedAt ? formatDate(String(curVolume.modified_at || curVolume.modifiedAt)) : 'N/A'),
    publishedDate: formatDate(String(curVolume.published_at || curVolume.publishedAt || curVolume.publishedDate || '')),
    description: String(curVolume.description || curVolume.summary || 'Sin sinopsis disponible.'),
    displayTitle: String(curSeries?.seriesName || curVolume.series_name || curVolume.english_title || curVolume.englishTitle || curVolume.title || curSeries?.title || curVolume.series || 'Libro sin título'),
    romajiTitle: String(curVolume.title || curVolume.romaji_title || getRomajiTitle()),
    illustrator: String(curVolume.illustrator || 'N/A'),
    translator: String(curVolume.translator || 'ZeePub'),
    group: String(curVolume.group || curVolume.publisher || curVolume.translator || 'ZeePub'),
    publisher: String(curVolume.publisher || 'N/A'),
    typesetter: String(curVolume.layout_by || curVolume.layoutBy || curVolume.typesetter || 'N/A'),
    isbn: String(curVolume.isbn || 'N/A'),
    asin: String(curVolume.asin || 'N/A'),
    demography: Array.isArray(curVolume.demographics) ? curVolume.demographics : (Array.isArray(curVolume.demography) ? curVolume.demography : []),
    genres: Array.isArray(curVolume.tags) ? curVolume.tags : (Array.isArray(curVolume.genres) ? curVolume.genres : (Array.isArray(curSeries?.genres) ? curSeries.genres : [])),
    is_uncensored: curVolume.is_uncensored === 1 || curVolume.is_uncensored === true,
    color_mode: curVolume.color_mode,
    volume: curVolume.volume !== undefined ? curVolume.volume : curVolume.volumeNumber,
    volumeDisplay: (curVolume.volume === 0 || curVolume.volumeNumber === 0 || (!curVolume.volume && !curVolume.volumeNumber)) ? 'Único' : `${curVolume.volume || curVolume.volumeNumber}`
  };

  const formatDescription = (desc: string) => {
    if (!desc) return null;
    const cleanDesc = desc.replace(/<br\s*\/?>/gi, '\n');
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

  const detailItems = [
    { label: 'Serie', value: displayData.displayTitle, highlight: true, clickable: true, type: 'series' },
    { label: 'Volumen', value: displayData.volumeDisplay },
    { label: 'Tipo de libro', value: displayData.bookType, clickable: true, type: 'type' },
    { label: 'ISBN', value: displayData.isbn, highlight: true, font: 'mono' },
    { label: 'ASIN', value: displayData.asin, highlight: true, font: 'mono' },
    { label: 'Idioma', value: displayData.language, highlight: true, clickable: true, type: 'language' },
    { label: 'Traductor', value: displayData.translator || 'ZeePub', color: 'text-indigo-600 dark:text-indigo-400', clickable: true, type: 'translator' },
    { label: 'Grupo Traductor', value: displayData.publisher !== 'N/A' ? displayData.publisher : (displayData.group || 'ZeePub'), highlight: true, clickable: true, type: 'group' },
    { label: 'Fecha de publicación', value: displayData.publishedDate, highlight: true },
  ];

  const specItems = [
    { label: 'Formato', value: 'EPUB', highlight: true },
    { label: 'Versión Epub', value: `v${displayData.epubVersion}` },
    { label: 'Palabras', value: (displayData.wordCount !== undefined && displayData.wordCount !== null) ? displayData.wordCount.toLocaleString() : 'N/A' },
    { label: 'Páginas', value: (displayData.pages !== undefined && displayData.pages !== null) ? displayData.pages : 'N/A' },
    { label: 'Maquetador', value: displayData.typesetter, highlight: true, clickable: true, type: 'typesetter' },
    { label: 'Lectura Aprox.', value: displayData.readTime },
    { label: 'Tamaño', value: displayData.size, highlight: true, font: 'mono' },
    { label: 'Uploader', value: displayData.uploader, color: 'text-purple-600 dark:text-purple-400', clickable: true, type: 'uploader' },
    { label: 'Fecha de actualización', value: displayData.lastUpdated, highlight: true },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-900 dark:text-gray-100 bg-transparent">
      <ReportIssueModal
        isOpen={isReportModalOpen}
        onClose={() => setIsReportModalOpen(false)}
        contextData={`Book: ${displayData.title} (ID: ${bookId || initialVolume?.id})`}
      />
      <RatingModal
        isOpen={isRatingModalOpen}
        onClose={() => setIsRatingModalOpen(false)}
        onSubmit={handleRateSubmit}
        onDelete={handleRateDelete}
        title={displayData.title}
        currentRating={localRating}
      />

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto pb-44 md:pb-20 custom-scrollbar animate-fade-in-up">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">

            {/* LEFT COLUMN: Cover & Actions */}
            <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-8">
              <BookCover
                title={displayData.title}
                coverUrl={displayData.coverUrl}
                coverThumbUrl={displayData.coverThumbUrl}
                settings={settings}
              />

              <BookActions
                hasDownloaded={hasDownloaded}
                onDownload={handleDownload}
                onOpenRating={() => setIsRatingModalOpen(true)}
                onOpenReport={() => setIsReportModalOpen(true)}
                onOpenSchedule={() => setIsScheduleModalOpen(true)}
                rating={localRating}
              />

              {/* Stats Block (Sidebar - Desktop) */}
              <div className="hidden md:block glass-panel p-4 rounded-premium-lg border border-white/5 space-y-4 shadow-premium">
                <div className="flex items-center justify-between pb-3 border-b border-white/5">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Valoración</span>
                  <div className="flex flex-col items-end">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-gray-900 dark:text-white font-bold">{displayData.rating > 0 ? displayData.rating.toFixed(1) : '—'}</span>
                    </div>
                    {displayData.ratingCount > 0 && (
                      <span className="text-[10px] text-gray-400 mt-1">{displayData.ratingCount} {displayData.ratingCount === 1 ? 'voto' : 'votos'}</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center justify-between pb-3 border-b border-white/5">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Descargas Totales</span>
                  <div className="flex items-center gap-1.5 text-primary">
                    <Download className="w-4 h-4" />
                    <span className="text-gray-900 dark:text-white font-bold">{displayData.downloadCount}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400">
                  <span>Última Actualización</span>
                  <span className="text-gray-900 dark:text-white font-bold">{displayData.lastUpdated}</span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Content */}
            <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-6">

              <BookHeader
                displayTitle={displayData.displayTitle}
                romajiTitle={displayData.romajiTitle}
                seriesName={curSeries?.title}
                author={curSeries.author}
                rating={displayData.rating}
                ratingCount={displayData.ratingCount}
                downloadCount={displayData.downloadCount}
                illustrator={displayData.illustrator}
                volumeNumber={displayData.volume}
                publishedDate={displayData.publishedDate}
                translator={displayData.translator}
                lastUpdated={displayData.lastUpdated}
                group={displayData.group}
                color_mode={displayData.color_mode}
                is_uncensored={displayData.is_uncensored}
                onSearch={handleSearch}
              />

              {/* Genres & Tags */}
              <div className="flex flex-wrap gap-2">
                {displayData.demography.map((tag: string) => (
                  <button
                    key={tag}
                    onClick={() => handleSearch(tag, 'demography')}
                    className="px-3 py-1.5 rounded-premium-sm bg-[#004d40] text-[#4db6ac] border border-[#00695c] text-[10px] font-black uppercase tracking-wider shadow-sm hover:bg-[#00695c] hover:text-white transition-colors"
                  >
                    {tag}
                  </button>
                ))}
                {displayData.genres.map((genre: string) => (
                  <button
                    key={genre}
                    onClick={() => handleSearch(genre, 'genre')}
                    className="px-3 py-1.5 rounded-premium-sm bg-gray-200 dark:bg-[#1f2937] text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-[#374151] text-[10px] font-bold uppercase tracking-wider hover:bg-gray-300 dark:hover:bg-[#374151] hover:text-black dark:hover:text-white hover:border-gray-400 dark:hover:border-gray-500 transition-colors cursor-pointer"
                  >
                    {genre}
                  </button>
                ))}
              </div>

              {/* Synopsis */}
              <div className="glass-panel border border-white/5 rounded-premium-lg p-6 lg:p-8 shadow-premium">
                <div className="flex items-center gap-2 mb-4 text-primary">
                  <FileText className="w-5 h-5" />
                  <h3 className="text-xs font-black uppercase tracking-widest">Sinopsis</h3>
                </div>
                <div className="text-gray-700 dark:text-gray-300 text-sm sm:text-base leading-7 sm:leading-8 font-medium text-justify">
                  {formatDescription(displayData.description)}
                </div>
              </div>

              {/* Details and Specs Grids */}
              {/* Specs Collapsible Glass Card */}
              <div className="glass-panel border border-white/5 rounded-premium-lg overflow-hidden transition-all duration-500 hover:border-primary/20 hover:shadow-premium group/specs shadow-premium">
                <details className="group/details">
                  <summary className="flex items-center justify-between p-6 cursor-pointer list-none select-none">
                    <div className="flex items-center gap-3 text-primary">
                      <div className="p-2 bg-primary/10 rounded-premium-md group-hover/specs:bg-primary group-hover/specs:text-white transition-colors">
                        <FileText className="w-5 h-5" />
                      </div>
                      <h3 className="text-sm font-black uppercase tracking-widest text-white">Ficha Técnica</h3>
                    </div>
                    <div className="w-8 h-8 rounded-premium-full bg-white/5 flex items-center justify-center group-hover/specs:bg-white/10 transition-colors">
                      <span className="text-white text-xl font-bold transition-transform duration-300 group-open/details:rotate-180">↓</span>
                    </div>
                  </summary>

                  <div className="px-6 pb-8 animate-in slide-in-from-top-4 fade-in duration-300">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-12 gap-y-6">
                      {/* Left Column */}
                      <div className="space-y-4">
                        {detailItems.map((item, idx) => (
                          <div key={idx} className="flex flex-col gap-1 border-b border-white/5 pb-2 last:border-0">
                            <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider">{item.label}</span>
                            <span className={`text-sm font-medium ${item.highlight ? 'text-white' : 'text-gray-300'} ${item.clickable ? 'hover:text-primary cursor-pointer transition-colors' : ''} ${item.font === 'mono' ? 'font-mono' : ''}`}
                              onClick={() => item.clickable && item.value && onSearch && onSearch(String(item.value), item.type)}>
                              {item.value || 'N/A'}
                            </span>
                          </div>
                        ))}
                      </div>
                      {/* Right Column */}
                      <div className="space-y-4">
                        {specItems.map((item, idx) => (
                          <div key={idx} className="flex flex-col gap-1 border-b border-white/5 pb-2 last:border-0">
                            <span className="text-[10px] uppercase font-bold text-gray-500 tracking-wider">{item.label}</span>
                            <span className={`text-sm font-medium ${item.highlight ? 'text-white' : 'text-gray-300'} ${item.clickable ? 'hover:text-primary cursor-pointer transition-colors' : ''} ${item.font === 'mono' ? 'font-mono' : ''}`}
                              onClick={() => item.clickable && item.value && onSearch && onSearch(String(item.value), item.type)}>
                              {item.value || 'N/A'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </details>
              </div>

            </div>
          </div>
        </div>
      </div>

      <ScheduleModal
        isOpen={isScheduleModalOpen}
        onClose={() => setIsScheduleModalOpen(false)}
        bookHash={curVolume.book_hash || 'unknown'}
        bookTitle={displayData.title}
      />
    </div>
  );
};
