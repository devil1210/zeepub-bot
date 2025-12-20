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
    <div className="min-h-screen bg-background text-foreground font-sans">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <button onClick={handleBack} className={`${navigationStack.length > 0 ? 'text-primary' : 'text-muted-foreground/40 pointer-events-none'}`}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M15 18l-6-6 6-6" />
            </svg>
          </button>

          <h1 className="text-lg font-semibold tracking-tight">ZeePubBot</h1>

          <button
            onClick={() => {
              if (isAdmin || isFacebookPublisher) {
                const newMode = !adminMode;
                setAdminMode(newMode);
                setNavigationStack([]);
                WebApp.BackButton.hide();
                const url = newMode && adminConfig ? adminConfig.admin_root_url : null;
                loadFeed(url);
              }
            }}
            className={`transition-colors ${adminMode ? 'text-primary' : 'text-muted-foreground'}`}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {adminMode ? <path d="M12 2a10 10 0 1 0 0 20 10 10 0 1 0 0-20z" /> : <circle cx="12" cy="12" r="1" />}
              {adminMode && <path d="M12 8v8" />}
              {adminMode && <path d="M8 12h8" />}
              {!adminMode && <circle cx="12" cy="5" r="1" />}
              {!adminMode && <circle cx="12" cy="19" r="1" />}
            </svg>
          </button>
        </div>
      </header>

      {/* Bot Profile Section - Solo visible en Home */}
      {navigationStack.length === 0 && !loading && (
        <div className="max-w-2xl mx-auto px-4 py-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex flex-col items-center text-center mb-8">
            <div className="w-24 h-24 mb-4 rounded-full border-2 border-primary/20 overflow-hidden shadow-xl bg-card">
              <img
                src="https://raw.githubusercontent.com/devil1210/zeepub-bot/main/zeepub-web/public/logo.png"
                alt="ZeePubBot"
                className="w-full h-full object-cover"
                onError={(e) => {
                  e.target.onerror = null;
                  e.target.src = "https://ui-avatars.com/api/?name=ZeePub&background=2481cc&color=fff";
                }}
              />
            </div>
            <h2 className="text-3xl font-bold mb-2 tracking-tight">ZeePubBot</h2>
            <p className="text-muted-foreground mb-4 font-medium">@ZeePubBot</p>
            <p className="text-sm text-foreground/80 leading-relaxed max-w-md">
              Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚
            </p>
            <button className="text-primary text-sm mt-3 font-medium hover:underline transition-all">Leer más →</button>
          </div>

          {/* Search */}
          <div className="mb-8">
            <div className="relative group">
              <div className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none group-focus-within:text-primary transition-colors">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </div>
              <input
                type="text"
                placeholder="Buscar libros..."
                onChange={(e) => debouncedSearch(e.target.value)}
                className="w-full h-12 pl-12 pr-4 bg-card border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all shadow-sm placeholder:text-muted-foreground/50"
              />
            </div>
          </div>
        </div>
      )}

      {/* Main Content List */}
      <div ref={scrollContainerRef} className="max-w-2xl mx-auto px-4 pb-32">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 space-y-4">
            <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            <p className="text-sm text-muted-foreground animate-pulse">Cargando biblioteca...</p>
          </div>
        ) : error ? (
          <div className="p-4 bg-destructive/10 text-destructive text-sm rounded-xl text-center border border-destructive/20">
            <p className="font-semibold">Error</p>
            <p>{error}</p>
          </div>
        ) : (
          <div className="space-y-3">
            {items.length > 0 && <h3 className="text-xl font-bold mb-4 px-1">{navigationStack.length > 0 ? (currentTitle === 'ZeePub Mini' ? 'Contenido' : currentTitle) : 'Funciones'}</h3>}

            {items.map((item, index) => (
              <div
                key={item.id || index}
                onClick={() => {
                  if (isNavigationItem(item)) handleNavigate(item);
                  else if (isBook(item)) handleDownload(item);
                }}
                className="group bg-card p-4 rounded-xl border border-border hover:bg-secondary/50 active:scale-[0.98] transition-all cursor-pointer shadow-sm flex items-center gap-4"
              >
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0 overflow-hidden text-primary">
                  {item.links?.find(l => l.rel?.includes('cover') || l.rel?.includes('image'))?.href ? (
                    <img
                      src={item.links.find(l => l.rel?.includes('cover') || l.rel?.includes('image')).href}
                      alt={item.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      {isNavigationItem(item) ? <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" /> : <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />}
                      {isBook(item) && <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />}
                    </svg>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <h4 className="font-semibold text-foreground mb-1 truncate leading-tight">{item.title}</h4>
                  <p className="text-sm text-muted-foreground truncate">
                    {isBook(item) ? (item.author ? item.author.name : 'Libro') : (item.content ? item.content.text : 'Colección')}
                  </p>
                </div>

                <div className="text-muted-foreground group-hover:text-primary transition-colors">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                  </svg>
                </div>
              </div>
            ))}

            {items.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <p>No se encontraron resultados.</p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Pagination - Solo si es necesaria */}
      {(items.length > 0 || prevPageUrl) && (
        <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md border-t border-border flex justify-between items-center z-20">
          <button
            onClick={goToPrevPage}
            disabled={loading || (currentPage === 1 && !prevPageUrl)}
            className="p-3 rounded-full bg-card border border-border disabled:opacity-30 hover:bg-secondary transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6" /></svg>
          </button>
          <span className="text-sm font-medium text-muted-foreground">Página {currentPage}</span>
          <button
            onClick={goToNextPage}
            disabled={loading || (currentPage >= totalPages && !nextPageUrl)}
            className="p-3 rounded-full bg-card border border-border disabled:opacity-30 hover:bg-secondary transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6" /></svg>
          </button>
        </div>
      )}
    </div>
  );
}

export default App;
