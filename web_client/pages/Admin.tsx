import React, { useState, useEffect } from 'react';
import {
  DollarSign,
  Zap,
  Cloud,
  Star,
  TrendingUp,
  Search,
  Bell,
  LayoutDashboard,
  Layers,
  User,
  Heart,
  Gem,
  Medal,
  Save,
  Plus,
  RotateCcw,
  Ban,
  CheckCircle,
  ArrowRight,
  Activity,
  Server,
  Terminal,
  Eraser,
  Database,
  Scan,
  Cpu,
  HardDrive,
  ArrowLeft,
  Home,
  Reply
} from 'lucide-react';
import { UserPermissions } from './UserPermissions';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

interface AdminStats {
  revenue: number;
  activeSessions: number;
  storageUsedGB: number;
  storageTotalGB: number;
  popularBook: {
    title: string;
    downloads: number;
    author: string;
    cover?: string;
  } | null;
  growthTrend: { date: string; users: number; downloads: number; }[];
}

interface UserLevel {
  id: string;
  name: string;
  priority: number;
  color: string;
  hasAccess: boolean;
  dailyDownloads: number;
  earlyAccess: boolean;
  customThemes: boolean;
  price: number;
}

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'overview' | 'system' | 'tiers'>('overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [levels, setLevels] = useState<UserLevel[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAdminData = async () => {
    try {
      const statsData = await api.rpc('admin_stats', {});
      const levelsData = await api.rpc('admin_get_tiers', {});
      setStats(statsData as AdminStats);
      setLevels(levelsData.levels as UserLevel[]);
    } catch (error) {
      console.error("Error fetching admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
    // Refresh stats every minute
    const interval = setInterval(() => {
      api.rpc('admin_stats', {}).then(data => setStats(data as AdminStats));
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  if (selectedUserId) {
    return (
      <div className="p-4 md:p-8 max-w-7xl mx-auto h-full">
        <UserPermissions onBack={() => setSelectedUserId(null)} />
      </div>
    );
  }

  const viewOptions = [
    { id: 'overview', label: 'Resumen', icon: LayoutDashboard },
    { id: 'system', label: 'Sistema', icon: Activity },
    { id: 'tiers', label: 'Niveles', icon: Layers },
  ] as const;

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto flex flex-col h-full overflow-hidden relative text-slate-800 dark:text-slate-100 font-sans pb-32 md:pb-6">
      {/* Admin Header with Tabs */}
      <header
        className="md:hidden flex items-center justify-between px-4 py-4 z-40 sticky top-0 border-b border-black/5 dark:border-white/10 shrink-0"
        style={{
          background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
          backdropFilter: `blur(${settings.glassBlur}px)`,
          WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
        }}
      >
        <div className="flex items-center gap-2">
          <button onClick={() => onNavigate && onNavigate('dashboard')} className="p-1 text-gray-400 hover:text-white transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <span className="font-bold text-lg text-gray-900 dark:text-white">Administración</span>
        </div>
      </header>

      {/* Desktop Header */}
      <header className="hidden md:flex flex-col md:flex-row items-start md:items-center justify-between mb-8 z-20 gap-4 shrink-0 relative">
        {/* Navigation Tabs (Hidden on Mobile, moved to bottom bar) */}
        <div className="hidden md:flex glass-panel p-1.5 rounded-xl items-center gap-1 shadow-lg border border-white/5 w-full md:w-auto overflow-x-auto no-scrollbar">
          {viewOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => setCurrentView(option.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap flex-1 md:flex-none justify-center ${currentView === option.id
                ? 'bg-primary text-white shadow-lg shadow-primary/20'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
            >
              <option.icon className={`w-4 h-4 ${currentView === option.id ? 'text-white' : 'text-gray-500'}`} />
              {option.label}
            </button>
          ))}
        </div>

        {/* Tools */}
        <div className="flex items-center gap-3 w-full md:w-auto">
          <div className="relative flex-1 md:flex-none">
            <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-gray-400">
              <Search className="w-4 h-4" />
            </span>
            <input
              className="w-full md:w-64 pl-10 pr-4 py-2.5 bg-black/20 border border-white/10 rounded-xl text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary text-white placeholder-gray-500 transition-all"
              placeholder="Buscar herramienta..."
              type="text"
            />
          </div>
          <button className="relative p-2.5 text-gray-400 hover:text-white transition-colors bg-black/20 rounded-xl border border-white/10 hover:bg-white/5">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-[#121212]"></span>
          </button>
        </div>
      </header>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto pr-2 pb-32 md:pb-6 custom-scrollbar">

        {/* ==================== VIEW 1: OVERVIEW (KPIs) ==================== */}
        {currentView === 'overview' && (
          <div className="animate-in fade-in duration-300 space-y-8 px-1">
            <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
              <div>
                <h2 className="text-3xl font-black text-white mb-2 tracking-tight">Resumen de Plataforma</h2>
                <p className="text-gray-400 text-sm">Métricas de rendimiento en tiempo real.</p>
              </div>
              <div className="flex gap-2">
                <button className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-gray-400 hover:text-white bg-white/5 rounded-lg border border-white/10 transition-colors shadow-sm">7 Días</button>
                <button className="px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white bg-primary rounded-lg shadow-lg shadow-primary/30 hover:bg-primary-dark transition-all">30 Días</button>
              </div>
            </div>

            {/* Crystal KPI Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <DollarSign className="w-16 h-16 text-primary" />
                </div>
                <div className="flex flex-col h-full justify-between relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-primary/20 rounded-xl text-primary shadow-sm border border-primary/20">
                      <DollarSign className="w-5 h-5" />
                    </div>
                    <span className="flex items-center text-[#0bda5e] text-[10px] font-black bg-[#0bda5e]/10 px-2.5 py-1 rounded-full border border-[#0bda5e]/20 backdrop-blur-md uppercase tracking-tighter">
                      <TrendingUp className="w-3 h-3 mr-1" /> +12.5%
                    </span>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-[10px] font-black mb-1 uppercase tracking-widest">Ingresos Totales</h3>
                    <p className="text-3xl font-bold text-white tracking-tight">${stats?.revenue.toFixed(2) || '0.00'}</p>
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <Zap className="w-16 h-16 text-[#2AABEE]" />
                </div>
                <div className="flex flex-col h-full justify-between relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-[#2AABEE]/20 rounded-xl text-[#2AABEE] shadow-sm border border-[#2AABEE]/20">
                      <Zap className="w-5 h-5" />
                    </div>
                    <span className="flex items-center text-[#2AABEE] text-[10px] font-black bg-[#2AABEE]/10 px-2.5 py-1 rounded-full border border-[#2AABEE]/20 backdrop-blur-md uppercase tracking-widest">
                      En Vivo
                    </span>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-[10px] font-black mb-1 uppercase tracking-widest">Sesiones Activas</h3>
                    <div className="flex items-baseline gap-2">
                      <p className="text-3xl font-bold text-white tracking-tight">{stats?.activeSessions || 0}</p>
                      <span className="relative flex h-3 w-3">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="flex flex-col h-full justify-between relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-purple-500/20 rounded-xl text-purple-400 shadow-sm border border-purple-500/20">
                      <Cloud className="w-5 h-5" />
                    </div>
                    <span className="text-gray-400 text-[10px] font-black uppercase tracking-widest">45% Capacidad</span>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-[10px] font-black mb-2 uppercase tracking-widest">Almacenamiento</h3>
                    <div className="flex items-end gap-1 mb-2">
                      <p className="text-2xl font-bold text-white tracking-tight">{stats?.storageUsedGB || 0}<span className="text-lg text-gray-500 font-normal ml-0.5">GB</span></p>
                      <p className="text-[10px] text-gray-500 font-black mb-1 uppercase">/ {stats?.storageTotalGB || 1000}GB</p>
                    </div>
                    <div className="w-full bg-slate-900/50 rounded-full h-2 overflow-hidden border border-white/5">
                      <div
                        className="bg-gradient-to-r from-purple-600 to-purple-400 h-2 rounded-full shadow-[0_0_8px_rgba(168,85,247,0.4)] transition-all duration-1000"
                        style={{ width: `${Math.min(100, ((stats?.storageUsedGB || 0) / (stats?.storageTotalGB || 1000)) * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-4 relative overflow-hidden group flex items-center gap-4 hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="h-full w-16 bg-cover bg-center rounded-lg shadow-lg shrink-0 border border-white/10" style={{ backgroundImage: stats?.popularBook?.cover ? `url('${stats.popularBook.cover}')` : "url('/api/library/covers/default.jpg')" }}></div>
                <div className="flex flex-col justify-center min-w-0">
                  <div className="flex items-center gap-1 text-yellow-400 mb-1">
                    <Star className="w-3 h-3 fill-current" />
                    <span className="text-[9px] font-black text-white uppercase tracking-tighter">Popular</span>
                  </div>
                  <h3 className="text-white font-bold leading-tight line-clamp-1 truncate text-sm" title={stats?.popularBook?.title || 'Cargando...'}>{stats?.popularBook?.title || 'Atomic Habits'}</h3>
                  <p className="text-[10px] text-gray-400 truncate font-medium">{stats?.popularBook?.author || 'James Clear'}</p>
                  <p className="text-[10px] text-primary mt-2 font-black uppercase tracking-tight">{stats?.popularBook?.downloads || 0} Descargas</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
              <div className="xl:col-span-2 glass-panel rounded-2xl p-6 overflow-hidden flex flex-col border border-white/5">
                <div className="flex justify-between items-center mb-8">
                  <div>
                    <h3 className="text-lg font-black text-white uppercase tracking-tight">Tendencia de Crecimiento</h3>
                    <p className="text-xs text-gray-400">Interacción de usuarios vs consumo de contenido.</p>
                  </div>
                  <div className="flex items-center gap-4 bg-white/5 p-2 rounded-xl border border-white/5">
                    <div className="flex items-center gap-2 px-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-primary shadow-[0_0_8px_rgba(43,108,238,0.5)]"></span>
                      <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Usuarios</span>
                    </div>
                    <div className="flex items-center gap-2 px-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-[#2AABEE] shadow-[0_0_8px_rgba(42,171,238,0.5)]"></span>
                      <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Descargas</span>
                    </div>
                  </div>
                </div>

                {/* Graph placeholder */}
                <div className="flex-1 min-h-[300px] flex items-end justify-between font-mono text-[10px] text-gray-500 overflow-hidden relative">
                  {/* ... svg path remains same ... */}
                  <svg className="absolute inset-0 h-full w-full z-10" preserveAspectRatio="none" viewBox="0 0 750 300">
                    <path className="fill-primary/5" d="M0,280 C50,250 100,290 150,200 C200,110 250,180 300,150 C350,120 400,50 450,80 C500,110 550,60 600,40 C650,20 700,50 750,30 L750,300 L0,300 Z" stroke="none"></path>
                    <path d="M0,280 C50,250 100,290 150,200 C200,110 250,180 300,150 C350,120 400,50 450,80 C500,110 550,60 600,40 C650,20 700,50 750,30" fill="none" stroke="#2b6cee" strokeLinecap="round" strokeWidth="3"></path>
                  </svg>
                </div>
              </div>

              {/* Right side widgets in overview */}
              <div className="space-y-6">
                <div className="glass-panel p-6 rounded-2xl border border-white/5">
                  <h3 className="text-sm font-black uppercase tracking-widest mb-4">Actividad Pico</h3>
                  <div className="grid grid-cols-7 gap-2">
                    {Array.from({ length: 28 }).map((_, i) => (
                      <div key={i} className="h-4 rounded-sm bg-primary/20" style={{ opacity: Math.random() * 0.8 + 0.2 }}></div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ... (VIEW 2: SYSTEM remains similar, ensuring it fits under new design) ... */}
        {currentView === 'system' && (
          <div className="animate-in fade-in duration-300 space-y-8 px-1">
            <h2 className="text-3xl font-black text-white">Infraestructura</h2>
            {/* System grid/tools ... */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Stats cards ... */}
              <div className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col gap-2">
                <span className="text-[10px] font-black uppercase text-gray-500">Uptime</span>
                <span className="text-2xl font-bold font-mono">14d 22h</span>
              </div>
              <div className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col gap-2">
                <span className="text-[10px] font-black uppercase text-gray-500">CPU</span>
                <span className="text-2xl font-bold font-mono">12%</span>
              </div>
              <div className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col gap-2">
                <span className="text-[10px] font-black uppercase text-gray-500">Memory</span>
                <span className="text-2xl font-bold font-mono">2.4 GB</span>
              </div>
            </div>
          </div>
        )}

        {/* ==================== VIEW 3: TIERS (User Mgmt) ==================== */}
        {currentView === 'tiers' && (
          <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-10 animate-in fade-in duration-300 px-1">
            <h1 className="text-4xl font-black text-white uppercase">Niveles</h1>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {levels.map((level) => (
                <div key={level.id} className="glass-panel p-6 rounded-2xl border border-white/5 relative flex flex-col">
                  <h3 className="text-2xl font-black mb-4">{level.name}</h3>
                  <div className="space-y-4 mb-6">
                    <div className="flex justify-between items-center text-xs">
                      <span>Descargas Diarias</span>
                      <span className="font-bold">{level.dailyDownloads}</span>
                    </div>
                  </div>
                  <button className="mt-auto w-full py-3 bg-white/5 hover:bg-primary transition-all rounded-xl text-[10px] font-black uppercase tracking-widest">
                    Guardar
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Mobile Bottom Navigation for Admin - Refined Design */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-50 animate-in slide-in-from-bottom-4 duration-300">
        <div
          className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
          }}
        >
          <button
            onClick={() => onNavigate && onNavigate('dashboard')}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-500 hover:text-white"
          >
            <div className="p-1.5 rounded-full">
              <Home className="w-4 h-4" strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={() => setCurrentView('overview')}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${currentView === 'overview' ? 'text-primary font-bold' : 'text-gray-500'}`}
          >
            <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === 'overview' ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-1px]' : ''}`}>
              <LayoutDashboard className={`w-4 h-4 ${currentView === 'overview' ? 'text-white' : ''}`} strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Resumen</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={() => setCurrentView('system')}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${currentView === 'system' ? 'text-primary font-bold' : 'text-gray-500'}`}
          >
            <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === 'system' ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-1px]' : ''}`}>
              <Activity className={`w-4 h-4 ${currentView === 'system' ? 'text-white' : ''}`} strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Sistema</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          <button
            onClick={() => setCurrentView('tiers')}
            className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${currentView === 'tiers' ? 'text-primary font-bold' : 'text-gray-500'}`}
          >
            <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === 'tiers' ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-1px]' : ''}`}>
              <Layers className={`w-4 h-4 ${currentView === 'tiers' ? 'text-white' : ''}`} strokeWidth={2} />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Niveles</span>
          </button>
        </div>
      </div>
    </div>
  );
};