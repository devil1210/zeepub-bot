import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
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
}

export const SeriesDetail: React.FC<SeriesDetailProps> = ({ series, onBack, onSelectVolume }) => {
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
            description: (data.summary || data.description || series.description)?.replace(/<br\s*\/?>/gi, '\n')
          } as Series);
          if (data.volumes) {
            const mappedVols: Volume[] = data.volumes.map((v: any) => ({
              id: v.id,
              seriesId: data.id,
              title: v.title,
              volumeNumber: v.seriesIndex || 1,
              coverUrl: v.cover || data.cover,
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
              romajiTitle: v.romaji,
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
              epubVersion: v.epubVersion
            }));
            setVolumes(mappedVols);

            // Preload volume covers
            const volCovers = mappedVols.map(v => v.coverUrl);
            preloadImages(volCovers);

            // Update synopsis from the first volume if available
            if (mappedVols.length > 0) {
              const firstVol = [...mappedVols].sort((a, b) => (a.volumeNumber || 0) - (b.volumeNumber || 0))[0];
              if (firstVol.description) {
                setRealSeries(prev => ({
                  ...prev,
                  description: firstVol.description?.replace(/<br\s*\/?>/gi, '\n')
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

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-100">

      {/* Mobile Header */}
      <header className="md:hidden h-16 bg-background/80 backdrop-blur border-b border-white/10 flex items-center justify-between px-4 shrink-0 z-40 sticky top-0">
        <span className="font-bold text-lg">Zeepub<span className="text-primary">Bot</span></span>
        <button onClick={onBack} className="text-gray-400 hover:text-primary">
          <ArrowLeft className="w-6 h-6" />
        </button>
      </header>

      <div className="relative w-full h-80 shrink-0 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center blur-sm scale-110 opacity-50"
          style={{ backgroundImage: `url('${realSeries.coverUrl}')` }}
        ></div>

        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/50 to-transparent"></div>
        <div className="absolute inset-0 bg-gradient-to-r from-black/80 to-transparent"></div>

        <div className="absolute bottom-0 w-full px-4 sm:px-6 lg:px-8 pb-8 z-20">
          <div className="max-w-5xl mx-auto flex flex-col sm:flex-row gap-6 items-end sm:items-end">
            <div className="hidden sm:block relative shrink-0 w-32 h-48 sm:w-40 sm:h-60 -mb-4 shadow-2xl rounded-lg overflow-hidden ring-4 ring-white/10">
              <img alt={`${realSeries.title} Cover`} className="w-full h-full object-cover" src={realSeries.coverUrl} />
            </div>

            <div className="flex-1 pb-2 w-full">
              <div className="flex items-center gap-3 mb-4">
                <span className="px-2.5 py-1 rounded-full text-[10px] sm:text-xs font-black bg-green-500/10 text-green-400 border border-green-500/20 uppercase tracking-widest whitespace-nowrap">
                  {realSeries.genre}
                </span>
                <span className="flex items-center gap-1.5 text-yellow-500 text-xs sm:text-sm font-black">
                  <Star className="w-4 h-4 fill-current" />
                  {realSeries.rating}
                </span>
              </div>

              <h1 className="text-2xl sm:text-4xl md:text-5xl font-extrabold text-white mb-2 leading-tight">
                {realSeries.title}
              </h1>
              <p className="text-white/80 text-sm sm:text-base mb-6 font-medium">Por {realSeries.author}</p>

              <div className="relative mb-6">
                <p className="text-gray-200 text-xs sm:text-sm line-clamp-3 max-w-2xl leading-relaxed whitespace-pre-line">
                  {realSeries.description || "Sin descripción disponible."}
                </p>
                {realSeries.description && realSeries.description.length > 150 && (
                  <button
                    onClick={() => setIsSynopsisModalOpen(true)}
                    className="mt-2 text-[#2AABEE] text-xs font-bold hover:underline py-1"
                  >
                    Ver más...
                  </button>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-4 text-xs sm:text-sm text-gray-300 font-mono">
                <span className="flex items-center gap-1.5"><Library className="w-4 h-4 text-primary" /> {volumes.length} Volúmenes</span>
                <span className="flex items-center gap-1.5"><Clock className="w-4 h-4 text-primary" /> {realSeries.status || 'Completado'}</span>
                {realSeries.lastUpdated && (
                  <span className="flex items-center gap-1.5"><Calendar className="w-4 h-4 text-primary" /> Actualizado: {realSeries.lastUpdated}</span>
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
            <div className="flex gap-2 bg-white/5 p-1 rounded-xl border border-white/5">
              <button
                onClick={() => setViewMode('list')}
                className={`p-1.5 rounded-lg transition-all ${viewMode === 'list' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-gray-500 hover:text-gray-300'}`}
              >
                <List className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`p-1.5 rounded-lg transition-all ${viewMode === 'grid' ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-gray-500 hover:text-gray-300'}`}
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
                  className="group relative flex gap-4 p-4 rounded-xl border border-white/5 bg-[#0d1117]/80 hover:bg-[#161b22] hover:border-[#2AABEE]/30 transition-all duration-200 cursor-pointer overflow-hidden shadow-sm"
                >
                  {/* Image */}
                  <div className="shrink-0 aspect-[2/3] bg-slate-800 rounded-lg overflow-hidden shadow-lg border border-white/5" style={{ width: settings.coverWidth }}>
                    <img alt={vol.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" src={vol.coverUrl} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0 flex flex-col">
                    <div className="mb-1">
                      <h3 className="text-white font-bold text-base sm:text-lg leading-tight line-clamp-2">
                        {vol.romajiTitle || vol.title}
                      </h3>
                      <p className="text-gray-500 text-xs italic font-serif mt-0.5 line-clamp-1">
                        {vol.romajiTitle ? vol.title : ''}
                      </p>
                    </div>

                    <div className="mb-2">
                      <p className="text-[#2AABEE] text-sm font-medium">
                        {series.author} {vol.illustrator ? `- ${vol.illustrator}` : ''}
                      </p>
                      <p className="text-gray-400 text-xs mt-0.5">
                        Volumen {vol.volumeNumber} <span className="text-[#2AABEE] font-bold">{vol.uploader}</span>
                      </p>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-bold mb-auto">
                      <div className="flex items-center gap-1.5 text-gray-400">
                        <Star className="w-3.5 h-3.5 text-yellow-500 fill-current" />
                        <span className="text-gray-200">{vol.rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-[#2AABEE]">
                        <Download className="w-3.5 h-3.5" />
                        <span>{vol.downloadCount}</span>
                      </div>
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3">
                      <button
                        className="flex items-center gap-2 px-5 py-2 rounded-lg bg-transparent border border-[#2AABEE]/40 text-[#2AABEE] text-[10px] font-black tracking-widest hover:bg-[#2AABEE] hover:text-white transition-all uppercase"
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

                  <div className="hidden sm:flex items-center justify-center pl-2 text-gray-600 group-hover:text-[#2AABEE] transition-colors">
                    <ChevronRight className="w-6 h-6" />
                  </div>
                </div>
              ) : (
                <div
                  key={vol.id}
                  onClick={() => onSelectVolume(vol, realSeries)}
                  className="group relative flex flex-col gap-3 rounded-xl p-3 transition-all duration-300 glass-panel hover:bg-white/10 hover:-translate-y-0.5 cursor-pointer border border-white/5"
                >
                  <div className="relative aspect-[2/3] w-full overflow-hidden rounded-lg bg-gray-800 shadow-md">
                    <img
                      alt={vol.title}
                      className="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                      src={vol.coverUrl}
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-60"></div>
                    <div className="absolute bottom-2 left-2 right-2">
                      <span className="text-[10px] font-black text-white/90 uppercase tracking-widest bg-primary/80 px-2 py-0.5 rounded shadow-sm">Vol {vol.volumeNumber}</span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1">
                    <h3 className="truncate text-sm font-bold text-white group-hover:text-primary transition-colors">
                      {vol.romajiTitle || vol.title}
                    </h3>
                    <div className="flex items-center justify-between text-[10px] font-bold text-gray-400">
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                        <span>{vol.rating.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Download className="w-3 h-3 text-[#2AABEE]" />
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
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-50 animate-in slide-in-from-bottom-4 duration-300 flex flex-col gap-3 max-w-5xl mx-auto">
        {isSortMenuOpen && (
          <div
            className="glass-panel rounded-2xl p-4 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-2 fade-in duration-200"
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
                  className={`flex items-center justify-center gap-2 px-3 py-3 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border ${activeSort === option.id ? 'bg-[#2AABEE] text-white border-[#2AABEE] shadow-lg shadow-blue-500/20' : 'bg-white/5 text-gray-400 border-white/5 hover:bg-white/10 hover:text-white'}`}
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
            <div className={`p-1.5 rounded-full transition-all duration-300 ${isSortMenuOpen ? 'bg-[#2AABEE] shadow-[0_0_15px_rgba(43,108,238,0.5)] translate-y-[-2px]' : ''}`}>
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
                <BookOpen className="w-5 h-5 text-[#2AABEE]" />
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
                className="px-6 py-2 bg-[#2AABEE] text-white text-xs font-black uppercase tracking-widest rounded-lg hover:bg-[#2AABEE]/80"
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