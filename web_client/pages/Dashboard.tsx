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
  ArrowDownToLine
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
    <div className="max-w-[1600px] mx-auto px-4 md:px-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-8">

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

        {/* LEFT COLUMN (Main Content) */}
        <div className="lg:col-span-8 space-y-8">

          {/* Hero / Greeting */}
          <div className="pt-4 md:pt-2 relative group">
            <div className="absolute -inset-4 bg-gradient-to-r from-primary/10 to-transparent rounded-[3rem] blur-3xl opacity-0 group-hover:opacity-100 transition duration-1000"></div>
            <div className="relative">
              <h1 className="text-4xl md:text-5xl lg:text-7xl font-black text-gray-900 dark:text-white tracking-tighter mb-4 leading-[1.1]">
                Hola, <span className="text-transparent bg-clip-text bg-gradient-to-br from-primary via-blue-400 to-indigo-500 animate-gradient-x">{userName}</span> 👋
              </h1>
              <p className="text-gray-400 text-xl mb-4 font-medium opacity-80 max-w-xl">
                {extendedInfo?.customStatus || "Hoy es un gran día para descubrir mundos nuevos a través de la lectura."}
              </p>
              {extendedInfo?.insignias && extendedInfo.insignias.length > 0 && (
                <div className="flex flex-wrap gap-2.5 mt-4">
                  {extendedInfo.insignias.map((badge, idx) => (
                    <div
                      key={idx}
                      className="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest bg-[var(--panel-bg-subtle)] text-gray-300 border border-[var(--panel-border)] hover:border-primary/50 hover:bg-primary/10 hover:text-primary transition-all duration-300 cursor-default flex items-center gap-2"
                    >
                      <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></div>
                      {badge}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Main Search Bar (Floating Glass) */}
          <div className="relative group w-full">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary/20 via-purple-600/20 to-blue-500/20 rounded-[2.5rem] blur-2xl opacity-50 group-hover:opacity-100 transition duration-1000 group-hover:duration-500"></div>
            <div className="relative glass-panel rounded-[2rem] p-3 flex items-center shadow-2xl backdrop-blur-2xl">
              <div className="pl-6 text-primary">
                <Search className="w-7 h-7" strokeWidth={2.5} />
              </div>
              <input
                type="text"
                placeholder="Busca mundos, autores, historias..."
                className="w-full bg-transparent text-white p-5 text-lg md:text-xl placeholder-gray-500 focus:outline-none font-medium"
                onClick={() => onNavigate && onNavigate('search')}
              />
              <button
                onClick={() => onNavigate && onNavigate('search')}
                className="hidden sm:flex bg-primary hover:bg-primary/90 text-white px-8 py-3.5 rounded-2xl text-sm font-black uppercase tracking-widest transition-all shadow-lg shadow-primary/20 active:scale-95 mr-2"
              >
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
                { id: 'settings', icon: Settings, label: 'Ajustes', desc: 'Personalización', color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/20', visible: true },
              ].filter(a => a.visible);

              const gridCols = 'grid-cols-2 sm:grid-cols-4';

              return (
                <div className={`grid gap-5 ${gridCols}`}>
                  {actions.map((item, i) => {
                    return (
                      <button
                        key={item.id}
                        onClick={() => onNavigate && onNavigate(item.id)}
                        className="group relative h-40 flex flex-col items-center justify-center text-center gap-3 active:scale-95 transition-all duration-500"
                      >
                        {/* Glow and Background */}
                        <div className={`absolute inset-0 rounded-[2.5rem] bg-[var(--panel-bg)] border border-[var(--panel-border)] group-hover:bg-[var(--panel-bg-lighter)] group-hover:border-[var(--panel-border-hover)] group-hover:shadow-2xl transition-all duration-500`}></div>
                        <div className={`absolute -inset-0.5 bg-gradient-to-br from-white/10 to-transparent rounded-[2.5rem] opacity-0 group-hover:opacity-10 transition duration-500`}></div>

                        {/* Icon Circle */}
                        <div className={`relative z-10 p-4 rounded-2xl ${item.bg} ${item.color} border border-[var(--panel-border)] shadow-inner group-hover:scale-110 group-hover:-translate-y-1 transition-all duration-500`}>
                          <item.icon className="w-7 h-7" strokeWidth={2.5} />
                        </div>

                        <div className="relative z-10">
                          <span className="block text-white font-black text-xs uppercase tracking-[0.1em] mb-1">{item.label}</span>
                          <span className="block text-gray-500 text-[9px] font-bold uppercase tracking-widest opacity-60 group-hover:opacity-100 transition-opacity">{item.desc}</span>
                        </div>

                        {/* Hover Decorative Element */}
                        <div className={`absolute bottom-6 w-1 h-1 rounded-full ${item.bg.replace('bg-', 'bg-').split('/')[0]} opacity-0 group-hover:opacity-100 group-hover:scale-[3] transition-all duration-500`}></div>
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
                      className="group relative h-32 flex flex-col items-center justify-center text-center gap-2 active:scale-95 transition-all duration-500"
                    >
                      <div className={`absolute inset-0 rounded-[2rem] bg-[var(--panel-bg)] border border-[var(--panel-border)] group-hover:bg-[var(--panel-bg-lighter)] group-hover:border-[var(--panel-border-hover)] group-hover:shadow-2xl transition-all duration-500`}></div>
                      <div className={`relative z-10 p-3 rounded-xl ${item.bg} ${item.color} border border-[var(--panel-border)] shadow-inner group-hover:scale-110 group-hover:-translate-y-1 transition-all duration-500`}>
                        <item.icon className="w-6 h-6" strokeWidth={2.5} />
                      </div>
                      <div className="relative z-10">
                        <span className="block text-white font-black text-[10px] uppercase tracking-[0.1em] mb-0.5">{item.label}</span>
                        <span className="block text-gray-500 text-[8px] font-bold uppercase tracking-widest opacity-60 group-hover:opacity-100 transition-opacity">{item.desc}</span>
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
          <div className="glass-panel rounded-[2.5rem] p-8 relative overflow-hidden group hover:scale-[1.01] transition-all duration-700 shadow-premium">
            <div
              className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 rounded-full blur-[100px] group-hover:bg-primary/20 transition-all duration-1000 pointer-events-none"
              style={{ opacity: settings.cardGlowIntensity }}
            ></div>

            <div className="flex items-center gap-5 mb-10 relative z-10">
              <div className="relative group/avatar">
                <div className="absolute -inset-1.5 bg-gradient-to-tr from-primary via-purple-500 to-blue-400 rounded-[2rem] blur opacity-40 group-hover/avatar:opacity-100 transition duration-700 animate-pulse"></div>
                <div className="relative w-20 h-20 rounded-[1.75rem] p-[2px] bg-white/10 overflow-hidden shadow-2xl">
                  <div className="w-full h-full rounded-[1.6rem] bg-[#0a0a0c] flex items-center justify-center overflow-hidden">
                    <img
                      src={tgUser?.photo_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"}
                      alt="Profile"
                      className="w-full h-full object-cover group-hover/avatar:scale-110 transition duration-1000"
                    />
                  </div>
                  <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 border-[3px] border-[#0a0a0c] rounded-full shadow-lg z-20"></div>
                </div>
              </div>
              <div>
                <h3 className="text-white font-black text-2xl tracking-tighter leading-none mb-1">{userLevel}</h3>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-primary font-black uppercase tracking-[0.2em]">{status?.user?.role || "Free Member"}</span>
                  <div className="w-1 h-1 rounded-full bg-white/20"></div>
                  <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">{tgUser?.username ? `@${tgUser.username}` : `ID: ${tgUser?.id}`}</span>
                </div>
              </div>
            </div>

            <div className="space-y-8 relative z-10">
              <div className="bg-[var(--panel-bg-subtle)] rounded-[2rem] p-6 border border-[var(--panel-border)] shadow-inner backdrop-blur-md relative overflow-hidden group/quota">
                <div className="absolute top-0 right-0 p-2 opacity-5">
                  <Zap className="w-20 h-20 text-primary" />
                </div>
                <div className="flex justify-between items-end mb-4 relative z-10">
                  <span className="text-gray-400 text-[10px] font-black uppercase tracking-[0.2em] flex items-center gap-2">
                    <Zap className="w-4 h-4 text-primary animate-pulse" />
                    Consumo Diario
                  </span>
                  <div className="flex items-baseline gap-1">
                    <span className="text-white font-black text-2xl tracking-tighter">{downloadsUsed}</span>
                    <span className="text-gray-600 font-bold text-sm uppercase">/ {limitDisplay}</span>
                  </div>
                </div>
                {!isUnlimited && (
                  <div className="relative w-full h-2.5 bg-black/40 rounded-full overflow-hidden p-[1px] border border-[var(--panel-border)]">
                    <div className="absolute inset-0 bg-primary/20 blur-[2px]"></div>
                    <div className="relative h-full bg-gradient-to-r from-primary via-blue-400 to-indigo-500 rounded-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)] transition-all duration-1000 ease-out" style={{ width: `${progressPercent}%` }}></div>
                  </div>
                )}
                {isUnlimited && (
                  <div className="w-full h-2 bg-gradient-to-r from-yellow-500/20 via-amber-400/40 to-yellow-200/20 rounded-full animate-shimmer bg-[length:200%_100%]"></div>
                )}
              </div>

              <div className="grid grid-cols-2 gap-5">
                <div className="glass-panel rounded-[1.75rem] p-5 border-[var(--panel-border)] flex flex-col items-center justify-center text-center group/stat hover:bg-[var(--panel-bg-lighter)] hover:border-[var(--panel-border-hover)] transition-all duration-500">
                  <div className="p-3 bg-green-500/10 rounded-2xl text-green-400 mb-3 border border-green-500/10 shadow-lg group-hover/stat:scale-110 group-hover/stat:rotate-3 transition-all duration-500">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tighter">Top 5%</span>
                  <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest mt-1 opacity-60">Status Ranking</span>
                </div>
                <div className="glass-panel rounded-[1.75rem] p-5 border-[var(--panel-border)] flex flex-col items-center justify-center text-center group/stat hover:bg-[var(--panel-bg-lighter)] hover:border-[var(--panel-border-hover)] transition-all duration-500">
                  <div className="p-3 bg-primary/10 rounded-2xl text-primary mb-3 border border-primary/10 shadow-lg group-hover/stat:scale-110 group-hover/stat:-rotate-3 transition-all duration-500">
                    <Download className="w-5 h-5" />
                  </div>
                  <span className="text-white font-black text-2xl tracking-tighter">{totalDownloads}</span>
                  <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest mt-1 opacity-60">Libros Leídos</span>
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