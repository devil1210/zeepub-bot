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
  List,
  RefreshCw
} from 'lucide-react';
import { useTelegram } from '../contexts/TelegramContext';
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
  const [isSyncing, setIsSyncing] = useState(false);
  const { isAdmin } = useTelegram();

  const handleSyncSeries = async () => {
    if (isSyncing || !realSeries.series_hash) return;
    setIsSyncing(true);
    try {
      const res = await api.adminScanSeries(realSeries.series_hash, true);
      if (res.success) {
        // Show success message (using native alert for now if no toast system)
        if (typeof (window as any).Telegram?.WebApp?.showAlert === 'function') {
          (window as any).Telegram.WebApp.showAlert(res.message || "Sincronización iniciada.");
        } else {
          alert(res.message || "Sincronización iniciada.");
        }
      } else {
        alert(res.error || "Error al iniciar sincronización.");
      }
    } catch (e: any) {
      alert("Error: " + e.message);
    } finally {
      setIsSyncing(false);
    }
  };

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
              coverUrl: {
                cover_low: v.cover_low,
                cover_medium: v.cover_medium,
                cover_high: v.cover_high,
                cover_original: v.cover_original,
                cover: v.cover || data.cover
              },
              coverThumbUrl: v.cover_thumb || v.cover_low || v.cover || data.cover_thumb || data.cover,
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
              cleanTitle: v.clean_title,
              is_uncensored: v.is_uncensored,
              color_mode: v.color_mode
            }));
            setVolumes(mappedVols);

            // Preload volume thumbnails for faster grid/list viewing
            const volCovers = mappedVols.map(v => getCoverUrl(v.coverUrl, v.coverThumbUrl, settings.coverQuality));
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
      mainContainer.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      window.scrollTo({ top: 0, behavior: 'smooth' });
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

      <div className="relative w-full min-h-[480px] sm:min-h-[520px] shrink-0 overflow-hidden flex flex-col">
        <div
          className="absolute inset-0 bg-cover bg-center blur-sm scale-110 opacity-50"
          style={{ backgroundImage: `url('${getCoverUrl(realSeries.coverUrl, realSeries.coverThumbUrl, settings.coverQuality)}')` }}
        ></div>

        <div className="absolute inset-0 bg-gradient-to-b from-black/80 via-black/40 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/90 via-black/40 to-transparent"></div>

        {/* Action Buttons Overlay - Desktop/Tablet */}
        <div
          className="relative z-30 flex items-center justify-between px-4 sm:px-6 lg:px-8"
          style={{ paddingTop: '3rem' }}
        >
          <button
            onClick={onBack}
            className="p-3 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white border border-white/10 transition-all active:scale-95 shadow-lg group"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
          </button>

          <div className="flex items-center gap-3">
            {isAdmin && realSeries.series_hash && (
              <button
                onClick={handleSyncSeries}
                disabled={isSyncing}
                className={`px-4 py-2.5 bg-black/40 hover:bg-black/60 backdrop-blur-md rounded-full text-white border border-white/10 transition-all active:scale-95 shadow-lg group flex items-center gap-2 ${isSyncing ? 'opacity-50 cursor-not-allowed' : ''}`}
                title="Sincronizar esta serie"
              >
                <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : 'group-hover:rotate-180 transition-transform duration-500'}`} />
                <span className="text-[10px] font-black uppercase tracking-widest sm:inline hidden">Sincronizar</span>
              </button>
            )}

            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center shadow-lg shadow-primary/20 pointer-events-auto">
              <BookOpen className="text-white w-5 h-5" />
            </div>
          </div>
        </div>

        <div
          className="relative w-full px-4 sm:px-6 lg:px-8 pb-6 z-20 flex-1"
          style={{ paddingTop: '2rem' }}
        >
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row gap-6 items-end sm:items-end">
            <div className="hidden sm:block relative shrink-0 w-32 h-48 sm:w-40 sm:h-60 shadow-2xl rounded-lg overflow-hidden">
              <img alt={`${realSeries.title} Cover`} className="w-full h-full object-cover" src={getCoverUrl(realSeries.coverUrl, realSeries.coverThumbUrl, settings.coverQuality)} />
            </div>

            <div className="flex-1 pb-4 w-full">
              <div className="flex flex-wrap items-center gap-4 mb-4 animate-in fade-in slide-in-from-left duration-700">
                <button
                  onClick={() => onSearch?.(realSeries.genre || '')}
                  className="px-4 py-1.5 rounded-full text-[10px] font-black bg-primary/20 text-primary border border-primary/30 uppercase tracking-[0.2em] hover:bg-primary/30 transition-all shadow-lg shadow-primary/10"
                >
                  {realSeries.genre || 'Fantasía'}
                </button>
                <div className="flex items-center gap-2 text-yellow-500 bg-white/5 px-3 py-1.5 rounded-full border border-white/10 shadow-xl">
                  <Star className="w-4 h-4 fill-current" />
                  <span className="text-[13px] font-black">{realSeries.rating > 0 ? realSeries.rating.toFixed(1) : '—'}</span>
                </div>
              </div>

              <h1 className="text-4xl sm:text-6xl font-black text-white mb-3 leading-[1.1] tracking-tighter drop-shadow-2xl animate-in fade-in slide-in-from-left duration-1000">
                {realSeries.englishTitle || realSeries.title}
              </h1>

              {realSeries.romajiTitle && (
                <h2 className="text-lg sm:text-2xl text-white/50 font-medium tracking-tight mb-6 leading-relaxed opacity-80 animate-in fade-in slide-in-from-left duration-1000 delay-100">
                  {realSeries.romajiTitle}
                </h2>
              )}

              <button
                onClick={() => onSearch?.(realSeries.author || '')}
                className="group flex items-center gap-3 text-white/70 text-sm font-bold uppercase tracking-[0.1em] mb-8 hover:text-primary transition-all duration-300"
              >
                <div className="w-1 h-4 bg-primary rounded-full group-hover:h-6 transition-all duration-300"></div>
                Por <span className="text-white group-hover:text-primary">{realSeries.author}</span>
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

          <div className={viewMode === 'list' ? "flex flex-col gap-4" : "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-6"}>
            {currentVolumes.map((vol, index) => (
              viewMode === 'list' ? (
                <div
                  key={vol.id}
                  onClick={() => onSelectVolume(vol, realSeries)}
                  className="group relative flex gap-6 p-6 rounded-[2.5rem] bg-white/[0.03] border border-white/5 hover:bg-white/[0.08] hover:border-primary/40 hover:shadow-[0_30px_80px_-15px_rgba(0,0,0,0.6)] transition-all duration-700 cursor-pointer overflow-hidden shadow-2xl mb-2"
                >
                  {/* Backdrop Glow */}
                  <div className="absolute -inset-20 bg-primary/5 blur-[100px] opacity-0 group-hover:opacity-100 transition-opacity duration-1000"></div>

                  {/* Image */}
                  <div className="relative shrink-0 aspect-[2/3] w-28 sm:w-36 rounded-2xl overflow-hidden shadow-2xl border border-white/10 group-hover:-translate-y-1 transition-transform duration-700">
                    <img
                      alt={vol.title}
                      className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                      src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)}
                    />
                    <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/80 to-transparent"></div>

                    {/* Floating Badges on Image (Mobile) */}
                    <div className="absolute top-3 left-3 flex flex-col gap-1.5 sm:hidden">
                      {vol.color_mode === 'color' && (
                        <div className="bg-gradient-to-br from-orange-400 to-pink-500 p-1.5 rounded-lg shadow-2xl border border-white/20">
                          <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 flex flex-col py-2 z-10">
                    <div className="mb-3">
                      <div className="flex flex-wrap items-center gap-3 mb-2.5">
                        <span className="text-[10px] font-black text-primary uppercase tracking-[0.25em] group-hover:tracking-[0.35em] transition-all">Volumen {vol.volumeNumber}</span>
                        <div className="flex gap-2">
                          {vol.color_mode === 'color' && (
                            <span className="bg-gradient-to-r from-orange-400 to-pink-500 text-white text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-widest shadow-lg border border-white/10">
                              Color
                            </span>
                          )}
                          {vol.is_uncensored && (
                            <span className="bg-red-500 text-white text-[9px] font-black px-3 py-1 rounded-full uppercase tracking-widest shadow-lg border border-white/10">
                              N/C
                            </span>
                          )}
                        </div>
                      </div>
                      <h3 className="text-white font-black text-xl sm:text-2xl leading-tight line-clamp-2 tracking-tighter group-hover:text-primary transition-colors">
                        {vol.cleanTitle || vol.title}
                      </h3>
                    </div>

                    <div className="flex items-center gap-6 mt-auto">
                      <div className="flex flex-col">
                        <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest mb-1">Valoración</span>
                        <div className="flex items-center gap-1.5 text-yellow-500">
                          <Star className="w-5 h-5 fill-current" />
                          <span className="text-base font-black text-gray-100">{vol.rating > 0 ? vol.rating.toFixed(1) : '—'}</span>
                        </div>
                      </div>
                      <div className="w-px h-8 bg-white/5"></div>
                      <div className="flex flex-col">
                        <span className="text-[10px] text-gray-500 font-extrabold uppercase tracking-widest mb-1">Lectores</span>
                        <div className="flex items-center gap-1.5 text-primary">
                          <Download className="w-5 h-5" />
                          <span className="text-base font-black text-gray-100">{vol.downloadCount}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-center pl-4">
                    <div className="w-14 h-14 rounded-[1.5rem] bg-white/5 flex items-center justify-center text-gray-500 group-hover:bg-primary group-hover:text-white group-hover:scale-110 active:scale-95 transition-all duration-500 shadow-2xl border border-white/5 group-hover:border-white/20">
                      <ChevronRight className="w-8 h-8" />
                    </div>
                  </div>
                </div>

              ) : (
                <div
                  key={vol.id}
                  onClick={() => onSelectVolume(vol, realSeries)}
                  className="group relative bg-white/[0.02] rounded-[2.5rem] overflow-hidden border border-white/5 hover:border-primary/40 shadow-2xl hover:shadow-primary/20 hover:-translate-y-2 transition-all duration-700 flex flex-col h-full cursor-pointer"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden bg-white/5 shadow-2xl">
                    <img
                      alt={vol.title}
                      className="absolute inset-0 w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                      src={getCoverUrl(vol.coverUrl, vol.coverThumbUrl, settings.coverQuality)}
                    />

                    {/* Floating Badges */}
                    <div className="absolute top-4 left-4 flex flex-col gap-2">
                      <span className="bg-primary text-white text-[10px] font-black px-4 py-2 rounded-xl uppercase tracking-widest shadow-2xl border border-white/10">
                        Vol {vol.volumeNumber}
                      </span>
                      {vol.color_mode === 'color' && (
                        <span className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[9px] font-black px-3 py-1.5 rounded-xl uppercase tracking-widest shadow-2xl border border-white/10">
                          Color
                        </span>
                      )}
                      {vol.is_uncensored && (
                        <span className="bg-red-500 text-white text-[9px] font-black px-3 py-1.5 rounded-xl uppercase tracking-widest shadow-2xl border border-white/10">
                          N/C
                        </span>
                      )}
                    </div>

                    {/* Gradient Overlay */}
                    <div className="absolute inset-x-0 bottom-0 p-6 bg-gradient-to-t from-black via-black/40 to-transparent">
                      <div className="flex items-center gap-2 text-yellow-400 mb-2">
                        <Star className="w-4 h-4 fill-current" />
                        <span className="text-[12px] font-black">{vol.rating > 0 ? vol.rating.toFixed(1) : '—'}</span>
                      </div>
                      <h3 className="text-white font-black text-sm sm:text-lg leading-tight line-clamp-2 drop-shadow-2xl group-hover:text-primary transition-colors tracking-tight">
                        {vol.cleanTitle || vol.title}
                      </h3>
                    </div>
                  </div>

                  {/* Hover Accent Glow */}
                  <div className="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
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