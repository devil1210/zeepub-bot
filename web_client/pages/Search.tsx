import React, { useState, useRef, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useSearchNav } from '../contexts/SearchNavContext';
import {
  Search as SearchIcon,
  Filter,
  Star,
  Download,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
  ArrowUp,
  ArrowDownUp,
  Calendar,
  Clock,
  Check,
  LayoutGrid,
  List,
  Book,
  Hash,
  Home,
  PlusCircle
} from 'lucide-react';
import { Series } from '../types';
import { SearchScopeModal } from '../components/SearchScopeModal';
import { api } from '../src/services/api';
import { preloadImages } from '../src/utils/imagePreloader';
import { getCoverUrl } from '../src/utils/imageUtils';

interface SearchProps {
  onSelectSeries: (series: Series) => void;
  onNavigate?: (tab: string) => void;
}

export const Search: React.FC<SearchProps> = ({ onSelectSeries, onNavigate }) => {
  const { settings } = useTheme();
  const {
    state: navState,
    setPageInfo,
    setActiveSort: setNavActiveSort,
    setVisible,
    setSearchTerm: setNavSearchTerm,
    setSelectedScope: setNavSelectedScope,
    setViewMode: setNavViewMode,
    setLoading: setNavLoading,
    registerCallbacks
  } = useSearchNav();

  const [isScopeModalOpen, setIsScopeModalOpen] = useState(false);
  const [activeSort, setActiveSort] = useState(navState.activeSort || 'a-z');
  const [selectedScope, setSelectedScope] = useState(navState.selectedScope || 'TODOS');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>(navState.viewMode || 'list');
  const [searchTerm, setSearchTerm] = useState(navState.searchTerm);

  // Data State
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState(false);

  // Pagination State - Initialize from context
  const [currentPage, setCurrentPage] = useState(navState.currentPage || 1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);

  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Sync state to context for Layout's header/nav components
  useEffect(() => {
    setPageInfo(currentPage, totalPages);
  }, [currentPage, totalPages]);

  useEffect(() => {
    setNavActiveSort(activeSort);
  }, [activeSort]);

  useEffect(() => {
    setNavSearchTerm(searchTerm);
  }, [searchTerm]);

  useEffect(() => {
    setNavSelectedScope(selectedScope);
  }, [selectedScope]);

  useEffect(() => {
    setNavViewMode(viewMode);
  }, [viewMode]);

  useEffect(() => {
    setNavLoading(loading);
  }, [loading]);

  // Make header/nav visible when this component mounts, hide on unmount
  useEffect(() => {
    setVisible(true);
    return () => setVisible(false);
  }, []);

  // Register callbacks for header/nav buttons
  useEffect(() => {
    registerCallbacks({
      onPrevPage: () => setCurrentPage(prev => Math.max(1, prev - 1)),
      onNextPage: () => setCurrentPage(prev => Math.min(totalPages, prev + 1)),
      onSortChange: (sort: string) => setActiveSort(sort),
      onSearchChange: (term: string) => setSearchTerm(term),
      onScopeClick: () => setIsScopeModalOpen(true),
      onViewModeChange: (mode: 'list' | 'grid') => setViewMode(mode)
    });
  }, [totalPages]);

  // Perform Search
  const doSearch = async (query: string, page: number) => {
    setLoading(true);
    try {
      // Pass the activeSort to the backend for global sorting
      // When scope is "TODOS", search in all categories
      const searchScope = selectedScope === 'TODOS' ? '' : selectedScope.toLowerCase();
      const res = await api.searchBooks(query, page, searchScope, activeSort);

      if (res && res.results) {
        // Map backend results to Series type
        const mapped: Series[] = res.results.map((item: any) => ({
          id: item.id || item.link,
          series_hash: item.series_hash,
          title: item.title,
          author: item.author,
          coverUrl: item.cover || '',
          coverThumbUrl: item.cover_thumb || item.cover || '',
          description: item.summary,
          genre: item.categories ? item.categories.join(', ') : '',
          format: item.fileType ? item.fileType.replace('application/', '').toUpperCase() : 'EPUB',
          rating: item.rating_average || 0,
          voteCount: item.rating_count || 0,
          downloadCount: item.download_count || 0,
          volumesCount: item.numBooks || 1,
          status: 'Completed',
          lastUpdated: item.updatedDate || 'Reciente',
          illustrator: item.illustrator,
          translator: item.translator,
          typesetter: item.typesetter,
          group: item.group,
          book_type: item.book_type || 'Novela Ligera',
          is_uncensored: item.is_uncensored,
          color_mode: item.color_mode,
          volumes: []
        }));

        setSeries(mapped);
        setTotalPages(res.totalPages || 1);
        setTotalResults(res.totalResults || mapped.length);

        const currentCovers = mapped
          .map(s => {
            const url = s.coverThumbUrl || s.coverUrl;
            return typeof url === 'string' ? url : url?.cover || '';
          })
          .filter(Boolean);

        preloadImages(currentCovers as string[]);
        scrollToTop();

        // Preload next page in background if available
        if (page < (res.totalPages || 1)) {
          api.searchBooks(query, page + 1, searchScope, activeSort).then(nextRes => {
            if (nextRes && nextRes.results) {
              const nextCovers = nextRes.results
                .map((item: any) => {
                  const url = item.cover_thumb || item.cover || '';
                  return typeof url === 'string' ? url : url?.cover || '';
                })
                .filter(Boolean);
              preloadImages(nextCovers as string[]);
            }
          });
        }
      } else {
        setSeries([]);
      }
    } catch (e) {
      console.error("Search error", e);
    } finally {
      setLoading(false);
    }
  };

  // Reset page on search term or scope change
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, selectedScope, activeSort]);

  // Initial Search & Search on Enter
  useEffect(() => {
    // Debounce could be added here
    const timer = setTimeout(() => {
      doSearch(searchTerm, currentPage);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm, currentPage, selectedScope, activeSort]);

  // Restore Scroll Position on Mount
  useEffect(() => {
    const savedScrollPos = sessionStorage.getItem('search_scroll_pos');
    if (savedScrollPos) {
      const mainContainer = document.querySelector('main');
      if (mainContainer) {
        setTimeout(() => {
          mainContainer.scrollTop = parseInt(savedScrollPos);
        }, 0);
      }
    }
  }, []);

  const handleSelectSeries = (series: Series) => {
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
      sessionStorage.setItem('search_scroll_pos', mainContainer.scrollTop.toString());
    }
    onSelectSeries(series);
  };

  const scrollToTop = (behavior: ScrollBehavior = 'smooth') => {
    const mainContainer = document.querySelector('main');
    if (mainContainer) {
      mainContainer.scrollTo({ top: 0, behavior });
    } else {
      window.scrollTo({ top: 0, behavior });
    }
  };

  useEffect(() => {
    scrollToTop('smooth');
  }, [currentPage]);

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(prev => prev + 1);
      scrollToTop();
    }
  };

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(prev => prev - 1);
      scrollToTop();
    }
  };

  const currentSeries = React.useMemo(() => {
    // Now that results are sorted on the backend, we don't need to re-sort here
    // unless we want to handle numeric nuances better than the DB ILIKE/ORDER BY.
    // However, the user wants global sorting, so we return the series as they come.
    return series;
  }, [series]);

  const sortOptions = [
    { id: 'a-z', label: 'A-Z', icon: ArrowUp },
    { id: 'z-a', label: 'Z-A', icon: ArrowUp },
    { id: 'downloads', label: 'DESCARGAS', icon: Download },
    { id: 'rating', label: 'VALORACIÓN', icon: Star },
    { id: 'added', label: 'AÑADIDO', icon: Calendar },
    { id: 'updated', label: 'ACTUALIZADO', icon: Clock },
  ];

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-300 relative" ref={scrollContainerRef}>

      <SearchScopeModal
        isOpen={isScopeModalOpen}
        onClose={() => setIsScopeModalOpen(false)}
        selectedScope={selectedScope}
        onSelectScope={setSelectedScope}
      />

      {/* List Content - Header/Nav rendered at Layout level */}
      <div className="flex-1 px-4 pb-32 md:pb-6">
        <div className="max-w-7xl mx-auto space-y-3">

          {viewMode === 'list' ? (
            // LIST VIEW
            currentSeries.map((series) => (
              <div
                key={series.id}
                onClick={() => handleSelectSeries(series)}
                className="group flex gap-4 p-3 rounded-xl glass-panel hover:bg-white/5 transition-all duration-200 cursor-pointer relative overflow-hidden shadow-sm"
              >
                {/* Left: Cover Image */}
                <div className="relative shrink-0 w-[85px] sm:w-[100px] aspect-[2/3] shadow-lg rounded-md overflow-hidden bg-slate-200 dark:bg-slate-800">
                  <img
                    alt={series.title}
                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                    src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)}
                  />
                </div>

                {/* Right: Details */}
                <div className="flex flex-col flex-1 min-w-0 py-0.5">
                  {/* Title */}
                  <div className="flex justify-between items-start gap-2">
                    <h3 className="text-base sm:text-lg font-bold text-gray-900 dark:text-white leading-tight mb-1 line-clamp-2 sm:line-clamp-1">
                      {series.title}
                    </h3>
                    <button
                      onClick={(e) => { e.stopPropagation(); /* Add logic */ }}
                      className="p-1.5 rounded-full bg-white/5 hover:bg-[var(--color-primary)]/20 text-gray-400 hover:text-[var(--color-primary)] transition-colors shrink-0"
                    >
                      <PlusCircle className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Author */}
                  <p className="text-sm text-[var(--color-primary)] font-medium mb-1.5 truncate">
                    {series.author}
                  </p>

                  {/* Genres */}
                  <div className="flex flex-col gap-0.5">
                    <p className="text-[10px] text-gray-500 line-clamp-1">
                      <span className="font-bold text-gray-600 uppercase tracking-wide mr-1">GÉNEROS:</span>
                      {series.genre}
                    </p>
                    <p className="text-[9px] text-gray-400 line-clamp-1 italic">
                      {[
                        series.illustrator && `Ilustr: ${series.illustrator}`,
                        series.translator && `Traductor: ${series.translator}`,
                        series.group && `Grupo: ${series.group}`,
                      ].filter(Boolean).join(' • ')}
                    </p>
                  </div>

                  {/* Meta Info Row */}
                  <div className="flex flex-wrap items-center gap-2 mt-3 mb-2">
                    <span className="text-[10px] sm:text-xs font-bold text-gray-400 uppercase tracking-widest">
                      {series.volumesCount} {series.volumesCount === 1 ? 'VOLUMEN' : 'VOLÚMENES'}
                    </span>

                    {series.book_type && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/10 text-primary uppercase tracking-wider border border-primary/20">
                        {series.book_type}
                      </span>
                    )}
                    {series.format && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#004d40] text-[#4db6ac] uppercase tracking-wider border border-[#00695c]/30">
                        {series.format}
                      </span>
                    )}
                    {series.color_mode === 'color' && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-wider shadow-sm">
                        A Color
                      </span>
                    )}
                    {series.is_uncensored && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-red-500 uppercase tracking-wider border border-red-500/30">
                        Sin Censura
                      </span>
                    )}
                  </div>

                  {/* Stats Row */}
                  <div className="flex items-center gap-4 text-xs font-bold text-gray-500 dark:text-gray-400">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span className="text-gray-700 dark:text-gray-300">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                      <span className="text-gray-400 dark:text-gray-600 font-normal">({series.voteCount || 0})</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-[var(--color-primary)]">
                      <Download className="w-3.5 h-3.5" />
                      <span>{series.downloadCount || 0}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            // GRID VIEW
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {currentSeries.map((series) => (
                <div
                  key={series.id}
                  onClick={() => handleSelectSeries(series)}
                  className="group relative glass-panel rounded-2xl overflow-hidden hover:bg-white/5 shadow-sm hover:shadow-xl hover:shadow-[var(--color-primary)]/10 hover:-translate-y-1 transition-all duration-300 flex flex-col h-full cursor-pointer"
                >
                  {/* Format Badge (Top Right) */}
                  <div className="absolute top-3 right-3 z-10">
                    <span className="bg-black/60 backdrop-blur text-white text-[10px] font-bold px-2 py-1 rounded-md uppercase tracking-wider">
                      {series.book_type || 'EPUB'}
                    </span>
                  </div>

                  {/* Image Container */}
                  <div className="relative aspect-[2/3] overflow-hidden bg-slate-200 dark:bg-slate-800">
                    <img
                      alt={series.title}
                      className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100"
                      src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)}
                    />
                    {/* Bottom Gradient & Text Overlay */}
                    <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/40 to-transparent opacity-90"></div>
                    <div className="absolute bottom-4 left-4 right-4">
                      <h3 className="text-white font-bold text-base leading-tight line-clamp-2 drop-shadow-[0_2px_2px_rgba(0,0,0,0.8)]">
                        {series.title}
                      </h3>
                      <p className="text-gray-200 text-xs font-medium mt-1 truncate drop-shadow-[0_1px_1px_rgba(0,0,0,0.8)]">
                        {series.author}
                      </p>
                    </div>
                  </div>

                  {/* Details Container */}
                  <div className="p-4 flex flex-col flex-1 bg-transparent">
                    {/* Top Row: Genre & Rating */}
                    <div className="flex items-center justify-between gap-2 mb-3">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-[var(--color-primary)]/10 text-[var(--color-primary)] border border-[var(--color-primary)]/20 truncate max-w-[70%]">
                        {series.genre?.split(',')[0]}
                      </span>
                      <div className="flex items-center gap-1 shrink-0">
                        <Star className="w-3 h-3 text-yellow-500 fill-current" />
                        <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300">
                          {series.rating > 0 ? series.rating.toFixed(1) : '—'}
                        </span>
                      </div>
                    </div>

                    {/* Meta Row: Color/Censura badges in Grid */}
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      {series.color_mode === 'color' && (
                        <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-wider shadow-sm">
                          A Color
                        </span>
                      )}
                      {series.is_uncensored && (
                        <span className="px-1.5 py-0.5 rounded text-[8px] font-bold bg-red-500/10 text-red-500 uppercase tracking-wider border border-red-500/30">
                          Sin Censura
                        </span>
                      )}
                    </div>

                    {/* Bottom Row: Volumes & Updated */}
                    <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-500 mb-4 font-mono">
                      <div className="flex items-center gap-1.5" title="Volúmenes">
                        <Book className="w-3.5 h-3.5" />
                        <span>{series.volumesCount} Vols</span>
                      </div>
                      <div className="flex items-center gap-1.5" title="Actualizado">
                        <Clock className="w-3.5 h-3.5" />
                        <span>Hoy</span>
                      </div>
                    </div>

                    {/* Footer: Publisher & Download */}
                    <div className="mt-auto pt-3 border-t border-white/5 flex items-center justify-between">
                      <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">
                        {series.status === 'Ongoing' ? 'EN EMISIÓN' : 'FINALIZADO'}
                      </span>
                      <div className="flex gap-2">
                        <button className="p-2 rounded-full bg-white/5 text-gray-400 hover:bg-[var(--color-primary)] hover:text-white transition-colors" onClick={(e) => { e.stopPropagation(); }}>
                          <PlusCircle className="w-4 h-4" />
                        </button>
                        <button className="p-2 rounded-full bg-white/5 text-gray-400 hover:bg-[var(--color-primary)] hover:text-white transition-colors">
                          <Download className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination Info */}
          <div className="text-center py-4 text-xs text-gray-500 font-medium">
            Página {currentPage} de {totalPages} • {totalResults} Resultados
          </div>
        </div>
      </div>

    </div>
  );
};