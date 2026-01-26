import React, { useEffect, useState } from 'react';
import {
  Search,
  Zap,
  BookOpen,
  Settings,
  TrendingUp,
  Clock,
  ArrowRight,
  Download,
  Star,
  PlayCircle,
  Library,
  RefreshCw,
  ShieldCheck,
  Copy,
  Upload,
  History,
  ShieldHalf,
  ArrowDownToLine,
  BrainCircuit
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTelegram } from '../contexts/TelegramContext';
import { useTheme } from '../contexts/ThemeContext';
import { preloadImages } from '../src/utils/imagePreloader';

interface DashboardProps {
  onNavigate?: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { user: tgUser, status, showRecommendations, extendedInfo, isAdmin } = useTelegram();
  const { settings } = useTheme();
  const [history, setHistory] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      console.log("📊 Dashboard: Starting data fetch...");
      try {
        const historyPromise = api.getDownloadHistory();

        let recommendationsRes;
        const today = new Date().toDateString();
        const cachedRecs = localStorage.getItem('zeepub_daily_recs');
        const cachedDate = localStorage.getItem('zeepub_recs_date');

        if (showRecommendations) {
          if (cachedRecs && cachedDate === today) {
            try {
              const parsed = JSON.parse(cachedRecs);
              setRecommendations(parsed);
              preloadImages(parsed.map((r: any) => r.cover_thumb || r.cover || ''));
              recommendationsRes = { results: parsed }; // Already set
            } catch (e) {
              recommendationsRes = api.getRecommendations(4);
            }
          } else {
            recommendationsRes = api.getRecommendations(4);
          }
        }

        const [historyRes, recRes] = await Promise.all([
          historyPromise,
          recommendationsRes instanceof Promise ? recommendationsRes : Promise.resolve(recommendationsRes)
        ]);

        console.log("📊 Dashboard: Data received", { historyRes, recRes });

        if (historyRes && historyRes.downloads) {
          setHistory(historyRes.downloads);
        }

        if (showRecommendations && recRes && recRes.results && !(cachedRecs && cachedDate === today)) {
          setRecommendations(recRes.results);
          localStorage.setItem('zeepub_daily_recs', JSON.stringify(recRes.results));
          localStorage.setItem('zeepub_recs_date', today);
          // Preload recommendation thumbnails for faster grid viewing
          const covers = recRes.results.map((r: any) => r.cover_thumb || r.cover || '');
          preloadImages(covers);
        }
      } catch (error) {
        console.error("❌ Dashboard data fetch failed", error);
      } finally {
        console.log("📊 Dashboard: Fetch finished.");
        setLoading(false);
      }
    };
    fetchData();
  }, [showRecommendations]);

  console.log("📊 Dashboard Rendering", { tgUser, status, extendedInfo });
  const userName = extendedInfo?.nickname || extendedInfo?.name || (tgUser ? `${tgUser.first_name}${tgUser.last_name ? ' ' + tgUser.last_name : ''}` : (status?.user?.username || "Lector"));
  const userLevel = status?.user?.status_label || "Lector";
  const downloadsUsed = status?.user?.downloads?.used || 0;
  const downloadsLimit = status?.user?.downloads?.limit || 0;
  const isUnlimited = status?.user?.downloads?.limit === -1 || status?.hasUnlimitedDownloads;
  const limitDisplay = isUnlimited ? "∞" : downloadsLimit;
  const totalDownloads = status?.user?.downloads?.total || 0;

  // Colorful card configurations (gradient borders when enabled) - matching icon colors
  const colorfulCardStyles = [
    { gradient: 'from-blue-500 to-cyan-400', shadow: 'shadow-blue-500/30' },
    { gradient: 'from-purple-500 to-pink-400', shadow: 'shadow-purple-500/30' },
    { gradient: 'from-green-500 to-emerald-400', shadow: 'shadow-green-500/30' },
    { gradient: 'from-amber-500 to-yellow-400', shadow: 'shadow-amber-500/30' },
  ];

  // Get colorful card opacity (default 0.95 = mostly opaque bg)
  const cardBgOpacity = settings.colorfulCardOpacity ?? 0.85;

  // Calculate percentage for progress bar
  let progressPercent = 0;
  if (!isUnlimited && downloadsLimit > 0) {
    progressPercent = (downloadsUsed / downloadsLimit) * 100;
  }

  return (
    <div className="max-w-[1800px] mx-auto px-4 md:px-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-8">

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* LEFT COLUMN (Main Content) */}
        <div className="lg:col-span-8 space-y-8">

          {/* Hero / Greeting */}
          <div className="pt-6 md:pt-4 relative group">
            <div className="absolute -top-20 -left-20 w-80 h-80 bg-primary/5 rounded-full blur-[100px] pointer-events-none animate-pulse-slow"></div>
            <div className="relative">
              <div className="flex items-center gap-3 mb-4 animate-in fade-in slide-in-from-left-4 duration-700">
                <span className="px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-[0.2em]">
                  Vista General
                </span>
                <div className="w-1.5 h-1.5 rounded-full bg-gray-600"></div>
                <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest">
                  {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                </span>
              </div>
              <h1 className="text-5xl md:text-6xl lg:text-8xl font-black text-gray-900 dark:text-white tracking-tighter mb-6 leading-[0.95] drop-shadow-2xl">
                Hola, <br />
                <span className="text-transparent bg-clip-text bg-gradient-to-br from-primary via-blue-400 to-indigo-500 animate-gradient-x">
                  {userName}
                </span> 👋
              </h1>
              <p className="text-gray-400 text-xl md:text-2xl mb-2 font-medium opacity-80 max-w-2xl leading-relaxed">
                {extendedInfo?.customStatus || "Hoy es un gran día para descubrir mundos nuevos a través de la lectura."}
              </p>

              {extendedInfo?.insignias && extendedInfo.insignias.length > 0 && (
                <div className="flex flex-wrap gap-2.5 mt-8">
                  {extendedInfo.insignias.map((badge, idx) => (
                    <div
                      key={idx}
                      className="px-5 py-2 rounded-2xl text-[10px] font-black uppercase tracking-widest bg-white/5 text-gray-300 border border-white/10 hover:border-primary/50 hover:bg-primary/10 hover:text-primary transition-all duration-500 cursor-default flex items-center gap-2 group/badge"
                    >
                      <div className="w-2 h-2 rounded-full bg-primary group-hover:scale-125 transition-transform shadow-[0_0_8px_rgba(var(--color-primary-rgb),0.5)]"></div>
                      {badge}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main Search Bar (Floating Glass) */}
          <div className="relative group w-full pt-4">
            <div className="absolute -inset-2 bg-gradient-to-r from-primary/30 via-purple-600/20 to-blue-500/30 rounded-[3rem] blur-3xl opacity-30 group-hover:opacity-60 transition duration-1000 group-hover:duration-500 animate-pulse-slow"></div>
            <div className="relative glass-panel rounded-[2.5rem] p-4 flex items-center shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5)] backdrop-blur-3xl border-white/10 ring-1 ring-white/5 transition-all duration-500 group-focus-within:ring-primary/40 group-focus-within:border-primary/40">
              <div className="pl-6 text-primary group-focus-within:scale-110 transition-transform duration-500">
                <Search className="w-8 h-8" strokeWidth={3} />
              </div>
              <input
                type="text"
                placeholder="Busca mundos, autores, historias..."
                aria-label="Buscar en la biblioteca"
                className="w-full bg-transparent text-white px-6 py-4 text-xl md:text-2xl placeholder-gray-600 focus:outline-none font-medium selection:bg-primary/30"
                onClick={() => onNavigate && onNavigate('search')}
              />
              <button
                onClick={() => onNavigate && onNavigate('search')}
                className="hidden sm:flex bg-primary hover:bg-primary/90 text-white px-10 py-4 rounded-2xl text-xs font-black uppercase tracking-[0.2em] transition-all shadow-[0_10px_25px_-5px_rgba(var(--color-primary-rgb),0.4)] active:scale-95 mr-2 group/btn relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover/btn:animate-shimmer"></div>
                Buscar
              </button>
            </div>
          </div>

          <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
            <h3 className="text-[11px] font-black text-primary/60 uppercase tracking-[0.3em] mb-6 px-1 drop-shadow-sm">Acceso Directo</h3>
            {(() => {
              const actions = [
                { id: 'search', icon: Search, label: 'Catálogo', desc: 'Explorar Todo', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', visible: true },
                { id: 'library', icon: Library, label: 'Biblioteca', desc: 'Mis Libros', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: status?.user?.has_library_access !== false },
                { id: 'requests', icon: BookOpen, label: 'Pedidos', desc: 'Solicitar Libros', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', visible: status?.user?.can_request_books !== false },
                { id: 'ai', icon: BrainCircuit, label: 'AI Hub', desc: 'IA Gardener', color: 'text-purple-500', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: isAdmin },
                { id: 'settings', icon: Settings, label: 'Ajustes', desc: 'Personalización', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', visible: true },
              ].filter(a => a.visible);

              const gridCols = 'grid-cols-2 sm:grid-cols-4';

              return (
                <div className={`grid gap-6 ${gridCols}`}>
                  {actions.map((item, i) => {
                    return (
                      <button
                        key={item.id}
                        onClick={() => onNavigate && onNavigate(item.id)}
                        className="group relative h-44 flex flex-col items-center justify-center text-center gap-4 cursor-pointer active:scale-95 hover:scale-[1.02] transition-all duration-500"
                        aria-label={`Acceder a ${item.label}`}
                      >
                        {/* Glow and Background */}
                        <div className={`absolute inset-0 rounded-[2.8rem] bg-[var(--panel-bg)] border border-[var(--panel-border)] group-hover:bg-white/[0.07] group-hover:border-white/20 group-hover:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] transition-all duration-700`}></div>

                        {/* Dynamic Icon Background Glow */}
                        <div className={`absolute w-16 h-16 rounded-full ${item.bg} blur-2xl opacity-0 group-hover:opacity-40 transition-opacity duration-700`}></div>

                        {/* Icon Container */}
                        <div className={`relative z-10 p-5 rounded-[1.6rem] ${item.bg} ${item.color} border border-white/5 shadow-inner group-hover:scale-110 group-hover:-translate-y-2 transition-all duration-700`}>
                          <item.icon className="w-8 h-8" strokeWidth={2.5} />
                        </div>

                        <div className="relative z-10">
                          <span className="block text-white font-black text-[13px] uppercase tracking-[0.15em] mb-1.5 drop-shadow-sm group-hover:text-primary transition-colors">{item.label}</span>
                          <span className="block text-gray-500 text-[10px] font-bold uppercase tracking-[0.2em] opacity-50 group-hover:opacity-100 transition-opacity duration-500">{item.desc}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              );
            })()}
          </div>


          {/* Recommendations Section */}
          {showRecommendations && (
            <div className="animate-in fade-in slide-in-from-bottom-8 duration-1000 delay-300">
              <div className="flex items-center justify-between mb-8">
                <div className="flex flex-col">
                  <h3 className="text-xs font-black text-gray-500 uppercase tracking-[0.25em] flex items-center gap-2 mb-1">
                    <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                    Selección Especial
                  </h3>
                  <span className="text-white text-xl font-black">Lecturas Recomendadas</span>
                </div>
                <button
                  onClick={() => onNavigate && onNavigate('search')}
                  className="px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest bg-[var(--panel-bg-subtle)] hover:bg-[var(--panel-bg)] text-gray-300 transition-all border border-[var(--panel-border)] flex items-center gap-2 group"
                >
                  Explorar Todo <ArrowRight className="w-3 h-3 group-hover:translate-x-1 transition-transform" />
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 md:gap-8">
                {loading ? (
                  Array(4).fill(0).map((_, i) => (
                    <div key={i} className="aspect-[2/3] rounded-[1.5rem] bg-[var(--panel-bg-subtle)] animate-shimmer border border-[var(--panel-border)] bg-gradient-to-r from-transparent via-white/5 to-transparent bg-[length:200%_100%] shadow-inner"></div>
                  ))
                ) : (
                  recommendations.map((book, i) => (
                    <div
                      key={i}
                      className="group cursor-pointer flex flex-col"
                      onClick={() => onNavigate && onNavigate(`book:${book.id}`)}
                    >
                      <div className="relative aspect-[2/3] rounded-[1.5rem] overflow-hidden mb-4 border border-[var(--panel-border)] shadow-2xl group-hover:scale-[1.04] group-hover:shadow-primary/30 transition-all duration-700 ring-1 ring-[var(--panel-border)]">
                        <img
                          src={book.cover_thumb || book.cover || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&q=80&w=200"}
                          alt={book.title}
                          className="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110"
                        />
                        {/* Type Badge */}
                        <div className="absolute top-3 right-3 z-10">
                          <span className="bg-black/80 backdrop-blur-md text-white text-[9px] font-black px-2 py-0.5 rounded-lg uppercase tracking-widest border border-white/10">
                            {book.book_type || 'EPUB'}
                          </span>
                        </div>
                        <div className="absolute top-10 right-3 z-10 flex flex-col gap-1.5 items-end">
                          {book.color_mode === 'color' && (
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-black bg-gradient-to-r from-orange-400 to-pink-500 text-white uppercase tracking-wider shadow-sm">
                              A Color
                            </span>
                          )}
                          {book.is_uncensored && (
                            <span className="px-1.5 py-0.5 rounded text-[8px] font-black bg-red-500/10 text-red-500 uppercase tracking-wider border border-red-500/30">
                              Sin Censura
                            </span>
                          )}
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-500 flex flex-col justify-end p-5">
                          <div className="flex items-center gap-1.5 text-yellow-400 mb-2">
                            <Star className="w-3 h-3 fill-current" />
                            <span className="text-xs font-black">{book.rating_average > 0 ? book.rating_average.toFixed(1) : '—'}</span>
                          </div>
                          <span className="text-sm font-black text-white leading-tight drop-shadow-lg">{book.cleanTitle || book.title}</span>
                          <span className="text-[10px] text-gray-400 mt-1 font-bold uppercase tracking-widest truncate">{book.author || 'Zeepub Author'}</span>
                          {book.categories && (
                            <span className="text-[9px] text-gray-500 font-medium italic mt-0.5 line-clamp-1 opacity-80">
                              {Array.isArray(book.categories) ? book.categories.join(', ') : book.categories}
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-center px-2">
                        <p className="text-sm font-black text-white truncate mb-0.5 group-hover:text-primary transition-colors">{book.cleanTitle || book.title}</p>
                        <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest opacity-60">Volumen {book.seriesIndex || (i + 1)}</p>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* New Admin/Tools Section */}
          <div className="animate-in fade-in slide-in-from-bottom-8 duration-700 delay-500 mt-12">
            <h3 className="text-[11px] font-black text-primary/60 uppercase tracking-[0.3em] mb-6 px-1 drop-shadow-sm">Panel de Control</h3>
            {(() => {
              const adminActions = [
                { id: 'downloads', icon: ArrowDownToLine, label: 'Descargas', desc: 'Mis Libros', color: 'text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20', visible: true },
                { id: 'upload', icon: Upload, label: 'Subir Epub', desc: 'Aportar Contenido', color: 'text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20', visible: status?.user?.can_upload_epub !== false },
                { id: 'admin?view=duplicates', icon: Copy, label: 'Duplicados', desc: 'Gestión DB', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', visible: isAdmin },
                { id: 'admin', icon: ShieldCheck, label: 'Admin Panel', desc: 'Sistema Global', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/20', visible: isAdmin },
                { id: 'admin?view=uploads', icon: History, label: 'Subidas', desc: 'Historial Global', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', visible: isAdmin },
                { id: 'admin?view=access', icon: ShieldHalf, label: 'Niveles', desc: 'Accesos', color: 'text-indigo-400', bg: 'bg-indigo-500/10', border: 'border-indigo-500/20', visible: isAdmin },
              ].filter(a => a.visible);

              const adminGridCols = adminActions.length > 4 ? 'grid-cols-2 md:grid-cols-3' : 'grid-cols-2 sm:grid-cols-4';

              return (
                <div className={`grid gap-5 ${adminGridCols}`}>
                  {adminActions.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => onNavigate && onNavigate(item.id)}
                      className="group relative h-36 flex flex-col items-center justify-center text-center gap-3 cursor-pointer active:scale-95 hover:scale-[1.02] transition-all duration-500"
                      aria-label={`Administrar ${item.label}`}
                    >
                      <div className={`absolute inset-0 rounded-[2.2rem] bg-[var(--panel-bg)] border border-[var(--panel-border)] group-hover:bg-white/[0.05] group-hover:border-white/20 group-hover:shadow-[0_20px_40px_-10px_rgba(0,0,0,0.4)] transition-all duration-700`}></div>

                      <div className={`relative z-10 p-4 rounded-2xl ${item.bg} ${item.color} border border-white/5 shadow-inner group-hover:scale-110 group-hover:-translate-y-2 transition-all duration-700`}>
                        <item.icon className="w-6 h-6" strokeWidth={2.5} />
                      </div>

                      <div className="relative z-10">
                        <span className="block text-white font-black text-[11px] uppercase tracking-[0.12em] mb-1 group-hover:text-primary transition-colors">{item.label}</span>
                        <span className="block text-gray-500 text-[9px] font-bold uppercase tracking-[0.15em] opacity-50 group-hover:opacity-100 transition-opacity duration-500">{item.desc}</span>
                      </div>
                    </button>
                  ))}
                </div>
              );
            })()}
          </div>

        </div>

        {/* RIGHT COLUMN (Sidebar Widgets for Desktop) */}
        <div className="lg:col-span-4 space-y-6">

          {/* Profile / Stats Widget */}
          <div className="glass-panel rounded-[3rem] p-10 relative overflow-hidden group hover:scale-[1.01] transition-all duration-700 shadow-premium border-white/10">
            <div
              className="absolute -top-32 -right-32 w-80 h-80 bg-primary/10 rounded-full blur-[120px] group-hover:bg-primary/20 transition-all duration-1000 pointer-events-none"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>

            <div className="flex items-center gap-6 mb-12 relative z-10">
              <div className="relative group/avatar">
                <div className="absolute -inset-2 bg-gradient-to-tr from-primary via-purple-500 to-blue-400 rounded-3xl blur opacity-30 group-hover/avatar:opacity-80 transition duration-700 animate-pulse"></div>
                <div className="relative w-24 h-24 rounded-[2rem] p-[3px] bg-white/10 overflow-hidden shadow-2xl">
                  <div className="w-full h-full rounded-[1.85rem] bg-[#0a0a0c] flex items-center justify-center overflow-hidden">
                    <img
                      src={tgUser?.photo_url || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=200"}
                      alt="Profile"
                      className="w-full h-full object-cover group-hover/avatar:scale-110 transition duration-1000"
                    />
                  </div>
                  <div className="absolute bottom-1 right-1 w-7 h-7 bg-green-500 border-4 border-[#0a0a0c] rounded-full shadow-lg z-20"></div>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-white font-black text-3xl tracking-tighter leading-none mb-2 truncate">{userLevel}</h3>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="px-2 py-0.5 rounded-lg bg-primary/20 text-primary text-[9px] font-black uppercase tracking-[0.2em] border border-primary/20">{status?.user?.role || "Free Member"}</span>
                  <div className="w-1.5 h-1.5 rounded-full bg-white/10"></div>
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest truncate">{tgUser?.username ? `@${tgUser.username}` : `ID: ${tgUser?.id}`}</span>
                </div>
              </div>
            </div>

            <div className="space-y-10 relative z-10">
              <div className="bg-white/[0.03] rounded-[2.5rem] p-8 border border-white/5 shadow-inner backdrop-blur-3xl relative overflow-hidden group/quota">
                <div className="absolute -top-6 -right-6 p-2 opacity-[0.03] rotate-12">
                  <Zap className="w-32 h-32 text-primary" />
                </div>
                <div className="flex justify-between items-end mb-6 relative z-10">
                  <div className="flex flex-col gap-1">
                    <span className="text-gray-500 text-[10px] font-black uppercase tracking-[0.25em] flex items-center gap-2">
                      <Zap className="w-4 h-4 text-primary animate-pulse" />
                      Consumo Diario
                    </span>
                    <span className="text-white font-black text-4xl tracking-tighter">{downloadsUsed}</span>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <span className="text-gray-700 text-[8px] font-black uppercase tracking-widest">Límite Total</span>
                    <span className="text-gray-500 font-black text-xl tracking-tighter">/ {limitDisplay}</span>
                  </div>
                </div>

                {!isUnlimited && (
                  <div className="relative w-full h-3 bg-black/40 rounded-full overflow-hidden p-[1px] border border-white/5 shadow-inner">
                    <div className="absolute inset-0 bg-primary/10 blur-[4px]"></div>
                    <div
                      className="relative h-full bg-gradient-to-r from-primary via-blue-400 to-indigo-500 rounded-full shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.6)] transition-all duration-1000 ease-out-expo"
                      style={{ width: `${progressPercent}%` }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                    </div>
                  </div>
                )}
                {isUnlimited && (
                  <div className="w-full h-2.5 bg-gradient-to-r from-amber-500/20 via-yellow-400/40 to-amber-200/20 rounded-full animate-shimmer bg-[length:200%_100%]"></div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-6">
                <div className="glass-panel rounded-[2rem] p-6 border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] hover:border-white/20 transition-all duration-700">
                  <div className="p-4 bg-blue-500/10 rounded-2xl text-blue-400 mb-4 border border-blue-500/10 shadow-xl group-hover/stat:scale-110 group-hover/stat:rotate-3 transition-all duration-700">
                    <TrendingUp className="w-6 h-6" strokeWidth={2.5} />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tighter">Top 5%</span>
                  <span className="text-[10px] text-gray-500 uppercase font-black tracking-widest mt-2 opacity-50">Status Ranking</span>
                </div>
                <div className="glass-panel rounded-[2rem] p-6 border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] hover:border-white/20 transition-all duration-700">
                  <div className="p-4 bg-primary/10 rounded-2xl text-primary mb-4 border border-primary/10 shadow-xl group-hover/stat:scale-110 group-hover/stat:-rotate-3 transition-all duration-700">
                    <Download className="w-6 h-6" strokeWidth={2.5} />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tighter">{totalDownloads}</span>
                  <span className="text-[10px] text-gray-500 uppercase font-black tracking-widest mt-2 opacity-50">Libros Leídos</span>
                </div>
              </div>
            </div>
          </div>

          {/* Recent Activity Feed */}
          <div className="glass-panel p-8 rounded-[2.5rem] relative overflow-hidden group">
            <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.3em] mb-6 flex items-center justify-between">
              Actividad Reciente
              <Clock className="w-3.5 h-3.5 opacity-40" />
            </h4>
            <div className="space-y-5">
              {[
                { action: 'Descargado', title: 'Oregairu Vol. 14', time: 'Hace 2h', icon: Download, color: 'text-primary' },
                { action: 'Agregado', title: 'Mushoku Tensei Especial', time: 'Ayer', icon: Star, color: 'text-yellow-500' },
              ].map((act, i) => (
                <div key={i} className="flex items-center gap-4 group/item">
                  <div className={`p-2 rounded-xl bg-[var(--panel-bg-subtle)] ${act.color} group-hover/item:scale-110 transition-transform`}>
                    <act.icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-white truncate">{act.title}</p>
                    <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mt-0.5">{act.action} • {act.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Daily Quote / Tip */}
          <div className="glass-panel p-10 rounded-[2.5rem] border border-white/5 bg-gradient-to-br from-primary/10 via-transparent to-transparent relative overflow-hidden group shadow-2xl">
            <div className="absolute -top-10 -left-10 text-white opacity-[0.03] font-black text-9xl">“</div>
            <p className="text-gray-300 text-base italic font-medium leading-relaxed relative z-10 text-center px-4">"Un lector vive mil vidas antes de morir. Aquel que nunca lee vive solo una."</p>
            <div className="flex items-center justify-center gap-4 mt-6 relative z-10">
              <div className="w-8 h-px bg-white/10"></div>
              <p className="text-primary text-[10px] font-black uppercase tracking-[0.2em] opacity-80">George R.R. Martin</p>
              <div className="w-8 h-px bg-white/10"></div>
            </div>
            <div
              className="absolute -right-8 -bottom-8 w-32 h-32 bg-primary/5 rounded-full blur-3xl group-hover:scale-150 transition-all duration-1000"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>
          </div>

        </div>

      </div>
    </div>
  );
};