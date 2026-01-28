import React, { useEffect } from 'react';
import { MemoryRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { TelegramProvider, useTelegram } from './contexts/TelegramContext';
import { NavigationProvider, useNavigation } from './contexts/NavigationContext';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Dashboard } from './pages/Dashboard';
import { Search } from './pages/Search';
import { Admin } from './pages/Admin';
import { Reader } from './pages/Reader';
import { Settings } from './pages/Settings';
import { SeriesDetail } from './pages/SeriesDetail';
import { BookDetail } from './pages/BookDetail';
import { BookDetailById } from './pages/BookDetailById';
import { RequestBook } from './pages/RequestBook';
import { Library } from './pages/Library';
import { Downloads } from './pages/Downloads';
import { UploadEpub } from './pages/Upload';
import { AIHub } from './pages/AIHub';
import { Series, Volume, Book } from './types';

// Custom hook to bridge legacy onNavigate prop to React Router
const useLegacyNavigation = () => {
  const navigate = useNavigate();

  return (tab: string, series?: Series | null, volume?: Volume | null) => {
    // Handle 'book:ID' shortcut
    if (tab.startsWith('book:')) {
      const bookId = tab.split(':')[1];
      navigate(`/book/${bookId}`);
      return;
    }

    // Handle Volume Detail (BookDetail)
    if (volume && series) {
      navigate(`/read/${series.id}/${volume.id}`, { state: { series, volume } });
      return;
    }

    // Handle Series Detail
    if (series) {
      navigate(`/series/${series.id}`, { state: { series } });
      return;
    }

    // Handle Main Tabs
    const path = tab === 'dashboard' ? '/' : `/${tab}`;
    navigate(path);
  };
};

/**
 * Handles Telegram Back Button integration with internal history stack
 */
const TelegramNavigationHandler: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { webApp } = useTelegram();
  const { state: navState, popHistory } = useNavigation();

  useEffect(() => {
    if (!webApp?.BackButton) return;

    const handleBack = () => {
      // Check internal stack length
      if (navState.historyStack.length > 1) {
        navigate(-1);
        // popHistory is handled by the HistoryTracker via POP event, 
        // but if we trigger it programmatically, we should ensure consistency.
        // Actually, let HistoryTracker handle state updates based on location changes.
      } else {
        // Fallback: If we are deep but stack is empty (reload), go home
        if (location.pathname !== '/') {
          navigate('/');
        } else {
          // Close app? Or do nothing?
          // webApp.close(); 
        }
      }
    };

    const rootPaths = ['/', '/search', '/library', '/requests', '/settings', '/downloads', '/admin'];
    // We consider it "root" if stack is 1 AND we are at a known root path.
    // Or if stack is > 1 we definitely show Back button.
    const isRoot = navState.historyStack.length <= 1 && rootPaths.includes(location.pathname);

    if (isRoot) {
      webApp.BackButton.hide();
    } else {
      webApp.BackButton.show();
      webApp.BackButton.onClick(handleBack);
    }

    return () => {
      webApp.BackButton.offClick(handleBack);
    };
  }, [webApp, location.pathname, navState.historyStack.length, navigate]);

  return null;
};

import { NavigationType, useNavigationType } from 'react-router-dom';

// Syncs MemoryRouter events with our internal stack context
const HistoryTracker: React.FC = () => {
  const location = useLocation();
  const navType = useNavigationType();
  const { pushHistory, popHistory, resetHistory } = useNavigation();

  useEffect(() => {
    if (navType === NavigationType.Push) {
      pushHistory(location.pathname);
    } else if (navType === NavigationType.Pop) {
      popHistory();
    } else if (navType === NavigationType.Replace) {
      // Replace: usually swaps the current top. 
      // We'll simplisticly pop then push, or just do nothing if it's strictly replacing content.
      // For now, let's treat it as a no-op on stack size, but update top? 
      // Simply: do nothing on stack size, assume same depth.
    }
  }, [location.pathname, navType]);

  // Reset on mount if at root? No, context persists.
  return null;
};

// Wrapper Component to inject legacy navigation prop
const PageWrapper: React.FC<{ Component: React.FC<any>; props?: any }> = ({ Component, props }) => {
  const onNavigate = useLegacyNavigation();
  return <Component onNavigate={onNavigate} {...props} />;
};

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    const main = document.querySelector('main');
    if (main) {
      main.scrollTo(0, 0);
    } else {
      window.scrollTo(0, 0);
    }
  }, [pathname]);
  return null;
};

const AppContent: React.FC = () => {
  const onNavigate = useLegacyNavigation();
  const location = useLocation();
  const { isAdmin } = useTelegram();

  // Determine active tab for Layout
  const getActiveTab = (pathname: string) => {
    if (pathname === '/') return 'dashboard';
    return pathname.substring(1).split('/')[0]; // e.g. /search -> search
  };

  return (
    <>
      <ScrollToTop />
      <HistoryTracker />
      <TelegramNavigationHandler />
      <Layout activeTab={getActiveTab(location.pathname)} onTabChange={onNavigate}>
        <Routes>
          <Route path="/" element={<PageWrapper Component={Dashboard} />} />
          <Route path="/search" element={<Search onNavigate={onNavigate} onSelectSeries={(s) => onNavigate('search', s)} />} />
          <Route path="/library" element={
            <Library
              onNavigate={onNavigate}
              onSelectBook={(title, author, cover) => {
                // Mock conversion for library click
                // In real app, maybe Library should return Series object?
                const mockSeries: Series = {
                  id: 'lib-series-1',
                  title: title,
                  author: author,
                  coverUrl: cover,
                  description: 'Description loaded from library...',
                  genre: 'Fantasy',
                  rating: 0,
                  volumesCount: 1,
                  status: 'Ongoing',
                  lastUpdated: 'Hoy',
                  volumes: []
                };
                const mockVolume: Volume = {
                  id: 'lib-vol-1',
                  seriesId: 'lib-series-1',
                  title: title,
                  volumeNumber: 1,
                  coverUrl: cover,
                  publishedDate: '2023',
                  pages: 300,
                  format: 'EPUB',
                  rating: 0
                };
                onNavigate('search', mockSeries, mockVolume);
              }}
            />
          } />
          <Route path="/requests" element={<PageWrapper Component={RequestBook} />} />
          <Route path="/settings" element={<PageWrapper Component={Settings} />} />
          <Route path="/downloads" element={
            <Downloads
              onNavigate={onNavigate}
              onBookClick={() => onNavigate('search')}
            />
          } />
          <Route path="/upload" element={<PageWrapper Component={UploadEpub} />} />
          <Route path="/ai" element={
            isAdmin ? <PageWrapper Component={AIHub} /> : <Navigate to="/" replace />
          } />
          <Route path="/admin" element={
            isAdmin ? <PageWrapper Component={Admin} /> : <Navigate to="/" replace />
          } />

          {/* Details Routes */}
          <Route path="/book/:bookId" element={<BookDetailByIdWrapper />} />
          <Route path="/series/:seriesId" element={<SeriesDetailWrapper />} />
          <Route path="/read/:seriesId/:volumeId" element={<BookDetailWrapper />} />
          <Route path="/reader" element={<Reader onClose={() => onNavigate('dashboard')} />} />
        </Routes>
      </Layout>
    </>
  );
};

// Wrappers to handle params and state
const BookDetailByIdWrapper = () => {
  const navigate = useNavigate();
  const onNavigate = useLegacyNavigation();
  const { pathname } = useLocation();
  const bookId = pathname.split('/')[2];

  return <BookDetailById bookId={bookId} onBack={() => navigate(-1)} onNavigate={onNavigate} />;
};

const SeriesDetailWrapper = () => {
  const navigate = useNavigate();
  const onNavigate = useLegacyNavigation();
  const { setSearchTerm, state: navState } = useNavigation();
  const location = useLocation();
  const pathname = location.pathname;
  const series = location.state?.series as Series;

  // Extract ID if missing state
  const seriesId = series?._id || series?.id || pathname.split('/')[2];

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    onNavigate('search');
  };

  const handleBack = () => {
    if (navState.historyStack.length > 1) {
      navigate(-1);
      return;
    }

    navigate('/search');
  };

  const handleSelectVolume = (vol: Volume, selectedSeries?: Series) => {
    const targetSeries = selectedSeries || series || ({ id: seriesId } as Series);
    const targetSeriesId = targetSeries?.id || seriesId;

    if (!targetSeriesId || !vol?.id) {
      return;
    }

    const route = `/read/${targetSeriesId}/${vol.id}`;
    navigate(route, {
      state: { series: targetSeries, volume: vol }
    });
  };

  return (
    <SeriesDetail
      series={series || ({ id: seriesId } as any)}
      onBack={handleBack}
      onSelectVolume={handleSelectVolume}
      onSearch={handleSearch}
    />
  );
};

const BookDetailWrapper = () => {
  const navigate = useNavigate();
  const onNavigate = useLegacyNavigation();
  const { setSearchTerm, state: navState } = useNavigation();
  const location = useLocation();
  const pathname = location.pathname;
  const { series, volume } = location.state || {}; // Cast as needed

  // Extract IDs from pathname if state is missing
  const parts = pathname.split('/');
  const volumeId = volume?.id || parts[3];

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    onNavigate('search');
  };

  const seriesId = series?.id || parts[2];

  const handleBack = () => {
    if (navState.historyStack.length > 1) {
      navigate(-1);
      return;
    }

    if (seriesId) {
      navigate(`/series/${seriesId}`, { state: { series } });
      return;
    }

    navigate('/search');
  };

  return (
    <BookDetail
      series={series}
      volume={volume}
      bookId={volumeId}
      onBack={handleBack}
      onSearch={handleSearch}
      onNavigate={onNavigate}
    />
  );
};

const App: React.FC = () => {

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <TelegramProvider>
          <NavigationProvider>
            <MemoryRouter>
              <AppContent />
            </MemoryRouter>
          </NavigationProvider>
        </TelegramProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
