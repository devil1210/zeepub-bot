import React, { useEffect, Suspense, useCallback } from 'react';
import { MemoryRouter, Routes, Route, useNavigate, useLocation, useParams, Navigate, NavigationType, useNavigationType } from 'react-router-dom';
import { ThemeProvider } from '@shared/contexts/ThemeContext';
import { TelegramProvider, useTelegram } from '@shared/contexts/TelegramContext';
import { NavigationProvider, useNavigation } from '@shared/contexts/NavigationContext';
import { Layout } from '@components/Layout';
import { ErrorBoundary } from '@components/ErrorBoundary';

// Lazy loading pages for performance optimization
const Dashboard = React.lazy(() => import('@features/dashboard/pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Search = React.lazy(() => import('@features/search/pages/Search').then(m => ({ default: m.Search })));
const Admin = React.lazy(() => import('@features/admin/pages/Admin').then(m => ({ default: m.Admin })));
const Reader = React.lazy(() => import('@features/reader/pages/Reader').then(m => ({ default: m.Reader })));
const Settings = React.lazy(() => import('@features/settings/pages/Settings').then(m => ({ default: m.Settings })));
const RequestBook = React.lazy(() => import('@features/dashboard/pages/RequestBook').then(m => ({ default: m.RequestBook })));
const Library = React.lazy(() => import('@features/library/pages/Library').then(m => ({ default: m.Library })));
const Downloads = React.lazy(() => import('@features/library/pages/Downloads').then(m => ({ default: m.Downloads })));
const UploadEpub = React.lazy(() => import('@features/upload/pages/Upload').then(m => ({ default: m.UploadEpub })));
const AIHub = React.lazy(() => import('@features/ai/pages/AIHub').then(m => ({ default: m.AIHub })));
const BookDetailById = React.lazy(() => import('@features/book/pages/BookDetailById').then(m => ({ default: m.BookDetailById })));
const TemplateEditorPage = React.lazy(() => import('@features/publisher/pages/TemplateEditorPage').then(m => ({ default: m.TemplateEditorPage })));

import { Series, Volume } from '@shared/types';
import { LoginGate } from '@components/LoginGate';
import { registerServiceWorker } from '@shared/utils/serviceWorker';

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

// Custom hook to bridge legacy onNavigate prop to React Router
const useLegacyNavigation = () => {
  const navigate = useNavigate();

  return useCallback((tab: string, series?: Series | null, volume?: Volume | null) => {
    const performNavigation = () => {
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

    // Use View Transitions API if available
    if (document.startViewTransition) {
      document.startViewTransition(() => performNavigation());
    } else {
      performNavigation();
    }
  }, [navigate]);
};

/**
 * Handles Telegram Back Button integration with internal history stack
 */
const TelegramNavigationHandler: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { webApp } = useTelegram();
  const { state: navState } = useNavigation();

  useEffect(() => {
    if (!webApp?.BackButton) return;

    const handleBack = () => {
      if (navState.historyStack.length > 1) {
        navigate(-1);
      } else {
        if (location.pathname !== '/') {
          navigate('/');
        }
      }
    };

    const rootPaths = ['/', '/search', '/library', '/requests', '/settings', '/downloads', '/admin'];
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

// Syncs MemoryRouter events with our internal stack context
const HistoryTracker: React.FC = () => {
  const location = useLocation();
  const navType = useNavigationType();
  const { pushHistory, popHistory } = useNavigation();

  useEffect(() => {
    if (navType === NavigationType.Push) {
      pushHistory(location.pathname);
    } else if (navType === NavigationType.Pop) {
      popHistory();
    } else if (navType === NavigationType.Replace) {
      popHistory();
      pushHistory(location.pathname);
    }
  }, [location.pathname, navType]);

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
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<PageWrapper Component={Dashboard} />} />
            <Route path="/search" element={<Search onNavigate={onNavigate} onSelectSeries={(s) => onNavigate('search', s)} />} />
            <Route path="/library" element={
              <Library
                onNavigate={onNavigate}
                onSelectBook={(bookId) => {
                  onNavigate(`book:${bookId}`);
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
            <Route path="/admin/templates/new" element={
              isAdmin ? <PageWrapper Component={TemplateEditorPage} /> : <Navigate to="/" replace />
            } />
            <Route path="/admin/templates/:id" element={
              isAdmin ? <PageWrapper Component={TemplateEditorPage} /> : <Navigate to="/" replace />
            } />

            {/* Details Routes - All consolidated to use IDs from URL */}
            <Route path="/book/:bookId" element={<UniversalDetailWrapper />} />
            <Route path="/series/:seriesId" element={<UniversalDetailWrapper />} />
            <Route path="/read/:seriesId/:volumeId" element={<UniversalDetailWrapper />} />
            <Route path="/reader" element={<Reader onClose={() => onNavigate('dashboard')} />} />
          </Routes>
        </Suspense>
      </Layout>
    </>
  );
};

// Universal wrapper for any type of detail (Book or Series)
const UniversalDetailWrapper = () => {
  const navigate = useNavigate();
  const onNavigate = useLegacyNavigation();
  const params = useParams<{
    bookId?: string;
    seriesId?: string;
    volumeId?: string;
  }>();

  // Precedence: explicit bookId > volumeId (for /read) > seriesId
  const id = params.bookId ?? params.volumeId ?? params.seriesId ?? '';

  return (
    <BookDetailById
      bookId={id}
      onBack={() => navigate(-1)}
      onNavigate={onNavigate}
    />
  );
};


const AppContentWrapper: React.FC = () => {
  return (
    <NavigationProvider>
      <MemoryRouter>
        <AppContent />
      </MemoryRouter>
    </NavigationProvider>
  );
}

const App: React.FC = () => {
  // Register Service Worker on mount
  useEffect(() => {
    registerServiceWorker().then((registered) => {
      if (registered) {
        console.log('✅ Service Worker registered for offline support');
      }
    });
  }, []);

  return (
    <ErrorBoundary>
      <ThemeProvider>
        <TelegramProvider>
          <AppContentWrapper />
        </TelegramProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
