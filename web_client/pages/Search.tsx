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
        <div className="max-w-[1800px] mx-auto space-y-3">

          {viewMode === 'list' ? (
            // LIST VIEW
            currentSeries.map((series) => (
              <div
                key={series.id}
                onClick={() => handleSelectSeries(series)}
                className="group flex gap-5 p-4 rounded-[2rem] glass-panel hover:bg-white/[0.07] hover:border-white/20 hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.4)] transition-all duration-500 cursor-pointer relative overflow-hidden mb-4"
              >
                {/* Left: Cover Image */}
                <div className="relative shrink-0 w-[100px] sm:w-[120px] aspect-[2/3] shadow-2xl rounded-2xl overflow-hidden bg-white/5 border border-white/10 group-hover:scale-[1.03] transition-transform duration-700">
                  <img
                    alt={series.title}
                    className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                    src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)}
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent"></div>
                </div>

                {/* Right: Details */}
                <div className="flex flex-col flex-1 min-w-0 py-1">
                  {/* Title & Action */}
                  <div className="flex justify-between items-start gap-4 mb-2">
                    <h3 className="text-white font-black text-base sm:text-lg md:text-xl leading-tight line-clamp-2 tracking-tight group-hover:text-primary transition-colors flex-1 min-w-0">
                      {series.title}
                    </h3>
                    <button
                      onClick={(e) => { e.stopPropagation(); /* Add logic */ }}
                      className="p-2.5 rounded-xl bg-white/5 hover:bg-primary text-gray-400 hover:text-white transition-all duration-300 transform group-hover:scale-110 shadow-lg active:scale-90 shrink-0"
                    >
                      <PlusCircle className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Author & Genres */}
                  <div className="mb-4">
                    <p className="text-[10px] sm:text-xs text-primary font-black uppercase tracking-[0.15em] opacity-90">
                      {series.author}
                    </p>
                    {series.genre && (
                      <p className="text-[10px] sm:text-[11px] text-gray-500 font-medium italic opacity-70 mt-1 line-clamp-1">
                        {series.genre}
                      </p>
                    )}
                  </div>

                  {/* Stats Row */}
                  <div className="flex items-center gap-5 text-[10px] font-black uppercase tracking-[0.15em] text-gray-500 mb-4">
                    <div className="flex items-center gap-1.5 text-yellow-500">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span className="text-gray-300">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                      <span className="opacity-50 font-bold">({series.voteCount || 0})</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-blue-400">
                      <Download className="w-3.5 h-3.5" />
                      <span>{series.downloadCount || 0}</span>
                    </div>
                    <div className="hidden sm:flex items-center gap-1.5 text-purple-400">
                      <Book className="w-3.5 h-3.5" />
                      <span>{series.volumesCount} Vols</span>
                    </div>
                  </div>

                  {/* Metadata Tags */}
                  <div className="flex flex-wrap items-center gap-2 mt-auto">
                    {series.book_type && (
                      <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-white/5 text-gray-400 uppercase tracking-widest border border-white/10 group-hover:border-primary/40 group-hover:text-white transition-all">
                        {series.book_type}
                      </span>
                    )}
                    {series.format && (
                      <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-emerald-500/10 text-emerald-400 uppercase tracking-widest border border-emerald-500/20">
                        {series.format}
                      </span>
                    )}
                    {series.color_mode === 'color' && (
                      <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-widest shadow-lg">
                        Color
                      </span>
                    )}
                    {series.is_uncensored && (
                      <span className="px-2.5 py-1 rounded-lg text-[8px] sm:text-[9px] font-black bg-red-500/10 text-red-500 uppercase tracking-widest border border-red-500/20">
                        N/C
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            // GRID VIEW
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {currentSeries.map((series) => (
                <div
                  key={series.id}
                  onClick={() => handleSelectSeries(series)}
                  className="group relative bg-[#0f1115] rounded-[2.5rem] overflow-hidden border border-white/5 hover:border-primary/40 shadow-2xl hover:shadow-primary/20 hover:-translate-y-2 transition-all duration-700 flex flex-col h-full cursor-pointer"
                >
                  {/* Image Container */}
                  <div className="relative aspect-[2/3] overflow-hidden bg-white/5">
                    <img
                      alt={series.title}
                      className="object-cover w-full h-full group-hover:scale-110 transition-transform duration-1000 opacity-90 group-hover:opacity-100"
                      src={getCoverUrl(series.coverUrl, series.coverThumbUrl, settings.coverQuality)}
                    />

                    {/* Floating Badges */}
                    <div className="absolute top-4 right-4 flex flex-col gap-2 scale-90 origin-top-right">
                      <span className="bg-black/80 backdrop-blur-xl text-white text-[9px] font-black px-2.5 py-1 rounded-lg uppercase tracking-[0.2em] border border-white/10">
                        {series.book_type?.split(' ')[0] || 'EPUB'}
                      </span>
                      {series.color_mode === 'color' && (
                        <span className="bg-gradient-to-br from-orange-400 to-pink-500 text-white text-[8px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest shadow-xl">COLOR</span>
                      )}
                      {series.is_uncensored && (
                        <span className="bg-red-600 text-white text-[8px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest shadow-xl">N/C</span>
                      )}
                    </div>

                    {/* Overlay Info */}
                    <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-black via-black/40 to-transparent">
                      <div className="flex items-center gap-2 text-yellow-500 mb-2">
                        <Star className="w-3 h-3 fill-current" />
                        <span className="text-[11px] font-black">{series.rating > 0 ? series.rating.toFixed(1) : '—'}</span>
                      </div>
                      <h3 className="text-white font-black text-base leading-tight line-clamp-2 drop-shadow-xl group-hover:text-primary transition-colors">
                        {series.title}
                      </h3>
                      <p className="text-gray-400 text-[10px] font-bold uppercase tracking-widest mt-1.5 truncate">
                        {series.author}
                      </p>
                      {series.genre && (
                        <p className="text-[9px] text-gray-500 italic opacity-60 truncate">
                          {series.genre}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Hover Accent Glow */}
                  <div className="absolute -inset-20 bg-primary/5 blur-[80px] opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none"></div>
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