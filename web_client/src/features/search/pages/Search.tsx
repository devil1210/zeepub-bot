import React, { useState, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import {
  Star,
  Download,
  ArrowUp,
  Calendar,
  Clock,
} from 'lucide-react';
import { Series } from '@shared/types';
import { SearchScopeModal } from '../components/SearchScopeModal';
import { api } from '@shared/services/api';
import { preloadImages } from '@shared/utils/imagePreloader';
import { Virtualizer } from 'virtua';
import { useResponsiveColumns } from '@shared/hooks/useResponsiveColumns';

// Modular Components
import { SearchCardList } from '../components/SearchCardList';
import { SearchCardGrid } from '../components/SearchCardGrid';
import { SearchPagination } from '../components/SearchPagination';

const chunkArray = <T,>(array: T[], size: number): T[][] => {
  const chunked: T[][] = [];
  for (let i = 0; i < array.length; i += size) {
    chunked.push(array.slice(i, i + size));
  }
  return chunked;
};

interface SearchProps {
  onSelectSeries: (series: Series) => void;
  onNavigate?: (tab: string) => void;
}

export const Search: React.FC<SearchProps> = ({ onSelectSeries, onNavigate }) => {
  const { settings } = useTheme();
  const {
    state: navState,
    setContextType,
    setPageInfo,
    setActiveSort: setNavActiveSort,
    setVisible,
    setSearchTerm: setNavSearchTerm,
    setSelectedScope: setNavSelectedScope,
    setViewMode: setNavViewMode,
    setLoading: setNavLoading,
    registerCallbacks
  } = useNavigation();

  const [isScopeModalOpen, setIsScopeModalOpen] = useState(false);
  const [scrollEl, setScrollEl] = useState<HTMLElement | null>(null);
  const scrollRefObj = useMemo(() => ({ current: scrollEl }), [scrollEl]);

  useEffect(() => {
    // Attempt to find the main scroll container
    const el = document.querySelector('main');
    if (el) setScrollEl(el);
  }, []);
  const [activeSort, setActiveSort] = useState(navState.activeSort || 'a-z');
  const [selectedScope, setSelectedScope] = useState(navState.selectedScope || 'TODOS');
  const viewMode = navState.viewMode;
  const searchTerm = navState.searchTerm;

  // Data State
  const [series, setSeries] = useState<Series[]>([]);
  const [loading, setLoading] = useState(false);

  // Pagination State
  const [currentPage, setCurrentPage] = useState(navState.currentPage || 1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalResults, setTotalResults] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const isFirstRender = useRef(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isMounted = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const responsiveColumns = useResponsiveColumns();

  // Determine actual columns based on view mode
  const columns = useMemo(() => {
    return viewMode === 'list' ? 1 : responsiveColumns;
  }, [viewMode, responsiveColumns]);

  useEffect(() => {
    return () => {
      isMounted.current = false;
      if (abortControllerRef.current) abortControllerRef.current.abort();
    };
  }, []);

  useEffect(() => {
    setPageInfo(currentPage, totalPages);
  }, [currentPage, totalPages]);

  useEffect(() => setNavActiveSort(activeSort), [activeSort]);
  useEffect(() => setNavSelectedScope(selectedScope), [selectedScope]);
  useEffect(() => setNavLoading(loading), [loading]);

  useEffect(() => {
    setContextType('search');
    setVisible(true);
    return () => {
      setVisible(false);
      setContextType('main');
    };
  }, []);

  useEffect(() => {
    const unregister = registerCallbacks({
      onPrevPage: () => setCurrentPage(prev => Math.max(1, prev - 1)),
      onNextPage: () => setCurrentPage(prev => Math.min(totalPages, prev + 1)),
      onSortChange: (sort: string) => setActiveSort(sort),
      onSearchChange: (term: string) => {
        // This is now redundant but kept for safety if needed
      },
      onSearchSubmit: () => {
        doSearch(searchTerm, 1);
      },
      onScopeClick: () => setIsScopeModalOpen(true),
      onViewModeChange: (mode: 'list' | 'grid') => setNavViewMode(mode),
      onHome: () => onNavigate && onNavigate('dashboard')
    });
    return () => unregister();
  }, [totalPages, registerCallbacks]);

  const doSearch = async (query: string, page: number) => {
    // Abort previous request if any
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setLoading(true);
    try {
      const searchScope = selectedScope === 'TODOS' ? '' : selectedScope.toLowerCase();
      const res = await api.searchBooks(
        query,
        page,
        searchScope,
        activeSort,
        abortControllerRef.current.signal
      );

      if (res && res.success && res.result && Array.isArray(res.result.results)) {
        const resultsData = res.result;
        const mapped: Series[] = resultsData.results.map((item: any) => {
          const seriesId = item.series_hash ? `series_${item.series_hash}` : (item.id || item.link);
          return {
            id: seriesId,
            series_hash: item.series_hash,
            title: item.title,
            author: item.author,
            coverUrl: item.coverUrl || {
              cover_low: item.cover_low,
              cover_medium: item.cover_medium,
              cover_high: item.cover_high,
              cover_original: item.cover_original,
              cover: item.cover || ''
            },
            coverThumbUrl: item.cover_thumb || item.cover_low || item.cover || '',
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
            typesetter: item.layout_by || item.typesetter,
            group: item.translator || item.group,
            book_type: item.book_type || 'Novela Ligera',
            is_uncensored: item.is_uncensored,
            color_mode: item.color_mode,
            volumes: []
          };
        });

        if (!isMounted.current) return;

        // In infinite mode, append results; in paginated mode, replace
        if (settings.listMode === 'infinite' && page > 1) {
          setSeries(prev => [...prev, ...mapped]);
        } else {
          setSeries(mapped);
        }
        setTotalPages(resultsData.totalPages || 1);
        setTotalResults(resultsData.totalResults || mapped.length);

        const currentCovers = mapped
          .map(s => {
            const url = s.coverThumbUrl || s.coverUrl;
            return typeof url === 'string' ? url : url?.cover || '';
          })
          .filter(Boolean);

        preloadImages(currentCovers as string[]);
        if (settings.listMode !== 'infinite' || page === 1) {
          scrollToTop();
        }

        if (page < (resultsData.totalPages || 1)) {
          api.searchBooks(query, page + 1, searchScope, activeSort).then(nextRes => {
            if (nextRes && nextRes.success && nextRes.result && nextRes.result.results) {
              const nextCovers = nextRes.result.results
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
        setTotalPages(1);
        setTotalResults(0);
      }
    } catch (e: any) {
      if (axios.isCancel(e)) return;
      console.error("Search error", e);
    } finally {
      if (isMounted.current) {
        setLoading(false);
        setLoadingMore(false);
      }
    }
  };

  // Track previous search params to detect when to reset page
  const prevSearchParams = useRef({ searchTerm, selectedScope, activeSort });

  useEffect(() => {
    // Determine if we should reset to page 1
    const paramsChanged =
      prevSearchParams.current.searchTerm !== searchTerm ||
      prevSearchParams.current.selectedScope !== selectedScope ||
      prevSearchParams.current.activeSort !== activeSort;

    if (paramsChanged) {
      prevSearchParams.current = { searchTerm, selectedScope, activeSort };
      if (currentPage !== 1) {
        setCurrentPage(1);
        return; // The effect will trigger again with currentPage = 1
      }
    }

    const timer = setTimeout(() => {
      if (searchTerm || selectedScope !== 'TODOS') {
        doSearch(searchTerm, currentPage);
      } else {
        // Optional: clear results if search is empty, or show recommendations
        // For now, let's just do the search (it will return everything)
        doSearch(searchTerm, currentPage);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm, currentPage, selectedScope, activeSort]);

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
    if (settings.listMode !== 'infinite' || currentPage === 1) {
      scrollToTop('smooth');
    }
  }, [currentPage, settings.listMode]);

  const currentSeries = useMemo(() => series, [series]);
  const rows = useMemo(() => chunkArray(currentSeries, columns), [currentSeries, columns]);

  // Infinite scroll detection
  useEffect(() => {
    if (settings.listMode !== 'infinite') return;

    const mainContainer = document.querySelector('main');
    if (!mainContainer) return;

    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = mainContainer;
      const nearBottom = scrollTop + clientHeight >= scrollHeight - 200;

      if (nearBottom && !loading && !loadingMore && currentPage < totalPages) {
        setLoadingMore(true);
        setCurrentPage(prev => prev + 1);
      }
    };

    mainContainer.addEventListener('scroll', handleScroll, { passive: true });
    return () => mainContainer.removeEventListener('scroll', handleScroll);
  }, [settings.listMode, loading, loadingMore, currentPage, totalPages]);

  // View Transition Styles for native feel
  const viewTransitionStyles = {
    viewTransitionName: 'search-results'
  };

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-300 relative" ref={scrollContainerRef}>
      <SearchScopeModal
        isOpen={isScopeModalOpen}
        onClose={() => setIsScopeModalOpen(false)}
        selectedScope={selectedScope}
        onSelectScope={setSelectedScope}
      />
      <div className="flex-1 px-4 pb-32 md:pb-6 overflow-x-hidden">
        <div className="max-w-[1800px] mx-auto">
          {series.length > 0 && (
            <div className="w-full" style={viewTransitionStyles}>
              {viewMode === 'list' ? (
                <Virtualizer
                  scrollRef={scrollRefObj as React.RefObject<HTMLElement>}
                  bufferSize={500}
                >
                  {series.map((item) => (
                    <div key={item.id} className="mb-4">
                      <SearchCardList
                        series={item}
                        settings={settings}
                        onClick={() => handleSelectSeries(item)}
                      />
                    </div>
                  ))}
                </Virtualizer>
              ) : (
                <Virtualizer
                  scrollRef={scrollRefObj as React.RefObject<HTMLElement>}
                  bufferSize={1000}
                >
                  {rows.map((row, rowIndex) => (
                    <div
                      key={rowIndex}
                      className="grid gap-6 mb-6 px-1"
                      style={{
                        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`
                      }}
                    >
                      {row.map((item) => (
                        <SearchCardGrid
                          key={item.id}
                          series={item}
                          settings={settings}
                          onClick={() => handleSelectSeries(item)}
                        />
                      ))}
                    </div>
                  ))}
                </Virtualizer>
              )}
            </div>
          )}

          {/* Pagination or Infinite Load indicator */}
          {settings.listMode === 'paginated' ? (
            <SearchPagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalResults={totalResults}
            />
          ) : loadingMore ? (
            <div className="flex justify-center py-8">
              <div className="w-8 h-8 border-3 border-primary/20 border-t-primary rounded-full animate-spin"></div>
            </div>
          ) : currentPage < totalPages ? (
            <div className="text-center py-6 text-gray-500 text-sm">
              Desplázate para cargar más...
            </div>
          ) : series.length > 0 ? (
            <div className="text-center py-6 text-gray-500 text-sm">
              ✓ Fin de los resultados
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};
