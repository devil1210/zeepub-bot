import React, { useEffect } from 'react';
import { MemoryRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { TelegramProvider, useTelegram } from './contexts/TelegramContext';
import { SearchNavProvider, useSearchNav } from './contexts/SearchNavContext';
import { Layout } from './components/Layout';
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
 * Handles Telegram Back Button integration with React Router
 */
const TelegramNavigationHandler: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { webApp } = useTelegram();

  useEffect(() => {
    if (webApp?.BackButton) {
      // Show back button if we are not at root tabs
      const rootPaths = ['/', '/search', '/library', '/requests', '/settings', '/downloads', '/admin'];
      const isRoot = rootPaths.includes(location.pathname);

      if (!isRoot) {
        webApp.BackButton.show();
        webApp.BackButton.onClick(() => navigate(-1));
      } else {
        webApp.BackButton.hide();
      }
    }

    return () => {
      if (webApp?.BackButton) {
        webApp.BackButton.offClick(() => navigate(-1));
      }
    };
  }, [webApp, location, navigate]);

  return null;
};

// Wrapper Component to inject legacy navigation prop
const PageWrapper: React.FC<{ Component: React.FC<any>; props?: any }> = ({ Component, props }) => {
  const onNavigate = useLegacyNavigation();
  return <Component onNavigate={onNavigate} {...props} />;
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
                  rating: 5.0,
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
                  rating: 5.0
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
  const { setSearchTerm } = useSearchNav();
  const location = useLocation();
  const series = location.state?.series as Series;

  if (!series) return <Navigate to="/" />; // Fallback if no state

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    onNavigate('search');
  };

  return (
    <SeriesDetail
      series={series}
      onBack={() => navigate(-1)}
      onSelectVolume={(vol) => onNavigate('search', series, vol)}
      onSearch={handleSearch}
    />
  );
};

const BookDetailWrapper = () => {
  const navigate = useNavigate();
  const onNavigate = useLegacyNavigation();
  const { setSearchTerm } = useSearchNav();
  const location = useLocation();
  const { series, volume } = location.state || {}; // Cast as needed

  if (!series || !volume) return <Navigate to="/" />;

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    onNavigate('search');
  };

  return (
    <BookDetail
      series={series}
      volume={volume}
      onBack={() => navigate(-1)}
      onSearch={handleSearch}
      onNavigate={onNavigate}
    />
  );
};

const App: React.FC = () => {

  return (
    <ThemeProvider>
      <TelegramProvider>
        <SearchNavProvider>
          <MemoryRouter>
            <AppContent />
          </MemoryRouter>
        </SearchNavProvider>
      </TelegramProvider>
    </ThemeProvider>
  );
};

export default App;