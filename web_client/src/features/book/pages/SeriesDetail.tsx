import React, { useState, useEffect } from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { getCoverUrl } from '@shared/utils/imageUtils';
import { api } from '@shared/services/api';
import {
  ListOrdered,
  LayoutGrid,
  List
} from 'lucide-react';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { Series, Volume } from '@shared/types';
import { preloadImages } from '@shared/utils/imagePreloader';
import { SeriesHero } from '../components/SeriesHero';
import { VolumeList } from '../components/VolumeList';
import { SynopsisModal } from '../components/SynopsisModal';
import { useSeriesDetails } from '../hooks/useSeriesDetails';

interface SeriesDetailProps {
  series: Series;
  onBack: () => void;
  onSelectVolume: (volume: Volume, series: Series) => void;
  onSearch?: (term: string) => void;
}

export const SeriesDetail: React.FC<SeriesDetailProps> = ({ series, onBack, onSelectVolume, onSearch }) => {
  const { settings } = useTheme();
  const { webApp } = useTelegram();
  const { setContextType, registerCallbacks, setPageInfo, setVisible } = useNavigation();
  const { isAdmin } = useTelegram();
  const {
    realSeries,
    volumes,
    loading,
    isSyncing,
    handleSyncSeries
  } = useSeriesDetails(series, settings, webApp);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;
  const [activeSort, setActiveSort] = useState('num-asc');
  const [isSynopsisModalOpen, setIsSynopsisModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

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
    setPageInfo(currentPage, totalPages);
  }, [currentPage, totalPages]);

  const handleNextPageLocal = () => {
    setCurrentPage(prev => Math.min(totalPages, prev + 1));
  };

  const handlePrevPageLocal = () => {
    setCurrentPage(prev => Math.max(1, prev - 1));
  };

  useEffect(() => {
    setContextType('series');
    setVisible(true);
    const unregister = registerCallbacks({
      onPrevPage: handlePrevPageLocal,
      onNextPage: handleNextPageLocal,
      onSortChange: (sort: string) => setActiveSort(sort),
      onBack: onBack,
      onHome: () => onBack(),
    });
    return () => {
      unregister();
      setContextType('main');
    };
  }, [totalPages, onBack, registerCallbacks, setContextType, setVisible]);

  return (
    <div className="flex-1 flex flex-col min-h-0 relative font-sans text-gray-100">

      <SeriesHero
        series={realSeries}
        volumesCount={volumes.length}
        onBack={onBack}
        onSearch={onSearch}
        onOpenSynopsis={() => setIsSynopsisModalOpen(true)}
        isAdmin={isAdmin}
        isSyncing={isSyncing}
        onSync={handleSyncSeries}
        settings={settings}
      />

      {loading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
        </div>
      )}

      <div className="flex-1 pb-32">
        <div className="max-w-[1800px] mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <ListOrdered className="w-5 h-5 text-primary" />
              Lista de Volúmenes
            </h2>
            <div className="flex gap-2 glass-panel p-1 rounded-premium-sm border border-white/10 shadow-lg">
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

          <VolumeList
            volumes={currentVolumes}
            viewMode={viewMode}
            onSelectVolume={onSelectVolume}
            series={realSeries}
            settings={settings}
          />

          <div className="text-center py-4 text-xs text-gray-500 font-medium">
            Página {currentPage} de {totalPages} • {volumes.length} Volúmenes
          </div>
        </div>
      </div>

      <SynopsisModal
        isOpen={isSynopsisModalOpen}
        onClose={() => setIsSynopsisModalOpen(false)}
        description={realSeries.description}
      />

    </div>
  );
};
