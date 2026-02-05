import React, { useEffect, Suspense } from 'react';
import { MemoryRouter, Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';
import { TelegramProvider, useTelegram } from './contexts/TelegramContext';
import { NavigationProvider, useNavigation } from './contexts/NavigationContext';
import { Layout } from './components/Layout';
import { ErrorBoundary } from './components/ErrorBoundary';

// Lazy loading pages for performance optimization
const Dashboard = React.lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })));
const Search = React.lazy(() => import('./pages/Search').then(m => ({ default: m.Search })));
const Admin = React.lazy(() => import('./pages/Admin').then(m => ({ default: m.Admin })));
const Reader = React.lazy(() => import('./pages/Reader').then(m => ({ default: m.Reader })));
const Settings = React.lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const RequestBook = React.lazy(() => import('./pages/RequestBook').then(m => ({ default: m.RequestBook })));
const Library = React.lazy(() => import('./pages/Library').then(m => ({ default: m.Library })));
const Downloads = React.lazy(() => import('./pages/Downloads').then(m => ({ default: m.Downloads })));
const UploadEpub = React.lazy(() => import('./pages/Upload').then(m => ({ default: m.UploadEpub })));
const AIHub = React.lazy(() => import('./pages/AIHub').then(m => ({ default: m.AIHub })));
const BookDetailById = React.lazy(() => import('./pages/BookDetailById').then(m => ({ default: m.BookDetailById })));

import { Series, Volume } from './types';
import { LoginGate } from './components/LoginGate';
import { registerServiceWorker } from './src/utils/serviceWorker';

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[60vh]">
    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

// Custom hook to bridge legacy onNavigate prop to React Router
const useLegacyNavigation = () => {
  const navigate = useNavigate();

  return (tab: string, series?: Series | null, volume?: Volume | null) => {
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
  const { pathname } = useLocation();

  // Extract ID: 
  // /book/ID -> parts[2]
  // /series/ID -> parts[2]
  // /read/SID/VID -> parts[3] (prefer volume ID for fetching)
  const parts = pathname.split('/');
  const id = parts[parts.length - 1]; // Current logic: take the last part as primary ID

  return <BookDetailById bookId={id} onBack={() => navigate(-1)} onNavigate={onNavigate} />;
};


const AppContentWrapper: React.FC = () => {
  const { user, ready } = useTelegram();

  // If not ready, show nothing or a loader
  if (!ready) return null;

  // If no user is present (not in Telegram and no Supabase session), block access
  if (!user) {
    return <LoginGate />;
  }

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
