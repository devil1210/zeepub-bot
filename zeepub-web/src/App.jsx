import React, { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import { fetchFeed, searchBooks, fetchConfig, downloadBook, prepareFacebookPost, publishFacebookPost } from './api';
import BookListItem from './components/BookListItem';
import NavigationListItem from './components/NavigationListItem';
import SearchBar from './components/SearchBar';

const ITEMS_PER_PAGE = 20;

const useDebounce = (callback, delay) => {
  const callbackRef = React.useRef(callback);
  React.useLayoutEffect(() => {
    callbackRef.current = callback;
  });
  return React.useMemo(
    () => (...args) => {
      if (window.debounceTimer) clearTimeout(window.debounceTimer);
      window.debounceTimer = setTimeout(() => callbackRef.current(...args), delay);
    },
    [delay]
  );
};

function App() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [navigationStack, setNavigationStack] = useState([]);
  const [currentTitle, setCurrentTitle] = useState('ZeePub Mini');
  const [currentPage, setCurrentPage] = useState(1);
  const [nextPageUrl, setNextPageUrl] = useState(null);
  const [prevPageUrl, setPrevPageUrl] = useState(null);

  // Admin State
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminConfig, setAdminConfig] = useState(null);
  const [adminMode, setAdminMode] = useState(false); // true = Evil/Admin Mode
  const [selectedDestination, setSelectedDestination] = useState(null); // null = default (user)
  const [isFacebookPublisher, setIsFacebookPublisher] = useState(false);

  const scrollContainerRef = React.useRef(null);

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    WebApp.BackButton.onClick(() => handleBack());

    // Initial load
    const init = async () => {
      const uid = WebApp.initDataUnsafe?.user?.id;
      const config = await fetchConfig(uid);

      if (config) {
        setAdminConfig(config);
      }

      if (config && config.is_admin) {
        setIsAdmin(true);
        // Default destination to "me" (null in backend logic implies user_id, but we can be explicit if needed)
        // config.destinations[0] should be "Aquí"
        if (config.destinations && config.destinations.length > 0) {
          setSelectedDestination(config.destinations[0].id);
        }
      }
      if (config && config.is_facebook_publisher) {
        setIsFacebookPublisher(true);
        // If not admin but publisher, also set default destination if available
        if (!config.is_admin && config.destinations && config.destinations.length > 0) {
          setSelectedDestination(config.destinations[0].id);
        }
      }
      loadFeed();
    };
    init();
  }, []);

  const loadFeed = async (url = null, depth = 0) => {
    setLoading(true);
    setError(null);
    // Reset client-side page only if loading a new URL (not just searching)
    setCurrentPage(1);
    if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;

    const uid = WebApp.initDataUnsafe?.user?.id;

    try {
      // Determine URL to load
      let targetUrl = url;
      if (!targetUrl && adminMode && adminConfig?.admin_root_url) {
        targetUrl = adminConfig.admin_root_url;
      }

      const data = await fetchFeed(targetUrl, uid);
      if (data && data.entries) {

        // Auto-navegación DESACTIVADA para corregir bug de categorías
        // if (depth < 2 && data.entries.length > 0) { ... }

        setItems(data.entries);
        if (data.title) setCurrentTitle(data.title);

        // Capture pagination links - Relaxed check for OPDS spec
        const nextLink = data.links?.find(l => l.rel?.includes('next'));
        const prevLink = data.links?.find(l => l.rel?.includes('previous') || l.rel?.includes('prev'));

        setNextPageUrl(nextLink ? nextLink.href : null);
        setPrevPageUrl(prevLink ? prevLink.href : null);

      } else {
        setError('No se pudieron cargar los datos.');
      }
    } catch (err) {
      if (err.message === 'ACCESS_DENIED') {
        setError('ACCESS_DENIED');
      } else {
        setError('Error de conexión.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      loadFeed();
      setNavigationStack([]);
      WebApp.BackButton.hide();
      return;
    }

    setLoading(true);
    setCurrentPage(1);
    if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    try {
      const data = await searchBooks(query);
      if (data && data.entries) {
        setItems(data.entries);
        setCurrentTitle('Resultados de búsqueda');
      } else {
        setItems([]);
      }
    } catch (err) {
      console.error(err);
      setError('Error en la búsqueda.');
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = useDebounce(handleSearch, 500);

  const handleNavigate = (item) => {
    const navLink = item.links?.find(l =>
      l.rel === 'subsection' || l.type?.includes('opds-catalog')
    );

    if (navLink && navLink.href) {
      setNavigationStack(prev => [...prev, {
        items,
        title: currentTitle,
        page: currentPage,
        nextPageUrl, // Save next page URL
        prevPageUrl  // Save prev page URL
      }]);
      WebApp.BackButton.show();
      loadFeed(navLink.href);
    }
  };

  const handleBack = () => {
    if (navigationStack.length > 0) {
      const previous = navigationStack[navigationStack.length - 1];
      setItems(previous.items);
      setCurrentTitle(previous.title);
      setCurrentPage(previous.page || 1);
      setNextPageUrl(previous.nextPageUrl || null); // Restore next page URL
      setPrevPageUrl(previous.prevPageUrl || null); // Restore prev page URL
      setNavigationStack(prev => prev.slice(0, -1));
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;

      if (navigationStack.length === 1) {
        WebApp.BackButton.hide();
      }
    }
  };

  const handleDownload = async (book) => {
    // Mostrar confirmación antes de descargar
    const destName = adminConfig?.destinations?.find(d => d.id === selectedDestination)?.name || 'tu chat';
    const action = selectedDestination && selectedDestination !== 'me' ? `Publicar en ${destName}` : 'Descargar';

    WebApp.showConfirm(
      `¿Deseas ${action} "${book.title}"?`,
      async (confirmed) => {
        if (confirmed) {
          try {
            const actionMsg = action === 'Descargar' ? 'descarga' : action.toLowerCase();
            WebApp.showAlert(`Iniciando ${actionMsg}...`);

            // Pass selectedDestination if it's not "me"
            const target = selectedDestination === 'me' ? null : selectedDestination;
            const success = await downloadBook(book, target);

            if (success) {
              WebApp.showAlert('✅ Operación iniciada. Revisa el chat.');
            } else {
              WebApp.showAlert('❌ Error al iniciar.');
            }
          } catch (error) {
            console.error('Error downloading:', error);
            WebApp.showAlert('❌ Error de conexión.');
          }
        }
      }
    );
  };

  const handleFacebookPost = async (book) => {
    WebApp.showAlert('⏳ Preparando post...');
    const data = await prepareFacebookPost(book);

    if (!data) {
      WebApp.showAlert('❌ Error al preparar post.');
      return;
    }

    WebApp.showPopup({
      title: 'Vista Previa Facebook',
      message: data.caption.replace(/<[^>]*>/g, ''), // Strip HTML for popup
      buttons: [
        { id: 'publish', type: 'default', text: '🚀 Publicar' },
        { id: 'cancel', type: 'destructive', text: 'Cancelar' }
      ]
    }, async (btnId) => {
      if (btnId === 'publish') {
        WebApp.showAlert('⏳ Publicando...');
        const res = await publishFacebookPost(data.caption, data.cover_url);
        if (res && res.success) {
          WebApp.showAlert('✅ Publicado exitosamente!');
        } else {
          WebApp.showAlert('❌ Error al publicar.');
        }
      }
    });
  };

  const isNavigationItem = (item) => {
    return item.links?.some(l =>
      l.rel === 'subsection' ||
      (l.type?.includes('opds-catalog') && l.type?.includes('navigation'))
    );
  };

  const isBook = (item) => {
    return item.links?.some(l =>
      l.rel === 'http://opds-spec.org/acquisition' ||
      l.type?.includes('epub')
    );
  };

  // Paginación para todos los items
  const totalPages = Math.max(1, Math.ceil(items.length / ITEMS_PER_PAGE));
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  const currentItems = items.slice(startIndex, endIndex);

  const goToNextPage = () => {
    if (currentPage < totalPages) {
      // Client-side next page
      setCurrentPage(prev => prev + 1);
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    } else if (nextPageUrl) {
      // Server-side next page
      // Pass depth=2 to prevent auto-navigation logic from triggering on the new page results
      loadFeed(nextPageUrl, 2);
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    }
  };

  const goToPrevPage = () => {
    if (currentPage > 1) {
      // Client-side prev page
      setCurrentPage(prev => prev - 1);
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    } else if (prevPageUrl) {
      // Server-side prev page
      // Pass depth=2 to prevent auto-navigation logic
      loadFeed(prevPageUrl, 2);
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#17212b] text-white overflow-hidden font-sans">

      <header className="flex-none flex flex-col items-center pt-10 pb-6 bg-[#17212b]">
        {/* Profile Avatar */}
        <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-3xl shadow-lg mb-4 overflow-hidden border border-white/5">
          <span>📚</span>
        </div>

        {/* Title & Subtitle */}
        <h1 className="text-xl font-bold mb-1 tracking-tight">ZeePub</h1>
        <p className="text-[#7f8c99] text-[13px] text-center px-10 mb-6 leading-tight">
          ZeePub es el bot definitivo para gestionar y leer tus libros favoritos directamente en Telegram.
          <br />
          <span className="text-[#2481cc] font-medium cursor-pointer hover:underline text-[11px] mt-2 block">Learn more ˃</span>
        </p>

        <SearchBar onSearch={debouncedSearch} />

        {/* Admin Controls - Estilo Integrado y Sutil */}
        {(isAdmin || isFacebookPublisher) && (
          <div className="w-full max-w-sm px-6 mb-2">
            <div className="bg-[#242f3d]/40 rounded-full py-1.5 px-4 flex items-center justify-between">
              <span className="text-[10px] font-bold text-[#7f8c99] uppercase tracking-widest">Modo Avanzado</span>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => {
                    const newMode = !adminMode;
                    setAdminMode(newMode);
                    setNavigationStack([]);
                    WebApp.BackButton.hide();
                    const url = newMode && adminConfig ? adminConfig.admin_root_url : null;
                    loadFeed(url);
                  }}
                  className={`w-8 h-4 rounded-full relative transition-colors duration-200 focus:outline-none ${adminMode ? 'bg-[#2481cc]' : 'bg-[#17212b]'}`}
                >
                  <div className={`absolute top-0.5 left-0.5 w-3 h-3 bg-white rounded-full transition-transform duration-200 transform ${adminMode ? 'translate-x-4' : 'translate-x-0'}`} />
                </button>
                {adminMode && adminConfig?.destinations && (
                  <select
                    value={selectedDestination || 'me'}
                    onChange={(e) => setSelectedDestination(e.target.value)}
                    className="bg-transparent text-white text-[10px] font-bold outline-none cursor-pointer border-l border-white/10 pl-3 ml-1"
                  >
                    {adminConfig.destinations.map(d => (
                      <option key={d.id} value={d.id} className="bg-[#17212b]">{d.name}</option>
                    ))}
                  </select>
                )}
              </div>
            </div>
          </div>
        )}
      </header>

      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto bg-[#17212b]">
        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="w-6 h-6 border-2 border-blue-500/10 border-t-[#2481cc] rounded-full animate-spin"></div>
          </div>
        ) : error === 'ACCESS_DENIED' ? (
          <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
            <div className="text-5xl">🔒</div>
            <h2 className="text-lg font-bold">Acceso Exclusivo</h2>
            <p className="text-[#7f8c99] text-xs">Esta sección es para usuarios VIP.</p>
          </div>
        ) : error ? (
          <div className="mx-6 p-4 bg-red-500/5 text-red-400 text-xs rounded-xl text-center">
            {error}
          </div>
        ) : (
          <div className="pb-24">
            <div className="px-6 py-4">
              <h2 className="text-white text-[15px] font-bold">
                {navigationStack.length > 0 ? (currentTitle === 'ZeePub Mini' ? 'Contenido' : currentTitle) : 'Mis colecciones'}
              </h2>
            </div>

            <div className="mx-4 bg-[#212d3b] rounded-2xl overflow-hidden shadow-xl border border-white/5">
              {currentItems.map((item, index) => {
                const isLast = index === currentItems.length - 1;
                if (isNavigationItem(item)) {
                  return (
                    <NavigationListItem
                      key={item.id || index}
                      item={item}
                      onNavigate={handleNavigate}
                      isLast={isLast}
                    />
                  );
                } else if (isBook(item)) {
                  return (
                    <BookListItem
                      key={item.id || index}
                      book={item}
                      onDownload={handleDownload}
                      isFacebookPublisher={isFacebookPublisher}
                      onFacebookPost={handleFacebookPost}
                      isLast={isLast}
                    />
                  );
                }
                return null;
              })}

              {items.length === 0 && (
                <div className="flex flex-col items-center justify-center py-20 text-[#7f8c99]">
                  <span className="text-4xl mb-2 opacity-20">🔍</span>
                  <p className="text-xs">No se encontró nada</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Modern Mini App Navigation - Sutil y translúcida */}
      <div className="flex-none bg-[#17212b]/80 backdrop-blur-md px-8 py-4 flex items-center justify-between border-t border-white/5">
        <button
          onClick={goToPrevPage}
          disabled={loading || (currentPage === 1 && !prevPageUrl)}
          className="p-2.5 bg-[#242f3d]/60 rounded-full disabled:opacity-20 text-gray-400 hover:text-white transition-all active:scale-95"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="px-5 py-2 bg-[#242f3d]/60 rounded-full text-[10px] font-bold text-gray-500 uppercase tracking-widest border border-white/5">
          {currentPage} / {totalPages}
        </div>

        <button
          onClick={goToNextPage}
          disabled={loading || (currentPage >= totalPages && !nextPageUrl)}
          className="p-2.5 bg-[#242f3d]/60 rounded-full disabled:opacity-20 text-gray-400 hover:text-white transition-all active:scale-95"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>
  );
}

export default App;
