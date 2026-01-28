import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useNavigation } from '../contexts/NavigationContext';
import {
  Star,
  Download,
  ArrowUp,
  Calendar,
  Clock,
} from 'lucide-react';
import { Series } from '../types';
import { SearchScopeModal } from '../components/search/SearchScopeModal';
import { api } from '../src/services/api';
import { preloadImages } from '../src/utils/imagePreloader';

// Modular Components
import { SearchCardList } from '../components/search/SearchCardList';
import { SearchCardGrid } from '../components/search/SearchCardGrid';
import { SearchPagination } from '../components/search/SearchPagination';

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
  const isFirstRender = useRef(true);

  const scrollContainerRef = useRef<HTMLDivElement>(null);

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
    });
    return () => unregister();
  }, [totalPages, registerCallbacks]);

  const doSearch = async (query: string, page: number) => {
    setLoading(true);
    try {
      const searchScope = selectedScope === 'TODOS' ? '' : selectedScope.toLowerCase();
      const res = await api.searchBooks(query, page, searchScope, activeSort);

      if (res && Array.isArray(res.results)) {
        const mapped: Series[] = res.results.map((item: any) => {
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
            typesetter: item.typesetter,
            group: item.group,
            book_type: item.book_type || 'Novela Ligera',
            is_uncensored: item.is_uncensored,
            color_mode: item.color_mode,
            volumes: []
          };
        });

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
        setTotalPages(1);
        setTotalResults(0);
      }
    } catch (e) {
      console.error("Search error", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false;
      return;
    }
    setCurrentPage(1);
  }, [searchTerm, selectedScope, activeSort]);

  useEffect(() => {
    const timer = setTimeout(() => {
      doSearch(searchTerm, currentPage);
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
    scrollToTop('smooth');
  }, [currentPage]);

  const currentSeries = useMemo(() => series, [series]);

  return (
    <div className="flex flex-col h-full animate-in fade-in duration-300 relative" ref={scrollContainerRef}>
      <SearchScopeModal
        isOpen={isScopeModalOpen}
        onClose={() => setIsScopeModalOpen(false)}
        selectedScope={selectedScope}
        onSelectScope={setSelectedScope}
      />

      <div className="flex-1 px-4 pb-32 md:pb-6">
        <div className="max-w-[1800px] mx-auto space-y-3">
          {viewMode === 'list' ? (
            currentSeries.map((series) => (
              <SearchCardList
                key={series.id}
                series={series}
                settings={settings}
                onClick={() => handleSelectSeries(series)}
              />
            ))
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
              {currentSeries.map((series) => (
                <SearchCardGrid
                  key={series.id}
                  series={series}
                  settings={settings}
                  onClick={() => handleSelectSeries(series)}
                />
              ))}
            </div>
          )}

          <SearchPagination
            currentPage={currentPage}
            totalPages={totalPages}
            totalResults={totalResults}
          />
        </div>
      </div>
    </div>
  );
};
