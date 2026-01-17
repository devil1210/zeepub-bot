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
  Terminal,
  Eraser,
  Database,
  Cpu,
  HardDrive,
  ArrowLeft,
  Home,
  Settings,
  ArrowRight,
  TrendingDown,
  Monitor,
  BarChart3,
  Calendar,
  Download
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
      const [statsData, levelsData, usersData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminTiers(),
        api.getAdminUsers(20, 0, searchQuery)
      ]);
      setStats(statsData as AdminStats);
      setLevels(levelsData.levels as UserLevel[]);
      setUsers(usersData.users as AdminUser[]);
    } catch (error) {
      console.error("Error fetching admin data:", error);
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
            Panel <span className="text-primary">Admin</span>
          </h1>
          <p className="text-gray-400 text-sm md:text-base mt-2 flex items-center gap-2">
            <Activity className="w-4 h-4 text-green-500" />
            Control total de la plataforma ZeepubBot
          </p>
        </div>

        <div className="flex items-center gap-2 p-1 bg-white/5 rounded-2xl border border-white/5">
          {viewOptions.map((v) => (
            <button
              key={v.id}
              onClick={() => setCurrentView(v.id)}
              className={`flex items-center gap-2 px-4 md:px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all ${currentView === v.id
                ? 'bg-primary text-white shadow-lg shadow-primary/30'
                : 'text-gray-500 hover:text-white hover:bg-white/5'
                }`}
            >
              <v.icon className="w-4 h-4" />
              <span className="hidden sm:inline">{v.label}</span>
            </button>
          ))}
        </div>
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
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* CPU Widget */}
                <div className="glass-panel p-6 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-red-500/10 text-red-500 rounded-lg"><Cpu className="w-5 h-5" /></div>
                    <h4 className="text-xs font-black uppercase tracking-widest text-white">CPU Usage</h4>
                  </div>
                  <div className="flex items-end gap-2 mb-4">
                    <span className="text-4xl font-bold text-white">12.4</span>
                    <span className="text-lg text-gray-500 mb-1">%</span>
                  </div>
                  <div className="flex gap-1 h-8 items-end">
                    {[0.2, 0.4, 0.3, 0.8, 0.5, 0.2, 0.3, 0.4, 0.1, 0.4, 0.6, 0.3].map((h, i) => (
                      <div key={i} className="flex-1 bg-red-500/20 rounded-t-sm" style={{ height: `${h * 100}%` }}></div>
                    ))}
                  </div>
                </div>

                {/* Latency Widget */}
                <div className="glass-panel p-6 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-green-500/10 text-green-500 rounded-lg"><Monitor className="w-5 h-5" /></div>
                    <h4 className="text-xs font-black uppercase tracking-widest text-white">Avg. Latency</h4>
                  </div>
                  <div className="flex items-end gap-2 mb-4">
                    <span className="text-4xl font-bold text-white">48</span>
                    <span className="text-lg text-gray-500 mb-1">ms</span>
                  </div>
                  <p className="text-[10px] text-green-500 font-bold uppercase tracking-wider flex items-center gap-1">
                    <TrendingDown className="w-3 h-3" /> Optimizado
                  </p>
                </div>

                {/* Memory Widget */}
                <div className="glass-panel p-6 rounded-3xl border border-white/5">
                  <div className="flex items-center gap-3 mb-6">
                    <div className="p-2 bg-amber-500/10 text-amber-500 rounded-lg"><Database className="w-5 h-5" /></div>
                    <h4 className="text-xs font-black uppercase tracking-widest text-white">Memory Usage</h4>
                  </div>
                  <div className="flex items-end gap-2 mb-4">
                    <span className="text-4xl font-bold text-white">2.4</span>
                    <span className="text-lg text-gray-500 mb-1">GB</span>
                  </div>
                  <div className="w-full bg-white/5 rounded-full h-1.5">
                    <div className="w-[35%] h-full bg-amber-500 rounded-full"></div>
                  </div>
                </div>
              </div>

              {/* Maintenance Tools */}
              <div className="glass-panel p-8 rounded-[40px] border border-red-500/20 bg-red-500/5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/10 rounded-full blur-[100px] -mr-20 -mt-20"></div>
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-8 relative z-10">
                  <div className="max-w-md">
                    <h3 className="text-2xl font-black text-white flex items-center gap-3 mb-3">
                      <RotateCcw className="text-red-400 w-8 h-8" />
                      Mantenimiento Crítico
                    </h3>
                    <p className="text-gray-400 text-sm leading-relaxed">
                      Reinicia todos los contadores de la plataforma. Esta acción pondrá a cero las descargas diarias,
                      estadísticas de popularidad y registros de sesiones. <span className="text-red-400 font-bold underline">Uso exclusivo para fin de ciclo.</span>
                    </p>
                  </div>
                  <button
                    onClick={() => { if (confirm('¡ATENCIÓN! Se perderán todos los datos estadísticos históricos. ¿Continuar?')) { /* rpc call */ } }}
                    className="group px-8 py-5 bg-red-600 hover:bg-red-700 text-white text-xs font-black uppercase tracking-widest rounded-2xl shadow-xl shadow-red-600/20 transition-all flex items-center justify-center gap-3 active:scale-95"
                  >
                    <Eraser className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                    Reiniciar Sistema Global
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* ==================== TIERS VIEW ==================== */}
          {currentView === 'tiers' && (
            <div className="space-y-8 animate-in slide-in-from-bottom-4 duration-500">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-black text-white uppercase tracking-tight">Gestión de Membresías</h2>
                <button className="flex items-center gap-2 p-2 px-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/5 transition-colors text-[10px] font-black uppercase tracking-widest text-primary">
                  <Plus className="w-4 h-4" /> Nuevo Nivel
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {levels.map((level, idx) => (
                  <div key={level.id} className="glass-panel rounded-[32px] overflow-hidden border border-white/5 flex flex-col group hover:border-primary/50 transition-all relative">
                    {idx === 1 && <div className="absolute top-4 right-4 bg-primary text-white text-[8px] font-bold px-2 py-1 rounded-full uppercase">MÁS POPULAR</div>}
                    <div className="p-8 border-b border-white/5">
                      <h3 className="text-2xl font-black text-white mb-1">{level.name}</h3>
                      <p className="text-xs text-gray-500 font-medium">Nivel de prioridad {level.priority}</p>
                      <div className="mt-6 flex items-baseline gap-1">
                        <span className="text-3xl font-bold text-white">${level.price}</span>
                        <span className="text-xs text-gray-500 uppercase tracking-widest">/mes</span>
                      </div>
                    </div>
                    <div className="p-8 space-y-5 flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-gray-400 uppercase tracking-widest flex items-center gap-2">
                          <Download className="w-4 h-4 text-primary" /> Descargas/Día
                        </span>
                        <input
                          type="number"
                          className="w-16 bg-black/40 border border-white/5 rounded-lg p-2 text-center font-bold text-white text-sm"
                          value={level.dailyDownloads}
                          onChange={(e) => setLevels(levels.map(l => l.id === level.id ? { ...l, dailyDownloads: parseInt(e.target.value) } : l))}
                        />
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white/5 rounded-2xl border border-white/5">
                        <span className="text-xs font-bold text-gray-300">Early Access</span>
                        <div
                          onClick={() => setLevels(levels.map(l => l.id === level.id ? { ...l, earlyAccess: !l.earlyAccess } : l))}
                          className={`w-10 h-5.5 rounded-full relative transition-colors cursor-pointer ${level.earlyAccess ? 'bg-primary' : 'bg-gray-700'}`}
                        >
                          <div className={`absolute top-1 w-3.5 h-3.5 bg-white rounded-full transition-all ${level.earlyAccess ? 'left-5.5' : 'left-1'}`}></div>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-3 bg-white/5 rounded-2xl border border-white/5">
                        <span className="text-xs font-bold text-gray-300">Temas Custom</span>
                        <div
                          onClick={() => setLevels(levels.map(l => l.id === level.id ? { ...l, customThemes: !l.customThemes } : l))}
                          className={`w-10 h-5.5 rounded-full relative transition-colors cursor-pointer ${level.customThemes ? 'bg-primary' : 'bg-gray-700'}`}
                        >
                          <div className={`absolute top-1 w-3.5 h-3.5 bg-white rounded-full transition-all ${level.customThemes ? 'left-5.5' : 'left-1'}`}></div>
                        </div>
                      </div>
                    </div>
                    <div className="p-6 bg-white/5 border-t border-white/5">
                      <button
                        onClick={() => handleSaveLevel(level)}
                        disabled={savingLevel === level.id}
                        className={`w-full py-4 ${savingLevel === level.id ? 'bg-green-500 text-white' : 'bg-primary/10 text-primary hover:bg-primary hover:text-white'} text-xs font-black uppercase tracking-widest rounded-2xl transition-all flex items-center justify-center gap-2`}
                      >
                        {savingLevel === level.id ? <ShieldCheck className="w-4 h-4 animate-bounce" /> : <Save className="w-4 h-4" />}
                        {savingLevel === level.id ? 'Guardado' : 'Guardar Cambios'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* REGISTER TABLE - Match screenshot */}
              <div className="glass-panel rounded-[40px] border border-white/5 overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-700 mt-12">
                <div className="p-8 border-b border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-6">
                  <div>
                    <h3 className="text-xl font-black text-white uppercase flex items-center gap-3">
                      <Layers className="w-6 h-6 text-primary" />
                      Registros Activos
                    </h3>
                    <p className="text-xs text-gray-500 font-medium mt-1">Gestionar cuentas individuales y anular permisos.</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                      <input
                        type="text"
                        placeholder="Filtrar por ID o Usuario..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="bg-black/40 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-xs text-white focus:ring-1 ring-primary min-w-[240px]"
                      />
                    </div>
                    <button className="px-4 py-2.5 bg-white/5 text-xs font-black uppercase tracking-widest text-gray-400 rounded-xl hover:text-white transition-colors border border-white/5">Filtros</button>
                  </div>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-white/[0.02] border-b border-white/5">
                        <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">ID Registro</th>
                        <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">Identidad</th>
                        <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">Nivel de Acceso</th>
                        <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest">Utilización Cuota</th>
                        <th className="p-6 text-[10px] font-black text-gray-500 uppercase tracking-widest text-right">Ops</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.02]">
                      {users.map((user) => (
                        <tr key={user.id} className="hover:bg-white/[0.01] transition-colors group">
                          <td className="p-6 text-xs text-gray-500 font-mono">#{user.id}</td>
                          <td className="p-6">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary/20 to-purple-500/20 flex items-center justify-center text-[10px] font-black text-primary border border-white/5 uppercase">
                                {user.username.charAt(0)}
                              </div>
                              <span className="text-sm font-bold text-white">{user.username}</span>
                            </div>
                          </td>
                          <td className="p-6">
                            <select
                              value={levels.find(l => l.name === user.level.name)?.id || '6'}
                              onChange={(e) => handleUpdateUserLevel(user.id, e.target.value)}
                              style={{ color: user.level.color }}
                              className="bg-white/5 border border-white/10 rounded-lg py-1 px-3 text-[10px] font-black uppercase tracking-widest cursor-pointer focus:ring-1 ring-primary"
                            >
                              {levels.map(l => (
                                <option key={l.id} value={l.id} className="bg-gray-900 text-white">{l.name}</option>
                              ))}
                            </select>
                          </td>
                          <td className="p-6 min-w-[200px]">
                            <div className="flex flex-col gap-2">
                              <div className="flex justify-between text-[10px] font-black uppercase">
                                <span className={user.downloads.used >= user.downloads.limit && user.downloads.limit !== -1 ? 'text-red-400' : 'text-primary'}>
                                  {user.downloads.used} / {user.downloads.limit === -1 ? '∞' : user.downloads.limit}
                                </span>
                              </div>
                              <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full transition-all duration-1000 ${user.downloads.used >= user.downloads.limit && user.downloads.limit !== -1 ? 'bg-red-500' : 'bg-primary'}`}
                                  style={{ width: `${user.downloads.limit === -1 ? 0 : Math.min(100, (user.downloads.used / user.downloads.limit) * 100)}%` }}
                                ></div>
                              </div>
                            </div>
                          </td>
                          <td className="p-6 text-right">
                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500 hover:text-primary transition-colors">
                                <RotateCcw className="w-4 h-4" />
                              </button>
                              <button className="p-2 hover:bg-white/5 rounded-lg text-gray-500 hover:text-red-500 transition-colors">
                                <Eraser className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="p-6 bg-white/[0.01] border-t border-white/5 text-center">
                  <button className="text-[10px] font-black text-gray-500 uppercase tracking-widest hover:text-white transition-colors flex items-center gap-2 mx-auto disabled:opacity-50">
                    Siguiente Página <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Admin Mobile Floating Navigation */}
      <div className="md:hidden fixed bottom-6 left-4 right-4 z-50 animate-in slide-in-from-bottom-4 duration-300">
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
                <span className="text-[9px] font-black uppercase tracking-widest mt-1">{v.label.split(' ')[0]}</span>
              </button>
              {v.id !== 'tiers' && <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};
