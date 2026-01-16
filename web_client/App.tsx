import React, { useState, useEffect, useCallback } from 'react';
import { ThemeProvider } from './contexts/ThemeContext';
import { TelegramProvider, useTelegram } from './contexts/TelegramContext';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { Search } from './pages/Search';
import { Admin } from './pages/Admin';
import { Reader } from './pages/Reader';
import { Settings } from './pages/Settings';
import { SeriesDetail } from './pages/SeriesDetail';
import { BookDetail } from './pages/BookDetail';
import { RequestBook } from './pages/RequestBook';
import { Library } from './pages/Library';
import { Series, Volume } from './types';

// Define navigation state shape
interface NavState {
  tab: string;
  series?: Series | null;
  volume?: Volume | null;
}

const AppContent: React.FC = () => {
  const { webApp } = useTelegram();
  const [navStack, setNavStack] = useState<NavState[]>([{ tab: 'dashboard' }]);
  const [isReading, setIsReading] = useState(false);

  // Current active state is the last item in stack
  const currentState = navStack[navStack.length - 1];

  // Helper to push new state
  const navigateTo = useCallback((tab: string, series: Series | null = null, volume: Volume | null = null) => {
    setNavStack(prev => {
      // If we are just switching main tabs (dashboard, search, library, settings), clear stack and set new root
      if (['dashboard', 'search', 'library', 'settings', 'admin', 'requests'].includes(tab) && !series && !volume) {
          return [{ tab }];
      }
      // Otherwise push to stack (drill down)
      return [...prev, { tab, series, volume }];
    });
  }, []);

  // Back handler
  const handleBack = useCallback(() => {
    if (isReading) {
      setIsReading(false);
      return;
    }

    setNavStack(prev => {
      if (prev.length > 1) {
        return prev.slice(0, -1);
      }
      return prev; // Can't go back further than root
    });
  }, [isReading]);

  // Sync with Telegram BackButton
  useEffect(() => {
    if (webApp?.BackButton) {
      if (navStack.length > 1 || isReading) {
        webApp.BackButton.show();
        webApp.BackButton.onClick(handleBack);
      } else {
        webApp.BackButton.hide();
      }
    }
    return () => {
      if (webApp?.BackButton) {
        webApp.BackButton.offClick(handleBack);
      }
    };
  }, [webApp, navStack.length, isReading, handleBack]);


  // Navigation Helpers for Pages
  const onNavigate = (tab: string) => navigateTo(tab);
  
  const onSelectSeries = (series: Series) => {
    navigateTo('search', series, null);
  };

  const onSelectVolume = (volume: Volume) => {
     // Ensure we have the series context if possible, usually passed from SeriesDetail
     const currentSeries = currentState.series;
     if (currentSeries) {
         navigateTo('search', currentSeries, volume);
     }
  };

  const onVolumeBack = () => {
      handleBack(); // Pops volume, returns to Series
  };

  const onSeriesBack = () => {
      handleBack(); // Pops series, returns to List
  };

  // Helper for Library to jump straight to detail
  const handleLibraryBookClick = (bookTitle: string, author: string, cover: string) => {
      const mockSeries: Series = {
          id: 'lib-series-1',
          title: bookTitle,
          author: author,
          coverUrl: cover,
          description: 'Description loaded from library...',
          genre: 'Fantasy',
          rating: 5.0,
          volumesCount: 1,
          status: 'Ongoing',
          lastUpdated: 'Hoy',
          volumes: []
      };
      const mockVolume: Volume = {
          id: 'lib-vol-1',
          seriesId: 'lib-series-1',
          title: bookTitle,
          volumeNumber: 1,
          coverUrl: cover,
          publishedDate: '2023',
          pages: 300,
          format: 'EPUB',
          rating: 5.0
      };
      navigateTo('search', mockSeries, mockVolume);
  };

  const handleSearchNavigation = (term: string, type?: string) => {
      // In a real app, pass search params. For now, go to search root.
      navigateTo('search');
  };


  // Render Logic
  const renderContent = () => {
    const { tab, series, volume } = currentState;

    if (volume && series) {
      return (
        <BookDetail 
          volume={volume} 
          series={series} 
          onBack={onVolumeBack}
          onSearch={handleSearchNavigation}
          onNavigate={onNavigate}
        />
      );
    }
    
    if (series) {
      return (
        <SeriesDetail 
          series={series} 
          onBack={onSeriesBack} 
          onSelectVolume={onSelectVolume}
        />
      );
    }

    switch (tab) {
      case 'dashboard':
        return <Dashboard onNavigate={onNavigate} />;
      case 'search':
        return <Search onSelectSeries={onSelectSeries} onNavigate={onNavigate} />;
      case 'requests':
        return <RequestBook onNavigate={onNavigate} />;
      case 'admin':
        return <Admin onNavigate={onNavigate} />;
      case 'settings':
        return <Settings onNavigate={onNavigate} />;
      case 'library':
        return <Library onNavigate={onNavigate} onSelectBook={handleLibraryBookClick} />;
      default:
        return <Dashboard onNavigate={onNavigate} />;
    }
  };

  if (isReading) {
    return <Reader onClose={() => setIsReading(false)} />;
  }

  return (
    <Layout 
      activeTab={currentState.tab} 
      onTabChange={onNavigate}
      showMobileBottomNav={false}
    >
      {renderContent()}
    </Layout>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <TelegramProvider>
         <AppContent />
      </TelegramProvider>
    </ThemeProvider>
  );
};

export default App;