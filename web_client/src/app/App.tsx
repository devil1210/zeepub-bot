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
const FansubDetailPage = React.lazy(() => import('@features/publisher/pages/FansubDetailPage').then(m => ({ default: m.FansubDetailPage })));
const SeriesDetailPage = React.lazy(() => import('@features/admin/pages/SeriesDetailPage').then(m => ({ default: m.SeriesDetailPage })));
const SeriesManagerPage = React.lazy(() => import('@features/admin/pages/SeriesManagerPage').then(m => ({ default: m.SeriesManagerPage })));

// V2 Editorial Console Pages
const EditorialLayout = React.lazy(() => import('@features/editorial/layouts/EditorialLayout').then(m => ({ default: m.EditorialLayout })));
const EditorialDashboard = React.lazy(() => import('@features/editorial/pages/EditorialDashboard').then(m => ({ default: m.EditorialDashboard })));
const EditorialLibrary = React.lazy(() => import('@features/editorial/pages/EditorialLibrary').then(m => ({ default: m.EditorialLibrary })));
const EditorialSeries = React.lazy(() => import('@features/editorial/pages/EditorialSeries').then(m => ({ default: m.EditorialSeries })));
const EditorialVolumes = React.lazy(() => import('@features/editorial/pages/EditorialVolumes').then(m => ({ default: m.EditorialVolumes })));
const EditorialCalendar = React.lazy(() => import('@features/editorial/pages/EditorialCalendar').then(m => ({ default: m.EditorialCalendar })));
const EditorialPosts = React.lazy(() => import('@features/editorial/pages/EditorialPosts').then(m => ({ default: m.EditorialPosts })));
const EditorialTemplates = React.lazy(() => import('@features/editorial/pages/EditorialTemplates').then(m => ({ default: m.EditorialTemplates })));
const EditorialUsers = React.lazy(() => import('@features/editorial/pages/EditorialUsers').then(m => ({ default: m.EditorialUsers })));
const EditorialSettings = React.lazy(() => import('@features/editorial/pages/EditorialSettings').then(m => ({ default: m.EditorialSettings })));
const EditorialLegacyTools = React.lazy(() => import('@features/editorial/pages/EditorialLegacyTools').then(m => ({ default: m.EditorialLegacyTools })));

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

      if (tab === 'admin-datagrid' || tab === 'series-manager') {
        navigate('/admin/series-manager');
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

    const rootPaths = ['/', '/search', '/library', '/requests', '/settings', '/downloads', '/admin', '/app-v2'];
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

const ProtectedAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAdmin, ready, status } = useTelegram();

  if (!ready || (status === null && typeof window !== 'undefined' && (window as any).Telegram?.WebApp?.initData)) {
    return <PageLoader />;
  }

  if (!isAdmin) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

const AppContent: React.FC = () => {
  const onNavigate = useLegacyNavigation();
  const location = useLocation();
  const { user, status, ready } = useTelegram();

  // Check if current route is part of v2 Editorial Console
  const isV2 = location.pathname.startsWith('/app-v2');

  // Determine active tab for Layout
  const getActiveTab = (pathname: string) => {
    if (pathname === '/') return 'dashboard';
    return pathname.substring(1).split('/')[0]; // e.g. /search -> search
  };

  if (!ready) {
    return <PageLoader />;
  }

  if (isV2) {
    return (
      <>
        <ScrollToTop />
        <HistoryTracker />
        <TelegramNavigationHandler />
        <Suspense fallback={<PageLoader />}>
          <EditorialLayout>
            <Routes>
              <Route path="/app-v2" element={<EditorialDashboard />} />
              <Route path="/app-v2/library" element={<EditorialLibrary />} />
              <Route path="/app-v2/series" element={<EditorialSeries />} />
              <Route path="/app-v2/volumes" element={<EditorialVolumes />} />
              <Route path="/app-v2/calendar" element={<EditorialCalendar />} />
              <Route path="/app-v2/posts" element={<EditorialPosts />} />
              <Route path="/app-v2/templates" element={<EditorialTemplates />} />
              <Route path="/app-v2/users" element={
                <ProtectedAdminRoute>
                  <EditorialUsers />
                </ProtectedAdminRoute>
              } />
              <Route path="/app-v2/settings" element={<EditorialSettings />} />
              <Route path="/app-v2/legacy" element={<EditorialLegacyTools />} />
              <Route path="/app-v2/*" element={<Navigate to="/app-v2" replace />} />
            </Routes>
          </EditorialLayout>
        </Suspense>
      </>
    );
  }

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
              <ProtectedAdminRoute>
                <PageWrapper Component={AIHub} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={Admin} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin/templates/new" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={TemplateEditorPage} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin/templates/:id" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={TemplateEditorPage} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin/fansubs/:id" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={FansubDetailPage} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin/series/:id" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={SeriesDetailPage} />
              </ProtectedAdminRoute>
            } />
            <Route path="/admin/series-manager" element={
              <ProtectedAdminRoute>
                <PageWrapper Component={SeriesManagerPage} />
              </ProtectedAdminRoute>
            } />

            {/* Details Routes - All consolidated to use IDs from URL */}
            <Route path="/book/:bookId" element={<UniversalDetailWrapper />} />
            <Route path="/series/:seriesId" element={<UniversalDetailWrapper />} />
            <Route path="/read/:seriesId/:volumeId" element={<UniversalDetailWrapper />} />
            <Route path="/reader" element={<Reader onClose={() => onNavigate('dashboard')} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
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

  let id = '';
  if (params.volumeId) {
    id = params.volumeId;
  } else if (params.seriesId) {
    id = params.seriesId.startsWith('series_') ? params.seriesId : `series_${params.seriesId}`;
  } else if (params.bookId) {
    id = params.bookId;
  }

  return (
    <BookDetailById
      bookId={id}
      onBack={() => navigate(-1)}
      onNavigate={onNavigate}
    />
  );
};


const initialPath = typeof window !== 'undefined' ? (window.location.pathname + window.location.search) : '/';

const AppContentWrapper: React.FC = () => {
  return (
    <NavigationProvider>
      <MemoryRouter initialEntries={[initialPath]}>
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
