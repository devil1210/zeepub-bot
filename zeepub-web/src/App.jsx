import React, { useState, useEffect, useRef } from 'react';
import WebApp from '@twa-dev/sdk';
import { fetchFeed, searchBooks, fetchConfig, downloadBook, prepareFacebookPost, publishFacebookPost } from './api';
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Search, BookOpen, Settings, Info, Download, Heart, LinkIcon, ChevronRight } from "lucide-react"

const ITEMS_PER_PAGE = 20;

const useDebounce = (callback, delay) => {
    const callbackRef = useRef(callback);
    useEffect(() => {
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
    // Navigation & Data State
    const [view, setView] = useState('home'); // 'home' | 'feed'
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [navigationStack, setNavigationStack] = useState([]);
    const [currentTitle, setCurrentTitle] = useState('ZeePub Mini');
    const [currentPage, setCurrentPage] = useState(1);
    const [nextPageUrl, setNextPageUrl] = useState(null);
    const [prevPageUrl, setPrevPageUrl] = useState(null);

    // User/Config State
    const [isAdmin, setIsAdmin] = useState(false);
    const [adminConfig, setAdminConfig] = useState(null);
    const [adminMode, setAdminMode] = useState(false);
    const [selectedDestination, setSelectedDestination] = useState(null);
    const [isFacebookPublisher, setIsFacebookPublisher] = useState(false);
    const [botInfo, setBotInfo] = useState({
        name: "ZeePubBot",
        username: "@ZeePubBot",
        description: "Asistente de EPUB del grupo. Preciso, limpio y siempre listo para ayudarte. 📚",
        avatar: "https://raw.githubusercontent.com/devil1210/zeepub-bot/main/zeepub-web/public/logo.png",
    });

    const scrollContainerRef = useRef(null);

    // Initialize WebApp and Config
    useEffect(() => {
        WebApp.ready();
        WebApp.expand();
        WebApp.BackButton.onClick(() => handleBack());

        const init = async () => {
            const uid = WebApp.initDataUnsafe?.user?.id;
            const config = await fetchConfig(uid);

            if (config) {
                setAdminConfig(config);
                setIsAdmin(config.is_admin || false);
                setIsFacebookPublisher(config.is_facebook_publisher || false);

                if (config.destinations?.length > 0) {
                    setSelectedDestination(config.destinations[0].id);
                }
            }
        };
        init();
    }, []);

    // Back button visibility
    useEffect(() => {
        if (view === 'feed' || navigationStack.length > 0) {
            WebApp.BackButton.show();
        } else {
            WebApp.BackButton.hide();
        }
    }, [view, navigationStack]);

    const loadFeed = async (url = null, forceView = false) => {
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
            } else {
                setError('No se pudieron cargar los datos.');
            }
        } catch (err) {
            setError(err.message === 'ACCESS_DENIED' ? 'Acceso denegado' : 'Error de conexión.');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = async (query) => {
        if (query.trim()) {
            setView('feed');
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
                setError('Error en la búsqueda.');
            } finally {
                setLoading(false);
            }
        } else if (view === 'feed' && navigationStack.length === 0) {
            // Empty search in root feed -> back home?
            // setView('home');
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
            loadFeed(navLink.href);
        }
    };

    const handleBack = () => {
        if (navigationStack.length > 0) {
            const previous = navigationStack[navigationStack.length - 1];
            setItems(previous.items);
            setCurrentTitle(previous.title);
            setCurrentPage(previous.page || 1);
            setNextPageUrl(previous.nextPageUrl);
            setPrevPageUrl(previous.prevPageUrl);
            setNavigationStack(prev => prev.slice(0, -1));
            if (scrollContainerRef.current) scrollContainerRef.current.scrollTop = 0;
        } else if (view === 'feed') {
            setView('home');
            setItems([]);
            setCurrentTitle('ZeePub Mini');
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

    const menuItems = [
        { icon: BookOpen, label: "Catálogo Completo", onClick: () => loadFeed(null, true), description: "Explora todos los libros disponibles" },
        { icon: Info, label: "Comandos y Ayuda", onClick: () => WebApp.openTelegramLink('https://t.me/ZeePubSupport'), description: "Guía de uso y soporte" },
        { icon: Heart, label: "Apoyar Proyecto", onClick: () => WebApp.showAlert("¡Gracias por tu interés! Próximamente."), description: "Donaciones y mejoras" },
    ];

    return (
        <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">

            {/* Header Fiel a v0 */}
            <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="max-w-2xl mx-auto px-4 py-3 flex items-center justify-between">
                    <Button variant="ghost" size="icon" onClick={handleBack} className={view === 'home' ? 'opacity-0 pointer-events-none' : ''}>
                        <ChevronRight className="rotate-180" />
                    </Button>
                    <h1 className="text-lg font-semibold tracking-tight">ZeePubBot</h1>
                    <Button variant="ghost" size="icon" onClick={() => {
                        if (isAdmin) {
                            setAdminMode(!adminMode);
                            WebApp.showAlert(adminMode ? "Modo Usuario" : "Modo Administrador");
                        }
                    }}>
                        {isAdmin ? <Settings className={adminMode ? "text-primary" : ""} /> : <Info />}
                    </Button>
                </div>
            </header>

            {/* VISTA HOME */}
            {view === 'home' && (
                <main className="max-w-2xl mx-auto px-4 py-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex flex-col items-center text-center mb-10">
                        <Avatar className="w-24 h-24 mb-4 border-2 border-primary/20 shadow-xl">
                            <AvatarImage src={botInfo.avatar} alt={botInfo.name} />
                            <AvatarFallback className="bg-primary text-primary-foreground text-2xl">ZP</AvatarFallback>
                        </Avatar>
                        <h2 className="text-3xl font-bold mb-2 tracking-tight">{botInfo.name}</h2>
                        <p className="text-muted-foreground mb-4 font-medium">{botInfo.username}</p>
                        <p className="text-sm text-foreground/80 leading-relaxed max-w-md">{botInfo.description}</p>
                        <Button variant="link" className="text-primary mt-2" onClick={() => WebApp.showAlert("¡ZeePubBot es tu biblioteca inteligente!")}>
                            Leer más →
                        </Button>
                    </div>

                    <div className="mb-10 relative">
                        <div className="relative group">
                            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                            <Input
                                placeholder="Buscar por título o autor..."
                                className="pl-12 h-14 bg-card border-border rounded-2xl text-base shadow-sm focus:ring-primary/20"
                                onChange={(e) => debouncedSearch(e.target.value)}
                            />
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-xl font-bold px-1">Funciones</h3>
                        <div className="grid gap-3">
                            {menuItems.map((item, index) => (
                                <Card key={index}
                                    className="p-5 hover:bg-secondary/50 transition-all cursor-pointer border-border group active:scale-[0.98]"
                                    onClick={item.onClick}>
                                    <div className="flex items-center gap-5">
                                        <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center shrink-0 group-hover:bg-primary/20 transition-colors">
                                            <item.icon className="w-6 h-6 text-primary" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-semibold text-foreground mb-1">{item.label}</h4>
                                            <p className="text-sm text-muted-foreground">{item.description}</p>
                                        </div>
                                        <ChevronRight className="text-muted-foreground/50 group-hover:text-primary transition-colors" />
                                    </div>
                                </Card>
                            ))}
                        </div>
                    </div>

                    <div className="mt-10">
                        <h3 className="text-xl font-bold px-1 mb-4">Acceso Rápido</h3>
                        <Button className="w-full h-14 rounded-2xl text-lg font-semibold shadow-lg shadow-primary/20" onClick={() => WebApp.showAlert("Servicio operando normalmente ✅")}>
                            Estado del Bot
                        </Button>
                    </div>
                </main>
            )}

            {/* VISTA FEED */}
            {view === 'feed' && (
                <main ref={scrollContainerRef} className="max-w-2xl mx-auto px-4 py-6 pb-24 animate-in fade-in duration-300">
                    <div className="mb-6 flex items-center justify-between px-1">
                        <h3 className="text-2xl font-bold tracking-tight">{currentTitle === 'ZeePub Mini' ? 'Explorar' : currentTitle}</h3>
                        {loading && <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>}
                    </div>

                    {error ? (
                        <div className="py-12 text-center text-destructive">
                            <p className="font-medium">{error}</p>
                            <Button variant="outline" className="mt-4" onClick={() => loadFeed(null)}>Reintentar</Button>
                        </div>
                    ) : items.length > 0 ? (
                        <div className="grid gap-3">
                            {items.map((item, index) => (
                                <Card key={index}
                                    className="p-4 hover:bg-secondary/50 transition-all cursor-pointer border-border group active:scale-[0.99]"
                                    onClick={() => {
                                        if (isNavigationItem(item)) handleNavigate(item);
                                        else if (isBook(item)) handleDownload(item);
                                    }}>
                                    <div className="flex items-center gap-4">
                                        <div className="w-14 h-14 rounded-xl bg-muted flex items-center justify-center shrink-0 overflow-hidden border border-border/50">
                                            {item.links?.find(l => l.rel?.includes('cover') || l.rel?.includes('image'))?.href ? (
                                                <img src={item.links.find(l => l.rel?.includes('cover')).href}
                                                    alt={item.title}
                                                    className="w-full h-full object-cover group-hover:scale-110 transition-transform" />
                                            ) : (
                                                isNavigationItem(item) ? <BookOpen className="text-muted-foreground w-6 h-6" /> : <Download className="text-muted-foreground w-6 h-6" />
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <h4 className="font-semibold text-foreground truncate leading-tight">{item.title}</h4>
                                            <p className="text-sm text-muted-foreground truncate mt-1">
                                                {isBook(item) ? (item.author?.name || 'Autor Desconocido') : 'Colección'}
                                            </p>
                                        </div>
                                        <ChevronRight className="w-5 h-5 text-muted-foreground/30 group-hover:text-primary transition-colors" />
                                    </div>
                                </Card>
                            ))}
                        </div>
                    ) : !loading && (
                        <div className="py-20 text-center text-muted-foreground">
                            <Search className="w-12 h-12 mx-auto mb-4 opacity-10" />
                            <p>No se encontraron libros ni categorías.</p>
                            <Button variant="link" onClick={handleBack}>Regresar</Button>
                        </div>
                    )}

                    {/* Paginación */}
                    {(nextPageUrl || prevPageUrl) && (
                        <div className="fixed bottom-0 left-0 right-0 p-4 bg-background/80 backdrop-blur-md border-t border-border flex justify-between items-center z-50">
                            <Button variant="outline" size="sm" onClick={() => loadFeed(prevPageUrl)} disabled={!prevPageUrl || loading}>
                                <ChevronRight className="rotate-180 mr-1" /> Anterior
                            </Button>
                            <span className="text-sm font-medium">Página {currentPage}</span>
                            <Button variant="outline" size="sm" onClick={() => loadFeed(nextPageUrl)} disabled={!nextPageUrl || loading}>
                                Siguiente <ChevronRight className="ml-1" />
                            </Button>
                        </div>
                    )}
                </main>
            )}
        </div>
    );
}

export default App;
