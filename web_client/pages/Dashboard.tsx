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
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold bg-primary/10 text-primary border border-primary/20 animate-in zoom-in duration-300"
                    style={{ animationDelay: `${idx * 100}ms` }}
                  >
                    {badge}
                  </span>
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

          {/* Quick Actions Grid */}
          <div>
            <h3 className="text-sm font-bold text-gray-500 uppercase tracking-widest mb-4">Acciones Rápidas</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              {[
                { id: 'search', icon: Search, label: 'Catálogo', desc: 'Explorar', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-500/10', border: 'border-blue-500/20' },
                { id: 'library', icon: Library, label: 'Mi Biblioteca', desc: 'Mis Libros', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-500/10', border: 'border-purple-500/20' },
                { id: 'requests', icon: BookOpen, label: 'Solicitar', desc: 'Pedir Libro', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20' },
                { id: 'settings', icon: Settings, label: 'Ajustes', desc: 'Configuración', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20' },
              ].map((item, i) => {
                const colorStyle = colorfulCardStyles[i];
                return (
                  <button
                    key={i}
                    onClick={() => onNavigate && onNavigate(item.id)}
                    className={`relative p-5 rounded-2xl flex flex-col items-center justify-center text-center gap-3 hover:scale-[1.02] active:scale-95 transition-all duration-300 group shadow-lg overflow-hidden ${settings.colorfulCards ? colorStyle.shadow : ''}`}
                  >
                    {/* Gradient border effect when colorful cards enabled */}
                    {settings.colorfulCards && (
                      <div className={`absolute inset-0 bg-gradient-to-br ${colorStyle.gradient} rounded-2xl`}></div>
                    )}
                    <div
                      className={`absolute inset-[2px] rounded-xl ${settings.colorfulCards ? '' : 'glass-panel'}`}
                      style={settings.colorfulCards ? { background: `rgba(17, 24, 39, ${cardBgOpacity})` } : {}}
                    ></div>
                    <div className={`relative z-10 p-4 rounded-full ${item.bg} ${item.color} group-hover:scale-110 transition-transform duration-300 shadow-[0_0_15px_rgba(0,0,0,0.3)]`}>
                      <item.icon className="w-7 h-7" strokeWidth={1.5} />
                    </div>
                    <div className="relative z-10">
                      <span className="block text-gray-900 dark:text-white font-bold text-base leading-none mb-1">{item.label}</span>
                      <span className="block text-gray-500 text-[10px] font-medium uppercase tracking-wider">{item.desc}</span>
                    </div>
                  </button>
                )
              })}
            </div>
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
                        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-3">
                          <div className="flex items-center gap-1 text-yellow-400 mb-1">
                            <Star className="w-2.5 h-2.5 fill-current" />
                            <span className="text-[10px] font-bold">{book.rating_average || 'N/A'}</span>
                          </div>
                          <span className="text-[10px] font-black text-white line-clamp-2 leading-tight">{book.title}</span>
                        </div>
                      </div>
                      <p className="text-[11px] font-bold text-gray-400 truncate px-1 group-hover:text-primary transition-colors text-center">{book.title}</p>
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
          <div className="glass-panel rounded-3xl p-6 border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 rounded-full blur-[60px] pointer-events-none"></div>

            <div className="flex items-center justify-between mb-6 relative z-10">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full p-[2px] bg-gradient-to-tr from-yellow-400 to-yellow-600 shadow-lg flex items-center justify-center bg-black">
                  <span className="text-xl">👤</span>
                </div>
                <div>
                  <h3 className="text-gray-900 dark:text-white font-bold leading-none">{userLevel}</h3>
                  <p className="text-xs text-yellow-500 font-bold uppercase tracking-wider mt-1">{status?.user?.role || "Free"}</p>
                </div>
              </div>
            </div>

            <div className="space-y-4 relative z-10">
              <div className="bg-black/20 rounded-xl p-4 border border-white/5">
                <div className="flex justify-between items-end mb-2">
                  <span className="text-gray-400 text-xs font-bold uppercase tracking-wider flex items-center gap-2">
                    <Zap className="w-3 h-3 text-primary" />
                    Cuota Diaria
                  </span>
                  <span className="text-gray-900 dark:text-white font-bold">{downloadsUsed} <span className="text-gray-500 font-normal">/ {limitDisplay}</span></span>
                </div>
                {!isUnlimited && (
                  <div className="w-full h-2 bg-gray-800 rounded-full overflow-hidden">
                    <div className="h-full bg-gradient-to-r from-primary to-blue-400 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.5)]" style={{ width: `${progressPercent}%` }}></div>
                  </div>
                )}
                {isUnlimited && (
                  <div className="w-full h-2 bg-gradient-to-r from-yellow-500 to-yellow-200 rounded-full opacity-50"></div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-black/5 dark:bg-white/5 rounded-xl p-3 border border-black/5 dark:border-white/5 flex flex-col items-center justify-center text-center">
                  <TrendingUp className="w-5 h-5 text-green-500 mb-1" />
                  <span className="text-gray-900 dark:text-white font-bold text-lg">Top 5%</span>
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Ranking</span>
                </div>
                <div className="bg-black/5 dark:bg-white/5 rounded-xl p-3 border border-black/5 dark:border-white/5 flex flex-col items-center justify-center text-center">
                  <Download className="w-5 h-5 text-primary mb-1" />
                  <span className="text-gray-900 dark:text-white font-bold text-lg">{totalDownloads}</span>
                  <span className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Total DLS</span>
                </div>
              </div>
            </div>
          </div>

          {/* Daily Quote / Tip */}
          <div className="glass-panel p-5 rounded-2xl border border-white/5 bg-gradient-to-br from-white/5 to-transparent">
            <p className="text-gray-300 text-sm italic leading-relaxed">"Un lector vive mil vidas antes de morir. Aquel que nunca lee vive solo una."</p>
            <p className="text-gray-500 text-xs font-bold mt-3 text-right">— George R.R. Martin</p>
          </div>

        </div>

      </div>
    </div>
  );
};