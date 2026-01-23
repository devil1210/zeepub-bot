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
  RefreshCw
} from 'lucide-react';
import { api } from '../src/services/api';
import { useTelegram } from '../contexts/TelegramContext';
import { useTheme } from '../contexts/ThemeContext';
import { preloadImages } from '../src/utils/imagePreloader';

interface DashboardProps {
  onNavigate?: (tab: string) => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const { user: tgUser, status, showRecommendations, extendedInfo } = useTelegram();
  const { settings } = useTheme();
  const [history, setHistory] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
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
        console.error("Dashboard data fetch failed", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [showRecommendations]);

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
    <div className="max-w-[1600px] mx-auto px-4 md:px-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-8">

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* LEFT COLUMN (Main Content) */}
        <div className="lg:col-span-8 space-y-8">

          {/* Hero / Greeting */}
          <div className="pt-4 md:pt-2">
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black text-gray-900 dark:text-white tracking-tight mb-3">
              Hola, <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-400 dark:to-blue-400">{userName}</span> 👋
            </h1>
            <p className="text-gray-400 text-lg mb-2">
              {extendedInfo?.customStatus || "Tu biblioteca personal está lista."}
            </p>
            {extendedInfo?.insignias && extendedInfo.insignias.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {extendedInfo.insignias.map((badge, idx) => (
                  <button
                    key={idx}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 animate-in zoom-in duration-300 hover:bg-primary/20 hover:border-primary/40 hover:scale-105 transition-all cursor-pointer"
                    style={{ animationDelay: `${idx * 100}ms` }}
                    onClick={() => {
                      // Toggle edit mode or show badge options
                      if (typeof (window as any).Telegram?.WebApp?.showAlert === 'function') {
                        (window as any).Telegram.WebApp.showAlert(`Badge: ${badge}\n\nFunción de edición próximamente...`);
                      } else {
                        alert(`Badge: ${badge}\n\nFunción de edición próximamente...`);
                      }
                    }}
                    title={`Click para editar: ${badge}`}
                  >
                    {badge}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Main Search Bar */}
          <div className="relative group w-full">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-600 rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative glass-panel rounded-2xl p-2 flex items-center border border-white/10 shadow-2xl">
              <div className="pl-4 text-gray-400">
                <Search className="w-6 h-6" />
              </div>
              <input
                type="text"
                placeholder="Busca por título, autor, género o ISBN..."
                className="w-full bg-transparent text-white p-4 text-base md:text-lg placeholder-gray-500 focus:outline-none"
                onClick={() => onNavigate && onNavigate('search')}
              />
              <button
                onClick={() => onNavigate && onNavigate('search')}
                className="hidden sm:flex bg-white/10 hover:bg-white/20 text-white px-6 py-2.5 rounded-xl text-sm font-bold transition-all border border-white/5 mr-2"
              >
                Buscar
              </button>
            </div>
          </div>

          <div>
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.2em] mb-6 px-1">Acciones Rápidas</h3>
            {(() => {
              const actions = [
                { id: 'search', icon: Search, label: 'Catálogo', desc: 'Explorar', color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/20', glow: 'bg-blue-500/10', visible: true },
                { id: 'library', icon: Library, label: 'Mi Biblioteca', desc: 'Mis Libros', color: 'text-purple-400', bg: 'bg-purple-500/20', border: 'border-purple-500/20', glow: 'bg-purple-500/10', visible: status?.user?.has_library_access !== false },
                { id: 'requests', icon: BookOpen, label: 'Solicitar', desc: 'Pedir Libro', color: 'text-emerald-400', bg: 'bg-emerald-500/20', border: 'border-emerald-500/20', glow: 'bg-emerald-500/10', visible: status?.user?.can_request_books !== false },
                { id: 'settings', icon: Settings, label: 'Ajustes', desc: 'Configuración', color: 'text-amber-400', bg: 'bg-amber-500/20', border: 'border-amber-500/20', glow: 'bg-amber-500/10', visible: true },
              ].filter(a => a.visible);

              const gridCols = actions.length === 2 ? 'grid-cols-2' :
                actions.length === 3 ? 'grid-cols-2 sm:grid-cols-3' :
                  'grid-cols-2 sm:grid-cols-4';

              return (
                <div className={`grid gap-6 ${gridCols}`}>
                  {actions.map((item, i) => {
                    return (
                      <button
                        key={item.id}
                        onClick={() => onNavigate && onNavigate(item.id)}
                        className={`glass-panel relative p-6 rounded-[2rem] flex flex-col items-center justify-center text-center gap-4 hover:scale-[1.03] active:scale-95 transition-all duration-300 group shadow-xl overflow-hidden`}
                      >
                        <div className={`relative z-10 p-5 rounded-3xl ${item.bg} ${item.color} border border-white/5 shadow-inner group-hover:scale-110 transition-transform duration-500`}>
                          <item.icon className="w-8 h-8" strokeWidth={2} />
                        </div>
                        <div className="relative z-10">
                          <span className="block text-white font-black text-sm uppercase tracking-wider mb-1 mt-1">{item.label}</span>
                          <span className="block text-gray-500 text-[10px] font-black uppercase tracking-widest opacity-60">{item.desc}</span>
                        </div>

                        {/* Background Glow */}
                        <div
                          className={`absolute -right-8 -bottom-8 w-24 h-24 ${item.glow} rounded-full blur-2xl group-hover:scale-150 transition-all duration-700`}
                          style={{ opacity: settings.cardGlowIntensity }}
                        />
                      </button>
                    );
                  })}
                </div>
              );
            })()}
          </div>


          {/* Recommendations Section */}
          {showRecommendations && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 delay-200">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-sm font-black text-gray-500 uppercase tracking-widest flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-500" />
                  Recomendados para ti
                </h3>
                <button
                  onClick={() => onNavigate && onNavigate('search')}
                  className="text-[10px] font-black text-primary hover:text-white uppercase tracking-widest bg-primary/5 hover:bg-primary px-3 py-1.5 rounded-lg border border-primary/20 transition-all flex items-center gap-1"
                >
                  Ver Catálogo <ArrowRight className="w-3 h-3" />
                </button>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
                {loading ? (
                  Array(4).fill(0).map((_, i) => (
                    <div key={i} className="aspect-[2/3] rounded-2xl bg-white/5 animate-pulse border border-white/5 shadow-inner"></div>
                  ))
                ) : (
                  recommendations.map((book, i) => (
                    <div
                      key={i}
                      className="group cursor-pointer flex flex-col"
                      onClick={() => onNavigate && onNavigate(`book:${book.id}`)}
                    >
                      <div className="relative aspect-[2/3] rounded-2xl overflow-hidden mb-3 border border-white/10 shadow-2xl group-hover:scale-[1.05] group-hover:shadow-primary/20 transition-all duration-500 ring-1 ring-white/5">
                        <img
                          src={book.cover_thumb || book.cover || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&q=80&w=200"}
                          alt={book.title}
                          className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                        />
                        {/* Type Badge */}
                        <div className="absolute top-2 right-2 z-10">
                          <span className="bg-black/60 backdrop-blur text-white text-[8px] font-bold px-1.5 py-0.5 rounded-md uppercase tracking-wider border border-white/10 shadow-sm">
                            {book.book_type === 'NL' ? 'Novela Ligera' : book.book_type === 'NW' ? 'Novela Web' : book.book_type || 'EPUB'}
                          </span>
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
                          <div className="flex items-center gap-1 text-yellow-400 mb-1">
                            <Star className="w-2.5 h-2.5 fill-current" />
                            <span className="text-[10px] font-bold">{book.rating_average || 'N/A'}</span>
                          </div>
                          <span className="text-[10px] font-black text-white line-clamp-2 leading-tight">{book.cleanTitle || book.title}</span>
                        </div>
                      </div>
                      <p className="text-[11px] font-bold text-gray-400 truncate px-1 group-hover:text-primary transition-colors text-center">{book.cleanTitle || book.title}</p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

        </div>

        {/* RIGHT COLUMN (Sidebar Widgets for Desktop) */}
        <div className="lg:col-span-4 space-y-6">

          {/* Profile / Stats Widget */}
          <div className="glass-panel rounded-[2.5rem] p-8 relative overflow-hidden group hover:scale-[1.01] transition-all duration-500 shadow-2xl">
            <div
              className="absolute -top-12 -right-12 w-48 h-48 bg-primary/10 rounded-full blur-[80px] group-hover:bg-primary/20 transition-all duration-700 pointer-events-none"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>

            <div className="flex items-center justify-between mb-8 relative z-10">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-3xl p-1 bg-gradient-to-tr from-yellow-400 via-amber-500 to-yellow-600 shadow-[0_10px_30px_-5px_rgba(245,158,11,0.3)] flex items-center justify-center relative group-hover:scale-105 transition-transform duration-500">
                  <div className="w-full h-full rounded-[1.25rem] bg-[#0a0a0a] flex items-center justify-center overflow-hidden">
                    <span className="text-3xl">👤</span>
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 border-4 border-[#0a0a0a] rounded-full shadow-lg"></div>
                </div>
                <div>
                  <h3 className="text-white font-black text-xl tracking-tight leading-none">{userLevel}</h3>
                  <p className="text-[10px] text-primary font-black uppercase tracking-[0.2em] mt-2 opacity-80">{status?.user?.role || "Free"}</p>
                </div>
              </div>
            </div>

            <div className="space-y-6 relative z-10">
              <div className="bg-white/[0.03] rounded-3xl p-6 border border-white/5 shadow-inner">
                <div className="flex justify-between items-end mb-3">
                  <span className="text-gray-400 text-[10px] font-black uppercase tracking-widest flex items-center gap-2">
                    <Zap className="w-3.5 h-3.5 text-primary" />
                    Cuota Diaria
                  </span>
                  <span className="text-white font-black text-base">{downloadsUsed} <span className="text-gray-600 font-bold ml-1">/ {limitDisplay}</span></span>
                </div>
                {!isUnlimited && (
                  <div className="w-full h-3 bg-white/[0.05] rounded-full overflow-hidden p-[2px] border border-white/5">
                    <div className="h-full bg-gradient-to-r from-primary via-blue-400 to-primary rounded-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)] transition-all duration-1000" style={{ width: `${progressPercent}%` }}></div>
                  </div>
                )}
                {isUnlimited && (
                  <div className="w-full h-3 bg-gradient-to-r from-yellow-500 via-amber-400 to-yellow-200 rounded-full opacity-30 blur-[1px]"></div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="glass-panel rounded-3xl p-5 border border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] transition-all">
                  <div className="p-3 bg-green-500/20 rounded-2xl text-green-400 mb-3 border border-green-500/20 shadow-lg shadow-green-500/5 group-hover/stat:scale-110 transition-transform">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tight">Top 5%</span>
                  <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest mt-1">Ranking</span>
                </div>
                <div className="glass-panel rounded-3xl p-5 border border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] transition-all">
                  <div className="p-3 bg-primary/20 rounded-2xl text-primary mb-3 border border-primary/20 shadow-lg shadow-primary/5 group-hover/stat:scale-110 transition-transform">
                    <Download className="w-5 h-5" />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tight">{totalDownloads}</span>
                  <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest mt-1">Total DLS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Quote / Tip */}
          <div className="glass-panel p-8 rounded-[2rem] border border-white/5 bg-gradient-to-br from-white/5 to-transparent relative overflow-hidden group">
            <p className="text-gray-300 text-sm italic font-medium leading-relaxed relative z-10">"Un lector vive mil vidas antes de morir. Aquel que nunca lee vive solo una."</p>
            <p className="text-gray-500 text-[10px] font-black uppercase tracking-widest mt-4 text-right relative z-10 opacity-60">— George R.R. Martin</p>
            <div
              className="absolute -right-4 -bottom-4 w-16 h-16 bg-white/5 rounded-full blur-xl group-hover:scale-150 transition-all duration-700"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>
          </div>

        </div>

      </div>
    </div>
  );
};