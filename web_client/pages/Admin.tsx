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
  ShieldCheck,
  Save,
  Plus,
  RotateCcw,
  Activity,
  Server,
  Monitor,
  BarChart3,
  Calendar,
  Download,
  Archive,
  Database,
  Terminal,
  Cpu,
  HardDrive,
  RefreshCw,
  ArrowLeft,
  ArrowRight,
  Settings,
  Home,
  Eraser
} from 'lucide-react';
import { UserPermissions } from './UserPermissions';
import { TierConfiguration } from './TierConfiguration';
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
  totalUsers: number;
  totalBooks: number;
  downloads24h: number;
  uptime: string;
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

interface AdminUser {
  id: string;
  username: string;
  role: string;
  level: {
    name: string;
    color: string;
  };
  downloads: {
    used: number;
    limit: number;
    total: number;
  };
}

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [configuringTier, setConfiguringTier] = useState<{ name: string; color: string } | null>(null);
  const [currentView, setCurrentView] = useState<'overview' | 'system' | 'tiers'>('overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [levels, setLevels] = useState<UserLevel[]>([]);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [savingLevel, setSavingLevel] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      console.log('[Admin] Fetching admin data...');
      const [statsData, levelsData, usersData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminTiers(),
        api.getAdminUsers(20, 0, searchQuery)
      ]);
      console.log('[Admin] Stats:', statsData);
      console.log('[Admin] Levels:', levelsData);
      console.log('[Admin] Users:', usersData);
      setStats(statsData as AdminStats);
      setLevels(levelsData.levels as UserLevel[] || []);
      setUsers(usersData.users as AdminUser[] || []);
    } catch (error) {
      console.error("[Admin] Error fetching admin data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveLevel = async (level: UserLevel) => {
    try {
      setSavingLevel(level.id);
      await api.saveAdminTier(level);
      // Small feedback
      const originalLevels = [...levels];
      setLevels(levels.map(l => l.id === level.id ? level : l));
      setTimeout(() => setSavingLevel(null), 1000);
    } catch (error) {
      console.error("Error saving level:", error);
      setSavingLevel(null);
    }
  };

  const handleUpdateUserLevel = async (userId: string, levelId: string) => {
    try {
      await api.setAdminUserLevel(userId, parseInt(levelId));
      fetchAdminData();
    } catch (error) {
      console.error("Error updating user level:", error);
    }
  };

  const handleBackupLibrary = async () => {
    try {
      setLoading(true);
      const res = await api.adminBackupLibrary();
      alert(res.message || "Backup completado");
    } catch (error: any) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleScanLibrary = async (force: boolean = false) => {
    try {
      setLoading(true);
      const res = await api.adminScanLibrary(force);
      alert(res.message || "Escaneo completado");
      fetchAdminData();
    } catch (error: any) {
      alert("Error: " + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, [searchQuery]);

  useEffect(() => {
    const interval = setInterval(() => {
      api.getAdminStats().then(data => setStats(data as AdminStats));
    }, 60000);
    return () => clearInterval(interval);
  }, []);

  if (selectedUserId) {
    return <UserPermissions onBack={() => setSelectedUserId(null)} />;
  }

  const viewOptions = [
    { id: 'overview', label: 'Monitor', icon: BarChart3 },
    { id: 'system', label: 'Infraestructura', icon: Server },
    { id: 'tiers', label: 'Membresías', icon: ShieldCheck },
  ] as const;

  return (
    <div className="max-w-7xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-500 font-sans">

      {/* Dynamic Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div>
          <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight flex items-center gap-3">
            <ShieldCheck className="text-primary w-8 h-8 md:w-12 md:h-12" />
            Panel <span className="text-primary">de Control</span>
          </h1>
        </div>

        {/* Navigation Bar removed as requested - using bottom nav only */}
      </div>

      {loading ? (
        <div className="flex flex-col items-center justify-center py-24 gap-4">
          <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
          <p className="text-xs font-black text-gray-500 uppercase tracking-widest animate-pulse">Sincronizando base de datos...</p>
        </div>
      ) : (
        <div className="space-y-10">
          {/* ==================== KPI OVERVIEW ==================== */}
          {currentView === 'overview' && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-in slide-in-from-bottom-4 duration-500">
              {/* Rev Card */}
              <div className="glass-panel p-6 rounded-3xl border border-white/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl -mr-16 -mt-16 group-hover:bg-primary/20 transition-colors"></div>
                <div className="flex items-center justify-between mb-6">
                  <div className="p-3 bg-primary/10 rounded-2xl text-primary">
                    <DollarSign className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-black bg-green-500/10 text-green-400 px-2 py-1 rounded-full flex items-center gap-1 border border-green-500/10">
                    <TrendingUp className="w-3 h-3" /> +12%
                  </span>
                </div>
                <h3 className="text-gray-500 text-[10px] font-black uppercase tracking-widest mb-1">Ingresos de Hoy</h3>
                <p className="text-4xl font-bold text-white tracking-tight">${stats?.revenue.toFixed(2) || '0.00'}</p>
              </div>

              {/* Sessions Card */}
              <div className="glass-panel p-6 rounded-3xl border border-white/5 relative overflow-hidden group">
                <div className="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl -mr-16 -mt-16"></div>
                <div className="flex items-center justify-between mb-6">
                  <div className="p-3 bg-purple-500/10 rounded-2xl text-purple-400">
                    <Zap className="w-6 h-6" />
                  </div>
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                    <span className="text-[10px] font-black text-white uppercase tracking-widest">Live</span>
                  </div>
                </div>
                <h3 className="text-gray-500 text-[10px] font-black uppercase tracking-widest mb-1">Sesiones Activas</h3>
                <p className="text-4xl font-bold text-white tracking-tight">{stats?.activeSessions || 0}</p>
              </div>

              {/* Storage Health */}
              <div className="glass-panel p-6 rounded-3xl border border-white/5 relative overflow-hidden group">
                <div className="flex items-center justify-between mb-4">
                  <div className="p-3 bg-[#2AABEE]/10 rounded-2xl text-[#2AABEE]">
                    <Cloud className="w-6 h-6" />
                  </div>
                  <span className="text-[10px] font-black text-gray-500">450 solicitudes/min</span>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                    <span className="text-gray-500">Almacenamiento</span>
                    <span className="text-white">{Math.round(((stats?.storageUsedGB || 0) / (stats?.storageTotalGB || 1000)) * 100)}%</span>
                  </div>
                  <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div
                      className="h-full bg-gradient-to-r from-[#2AABEE] to-primary rounded-full shadow-[0_0_10px_rgba(42,171,238,0.3)] transition-all duration-1000"
                      style={{ width: `${((stats?.storageUsedGB || 0) / (stats?.storageTotalGB || 1000)) * 100}%` }}
                    ></div>
                  </div>
                  <p className="text-[10px] text-gray-600 font-mono">{stats?.storageUsedGB}GB / {stats?.storageTotalGB}GB UTILIZADO</p>
                </div>
              </div>

              {/* Top Content */}
              <div className="glass-panel p-4 rounded-3xl border border-white/5 flex items-center gap-4 group">
                <div className="h-20 w-14 bg-cover bg-center rounded-xl shadow-2xl border border-white/10 shrink-0 transform group-hover:rotate-3 transition-transform duration-300"
                  style={{ backgroundImage: `url('${stats?.popularBook?.cover || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&q=80&w=200"}')` }}>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-1 text-yellow-500 mb-1">
                    <Star className="w-3 h-3 fill-current" />
                    <span className="text-[9px] font-black uppercase text-white">Top Sales</span>
                  </div>
                  <h3 className="text-sm font-bold text-white truncate leading-tight mb-0.5">{stats?.popularBook?.title || "Atomic Habits"}</h3>
                  <p className="text-[10px] text-gray-500 truncate mb-2">{stats?.popularBook?.author || "James Clear"}</p>
                  <p className="text-[10px] font-black text-primary p-1 bg-primary/10 rounded-md inline-block uppercase">{stats?.popularBook?.downloads || 0} Descargas</p>
                </div>
              </div>
            </div>
          )}

          {/* ==================== SYSTEM VIEW ==================== */}
          {currentView === 'system' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">

              {/* Metric Cards from New Infrastructure Layout */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div className="glass-panel p-5 rounded-2xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                  <div className="relative z-10">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Usuarios Activos</p>
                    <h3 className="text-2xl font-bold text-white mt-1">{stats?.totalUsers?.toLocaleString() || '0'}</h3>
                    <div className="flex items-center mt-2 text-[10px] text-green-500 font-bold uppercase tracking-wider">
                      <TrendingUp className="w-3 h-3 mr-1" /> Sincronizado
                    </div>
                  </div>
                  <div className="p-3 bg-blue-500/10 rounded-xl text-primary">
                    <User className="w-5 h-5" />
                  </div>
                </div>

                <div className="glass-panel p-5 rounded-2xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                  <div className="relative z-10">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Índice Biblioteca</p>
                    <h3 className="text-2xl font-bold text-white mt-1">{stats?.totalBooks?.toLocaleString() || '0'}</h3>
                    <div className="flex items-center mt-2 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                      <Archive className="w-3 h-3 mr-1" /> {stats?.storageUsedGB} GB utilizados
                    </div>
                  </div>
                  <div className="p-3 bg-purple-500/10 rounded-xl text-purple-400">
                    <Layers className="w-5 h-5" />
                  </div>
                </div>

                <div className="glass-panel p-5 rounded-2xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                  <div className="relative z-10">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Descargas (24h)</p>
                    <h3 className="text-2xl font-bold text-white mt-1">{stats?.downloads24h?.toLocaleString() || '0'}</h3>
                    <div className="flex items-center mt-2 text-[10px] text-green-500 font-bold uppercase tracking-wider">
                      <TrendingUp className="w-3 h-3 mr-1" /> Hoy
                    </div>
                  </div>
                  <div className="p-3 bg-emerald-500/10 rounded-xl text-emerald-400">
                    <Download className="w-5 h-5" />
                  </div>
                </div>

                <div className="glass-panel p-5 rounded-2xl border border-white/5 flex items-start justify-between relative overflow-hidden group">
                  <div className="relative z-10">
                    <p className="text-[10px] font-black text-gray-500 uppercase tracking-widest">Estado Sistema</p>
                    <h3 className="text-2xl font-bold text-white mt-1">{stats?.uptime || '99.9%'}</h3>
                    <div className="flex items-center mt-2 text-[10px] text-green-500 font-bold uppercase tracking-wider">
                      <Zap className="w-3 h-3 mr-1" /> Online
                    </div>
                  </div>
                  <div className="p-3 bg-amber-500/10 rounded-xl text-amber-400">
                    <Activity className="w-5 h-5" />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Maintenance Section */}
                <div className="lg:col-span-1 glass-panel rounded-3xl p-6 flex flex-col border border-white/5">
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xs font-black text-white uppercase tracking-widest flex items-center gap-2">
                      <Settings className="text-primary w-4 h-4" /> Mantenimiento
                    </h3>
                    <span className="px-2 py-1 bg-green-500/10 text-green-500 text-[8px] font-bold rounded border border-green-500/20 uppercase">Operativo</span>
                  </div>
                  <div className="space-y-4">
                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 transition-colors group cursor-pointer">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-white text-[10px] uppercase">Escanear Biblioteca</h4>
                        <Activity className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                      </div>
                      <p className="text-[10px] text-gray-500 mb-3 uppercase tracking-tight">Indexar nuevo contenido en /mnt/books/incoming</p>
                      <button
                        onClick={() => handleScanLibrary(true)}
                        disabled={loading}
                        className="w-full py-2 text-[9px] font-black text-center bg-primary hover:bg-primary-dark text-white rounded-xl transition-all uppercase tracking-widest shadow-lg shadow-primary/20 active:scale-95 disabled:opacity-50"
                      >
                        {loading ? "Ejecutando..." : "Ejecutar Escaneo (Forzado)"}
                      </button>
                    </div>

                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 transition-colors group cursor-pointer">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-white text-[10px] uppercase">Backup Biblioteca a Supabase</h4>
                        <Database className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                      </div>
                      <p className="text-[10px] text-gray-500 mb-3 uppercase tracking-tight">Sincronizar libros y fuentes con Supabase Cloud</p>
                      <button
                        onClick={handleBackupLibrary}
                        disabled={loading}
                        className="w-full py-2 text-[9px] font-black text-center bg-purple-500 hover:bg-purple-600 text-white rounded-xl transition-all uppercase tracking-widest shadow-lg shadow-purple-500/20 active:scale-95 disabled:opacity-50"
                      >
                        {loading ? "Sincronizando..." : "Respaldar Biblioteca"}
                      </button>
                    </div>

                    <div className="p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-primary/50 transition-colors group cursor-pointer">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-white text-[10px] uppercase">Backup Base de Datos (SQLite)</h4>
                        <HardDrive className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                      </div>
                      <p className="text-[10px] text-gray-500 mb-3 uppercase tracking-tight">Generar archivo .bak de la base de datos local</p>
                      <button className="w-full py-2 text-[9px] font-black text-center bg-white/10 hover:bg-white/20 text-white rounded-xl transition-all uppercase tracking-widest active:scale-95 disabled:opacity-50 font-black">Generar .bak local</button>
                    </div>

                    <div className="p-4 rounded-2xl bg-red-500/5 border border-red-500/10 hover:border-red-500/50 transition-colors group cursor-pointer">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-red-400 text-[10px] uppercase">Resetear Sistema</h4>
                        <RotateCcw className="w-4 h-4 text-gray-500 group-hover:text-red-400 transition-colors" />
                      </div>
                      <p className="text-[10px] text-gray-500 mb-3 uppercase tracking-tight">Reinicia contadores y limpia cache global</p>
                      <button className="w-full py-2 text-[9px] font-black text-center bg-red-600 hover:bg-red-700 text-white rounded-xl transition-all uppercase tracking-widest shadow-lg shadow-red-600/20 active:scale-95">Reiniciar Global</button>
                    </div>
                  </div>
                </div>

                {/* System Logs */}
                <div className="lg:col-span-2 glass-panel rounded-3xl p-0 overflow-hidden flex flex-col h-[600px] border border-white/5">
                  <div className="p-4 border-b border-white/5 bg-white/[0.02] flex justify-between items-center">
                    <h3 className="text-[10px] font-black text-white uppercase tracking-widest flex items-center gap-2">
                      <Terminal className="w-4 h-4 text-gray-500" /> Live System Logs
                    </h3>
                    <div className="flex gap-1.5 px-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-red-500/30"></span>
                      <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/30"></span>
                      <span className="w-2.5 h-2.5 rounded-full bg-green-500/30"></span>
                    </div>
                  </div>
                  <div className="flex-1 bg-black/40 p-4 font-mono text-[10px] overflow-y-auto leading-relaxed">
                    <div className="space-y-1">
                      <div className="text-gray-500">[10:42:01] <span className="text-blue-400 font-bold">INFO</span>: Worker process started with PID 8821</div>
                      <div className="text-gray-500">[10:42:05] <span className="text-blue-400 font-bold">INFO</span>: Connecting to Telegram API... <span className="text-green-400 font-bold">OK</span></div>
                      <div className="text-gray-500">[10:42:06] <span className="text-yellow-400 font-bold">WARN</span>: High latency detected on webhook (450ms)</div>
                      <div className="text-gray-500">[10:43:12] <span className="text-blue-400 font-bold">INFO</span>: User <span className="text-purple-400">@devil1210</span> requested /scan_library</div>
                      <div className="text-gray-500 pl-4">→ Initializing Universal Hash Architecture scanner...</div>
                      <div className="text-gray-500 pl-4">→ Found 12 new EPUB files in /mnt/books/incoming</div>
                      <div className="text-gray-500 pl-4">→ Generating thumbnails (Glassmorphism applied)</div>
                      <div className="text-gray-500">[10:43:45] <span className="text-green-400 font-bold uppercase">SUCCESS</span>: Library index updated. +12 items.</div>
                      <div className="text-gray-500">[10:45:00] <span className="text-blue-400 font-bold">INFO</span>: Watchtower checking for updates...</div>
                      <div className="text-gray-300 animate-pulse">_</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}


          {/* ==================== TIERS VIEW ==================== */}
          {currentView === 'tiers' && !selectedUserId && !configuringTier && (
            <div className="max-w-[1200px] mx-auto w-full flex flex-col gap-10 animate-in fade-in duration-300 px-1">
              {/* Page Heading */}
              <div className="flex flex-wrap justify-between gap-6">
                <div className="flex min-w-72 flex-col gap-3">
                  <h1 className="text-4xl font-black text-white leading-tight tracking-tighter uppercase">Niveles y Acceso</h1>
                  <p className="text-gray-400 text-sm font-medium leading-relaxed max-w-2xl">
                    Configura permisos globales y niveles de suscripción para toda la base de usuarios.
                  </p>
                </div>
                <div className="flex items-end">
                  <button className="flex items-center gap-2 bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-xl font-black text-xs transition-all shadow-xl shadow-primary/30 uppercase tracking-widest border border-white/10">
                    <Plus className="w-5 h-5" />
                    Nuevo Nivel Personalizado
                  </button>
                </div>
              </div>

              {/* Tier Cards Row */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Free Tier */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5 relative overflow-hidden group hover:border-primary/30 transition-all">
                  <div className="absolute top-0 right-0 p-4 opacity-5">
                    <User className="w-16 h-16 text-gray-400" />
                  </div>
                  <div className="relative z-10">
                    <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 mb-2 block">Nivel por Defecto</span>
                    <h3 className="text-2xl font-black text-white mb-4">Gratuito</h3>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2 text-xs text-gray-400"><ShieldCheck className="w-3 h-3 text-green-500" /> Acceso a Catálogo Público</li>
                      <li className="flex items-center gap-2 text-xs text-gray-400"><ShieldCheck className="w-3 h-3 text-green-500" /> 1 Descarga Diaria</li>
                      <li className="flex items-center gap-2 text-xs text-gray-400"><Eraser className="w-3 h-3 text-red-500" /> Sin Solicitudes</li>
                    </ul>
                    <button
                      onClick={() => setConfiguringTier({ name: 'Gratuito', color: '#6b7280' })}
                      className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-bold text-white transition-colors border border-white/5"
                    >
                      Editar Permisos
                    </button>
                  </div>
                </div>

                {/* VIP Tier */}
                <div className="glass-panel p-6 rounded-2xl border border-primary/20 relative overflow-hidden group hover:border-primary/50 transition-all">
                  <div className="absolute inset-0 bg-primary/5"></div>
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <Star className="w-16 h-16 text-primary" />
                  </div>
                  <div className="relative z-10">
                    <span className="text-[10px] font-black uppercase tracking-widest text-primary mb-2 block">Más Popular</span>
                    <h3 className="text-2xl font-black text-white mb-4">VIP</h3>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-primary" /> Descargas Ilimitadas</li>
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-primary" /> Solicitudes Prioritarias</li>
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-primary" /> Acceso Anticipado</li>
                    </ul>
                    <button
                      onClick={() => setConfiguringTier({ name: 'VIP', color: settings.primaryColor })}
                      className="w-full py-2 rounded-lg bg-primary hover:bg-primary-dark text-xs font-bold text-white transition-colors shadow-lg shadow-primary/20"
                    >
                      Configurar
                    </button>
                  </div>
                </div>

                {/* Legend Tier */}
                <div className="glass-panel p-6 rounded-2xl border border-yellow-500/20 relative overflow-hidden group hover:border-yellow-500/50 transition-all">
                  <div className="absolute inset-0 bg-yellow-500/5"></div>
                  <div className="absolute top-0 right-0 p-4 opacity-10">
                    <TrendingUp className="w-16 h-16 text-yellow-500" />
                  </div>
                  <div className="relative z-10">
                    <span className="text-[10px] font-black uppercase tracking-widest text-yellow-500 mb-2 block">Supporter</span>
                    <h3 className="text-2xl font-black text-white mb-4">Leyenda</h3>
                    <ul className="space-y-2 mb-6">
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-yellow-500" /> Todo lo de VIP</li>
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-yellow-500" /> Insignia de Perfil</li>
                      <li className="flex items-center gap-2 text-xs text-gray-300"><ShieldCheck className="w-3 h-3 text-yellow-500" /> Canal de Soporte Directo</li>
                    </ul>
                    <button
                      onClick={() => setConfiguringTier({ name: 'Leyenda', color: '#eab308' })}
                      className="w-full py-2 rounded-lg bg-yellow-500/10 hover:bg-yellow-500/20 text-xs font-bold text-yellow-500 border border-yellow-500/20 transition-colors"
                    >
                      Configurar
                    </button>
                  </div>
                </div>
              </div>

              {/* Active Registrations Table */}
              <div className="glass-panel rounded-2xl border border-white/5 overflow-hidden">
                <div className="p-6 border-b border-white/5 flex flex-col md:flex-row justify-between md:items-center gap-4">
                  <div>
                    <h3 className="text-lg font-black text-white uppercase tracking-tight">Registros Activos</h3>
                    <p className="text-xs text-gray-400">Gestionar cuentas individuales y anular permisos.</p>
                  </div>
                  <div className="flex gap-2">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                      <input
                        type="text"
                        placeholder="Filtrar por ID o Usuario..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-9 pr-4 py-2 bg-black/20 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-primary w-64"
                      />
                    </div>
                    <button className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded-lg text-xs font-bold uppercase tracking-wider border border-white/5 transition-colors">Filtros</button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-white/5 border-b border-white/5">
                        <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">ID Registro</th>
                        <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Identidad</th>
                        <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Nivel de Acceso</th>
                        <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest">Utilización Cuota</th>
                        <th className="p-4 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Ops</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {users.map((user) => {
                        const tierName = user.level?.name || 'Gratis';
                        const isVip = tierName.toLowerCase().includes('vip') || tierName.toLowerCase().includes('premium');
                        const isLegend = tierName.toLowerCase().includes('legend') || tierName.toLowerCase().includes('admin') || tierName.toLowerCase().includes('staff');
                        const isWarning = user.downloads.used >= user.downloads.limit && user.downloads.limit !== -1;

                        return (
                          <tr
                            key={user.id}
                            className="hover:bg-white/5 transition-colors group cursor-pointer"
                            onClick={() => setSelectedUserId(user.id)}
                          >
                            <td className="p-4 text-xs font-mono text-gray-500 font-bold">#{user.id}</td>
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${isVip ? 'bg-purple-500/20 text-purple-400' :
                                  isLegend ? 'bg-yellow-500/20 text-yellow-400' :
                                    'bg-gray-700 text-gray-300'
                                  }`}>
                                  {user.username.charAt(0).toUpperCase()}
                                </div>
                                <span className="text-sm font-bold text-white">{user.username}</span>
                              </div>
                            </td>
                            <td className="p-4">
                              <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${isVip ? 'bg-purple-500/20 text-purple-300 border border-purple-500/20' :
                                isLegend ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/20' :
                                  'bg-white/10 text-gray-400 border border-white/10'
                                }`}>
                                {tierName}
                              </span>
                            </td>
                            <td className="p-4">
                              <div className="w-32">
                                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden mb-1">
                                  <div
                                    className={`h-full rounded-full ${isWarning ? 'bg-red-500' : 'bg-primary'}`}
                                    style={{ width: user.downloads.limit === -1 ? '5%' : `${Math.min(100, (user.downloads.used / user.downloads.limit) * 100)}%` }}
                                  ></div>
                                </div>
                                <span className={`text-[10px] font-mono ${isWarning ? 'text-red-400 font-bold' : 'text-gray-500'}`}>
                                  {user.downloads.used} / {user.downloads.limit === -1 ? '∞' : user.downloads.limit}
                                </span>
                              </div>
                            </td>
                            <td className="p-4 text-right">
                              <div className="flex justify-end gap-2 opacity-50 group-hover:opacity-100 transition-opacity">
                                <button
                                  className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
                                  onClick={(e) => { e.stopPropagation(); }}
                                >
                                  <RotateCcw className="w-4 h-4" />
                                </button>
                                <button
                                  className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"
                                  onClick={(e) => { e.stopPropagation(); }}
                                >
                                  <Eraser className="w-4 h-4" />
                                </button>
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="p-4 border-t border-white/5 bg-white/5 flex justify-center">
                  <button className="text-xs font-bold text-gray-400 hover:text-white uppercase tracking-widest flex items-center gap-2 transition-colors">
                    Recuperar Dataset Expandido <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* User Permissions Editor */}
          {currentView === 'tiers' && selectedUserId && (
            <UserPermissions
              onBack={() => setSelectedUserId(null)}
              userId={selectedUserId}
              userData={users.find(u => u.id === selectedUserId) ? {
                username: users.find(u => u.id === selectedUserId)!.username,
                id: selectedUserId,
                level: users.find(u => u.id === selectedUserId)!.level?.name || 'Básico'
              } : undefined}
            />
          )}

          {/* Tier Configuration Editor */}
          {currentView === 'tiers' && configuringTier && (
            <TierConfiguration
              tierName={configuringTier.name}
              tierColor={configuringTier.color}
              onBack={() => setConfiguringTier(null)}
              onSave={(config) => {
                console.log('Saving tier config:', config);
                // TODO: Save to backend
              }}
            />
          )}

          {/* User Permissions Editor */}
          {currentView === 'tiers' && selectedUserId && !configuringTier && (() => {
            const selectedUser = users.find(u => u.id === selectedUserId);
            return (
              <UserPermissions
                userId={selectedUserId}
                userData={selectedUser ? {
                  username: selectedUser.username,
                  id: selectedUser.id,
                  level: selectedUser.level?.name || 'Lector',
                  avatar: undefined
                } : undefined}
                onBack={() => setSelectedUserId(null)}
              />
            );
          })()}
        </div >

      )}

      {/* Admin Floating Navigation - Always visible for quick access */}
      <div className="fixed bottom-6 left-8 right-8 z-50 animate-in slide-in-from-bottom-4 duration-300 max-w-7xl mx-auto">
        <div
          className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
          style={{
            background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
            backdropFilter: `blur(${settings.glassBlur}px)`,
            WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
          }}
        >
          <button
            onClick={() => onNavigate && onNavigate('dashboard')}
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white"
          >
            <Home className="w-4 h-4" strokeWidth={2} />
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Salir</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          {viewOptions.map((v) => (
            <React.Fragment key={v.id}>
              <button
                onClick={() => setCurrentView(v.id)}
                className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${currentView === v.id ? 'text-primary' : 'text-gray-500'}`}
              >
                <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === v.id ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                  <v.icon className={`w-4 h-4 ${currentView === v.id ? 'text-white' : ''}`} strokeWidth={2.5} />
                </div>
                <span className={`text-[8px] font-black uppercase tracking-tight mt-1 whitespace-nowrap overflow-hidden text-center`}>{v.label}</span>
              </button>
              {v.id !== 'tiers' && <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div >
  );
};
