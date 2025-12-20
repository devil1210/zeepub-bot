import React, { useState, useEffect } from 'react';
import WebApp from '@twa-dev/sdk';
import { fetchFeed, searchBooks, fetchConfig, downloadBook, prepareFacebookPost, publishFacebookPost } from './api';
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, BookOpen, Settings, Info, Download, Heart, LinkIcon, ChevronRight } from "lucide-react"

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
  const [loading, setLoading] = useState(false);
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
  const [selectedDestination, setSelectedDestination] = useState(null);
  const [isFacebookPublisher, setIsFacebookPublisher] = useState(false);

  // View State for V0 Design
  const [view, setView] = useState('home'); // 'home' | 'feed'

  const scrollContainerRef = React.useRef(null);

  const [botInfo, setBotInfo] = useState({
    name: "ZeePubBot",
    username: "@ZeePubBot",
    description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
    avatar: "https://raw.githubusercontent.com/devil1210/zeepub-bot/main/zeepub-web/public/logo.png",
  });

  const menuItems = [
    { icon: BookOpen, label: "Explorar Libros", onClick: () => loadFeed(null, 0, true), description: "Ver todo el catálogo" },
    { icon: Search, label: "Buscar", onClick: () => { setView('feed'); handleSearch(''); }, description: "Encuentra por título o autor" },
    { icon: Info, label: "Ayuda", onClick: () => WebApp.openTelegramLink('https://t.me/ZeePubSupport'), description: "Soporte y comandos" },
  ];

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();
    WebApp.BackButton.onClick(() => handleBack());

    const init = async () => {
      const uid = WebApp.initDataUnsafe?.user?.id;
      const config = await fetchConfig(uid);

      if (config) {
        setAdminConfig(config);
      }

      if (config && config.is_admin) {
        setIsAdmin(true);
        if (config.destinations && config.destinations.length > 0) {
          setSelectedDestination(config.destinations[0].id);
        }
      }
      if (config && config.is_facebook_publisher) {
        setIsFacebookPublisher(true);
        if (!config.is_admin && config.destinations && config.destinations.length > 0) {
          setSelectedDestination(config.destinations[0].id);
        }
      }
    };
    init();
  }, []);

  const loadFeed = async (url = null, depth = 0, forceView = false) => {
    setLoading(true);
    setError(null);
    setCurrentPage(1);

    if (forceView) setView('feed');
    if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;

    const uid = WebApp.initDataUnsafe?.user?.id;

    try {
      let targetUrl = url;
      if (!targetUrl && adminMode && adminConfig?.admin_root_url) {
        targetUrl = adminConfig.admin_root_url;
      }

      const data = await fetchFeed(targetUrl, uid);
      if (data && data.entries) {
        setItems(data.entries);
        if (data.title) setCurrentTitle(data.title);

        const nextLink = data.links?.find(l => l.rel?.includes('next'));
        const prevLink = data.links?.find(l => l.rel?.includes('previous') || l.rel?.includes('prev'));

        setNextPageUrl(nextLink ? nextLink.href : null);
        setPrevPageUrl(prevLink ? prevLink.href : null);

        if (url || forceView) {
          WebApp.BackButton.show();
        }

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
    if (query.length > 0) {
      setView('feed');
      WebApp.BackButton.show();
    }

    if (!query.trim()) {
      loadFeed();
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
        nextPageUrl,
        prevPageUrl
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
      setNextPageUrl(previous.nextPageUrl || null);
      setPrevPageUrl(previous.prevPageUrl || null);
      setNavigationStack(prev => prev.slice(0, -1));
      if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
    } else {
      setView('home');
      setItems([]);
      WebApp.BackButton.hide();
    }
  };

  const handleDownload = async (book) => {
    const destName = adminConfig?.destinations?.find(d => d.id === selectedDestination)?.name || 'tu chat';
    const action = selectedDestination && selectedDestination !== 'me' ? `Publicar en ${destName}` : 'Descargar';
    WebApp.showConfirm(`¿Deseas ${action} "${book.title}"?`, async (confirmed) => {
      if (confirmed) {
        const target = selectedDestination === 'me' ? null : selectedDestination;
        const success = await downloadBook(book, target);
        if (success) WebApp.showAlert('✅ Operación iniciada.');
        else WebApp.showAlert('❌ Error al iniciar.');
      }
    });
  };

  const isNavigationItem = (item) => item.links?.some(l => l.rel === 'subsection' || (l.type?.includes('opds-catalog') && l.type?.includes('navigation')));
  const isBook = (item) => item.links?.some(l => l.rel === 'http://opds-spec.org/acquisition' || l.type?.includes('epub'));

  const totalPages = Math.max(1, Math.ceil(items.length / ITEMS_PER_PAGE));
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const endIndex = startIndex + ITEMS_PER_PAGE;
  // We use full items for search/feed if paginated server side, or client side depending on implementation. 
  // Assuming hybrid: items is current page from server.
  const currentItems = items;

  const goToNextPage = () => {
    if (nextPageUrl) loadFeed(nextPageUrl, 2);
  };

  const goToPrevPage = () => {
    if (prevPageUrl) loadFeed(prevPageUrl, 2);
  };

  return (
    <div className="min-h-screen bg-background text-foreground font-sans">

      <header className="sticky top-0 z-10 bg-card/95 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
          <button
            onClick={handleBack}
            className={`flex items-center justify-center w-8 h-8 rounded-full hover:bg-muted transition-colors ${view === 'home' ? 'opacity-0 pointer-events-none' : 'text-foreground/60'}`}
          >
            <ChevronRight className="w-5 h-5 rotate-180" />
          </button>

          <h1 className="text-lg font-semibold tracking-tight">ZeePubBot</h1>

          <button className="text-foreground/60 w-8 h-8 flex items-center justify-center hover:bg-muted rounded-full transition-colors"
            onClick={() => {
              if (isAdmin) {
                setAdminMode(!adminMode);
                WebApp.showAlert(adminMode ? "Modo Usuario" : "Modo Administrador");
              }
            }}>
            {isAdmin ? (adminMode ? <Settings className="w-5 h-5 text-primary" /> : <Settings className="w-5 h-5" />) : <Info className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* VIEW: HOME (Landing) */}
      {view === 'home' && (
        <div className="max-w-2xl mx-auto px-4 py-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex flex-col items-center text-center mb-8">
            <Avatar className="w-24 h-24 mb-4 border-2 border-primary/20 bg-card shadow-xl">
              <AvatarImage src={botInfo.avatar} alt={botInfo.name} className="object-cover" />
              <AvatarFallback className="bg-primary text-primary-foreground text-2xl">ZP</AvatarFallback>
            </Avatar>
            <h2 className="text-3xl font-bold mb-2 tracking-tight">{botInfo.name}</h2>
            <p className="text-muted-foreground mb-4 font-medium">{botInfo.username}</p>
            <p className="text-sm text-foreground/80 leading-relaxed max-w-md">{botInfo.description}</p>
          </div>

          {/* Search Input (Navigates to Feed on Type) */}
          <div className="mb-8 relative z-0">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Buscar..."
                onChange={(e) => {
                  if (e.target.value.length > 2) {
                    setView('feed');
                    debouncedSearch(e.target.value);
                  }
                }}
                className="pl-12 h-12 bg-card border-border rounded-xl text-base"
              />
            </div>
          </div>

          {/* Menu Items */}
          <div className="space-y-3">
            <h3 className="text-xl font-bold mb-4">Funciones</h3>
            {menuItems.map((item, index) => (
              <Card
                key={index}
                className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border active:scale-[0.99]"
                onClick={() => {
                  item.onClick && item.onClick();
                }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center flex-shrink-0">
                    <item.icon className="w-6 h-6 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-foreground mb-1">{item.label}</h4>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </div>
                  <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* VIEW: FEED (List of Books) */}
      {view === 'feed' && (
        <div ref={scrollContainerRef} className="max-w-2xl mx-auto px-4 pb-32 pt-4 animate-in fade-in duration-300">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 space-y-4">
              <div className="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
              <p className="text-sm text-muted-foreground animate-pulse">Cargando...</p>
            </div>
          ) : items.length > 0 ? (
            <div className="space-y-3">
              <h3 className="text-xl font-bold mb-4 px-1">{currentTitle === 'ZeePub Mini' ? 'Resultados' : currentTitle}</h3>
              {items.map((item, index) => (
                <Card
                  key={index}
                  className="p-4 hover:bg-secondary/50 transition-colors cursor-pointer border-border active:scale-[0.99]"
                  onClick={() => {
                    if (isNavigationItem(item)) handleNavigate(item);
                    else if (isBook(item)) handleDownload(item);
                  }}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center flex-shrink-0 overflow-hidden">
                      {item.links?.find(l => l.rel?.includes('cover') || l.rel?.includes('image'))?.href ? (
                        <img src={item.links.find(l => l.rel?.includes('cover')).href} alt={item.title} className="w-full h-full object-cover" />
                      ) : (
                        <BookOpen className="w-6 h-6 text-muted-foreground" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-foreground mb-1 line-clamp-1">{item.title}</h4>
                      <p className="text-sm text-muted-foreground line-clamp-1">
                        {isBook(item) ? (item.author?.name || 'Autor Desconocido') : 'Colección'}
                      </p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-muted-foreground flex-shrink-0" />
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No se encontraron resultados</p>
              <Button variant="link" onClick={() => setView('home')}>Volver al Inicio</Button>
            </div>
          )}

          {/* Pagination Footer */}
          {(items.length > 0 || prevPageUrl || nextPageUrl) && (
            <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md border-t border-border flex justify-between items-center z-20">
              <Button variant="outline" size="icon" onClick={goToPrevPage} disabled={loading || !prevPageUrl}>
                <ChevronRight className="w-4 h-4 rotate-180" />
              </Button>
              <div className="bg-secondary/50 px-4 py-1 rounded-full text-xs font-medium">
                {currentPage}
              </div>
              <Button variant="outline" size="icon" onClick={goToNextPage} disabled={loading || !nextPageUrl}>
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
