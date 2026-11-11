import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  ArrowLeft,
  Settings,
  List,
  ChevronLeft,
  ChevronRight,
  BookOpen,
  X,
  Loader2,
  Maximize,
  Minimize,
  Type,
  Sun,
  Moon,
  Compass
} from 'lucide-react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useNavigation } from '@shared/contexts/NavigationContext';

export interface ReaderProps {
  onClose?: () => void;
  bookId?: string;
  bookTitle?: string;
  epubUrl?: string;
}

interface TocItem {
  label: string;
  href: string;
  subitems?: TocItem[];
}

export const Reader: React.FC<ReaderProps> = ({
  onClose,
  bookId: propBookId,
  bookTitle: propBookTitle,
  epubUrl: propEpubUrl,
}) => {
  const { setContextType } = useNavigation();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  // Resolver parámetros desde props o URL search params
  const resolvedBookId = propBookId || searchParams.get('bookId') || searchParams.get('id') || '';
  const resolvedTitle = propBookTitle || searchParams.get('title') || 'Lectura Digital';
  const resolvedEpubUrl = propEpubUrl || searchParams.get('url') || (resolvedBookId ? `/api/download/${resolvedBookId}` : '');

  // Estados del Visor
  const [loading, setLoading] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentSection, setCurrentSection] = useState<string>('');
  const [toc, setToc] = useState<TocItem[]>([]);
  const [showToc, setShowToc] = useState<boolean>(false);
  const [showSettings, setShowSettings] = useState<boolean>(false);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);

  // Opciones de Personalización Visual (Estilo Premium Glassmorphism)
  const [theme, setTheme] = useState<'dark' | 'sepia' | 'light' | 'amoled'>('dark');
  const [fontSize, setFontSize] = useState<number>(105);
  const [lineHeight, setLineHeight] = useState<number>(1.6);
  const [fontFamily, setFontFamily] = useState<'sans' | 'serif'>('sans');

  const containerRef = useRef<HTMLDivElement>(null);
  const viewRef = useRef<any>(null);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Ocultar la barra de navegación flotante global durante la lectura
  useEffect(() => {
    setContextType('none');
    return () => setContextType('main');
  }, [setContextType]);

  // Manejo de salida
  const handleClose = useCallback(() => {
    if (onClose) {
      onClose();
    } else {
      navigate(-1);
    }
  }, [onClose, navigate]);

  // Guardado de progreso con debounce
  const debouncedSaveProgress = useCallback(
    (cfi: string, fraction: number) => {
      if (!resolvedBookId) return;

      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      saveTimeoutRef.current = setTimeout(async () => {
        try {
          await fetch('/api/v1/reading/progress', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              book_id: resolvedBookId,
              progress_cfi: cfi,
              percentage: fraction,
              device_name: 'ZeePub Web Reader',
              device_id: 'web-browser',
            }),
          });
        } catch (err) {
          console.warn('Aviso: No se pudo sincronizar el progreso de lectura:', err);
        }
      }, 800);
    },
    [resolvedBookId]
  );

  // Carga inicial del motor Foliate-js y el archivo EPUB
  useEffect(() => {
    let isMounted = true;
    let viewInstance: any = null;

    if (!resolvedEpubUrl) {
      setLoading(false);
      setLoadError('No se especificó ninguna URL o identificador de libro válido.');
      return;
    }

    async function loadFoliate() {
      try {
        setLoading(true);
        setLoadError(null);

        // 1. Obtener última posición guardada si existe bookId
        let savedCfi: string | null = null;
        if (resolvedBookId) {
          try {
            const resp = await fetch(`/api/v1/reading/progress/${resolvedBookId}`);
            if (resp.ok) {
              const data = await resp.json();
              if (data.progress_cfi) {
                savedCfi = data.progress_cfi;
              }
            }
          } catch {
            // Continuar sin progreso previo si falla la red
          }
        }

        // 2. Importar Foliate-js dinámicamente desde assets públicos
        const foliateUrl = '/assets/foliate/view.js';
        // @ts-ignore
        const foliateModule = await import(/* @vite-ignore */ foliateUrl);
        const ViewClass = foliateModule.View;

        if (!containerRef.current || !isMounted) return;

        // Limpiar contenedor previo si existiera
        containerRef.current.innerHTML = '';

        viewInstance = new ViewClass();
        viewRef.current = viewInstance;
        viewInstance.style.width = '100%';
        viewInstance.style.height = '100%';
        viewInstance.style.display = 'block';

        containerRef.current.appendChild(viewInstance);

        // Evento de reubicación de página (progreso, CFI y sección)
        viewInstance.addEventListener('relocate', (e: CustomEvent) => {
          if (!isMounted) return;
          const { cfi, fraction, tocItem } = e.detail || {};
          if (typeof fraction === 'number') {
            setProgress(Math.round(fraction * 100));
            debouncedSaveProgress(cfi, fraction);
          }
          if (tocItem?.label) {
            setCurrentSection(tocItem.label.trim());
          }
        });

        // 3. Abrir el libro desde la URL de streaming
        await viewInstance.open(resolvedEpubUrl);

        if (!isMounted) return;

        // Extraer tabla de contenidos
        if (viewInstance.book?.toc) {
          setToc(viewInstance.book.toc);
        }

        // 4. Iniciar en la posición guardada o al principio
        await viewInstance.init({
          lastLocation: savedCfi || undefined,
          showTextStart: true,
        });

        if (isMounted) {
          setLoading(false);
        }
      } catch (err: any) {
        console.error('Error inicializando Foliate Web Reader:', err);
        if (isMounted) {
          setLoading(false);
          setLoadError(err?.message || 'Error al procesar el archivo EPUB con Foliate-js.');
        }
      }
    }

    loadFoliate();

    return () => {
      isMounted = false;
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
      if (viewInstance) {
        try {
          viewInstance.close();
        } catch {}
      }
      if (containerRef.current) {
        containerRef.current.innerHTML = '';
      }
    };
  }, [resolvedEpubUrl, resolvedBookId, debouncedSaveProgress]);

  // Inyección de estilos y temas al Shadow DOM de Foliate
  useEffect(() => {
    if (!viewRef.current?.renderer) return;

    const themeColors = {
      dark: { bg: '#0f172a', fg: '#e2e8f0', link: '#38bdf8' },
      amoled: { bg: '#000000', fg: '#d1d5db', link: '#60a5fa' },
      sepia: { bg: '#fbf0d9', fg: '#4a3c2c', link: '#b45309' },
      light: { bg: '#ffffff', fg: '#1e293b', link: '#2563eb' },
    };

    const active = themeColors[theme];
    const fontStack = fontFamily === 'serif'
      ? '"Merriweather", "Georgia", "Cambria", serif'
      : '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

    const customCss = `
      @namespace epub "http://www.idpf.org/2007/ops";
      html {
        background-color: ${active.bg} !important;
        color: ${active.fg} !important;
        font-family: ${fontStack} !important;
        font-size: ${fontSize}% !important;
        line-height: ${lineHeight} !important;
      }
      body {
        background-color: ${active.bg} !important;
        color: ${active.fg} !important;
      }
      p, div, span, h1, h2, h3, h4, h5, h6, li {
        color: ${active.fg} !important;
      }
      a {
        color: ${active.link} !important;
      }
    `;

    try {
      viewRef.current.renderer.setStyles(customCss);
    } catch {}
  }, [theme, fontSize, lineHeight, fontFamily, loading]);

  // Navegación por teclado (Flechas y Espacio)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        viewRef.current?.next();
      } else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        viewRef.current?.prev();
      } else if (e.key === 'Escape') {
        if (showToc) setShowToc(false);
        else if (showSettings) setShowSettings(false);
        else handleClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showToc, showSettings, handleClose]);

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {});
      setIsFullscreen(true);
    } else {
      document.exitFullscreen().catch(() => {});
      setIsFullscreen(false);
    }
  };

  const handleNextPage = () => viewRef.current?.next();
  const handlePrevPage = () => viewRef.current?.prev();

  const handleNavigateToc = (href: string) => {
    if (viewRef.current) {
      viewRef.current.goTo(href);
      setShowToc(false);
    }
  };

  return (
    <div className={`fixed inset-0 z-50 flex flex-col select-none overflow-hidden font-sans transition-colors duration-300 ${
      theme === 'amoled' ? 'bg-black text-gray-200' :
      theme === 'sepia' ? 'bg-[#fbf0d9] text-[#4a3c2c]' :
      theme === 'light' ? 'bg-white text-gray-800' :
      'bg-[#0f172a] text-gray-200'
    }`}>
      {/* Top Header HUD (Glassmorphism ZeePub) */}
      <header className="fixed top-0 w-full z-40 px-4 sm:px-6 h-14 flex items-center justify-between glass-panel border-b border-white/10 shadow-lg">
        <div className="flex items-center gap-3">
          <button
            onClick={handleClose}
            className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            title="Volver"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="truncate max-w-[200px] sm:max-w-md">
            <h1 className="text-sm font-semibold truncate text-white">{resolvedTitle}</h1>
            <p className="text-xs text-gray-400 truncate">{currentSection || `${progress}% completado`}</p>
          </div>
        </div>

        <div className="flex items-center gap-1 sm:gap-2">
          {toc.length > 0 && (
            <button
              onClick={() => { setShowToc(!showToc); setShowSettings(false); }}
              className={`p-2 rounded-xl transition-colors ${showToc ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
              title="Tabla de Contenidos"
            >
              <List className="w-5 h-5" />
            </button>
          )}

          <button
            onClick={() => { setShowSettings(!showSettings); setShowToc(false); }}
            className={`p-2 rounded-xl transition-colors ${showSettings ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/10'}`}
            title="Ajustes de Lectura"
          >
            <Settings className="w-5 h-5" />
          </button>

          <button
            onClick={toggleFullscreen}
            className="hidden sm:flex p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            title={isFullscreen ? 'Salir de Pantalla Completa' : 'Pantalla Completa'}
          >
            {isFullscreen ? <Minimize className="w-5 h-5" /> : <Maximize className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Drawer: Tabla de Contenidos */}
      {showToc && (
        <aside className="fixed top-14 left-0 bottom-14 w-80 max-w-[85vw] z-50 glass-panel border-r border-white/15 p-4 shadow-2xl flex flex-col backdrop-blur-xl animate-in slide-in-from-left duration-200">
          <div className="flex items-center justify-between pb-3 border-b border-white/10 mb-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-white">
              <BookOpen className="w-4 h-4 text-primary" />
              <span>Índice de Capítulos</span>
            </div>
            <button onClick={() => setShowToc(false)} className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {toc.map((item, idx) => (
              <button
                key={idx}
                onClick={() => handleNavigateToc(item.href)}
                className="w-full text-left px-3 py-2 rounded-lg text-xs hover:bg-white/10 text-gray-300 hover:text-white transition-colors truncate"
              >
                {item.label}
              </button>
            ))}
          </div>
        </aside>
      )}

      {/* Drawer: Panel de Personalización Visual */}
      {showSettings && (
        <aside className="fixed top-16 right-4 sm:right-6 z-50 w-72 glass-panel border border-white/15 p-4 rounded-2xl shadow-2xl flex flex-col gap-4 backdrop-blur-2xl animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-2 border-b border-white/10">
            <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Ajustes del Lector</span>
            <button onClick={() => setShowSettings(false)} className="p-1 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Selector de Tema */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-gray-400">TEMA DE COLOR</label>
            <div className="grid grid-cols-4 gap-1.5">
              <button
                onClick={() => setTheme('dark')}
                className={`py-1.5 rounded-lg text-xs font-medium border text-center transition-all ${
                  theme === 'dark' ? 'border-primary bg-primary/20 text-white' : 'border-white/10 bg-slate-800 text-gray-400'
                }`}
              >
                Oscuro
              </button>
              <button
                onClick={() => setTheme('amoled')}
                className={`py-1.5 rounded-lg text-xs font-medium border text-center transition-all ${
                  theme === 'amoled' ? 'border-primary bg-primary/20 text-white' : 'border-white/10 bg-black text-gray-400'
                }`}
              >
                Negro
              </button>
              <button
                onClick={() => setTheme('sepia')}
                className={`py-1.5 rounded-lg text-xs font-medium border text-center transition-all ${
                  theme === 'sepia' ? 'border-amber-600 bg-amber-600/20 text-amber-900 font-bold' : 'border-white/10 bg-[#fbf0d9] text-[#5c4a35]'
                }`}
              >
                Sepia
              </button>
              <button
                onClick={() => setTheme('light')}
                className={`py-1.5 rounded-lg text-xs font-medium border text-center transition-all ${
                  theme === 'light' ? 'border-blue-500 bg-blue-500/20 text-slate-900 font-bold' : 'border-white/10 bg-white text-slate-800'
                }`}
              >
                Claro
              </button>
            </div>
          </div>

          {/* Tamaño de Fuente */}
          <div className="space-y-1.5">
            <div className="flex justify-between items-center text-[11px] text-gray-400 font-medium">
              <span>TAMAÑO DE TEXTO</span>
              <span className="font-mono text-white">{fontSize}%</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setFontSize(s => Math.max(75, s - 10))}
                className="flex-1 py-1 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-bold text-white transition-colors"
              >
                A -
              </button>
              <button
                onClick={() => setFontSize(s => Math.min(180, s + 10))}
                className="flex-1 py-1 bg-white/10 hover:bg-white/20 rounded-lg text-xs font-bold text-white transition-colors"
              >
                A +
              </button>
            </div>
          </div>

          {/* Tipografía */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-medium text-gray-400">TIPOGRAFÍA</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                onClick={() => setFontFamily('sans')}
                className={`py-1.5 rounded-lg text-xs font-sans border transition-all ${
                  fontFamily === 'sans' ? 'border-primary bg-primary/20 text-white' : 'border-white/10 bg-white/5 text-gray-400'
                }`}
              >
                Sans-Serif
              </button>
              <button
                onClick={() => setFontFamily('serif')}
                className={`py-1.5 rounded-lg text-xs font-serif border transition-all ${
                  fontFamily === 'serif' ? 'border-primary bg-primary/20 text-white' : 'border-white/10 bg-white/5 text-gray-400'
                }`}
              >
                Serif
              </button>
            </div>
          </div>
        </aside>
      )}

      {/* Área Central: Motor de Renderizado Foliate-js */}
      <main className="flex-1 w-full h-full relative pt-14 pb-14 overflow-hidden">
        {loading && (
          <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-3 bg-black/40 backdrop-blur-sm text-gray-300">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm font-medium">Cargando libro con Foliate-js...</p>
          </div>
        )}

        {loadError && (
          <div className="absolute inset-0 z-30 flex flex-col items-center justify-center gap-4 p-6 text-center">
            <div className="p-3 bg-red-500/20 text-red-400 rounded-2xl border border-red-500/30">
              <BookOpen className="w-8 h-8" />
            </div>
            <h3 className="text-base font-semibold text-white">No se pudo cargar el libro</h3>
            <p className="text-xs text-gray-400 max-w-sm">{loadError}</p>
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-xl text-xs font-medium text-white transition-colors"
            >
              Cerrar Visor
            </button>
          </div>
        )}

        {/* Zonas de toque lateral para avance rápido en móviles */}
        <div
          onClick={handlePrevPage}
          className="absolute left-0 top-14 bottom-14 w-1/6 z-20 cursor-w-resize opacity-0 hover:opacity-10 transition-opacity bg-gradient-to-r from-black/20 to-transparent"
          title="Página Anterior"
        />
        <div
          onClick={handleNextPage}
          className="absolute right-0 top-14 bottom-14 w-1/6 z-20 cursor-e-resize opacity-0 hover:opacity-10 transition-opacity bg-gradient-to-l from-black/20 to-transparent"
          title="Página Siguiente"
        />

        {/* Contenedor del Custom Element foliate-view */}
        <div ref={containerRef} className="w-full h-full" />
      </main>

      {/* Bottom Footer HUD (Glassmorphism ZeePub) */}
      <footer className="fixed bottom-0 w-full z-40 px-4 sm:px-6 h-14 glass-panel border-t border-white/10 flex items-center justify-between text-xs text-gray-400 shadow-lg">
        <div className="flex items-center gap-2">
          <button
            onClick={handlePrevPage}
            className="p-1.5 rounded-lg hover:bg-white/10 text-gray-300 hover:text-white transition-colors"
            title="Anterior"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={handleNextPage}
            className="p-1.5 rounded-lg hover:bg-white/10 text-gray-300 hover:text-white transition-colors"
            title="Siguiente"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
          <span className="hidden sm:inline font-mono text-[11px] text-gray-400">{currentSection || 'Lectura'}</span>
        </div>

        {/* Barra de progreso interactiva */}
        <div className="flex items-center gap-3 w-1/2 max-w-xs">
          <div className="relative flex-1 h-1.5 bg-gray-700/50 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="font-mono text-white text-xs font-semibold">{progress}%</span>
        </div>
      </footer>
    </div>
  );
};
