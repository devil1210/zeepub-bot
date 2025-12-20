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

      <header className="flex-none flex flex-col items-center pt-8 pb-4 bg-[#17212b]">
        {/* Profile Avatar */}
        <div className="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-4xl shadow-xl mb-4 overflow-hidden border-2 border-white/10">
          <span className="animate-pulse">📚</span>
        </div>

        {/* Title & Subtitle */}
        <h1 className="text-2xl font-bold mb-1">ZeePub</h1>
        <p className="text-[#7f8c99] text-sm text-center px-8 mb-6 leading-relaxed">
          ZeePub es el bot definitivo para gestionar y leer tus libros favoritos directamente en Telegram.
          <br />
          <span className="text-blue-400 font-medium cursor-pointer hover:underline text-xs mt-2 block">Saber más ˃</span>
        </p>

        <SearchBar onSearch={debouncedSearch} />

        {/* Admin Controls - Estilo Integrado */}
        {(isAdmin || isFacebookPublisher) && (
          <div className="w-full max-w-sm px-4 mb-4">
            <div className="bg-[#242f3d]/50 rounded-2xl p-3 border border-white/5 flex flex-col gap-2">
              <div className="flex items-center justify-between px-2">
                <span className="text-xs font-semibold text-blue-400 uppercase tracking-wider">Modo Avanzado</span>
                <button
                  onClick={() => {
                    const newMode = !adminMode;
                    setAdminMode(newMode);
                    setNavigationStack([]);
                    WebApp.BackButton.hide();
                    const url = newMode && adminConfig ? adminConfig.admin_root_url : null;
                    loadFeed(url);
                  }}
                  className={`w-10 h-5 rounded-full relative transition-colors duration-200 focus:outline-none ${adminMode ? 'bg-blue-500' : 'bg-gray-600'}`}
                >
                  <div className={`absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-transform duration-200 transform ${adminMode ? 'translate-x-5' : 'translate-x-0'}`} />
                </button>
              </div>

              {adminMode && adminConfig?.destinations && (
                <div className="flex items-center gap-3 px-2 py-1 bg-[#17212b]/50 rounded-xl">
                  <span className="text-[10px] text-gray-500 uppercase font-bold">Destino:</span>
                  <select
                    value={selectedDestination || 'me'}
                    onChange={(e) => setSelectedDestination(e.target.value)}
                    className="bg-transparent text-white text-xs w-full outline-none appearance-none cursor-pointer"
                  >
                    {adminConfig.destinations.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto bg-[#1c2733] rounded-t-[30px] border-t border-white/5">
        <div className="px-4 pt-6 pb-2">
          <h2 className="text-[#2481cc] text-xs font-bold uppercase tracking-widest mb-4 ml-1">
            {navigationStack.length > 0 ? 'Contenido' : 'Mis Colecciones'}
          </h2>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-48">
            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
          </div>
        ) : error === 'ACCESS_DENIED' ? (
          <div className="flex flex-col items-center justify-center p-12 text-center space-y-4">
            <div className="text-5xl">🔒</div>
            <h2 className="text-xl font-bold">Acceso Exclusivo</h2>
            <p className="text-gray-400 text-sm">Esta sección es para usuarios VIP.</p>
          </div>
        ) : error ? (
          <div className="mx-6 p-4 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-2xl text-center">
            {error}
          </div>
        ) : (
          <div className="pb-24">
            {currentItems.map((item, index) => {
              if (isNavigationItem(item)) {
                return (
                  <NavigationListItem
                    key={item.id || index}
                    item={item}
                    onNavigate={handleNavigate}
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
                  />
                );
              }
              return null;
            })}

            {items.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-gray-500">
                <span className="text-4xl mb-2">🔍</span>
                <p className="text-sm">No se encontró nada</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Minimal Navigation Bar (Floating/Sticky) */}
      <div className="flex-none bg-[#1c2733] border-t border-white/5 px-6 py-4 flex items-center justify-between">
        <button
          onClick={goToPrevPage}
          disabled={loading || (currentPage === 1 && !prevPageUrl)}
          className="p-2 bg-[#242f3d] rounded-full disabled:opacity-20 text-gray-300 hover:text-white transition-all shadow-lg active:scale-95"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <div className="flex items-center gap-4">
          {/* Center Status Info */}
          <div className="px-4 py-2 bg-[#242f3d] rounded-2xl text-[10px] font-bold text-gray-400 shadow-lg border border-white/5 uppercase tracking-widest">
            {currentPage} / {totalPages}
          </div>
        </div>

        <button
          onClick={goToNextPage}
          disabled={loading || (currentPage >= totalPages && !nextPageUrl)}
          className="p-2 bg-[#242f3d] rounded-full disabled:opacity-20 text-gray-300 hover:text-white transition-all shadow-lg active:scale-95"
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
