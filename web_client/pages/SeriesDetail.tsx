import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { getCoverUrl } from '../src/utils/imageUtils';
import { api } from '../src/services/api';
import {
  ArrowLeft,
  Star,
  Library,
  Clock,
  ListOrdered,
  SortAsc,
  Filter,
  Download,
  BookOpen,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  ArrowDownUp,
  Calendar,
  Reply,
  BookmarkPlus,
  Bookmark,
  LayoutGrid,
  List
} from 'lucide-react';
import { Series, Volume } from '../types';
import { preloadImages } from '../src/utils/imagePreloader';

interface SeriesDetailProps {
  series: Series;
  onBack: () => void;
  onSelectVolume: (volume: Volume, series: Series) => void;
  onSearch?: (term: string) => void;
}

export const SeriesDetail: React.FC<SeriesDetailProps> = ({ series, onBack, onSelectVolume, onSearch }) => {
  const { settings } = useTheme();
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [isSortMenuOpen, setIsSortMenuOpen] = useState(false);
  const [realSeries, setRealSeries] = useState<Series>(series);
  const [volumes, setVolumes] = useState<Volume[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSort, setActiveSort] = useState('num-asc');
  const [isSynopsisModalOpen, setIsSynopsisModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const data = await api.getBookDetail(series.id);
        if (data) {
          setRealSeries({
            ...series, // Preserve existing data if needed
            ...data,
            coverUrl: data.cover || series.coverUrl,
            description: (data.summary || data.description || series.description)?.replace(/<br\s*\/?>/gi, '\n'),
            englishTitle: data.english_title,
            spanishTitle: data.spanish_title,
            romajiTitle: data.romaji_title || data.romaji
          } as Series);
          if (data.volumes) {
            const mappedVols: Volume[] = data.volumes.map((v: any) => ({
              id: v.id,
              seriesId: data.id,
              title: v.title,
              volumeNumber: v.seriesIndex || 1,
              coverUrl: v.cover || data.cover,
              coverThumbUrl: v.cover_thumb || v.cover || data.cover_thumb || data.cover,
              publishedDate: v.publishedAt || 'N/A',
              pages: v.pageCount || 0,
              format: (v.bookType || 'EPUB').toUpperCase(),
              rating: v.rating_average || 0,
              description: v.summary || v.description,
              uploader: v.translator || 'ZeePub',
              downloadCount: v.download_count || 0,
              demography: v.demographics,
              tags: v.tags,
              // Metadata Enriquecida
              romajiTitle: v.romaji_title || v.romaji,
              englishTitle: v.english_title,
              spanishTitle: v.spanish_title,
              illustrator: v.illustrator,
              translator: v.translator,
              typesetter: v.layoutBy,
              group: v.publisher,
              isbn: v.isbn,
              asin: v.asin,
              wordCount: v.wordCount,
              readTime: v.readingTime ? `${v.readingTime} min` : 'N/A',
              size: v.fileSize ? `${(v.fileSize / (1024 * 1024)).toFixed(2)} MB` : '0 MB',
              language: v.language || 'Español',
              epubVersion: v.epubVersion,
              modifiedAt: v.modifiedAt,
              modifiedAtOpf: v.modifiedAtOpf,
              series: v.series,
              cleanTitle: v.clean_title
            }));
            setVolumes(mappedVols);

            // Preload volume thumbnails for faster grid/list viewing
            const volCovers = mappedVols.map(v => v.coverThumbUrl || v.coverUrl);
            preloadImages(volCovers);

            // Update synopsis from the first volume if available
            if (mappedVols.length > 0) {
              const firstVol = [...mappedVols].sort((a, b) => (a.volumeNumber || 0) - (b.volumeNumber || 0))[0];
              if (firstVol.description) {
                setRealSeries(prev => ({
                  ...prev,
                  description: firstVol.description
                }));
              }
            }
          }
        }
      } catch (err) {
        console.error("Error fetching series details", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [series.id]);

  const totalPages = Math.ceil(volumes.length / itemsPerPage);

  const sortedVolumes = React.useMemo(() => {
    const sorted = [...volumes];
    switch (activeSort) {
      case 'num-asc':
        return sorted.sort((a, b) => {
          const numA = typeof a.volumeNumber === 'string' ? parseFloat(a.volumeNumber) : (a.volumeNumber || 0);
          const numB = typeof b.volumeNumber === 'string' ? parseFloat(b.volumeNumber) : (b.volumeNumber || 0);
          return numA - numB;
        });
      case 'num-desc':
        return sorted.sort((a, b) => {
          const numA = typeof a.volumeNumber === 'string' ? parseFloat(a.volumeNumber) : (a.volumeNumber || 0);
          const numB = typeof b.volumeNumber === 'string' ? parseFloat(b.volumeNumber) : (b.volumeNumber || 0);
          return numB - numA;
        });
      case 'rating':
        return sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      case 'date':
        return sorted.sort((a, b) => String(b.publishedDate).localeCompare(String(a.publishedDate)));
      default:
        return sorted;
    }
  }, [volumes, activeSort]);

  const currentVolumes = sortedVolumes.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const scrollToTop = () => {
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
      mainContainer.scrollTo({ top: 0, behavior: 'instant' });
    } else {
      window.scrollTo(0, 0);
    }
  };

  useEffect(() => {
    scrollToTop();
  }, [currentPage]);

  const handleNextPage = () => {
    if (currentPage < totalPages) setCurrentPage(prev => prev + 1);
  };

  const handlePrevPage = () => {
    if (currentPage > 1) setCurrentPage(prev => prev - 1);
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

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-100">

      <div className="relative w-full min-h-[480px] sm:min-h-[520px] shrink-0 overflow-hidden flex flex-col justify-end">
        <div
          className="absolute inset-0 bg-cover bg-center blur-sm scale-110 opacity-50"
          style={{ backgroundImage: `url('${getCoverUrl(realSeries.coverUrl, realSeries.coverThumbUrl, settings.coverQuality)}')` }}
        ></div>

        <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/40 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/40 to-transparent"></div>

        {/* Action Buttons Overlay - Desktop/Tablet */}
        <div className="absolute top-6 left-6 right-6 z-30 flex items-center justify-between">
          <button
            onClick={onBack}
            className="p-3 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white border border-white/10 transition-all active:scale-95 shadow-lg group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          </button>
        </div>

        <div
          className="relative w-full px-4 sm:px-6 lg:px-8 pb-10 z-20"
          style={{ paddingTop: `calc(11rem + var(--banner-content-offset, 0px))` }}
        >
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row gap-6 items-end sm:items-end">
            <div className="hidden sm:block relative shrink-0 w-32 h-48 sm:w-40 sm:h-60 -mb-4 shadow-2xl rounded-lg overflow-hidden">
              <img alt={`${realSeries.title} Cover`} className="w-full h-full object-cover" src={getCoverUrl(realSeries.coverUrl, realSeries.coverThumbUrl, settings.coverQuality)} />
            </div>

            <div className="flex-1 pb-2 w-full">
              <div className="flex flex-wrap items-center gap-3 mb-4">
                <button
                  onClick={() => onSearch?.(realSeries.genre || '')}
                  className="px-2.5 py-1 rounded-lg text-[10px] sm:text-xs font-black bg-green-500/20 text-green-400 border border-green-500/30 uppercase tracking-widest leading-relaxed hover:bg-green-500/30 transition-all"
                >
                  {realSeries.genre}
                </button>
                <span className="flex items-center gap-1.5 text-yellow-500 text-xs sm:text-sm font-black">
                  <Star className="w-4 h-4 fill-current" />
                  {realSeries.rating}
                </span>
              </div>

              <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold text-white mb-2 leading-tight">
                {realSeries.englishTitle || realSeries.title}
              </h1>
              {realSeries.romajiTitle && (
                <h2 className="text-sm sm:text-lg text-white/60 italic font-serif mb-4 leading-relaxed">
                  {realSeries.romajiTitle}
                </h2>
              )}
              <button
                onClick={() => onSearch?.(realSeries.author || '')}
                className="text-white/80 text-sm sm:text-base mb-6 font-medium hover:text-primary transition-colors hover:underline"
              >
                Por {realSeries.author}
              </button>

              <div className="relative mb-6">
                <div className="text-gray-200 text-xs sm:text-sm line-clamp-3 max-w-2xl leading-relaxed font-medium">
                  {formatDescription(realSeries.description || "Sin descripción disponible.")}
                </div>
                {realSeries.description && realSeries.description.length > 150 && (
                  <button
                    onClick={() => setIsSynopsisModalOpen(true)}
                    className="mt-2 text-primary text-xs font-bold hover:underline py-1"
                  >
                    Ver más...
                  </button>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-gray-300 font-mono">
                <span className="flex items-center gap-1.5"><Library className="w-4 h-4 text-primary" /> {volumes.length} Volúmenes</span>
                <button
                  onClick={() => onSearch?.(realSeries.status || 'Completado')}
                  className="flex items-center gap-1.5 hover:text-primary transition-colors"
                >
                  <Clock className="w-4 h-4 text-primary" /> {realSeries.status || 'Completado'}
                </button>
                {realSeries.lastUpdated && (
                  <span className="flex items-center gap-1.5">
                    <Calendar className="w-4 h-4 text-primary" />
                    Actualizado: {(() => {
                      try {
                        const d = new Date(realSeries.lastUpdated);
                        if (isNaN(d.getTime())) return realSeries.lastUpdated; // Fallback if invalid
                        return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
                      } catch (e) {
                        return realSeries.lastUpdated;
                      }
                    })()}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
      )}

      <div className="flex-1 pb-32">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-primary" />
              Lista de Volúmenes
            </h2>
            <div className="flex gap-2 glass-panel p-1 rounded-xl border border-white/10 shadow-lg">
              <button
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-lg transition-all ${viewMode === 'list' ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/30' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-lg transition-all ${viewMode === 'grid' ? 'bg-gradient-to-r from-primary to-primary/80 text-white shadow-lg shadow-primary/30' : 'text-gray-400 hover:text-white hover:bg-white/5'}`}
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </div>

          <div className={viewMode === 'list' ? "flex flex-col gap-3" : "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4"}>
            {currentVolumes.map((vol, index) => (
              viewMode === 'list' ? (
                <div
                  key={vol.id}
                  onClick={() => onSelectVolume(vol, realSeries)}
                  className="group relative flex gap-4 p-4 rounded-xl border border-white/5 hover:bg-white/5 hover:border-primary/30 transition-all duration-200 cursor-pointer overflow-hidden shadow-sm"
                  style={{
                    backgroundColor: `rgba(var(--glass-rgb), ${settings.glassOpacity / 2})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                  }}
                >
                  {/* Image */}
                  <div className="shrink-0 aspect-[2/3] bg-slate-800 rounded-lg overflow-hidden shadow-lg border border-white/5" style={{ width: settings.coverWidth }}>
                    <img alt={vol.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 flex flex-col">
                    <div className="mb-1">
                      <h3 className="text-white font-bold text-base sm:text-lg leading-tight line-clamp-2">
                        {vol.cleanTitle || vol.title}
                      </h3>
                      <p className="text-gray-500 text-xs italic font-serif mt-0.5 line-clamp-1">
                        {vol.romajiTitle ? vol.title : ''}
                      </p>
                    </div>

                    <div className="mb-2">
                      <p className="text-primary text-sm font-medium">
                        {series.author} {vol.illustrator ? `- ${vol.illustrator} ` : ''}
                      </p>
                      <p className="text-gray-400 text-xs mt-0.5">
                        Volumen {vol.volumeNumber} <button onClick={(e) => { e.stopPropagation(); onSearch?.(vol.uploader || 'ZeePub'); }} className="text-primary font-bold hover:underline">{vol.uploader}</button>
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-bold mb-auto">
                      <div className="flex items-center gap-1.5 text-gray-400">
                        <Star className="w-3.5 h-3.5 text-yellow-500 fill-current" />
                        <span className="text-gray-200">{vol.rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-primary">
                        <Download className="w-3.5 h-3.5" />
                        <span>{vol.downloadCount}</span>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        className="flex items-center gap-2 px-5 py-2 rounded-lg bg-transparent border border-primary/40 text-primary text-[10px] font-black tracking-widest hover:bg-primary hover:text-white transition-all uppercase"
                        onClick={(e) => { e.stopPropagation(); onSelectVolume(vol, realSeries); }}
                      >
                        <Download className="w-3.5 h-3.5" />
                        DESCARGAR
                      </button>

                      <button
                        className="flex items-center gap-2 px-3 sm:px-5 py-2 rounded-lg bg-transparent border border-white/10 text-gray-400 text-[10px] sm:text-[10px] font-black tracking-widest hover:text-white hover:bg-white/10 transition-all uppercase whitespace-nowrap"
                        onClick={(e) => { e.stopPropagation(); /* Add logic */ }}
                      >
                        <Bookmark className="w-3.5 h-3.5" />
                        <span className="hidden sm:inline">BIBLIOTECA</span>
                        <span className="sm:hidden">+</span>
                      </button>
                    </div>
                  </div>

                  <div className="hidden sm:flex items-center justify-center pl-2 text-gray-600 group-hover:text-primary transition-colors">
                    <ChevronRight className="w-6 h-6" />
                  </div>
                </div>
              ) : (
                <div
                  key={vol.id}
                  onClick={() => onSelectVolume(vol, realSeries)}
                  className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer border border-white/5"
                  style={{
                    backgroundColor: `rgba(var(--glass-rgb), ${settings.glassOpacity / 2})`,
                    backdropFilter: `blur(${settings.glassBlur}px)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
                  }}
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
                    <img
                      alt={vol.title}
                      className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>
                    <div className="absolute bottom-2 left-2 right-2">
                      <span className="text-[10px] font-black text-white/90 uppercase tracking-widest bg-primary/80 px-2 py-0.5 rounded shadow-sm">Vol {vol.volumeNumber}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h3 className="truncate text-sm font-bold text-white group-hover:text-primary transition-colors">
                      {vol.cleanTitle || vol.title}
                    </h3>
                    <div className="flex items-center justify-between text-[10px] font-bold text-gray-400">
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                        <span>{vol.rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="w-3 h-3 text-primary" />
                        <span>{vol.downloadCount}</span>
                      </div>
                    </div>
                  </div>
                </div>
              )
            ))}

            <div className="text-center py-4 text-xs text-gray-500 font-medium">
              Página {currentPage} de {totalPages} • {volumes.length} Volúmenes
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <div className="md:hidden fixed bottom-6 left-8 right-8 z-50 animate-in slide-in-from-bottom-4 duration-300 flex flex-col gap-3 max-w-5xl mx-auto">
        {isSortMenuOpen && (
          <div
            className="glass-panel rounded-3xl p-4 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
            style={{
              background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
              backdropFilter: `blur(${settings.glassBlur}px)`,
              WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
            }}
          >
            <div className="grid grid-cols-2 gap-3">
              {[
                { id: 'num-asc', label: '1 - 9', icon: SortAsc },
                { id: 'num-desc', label: '9 - 1', icon: SortAsc },
                { id: 'date', label: 'FECHA', icon: Calendar },
                { id: 'rating', label: 'VALORACIÓN', icon: Star },
              ].map((option) => (
                <button
                  key={option.id}
                  onClick={() => {
                    setActiveSort(option.id);
                    setIsSortMenuOpen(false);
                  }}
                  className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border ${activeSort === option.id ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-white/5 text-gray-400 border-white/5 hover:bg-white/10 hover:text-white'}`}
                >
                  <option.icon className="w-3.5 h-3.5" />
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div
          className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
          }}
        >
          <button
            onClick={handlePrevPage}
            disabled={currentPage === 1}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white ${currentPage === 1 ? 'opacity-30 cursor-not-allowed' : ''}`}
          >
            <div className="p-1.5 rounded-full transition-all duration-300">
              <ChevronLeft className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Anterior</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={() => setIsSortMenuOpen(!isSortMenuOpen)}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 relative z-10 ${isSortMenuOpen ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
          >
            <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
              <ArrowDownUp className={`w-4 h-4 ${isSortMenuOpen ? 'text-white' : ''}`} strokeWidth={isSortMenuOpen ? 2.5 : 2} />
            </div>
            <span className={`text-[9px] font-black uppercase tracking-widest mt-1`}>Ordenar</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={onBack}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white`}
          >
            <div className="p-1.5 rounded-full transition-all duration-300">
              <Reply className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Volver</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={handleNextPage}
            disabled={currentPage === totalPages}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 relative z-10 text-gray-500 hover:text-black dark:hover:text-white ${currentPage === totalPages ? 'opacity-30 cursor-not-allowed' : ''}`}
          >
            <div className="p-1.5 rounded-full transition-all duration-300">
              <ChevronRight className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Siguiente</span>
          </button>
        </div>
      </div>

      {/* Synopsis Modal */}
      {isSynopsisModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
          <div
            className="bg-[#0d1117] border border-white/10 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-6 border-b border-white/5 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <BookOpen className="w-5 h-5 text-primary" />
                Sinopsis Completa
              </h3>
              <button
                onClick={() => setIsSynopsisModalOpen(false)}
                className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar">
              <p className="text-gray-300 text-sm sm:text-base leading-relaxed whitespace-pre-line text-justify">
                {realSeries.description}
              </p>
            </div>
            <div className="p-4 bg-black/20 border-t border-white/5 flex justify-end">
              <button
                onClick={() => setIsSynopsisModalOpen(false)}
                className="px-6 py-2 bg-primary text-white text-xs font-black uppercase tracking-widest rounded-lg hover:bg-primary/80"
              >
                Cerrar
              </button>
            </div>
          </div>
          {/* Overlay to close */}
          <div className="absolute inset-0 -z-10" onClick={() => setIsSynopsisModalOpen(false)}></div>
        </div>
      )}

    </div>
  );
};