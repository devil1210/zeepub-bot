import React, { useState, useEffect } from 'react';
import { api } from '../src/services/api';
import { getCoverUrl } from '../src/utils/imageUtils';
import {
  ArrowLeft,
  Share2,
  Flag,
  Calendar,
  Hash,
  User,
  ArrowDownToLine,
  Tag,
  Info,
  Library,
  FileText,
  Clock,
  Database,
  PenTool,
  Languages,
  FileBox,
  Layers,
  BookOpen,
  Globe,
  Star,
  Download,
  Home,
  Reply,
  Check,
  X,
  Loader2
} from 'lucide-react';
import { Volume, Series } from '../types';
import { ReportIssueModal } from '../components/ReportIssueModal';
import { RatingModal } from '../components/RatingModal';
import { useTheme } from '../contexts/ThemeContext';

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

  // Data State
  const [curVolume, setCurVolume] = useState<Volume | null>(initialVolume || null);
  const [curSeries, setCurSeries] = useState<Series | null>(initialSeries || null);
  const [loading, setLoading] = useState(!initialVolume);

  // UI State
  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false);
  const [isFullscreenCover, setIsFullscreenCover] = useState(false);
  const [hasDownloaded, setHasDownloaded] = useState(false);
  const [localRating, setLocalRating] = useState(initialVolume?.rating || 0);
  const [localDownloadCount, setLocalDownloadCount] = useState(initialVolume?.downloadCount || 0);

  // Fetch Data if needed
  useEffect(() => {
    const fetchData = async () => {
      if (initialVolume && initialSeries) {
        setLoading(false);
        return;
      }

      const idToFetch = bookId || initialVolume?.id;
      if (!idToFetch) return;

      try {
        setLoading(true);
        const res = await api.getBookDetail(idToFetch);
        // The API might return { book: ... } or the object directly
        const bookData = res.book || (res.id ? res : null);

        if (bookData) {
          // Map backend book to Volume
          const mappedVolume: Volume = {
            id: bookData.id,
            seriesId: bookData.seriesHash || 'unknown',
            title: bookData.title,
            volumeNumber: bookData.seriesIndex || 0,
            coverUrl: {
              cover_low: bookData.cover_low,
              cover_medium: bookData.cover_medium,
              cover_high: bookData.cover_high,
              cover_original: bookData.cover_original,
              cover: bookData.cover || ''
            },
            coverThumbUrl: bookData.cover_thumb || bookData.cover_low || bookData.cover || '',
            publishedDate: bookData.publishedAt || 'N/A',
            pages: bookData.pageCount || 0,
            format: (bookData.bookType || 'EPUB') as any,
            rating: bookData.rating_average || 0,
            description: bookData.description || bookData.summary,
            language: bookData.language || 'Español',
            size: bookData.fileSize ? `${(bookData.fileSize / 1024 / 1024).toFixed(2)} MB` : 'N/A',
            uploader: 'ZeePub',
            wordCount: bookData.wordCount,
            readTime: bookData.readingTime,
            tags: bookData.tags || [],
            demography: bookData.demographics || [],
            downloadCount: bookData.download_count || 0,
            ratingCount: bookData.rating_count || 0,
            illustrator: bookData.illustrator,
            translator: bookData.translator,
            typesetter: bookData.layoutBy,
            group: bookData.group,
            isbn: bookData.isbn,
            asin: bookData.asin,
            epubVersion: bookData.epubVersion,
            modifiedAt: bookData.modifiedAt,
            modifiedAtOpf: bookData.modifiedAtOpf,
            englishTitle: bookData.english_title,
            spanishTitle: bookData.spanish_title,
            romajiTitle: bookData.romaji_title || bookData.romaji,
            bookType: bookData.bookType || bookData.categoria || 'Novela Ligera'
          };

          const mappedSeries: Series = {
            id: bookData.seriesHash || 'unknown',
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
            romajiTitle: bookData.romaji_title || bookData.romaji,
            volumes: []
          };

          setCurVolume(mappedVolume);
          setCurSeries(mappedSeries);
          setLocalRating(mappedVolume.rating);
          setLocalDownloadCount(mappedVolume.downloadCount || 0);
        }
      } catch (err) {
        console.error("Failed to fetch book detail", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [bookId, initialVolume?.id]);


  // Check persistent download status
  useEffect(() => {
    if (!curVolume) return;
    const checkDownloadStatus = async () => {
      try {
        const historyRes = await api.getDownloadHistory();
        if (historyRes && historyRes.downloads) {
          const found = historyRes.downloads.some((d: any) => d.id === curVolume.id || d.title === curVolume.title);
          if (found) setHasDownloaded(true);
        }
      } catch (err) {
        console.error("Failed to check download history", err);
      }
    };
    checkDownloadStatus();
  }, [curVolume?.id, curVolume?.title]);

  const handleSearch = (term?: string, type?: string) => {
    if (term && onSearch) {
      onSearch(term, type);
    }
  };

  const handleDownload = async () => {
    if (!curVolume) return;
    try {
      await api.requestDownload(curVolume.id);
      setHasDownloaded(true);
      setLocalDownloadCount(prev => prev + 1);
    } catch (err) {
      console.error("Error downloading book", err);
      alert("Error al solicitar descarga: " + (err as Error).message);
    }
  };

  const handleRateSubmit = async (rating: number) => {
    if (!curVolume) return;
    try {
      const res = await api.rateBook(curVolume.id, rating);
      if (res && res.new_average !== undefined) {
        setLocalRating(res.new_average);
        setLocalDownloadCount(prev => prev); // trigger re-render if needed, though not used for count here
        // Update volume state to keep it in sync
        setCurVolume(prev => prev ? { ...prev, rating: res.new_average, downloadCount: res.total_votes ?? prev.downloadCount } : null);
      } else {
        setLocalRating(rating);
      }
      setIsRatingModalOpen(false);
    } catch (err) {
      console.error("Error rating book", err);
      alert("Error al enviar valoración: " + (err as Error).message);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr || dateStr === 'N/A' || dateStr === 'Reciente') return 'N/A';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const formatReadingTime = (minutes?: number) => {
    if (!minutes) return 'N/A';
    const hours = (minutes / 60).toFixed(2);
    return `${minutes} m / ${hours.replace('.', ',')} horas`;
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
      <button onClick={onBack} className="px-6 py-2 bg-primary text-white rounded-xl">Volver</button>
    </div>
  );

  const displayData = {
    ...curVolume,
    rating: localRating,
    downloadCount: localDownloadCount,
    title: String(curVolume.title || ''),
    language: String(curVolume.language || 'Español'),
    size: String(curVolume.size || '0 MB'),
    format: 'EPUB',
    bookType: String(curVolume.bookType || 'Novela Ligera'),
    epubVersion: String(curVolume.epubVersion || '3.0'),
    uploader: 'ZeePub',
    wordCount: curVolume.wordCount || 0,
    pages: curVolume.pages || 0,
    readTime: formatReadingTime(curVolume.wordCount ? Math.ceil(curVolume.wordCount / 200) : (typeof curVolume.readTime === 'number' ? curVolume.readTime : undefined)),
    lastUpdated: curVolume.modifiedAtOpf ? formatDate(String(curVolume.modifiedAtOpf)) : (curVolume.modifiedAt ? formatDate(String(curVolume.modifiedAt)) : 'N/A'),
    publishedDate: formatDate(String(curVolume.publishedDate || '')),
    description: String(curVolume.description || 'Sin sinopsis disponible.'),
    displayTitle: String(curVolume.englishTitle || curSeries?.englishTitle || curSeries?.title || curVolume.title || 'Libro sin título'),
    romajiTitle: String(curVolume.romajiTitle || curSeries?.romajiTitle || ''),
    illustrator: String(curVolume.illustrator || 'N/A'),
    translator: String(curVolume.translator || 'ZeePub'),
    group: String(curVolume.group || 'ZeePub'),
    typesetter: String(curVolume.typesetter || 'N/A'),
    isbn: String(curVolume.isbn || 'N/A'),
    asin: String(curVolume.asin || 'N/A'),
    demography: Array.isArray(curVolume.demography) ? curVolume.demography : (Array.isArray((curVolume as any).demographics) ? (curVolume as any).demographics : []),
    genres: Array.isArray((curVolume as any).genres) ? (curVolume as any).genres : (Array.isArray((curVolume as any).tags) ? (curVolume as any).tags : (Array.isArray(curSeries?.genres) ? curSeries.genres : []))
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

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-900 dark:text-gray-100 bg-transparent">
      <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />
      <RatingModal
        isOpen={isRatingModalOpen}
        onClose={() => setIsRatingModalOpen(false)}
        onSubmit={handleRateSubmit}
        title={displayData.title}
      />

      {/* Fullscreen Image Overlay */}
      {isFullscreenCover && (
        <div
          className="fixed inset-0 z-[100] bg-black/95 flex items-center justify-center p-4 animate-in fade-in duration-300"
          onClick={() => setIsFullscreenCover(false)}
        >
          <button
            className="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors z-[101]"
            onClick={(e) => { e.stopPropagation(); setIsFullscreenCover(false); }}
          >
            <X className="w-6 h-6 text-white" />
          </button>
          <img
            src={getCoverUrl(displayData.coverUrl, displayData.coverThumbUrl, 'original')}
            alt={displayData.title}
            className="max-w-full max-h-full object-contain rounded-lg shadow-2xl animate-in zoom-in-95 duration-300"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}

      {/* Navbar for Mobile */}
      <header
        className="md:hidden h-16 glass-panel border-b border-black/5 dark:border-white/10 flex items-center justify-between px-4 shrink-0 sticky top-0 z-40"
        style={{
          background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
          backdropFilter: `blur(${settings.glassBlur}px)`,
          WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
        }}
      >
        <button onClick={onBack} className="text-gray-600 dark:text-gray-400 hover:text-black dark:hover:text-white transition-colors">
          <ArrowLeft className="w-6 h-6" />
        </button>
        <span className="font-bold text-sm text-gray-900 dark:text-gray-200 truncate max-w-[200px]">{displayData.displayTitle}</span>
        <button onClick={() => setIsReportModalOpen(true)} className="text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition-colors">
          <Flag className="w-5 h-5" />
        </button>
      </header>

      {/* Desktop Back Button */}
      <div className="hidden md:flex pt-6 px-8 max-w-7xl mx-auto w-full">
        <button onClick={onBack} className="flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white transition-colors group">
          <div className="p-2 rounded-full bg-black/5 dark:bg-white/5 group-hover:bg-black/10 dark:group-hover:bg-white/10 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </div>
          <span className="text-sm font-bold uppercase tracking-widest">Volver</span>
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto pb-40 md:pb-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12">

            {/* LEFT COLUMN: Cover & Actions */}
            <div className="lg:col-span-4 xl:col-span-3 flex flex-col gap-6">
              {/* Cover Wrapper */}
              <div
                className="relative w-[70%] sm:w-[60%] lg:w-full mx-auto lg:mx-0 cursor-zoom-in group"
                onClick={() => setIsFullscreenCover(true)}
              >
                <div className="aspect-[2/3] rounded-xl overflow-hidden shadow-[0_10px_30px_rgba(0,0,0,0.2)] dark:shadow-[0_20px_50px_rgba(0,0,0,0.5)] ring-1 ring-black/5 dark:ring-white/10 relative">
                  <img src={getCoverUrl(displayData.coverUrl, displayData.coverThumbUrl, settings.coverQuality)} alt={displayData.title} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent"></div>
                  {/* Zoom Hint */}
                  <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-black/20">
                    <BookOpen className="w-10 h-10 text-white" />
                  </div>
                </div>
              </div>

              {/* Actions (Desktop mainly) */}
              <div className="hidden md:flex flex-col gap-3">
                <button
                  onClick={handleDownload}
                  className={`w-full py-3.5 text-white text-sm font-black uppercase tracking-widest rounded-xl shadow-lg transition-all transform active:scale-95 flex items-center justify-center gap-2 ${hasDownloaded ? 'bg-green-600 hover:bg-green-700 shadow-green-500/20' : 'bg-primary hover:brightness-110 shadow-primary/20'}`}
                >
                  {hasDownloaded ? (
                    <>
                      <Check className="w-5 h-5" />
                      Descargado
                    </>
                  ) : (
                    <>
                      <ArrowDownToLine className="w-5 h-5" />
                      Descargar
                    </>
                  )}
                </button>

                {/* 
                {hasDownloaded && (
                  <button
                    onClick={() => onNavigate && onNavigate('reader')}
                    className="w-full py-3.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-black uppercase tracking-widest rounded-xl shadow-lg shadow-indigo-500/20 transition-all transform active:scale-95 flex items-center justify-center gap-2"
                  >
                    <BookOpen className="w-5 h-5" />
                    Leer Online
                  </button>
                )} 
                */}

                <div className="flex flex-col gap-3">
                  <button
                    onClick={() => setIsRatingModalOpen(true)}
                    className="w-full py-3.5 bg-yellow-500 hover:bg-yellow-600 text-white text-sm font-black uppercase tracking-widest rounded-xl shadow-lg shadow-yellow-500/20 transition-all transform active:scale-95 flex items-center justify-center gap-2"
                  >
                    <Star className="w-5 h-5 fill-current" />
                    Valorar Libro
                  </button>

                  <button onClick={() => setIsReportModalOpen(true)} className="py-3.5 bg-red-50 dark:bg-red-500/10 hover:bg-red-100 dark:hover:bg-red-500/20 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 rounded-xl border border-red-200 dark:border-red-500/20 transition-colors flex items-center justify-center gap-2 text-xs font-bold uppercase tracking-wider">
                    <Flag className="w-4 h-4" />
                    Reportar Error
                  </button>
                </div>
              </div>


              {/* Extra Info visible in sidebar (Desktop) */}
              <div className="hidden md:block glass-panel p-4 rounded-xl border border-black/5 dark:border-white/5 space-y-4">

                {/* Rating Block */}
                <div className="flex items-center justify-between pb-3 border-b border-black/5 dark:border-white/5">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Valoración</span>
                  <div className="flex flex-col items-end">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-gray-900 dark:text-white font-bold">{displayData.rating > 0 ? displayData.rating.toFixed(1) : '—'}</span>
                    </div>
                    {displayData.ratingCount !== undefined && displayData.ratingCount > 0 && (
                      <span className="text-[10px] text-gray-400 mt-1">{displayData.ratingCount} {displayData.ratingCount === 1 ? 'voto' : 'votos'}</span>
                    )}
                  </div>
                </div>

                {/* Download Block */}
                <div className="flex items-center justify-between pb-3 border-b border-black/5 dark:border-white/5">
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400">Descargas Totales</span>
                  <div className="flex items-center gap-1.5 text-primary">
                    <Download className="w-4 h-4" />
                    <span className="text-gray-900 dark:text-white font-bold">{displayData.downloadCount}</span>
                  </div>
                </div>

                {/* Updated Block */}
                <div className="flex items-center justify-between text-xs font-medium text-gray-500 dark:text-gray-400">
                  <span>Última Actualización</span>
                  <span className="text-gray-900 dark:text-white font-bold">{displayData.lastUpdated}</span>
                </div>
              </div>
            </div>

            {/* RIGHT COLUMN: Content */}
            <div className="lg:col-span-8 xl:col-span-9 flex flex-col gap-6">

              {/* Header Info */}
              <div>
                {/* Group/Translator Badges - CLICKABLE */}
                <div className="mb-4 flex flex-wrap items-center gap-2 text-[10px] font-black uppercase tracking-wider">
                  <button
                    onClick={() => handleSearch(displayData.group, 'group')}
                    className="bg-primary/10 text-primary border border-primary/20 px-2 py-1 rounded-md hover:bg-primary hover:text-white transition-colors cursor-pointer"
                  >
                    {displayData.group}
                  </button>
                  <span className="text-gray-400 dark:text-gray-600 px-1">/</span>
                  <button
                    onClick={() => handleSearch(displayData.translator, 'translator')}
                    className="bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-400 border border-black/5 dark:border-white/10 px-2 py-1 rounded-md hover:bg-gray-200 dark:hover:bg-white/10 hover:text-black dark:hover:text-white transition-colors cursor-pointer"
                  >
                    {displayData.translator}
                  </button>
                </div>

                <h1 className="text-2xl sm:text-3xl lg:text-5xl font-extrabold text-gray-900 dark:text-white leading-tight mb-2">
                  {displayData.displayTitle}
                </h1>
                <h2 className="text-sm sm:text-lg text-gray-500 dark:text-gray-400 italic font-serif mb-6 leading-relaxed">
                  {displayData.romajiTitle}
                </h2>

                {/* Author/Stats Row - CLICKABLE */}
                <div className="flex flex-wrap items-center gap-x-6 gap-y-3 text-sm text-gray-600 dark:text-gray-400 border-b border-black/5 dark:border-white/5 pb-6 mb-2">
                  <button onClick={() => handleSearch(curSeries.author, 'author')} className="flex items-center gap-2 text-gray-900 dark:text-white group">
                    <User className="w-4 h-4 text-primary group-hover:scale-110 transition-transform" />
                    <span className="font-bold group-hover:underline cursor-pointer group-hover:text-primary transition-colors">{curSeries.author}</span>
                  </button>

                  <div className="flex items-center gap-1.5 text-yellow-500">
                    <Star className="w-4 h-4 fill-current" />
                    <span className="text-gray-900 dark:text-white font-bold">{displayData.rating > 0 ? displayData.rating.toFixed(1) : '—'}</span>
                    {displayData.ratingCount !== undefined && displayData.ratingCount > 0 && (
                      <span className="text-xs text-gray-400 font-medium">({displayData.ratingCount})</span>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5 text-primary">
                    <Download className="w-4 h-4" />
                    <span className="text-gray-900 dark:text-white font-bold">{displayData.downloadCount}</span>
                  </div>

                  <button onClick={() => handleSearch(displayData.illustrator, 'illustrator')} className="flex items-center gap-2 group hover:text-black dark:hover:text-gray-200 transition-colors">
                    <PenTool className="w-4 h-4" />
                    <span>{displayData.illustrator}</span>
                  </button>
                  <div className="flex items-center gap-2">
                    <Hash className="w-4 h-4" />
                    <span>{curVolume.volumeNumber > 0 ? `Volumen ${curVolume.volumeNumber}` : 'Volumen Único'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4" />
                    <span>{displayData.publishedDate}</span>
                  </div>
                  {displayData.translator && (
                    <button onClick={() => handleSearch(displayData.translator, 'translator')} className="flex items-center gap-2 group hover:text-black dark:hover:text-gray-200 transition-colors">
                      <Languages className="w-4 h-4 text-indigo-500" />
                      <span className="font-bold group-hover:underline">{displayData.translator}</span>
                    </button>
                  )}
                  {displayData.lastUpdated !== 'N/A' && (
                    <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                      <Clock className="w-4 h-4" />
                      <span className="font-bold">Actualizado: {displayData.lastUpdated}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Genres & Tags - CLICKABLE */}
              <div className="flex flex-wrap gap-2">
                {displayData.demography.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleSearch(tag, 'demography')}
                    className="px-3 py-1.5 rounded-lg bg-[#004d40] text-[#4db6ac] border border-[#00695c] text-[10px] font-black uppercase tracking-wider shadow-sm hover:bg-[#00695c] hover:text-white transition-colors"
                  >
                    {tag}
                  </button>
                ))}
                {displayData.genres.map((genre) => (
                  <button
                    key={genre}
                    onClick={() => handleSearch(genre, 'genre')}
                    className="px-3 py-1.5 rounded-lg bg-gray-200 dark:bg-[#1f2937] text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-[#374151] text-[10px] font-bold uppercase tracking-wider hover:bg-gray-300 dark:hover:bg-[#374151] hover:text-black dark:hover:text-white hover:border-gray-400 dark:hover:border-gray-500 transition-colors cursor-pointer"
                  >
                    {genre}
                  </button>
                ))}
              </div>

              {/* Synopsis */}
              <div className="glass-panel border border-black/5 dark:border-white/5 rounded-2xl p-6 lg:p-8 shadow-sm dark:shadow-xl">
                <div className="flex items-center gap-2 mb-4 text-primary">
                  <FileText className="w-5 h-5" />
                  <h3 className="text-xs font-black uppercase tracking-widest">Sinopsis</h3>
                </div>
                <div className="text-gray-700 dark:text-gray-300 text-sm sm:text-base leading-7 sm:leading-8 font-medium text-justify">
                  {formatDescription(displayData.description)}
                </div>
              </div>

              {/* Two Column Details Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Book Details */}
                <div className="glass-panel border border-black/5 dark:border-white/5 rounded-2xl p-6 shadow-sm dark:shadow-xl h-full">
                  <div className="flex items-center gap-2 mb-6 text-primary">
                    <Library className="w-5 h-5" />
                    <h3 className="text-xs font-black uppercase tracking-widest">Detalles del Libro</h3>
                  </div>
                  <div className="space-y-0.5">
                    {([
                      { label: 'Serie', value: curSeries.title, highlight: true, clickable: true, type: 'series' },
                      { label: 'Volumen', value: curVolume.volumeNumber > 0 ? `${curVolume.volumeNumber}` : 'Único' },
                      { label: 'Tipo de libro', value: displayData.bookType },
                      { label: 'ISBN', value: displayData.isbn, highlight: true, font: 'mono' },
                      { label: 'ASIN', value: displayData.asin, highlight: true, font: 'mono' },
                      { label: 'Idioma', value: displayData.language, highlight: true },
                      { label: 'Group', value: displayData.group, color: 'text-primary', clickable: true, type: 'group' },
                      { label: 'Traductor', value: displayData.translator || 'ZeePub', color: 'text-indigo-600 dark:text-indigo-400', clickable: true, type: 'translator' },
                      { label: 'Maquetador', value: displayData.typesetter, highlight: true, clickable: true, type: 'typesetter' },
                      { label: 'Fecha de publicación', value: displayData.publishedDate, highlight: true },
                    ] as any[]).map((item, idx) => (
                      <div key={idx} className="flex justify-between py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-black/5 dark:hover:bg-white/[0.02] px-2 -mx-2 rounded transition-colors">
                        <span className="text-sm text-gray-500 font-medium">{item.label}</span>
                        {item.clickable ? (
                          <button
                            onClick={() => handleSearch(String(item.value), item.type)}
                            className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px] hover:underline hover:text-primary transition-colors`}
                          >
                            {item.value}
                          </button>
                        ) : (
                          <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} truncate max-w-[200px]`}>
                            {item.value}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Tech Specs */}
                <div className="glass-panel border border-black/5 dark:border-white/5 rounded-2xl p-6 shadow-sm dark:shadow-xl h-full">
                  <div className="flex items-center gap-2 mb-6 text-primary">
                    <Database className="w-5 h-5" />
                    <h3 className="text-xs font-black uppercase tracking-widest">Ficha Técnica</h3>
                  </div>
                  <div className="space-y-0.5">
                    {([
                      { label: 'Formato', value: 'EPUB', highlight: true },
                      { label: 'Versión Epub', value: `v${displayData.epubVersion}` },
                      { label: 'Palabras', value: displayData.wordCount?.toLocaleString() || 'N/A' },
                      { label: 'Páginas', value: displayData.pages || 'N/A' },
                      { label: 'Lectura Aprox.', value: displayData.readTime },
                      { label: 'Tamaño', value: displayData.size, highlight: true, font: 'mono' },
                      { label: 'Uploader', value: displayData.uploader, color: 'text-purple-600 dark:text-purple-400' },
                      { label: 'Fecha de actualización', value: displayData.lastUpdated, highlight: true },
                    ] as any[]).map((item, idx) => (
                      <div key={idx} className="flex justify-between py-3 border-b border-black/5 dark:border-white/5 last:border-0 hover:bg-black/5 dark:hover:bg-white/[0.02] px-2 -mx-2 rounded transition-colors">
                        <span className="text-sm text-gray-500 font-medium">{item.label}</span>
                        {item.clickable ? (
                          <button
                            onClick={() => handleSearch(String(item.value), item.type)}
                            className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''} hover:underline hover:brightness-125 transition-all`}
                          >
                            {item.value}
                          </button>
                        ) : (
                          <span className={`text-sm text-right ${item.color || (item.highlight ? 'text-gray-900 dark:text-gray-200 font-bold' : 'text-gray-600 dark:text-gray-400')} ${item.font === 'mono' ? 'font-mono' : ''}`}>
                            {item.value}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>

      {/* Floating Bottom Navigation */}
      <div className="md:hidden fixed bottom-6 left-8 right-8 z-40 animate-in slide-in-from-bottom-4 duration-300 max-w-7xl mx-auto">
        <div
          className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
          }}
        >
          {/* Back */}
          <button
            onClick={onBack}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white"
          >
            <div className="p-1.5">
              <Reply className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Volver</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          {/* Home */}
          <button
            onClick={() => onNavigate && onNavigate('dashboard')}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-500 dark:text-gray-400 hover:text-black dark:hover:text-white"
          >
            <div className="p-1.5">
              <Home className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          {/* Rate */}
          {hasDownloaded && (
            <>
              {/* 
              <button
                onClick={() => onNavigate && onNavigate('reader')}
                className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-indigo-500 hover:text-indigo-600 active:scale-95"
              >
                <div className="p-1.5">
                  <BookOpen className="w-4 h-4" strokeWidth={2} />
                </div>
                <span className="text-[9px] font-black uppercase tracking-widest mt-1">Leer</span>
              </button>
              <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>
              */}

              <button
                onClick={() => setIsRatingModalOpen(true)}
                className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-yellow-500 hover:text-yellow-600 active:scale-95"
              >
                <div className="p-1.5">
                  <Star className="w-4 h-4 fill-current" strokeWidth={2} />
                </div>
                <span className="text-[9px] font-black uppercase tracking-widest mt-1">Valorar</span>
              </button>
              <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>
            </>
          )}

          {/* Download */}
          <button
            onClick={handleDownload}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${hasDownloaded ? 'text-green-600 dark:text-green-500' : 'text-primary'}`}
          >
            <div className={`p-1.5 rounded-full transition-all duration-300 ${!hasDownloaded ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
              {hasDownloaded ? <Check className="w-4 h-4" strokeWidth={2.5} /> : <Download className="w-4 h-4 text-white" strokeWidth={2.5} />}
            </div>
            <span className={`text-[9px] font-black uppercase tracking-widest mt-1 ${!hasDownloaded ? 'text-primary' : ''}`}>
              {hasDownloaded ? 'Listo' : 'Descargar'}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
