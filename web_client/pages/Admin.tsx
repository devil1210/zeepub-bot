import React, { useState } from 'react';
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
  ArrowLeft
} from 'lucide-react';
import { UserPermissions } from './UserPermissions';

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'overview' | 'system' | 'tiers'>('overview');

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
    <div className="p-4 md:p-8 max-w-7xl mx-auto flex flex-col h-full overflow-hidden relative text-slate-800 dark:text-slate-100 font-sans pb-4 md:pb-6">
      {/* Admin Header with Tabs */}
      <header className="flex flex-col md:flex-row items-start md:items-center justify-between mb-8 z-20 gap-4 shrink-0 relative">
        
        {/* Navigation Tabs (Hidden on Mobile, moved to bottom bar) */}
        <div className="hidden md:flex glass-panel p-1.5 rounded-xl items-center gap-1 shadow-lg border border-white/5 w-full md:w-auto overflow-x-auto no-scrollbar">
            {viewOptions.map((option) => (
                <button
                    key={option.id}
                    onClick={() => setCurrentView(option.id)}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-black uppercase tracking-widest transition-all whitespace-nowrap flex-1 md:flex-none justify-center ${
                        currentView === option.id
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

      {/* Main Content Area - Added pb-32 for mobile to prevent overlap with floating nav */}
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
                    <p className="text-3xl font-bold text-white tracking-tight">$4,290.00</p>
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-6 relative overflow-hidden group hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 transition-opacity pointer-events-none">
                  <Zap className="w-16 h-16 text-telegram-blue" />
                </div>
                <div className="flex flex-col h-full justify-between relative z-10">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-telegram-blue/20 rounded-xl text-telegram-blue shadow-sm border border-telegram-blue/20">
                      <Zap className="w-5 h-5" />
                    </div>
                    <span className="flex items-center text-telegram-blue text-[10px] font-black bg-telegram-blue/10 px-2.5 py-1 rounded-full border border-telegram-blue/20 backdrop-blur-md uppercase tracking-widest">
                      En Vivo
                    </span>
                  </div>
                  <div>
                    <h3 className="text-gray-400 text-[10px] font-black mb-1 uppercase tracking-widest">Sesiones Activas</h3>
                    <div className="flex items-baseline gap-2">
                      <p className="text-3xl font-bold text-white tracking-tight">1,240</p>
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
                      <p className="text-2xl font-bold text-white tracking-tight">450<span className="text-lg text-gray-500 font-normal ml-0.5">GB</span></p>
                      <p className="text-[10px] text-gray-500 font-black mb-1 uppercase">/ 1TB</p>
                    </div>
                    <div className="w-full bg-slate-900/50 rounded-full h-2 overflow-hidden border border-white/5">
                      <div className="bg-gradient-to-r from-purple-600 to-purple-400 h-2 rounded-full shadow-[0_0_8px_rgba(168,85,247,0.4)]" style={{ width: '45%' }}></div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="glass-panel rounded-2xl p-4 relative overflow-hidden group flex items-center gap-4 hover:translate-y-[-2px] transition-all border border-white/5">
                <div className="h-full w-16 bg-cover bg-center rounded-lg shadow-lg shrink-0 border border-white/10" style={{ backgroundImage: "url('https://lh3.googleusercontent.com/aida-public/AB6AXuDNN4FMDg3_CjS9YHw1nGZ4JItWisR_siKFT-hvY-GJOT3ANCaOjoQCqwFNh11csOqbW32AvpUd3Phbg6eYPIP1cbyrpXt4XAJ5x1rTmDvx1HfrlWdNL9tz2sQBRQxq2CrdS0xRfAZAX2X3WVfEQa8OvegVEUvYC-TJQYYqXdwkIMMGBUXkS1tLuXAtXhkVgsobRe0TeyyI-l6mnwT2L91DP17Yr5xN59YJ7Uv7SUGKthHsf4SU3T4F6EJGj-Wji-uzHySrLe079wI')" }}></div>
                <div className="flex flex-col justify-center min-w-0">
                  <div className="flex items-center gap-1 text-yellow-400 mb-1">
                    <Star className="w-3 h-3 fill-current" />
                    <span className="text-[9px] font-black text-white uppercase tracking-tighter">Popular</span>
                  </div>
                  <h3 className="text-white font-bold leading-tight line-clamp-1 truncate text-sm" title="Atomic Habits">Atomic Habits</h3>
                  <p className="text-[10px] text-gray-400 truncate font-medium">James Clear</p>
                  <p className="text-[10px] text-primary mt-2 font-black uppercase tracking-tight">1.1k Descargas</p>
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
                      <span className="w-2.5 h-2.5 rounded-full bg-telegram-blue shadow-[0_0_8px_rgba(42,171,238,0.5)]"></span>
                      <span className="text-[10px] font-black uppercase tracking-widest text-gray-400">Descargas</span>
                    </div>
                  </div>
                </div>
                
                <div className="w-full h-[320px] relative overflow-hidden mt-auto">
                  <div className="absolute inset-0 flex flex-col justify-between text-[10px] text-slate-600 font-mono pointer-events-none z-0">
                    <div className="flex w-full items-center"><span className="w-8 text-right pr-2 font-black">3K</span><div className="h-px bg-white/5 flex-1"></div></div>
                    <div className="flex w-full items-center"><span className="w-8 text-right pr-2 font-black">2K</span><div className="h-px bg-white/5 flex-1"></div></div>
                    <div className="flex w-full items-center"><span className="w-8 text-right pr-2 font-black">1K</span><div className="h-px bg-white/5 flex-1"></div></div>
                    <div className="flex w-full items-center"><span className="w-8 text-right pr-2 font-black">0</span><div className="h-px bg-white/5 flex-1"></div></div>
                  </div>
                  <div className="absolute bottom-0 left-8 right-0 flex justify-between text-[10px] text-slate-500 pt-2 font-black uppercase tracking-widest">
                    <span>Nov 01</span><span>Nov 15</span><span>Nov 30</span>
                  </div>
                  <svg className="absolute inset-0 left-8 h-[calc(100%-24px)] w-[calc(100%-32px)] z-10" preserveAspectRatio="none" viewBox="0 0 750 300">
                    <path className="fill-primary/5" d="M0,280 C50,250 100,290 150,200 C200,110 250,180 300,150 C350,120 400,50 450,80 C500,110 550,60 600,40 C650,20 700,50 750,30 L750,300 L0,300 Z" stroke="none"></path>
                    <path d="M0,280 C50,250 100,290 150,200 C200,110 250,180 300,150 C350,120 400,50 450,80 C500,110 550,60 600,40 C650,20 700,50 750,30" fill="none" stroke="#2b6cee" strokeLinecap="round" strokeWidth="3"></path>
                    <path d="M0,200 C60,210 120,180 180,220 C240,260 300,200 360,180 C420,160 480,190 540,140 C600,90 660,120 750,100" fill="none" stroke="#2AABEE" strokeDasharray="5,5" strokeLinecap="round" strokeWidth="2" opacity="0.6"></path>
                  </svg>
                </div>
              </div>

              <div className="flex flex-col gap-6">
                <div className="glass-panel rounded-2xl p-6 flex flex-col flex-1 border border-white/5">
                  <h3 className="text-lg font-black text-white uppercase tracking-tight mb-4">Actividad Pico</h3>
                  <div className="flex-1 grid grid-cols-[auto_1fr] gap-3">
                    <div className="flex flex-col justify-between text-[10px] text-gray-500 font-black uppercase py-1 pr-1">
                      <span>L</span><span>M</span><span>V</span><span>D</span>
                    </div>
                    <div className="grid grid-rows-7 grid-cols-12 gap-2 h-full w-full">
                      {Array.from({length: 84}).map((_, i) => (
                        <div key={i} className="rounded-sm transition-all hover:ring-2 hover:ring-primary/40 ring-offset-2 ring-offset-[#0d121c]" style={{ backgroundColor: `rgba(43, 108, 238, ${Math.random() > 0.3 ? Math.random() * 0.9 + 0.1 : 0.05})` }}></div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="glass-panel rounded-2xl p-6 border border-white/5">
                  <div className="flex justify-between items-center mb-6">
                    <h3 className="text-lg font-black text-white uppercase tracking-tight">Actividad Reciente</h3>
                    <ArrowRight className="w-4 h-4 text-primary" />
                  </div>
                  <div className="space-y-5">
                    {[
                      { u: '@alex_crypto', t: 'VIP', c: 'from-blue-600 to-indigo-600', m: 'Suscripción VIP', tm: '2m' },
                      { u: '@sarah_reads', t: 'PRO', c: 'from-purple-600 to-pink-600', m: 'Alcanzó 500 DLs', tm: '14m' },
                      { u: '@mike_z', t: 'NEW', c: 'from-emerald-600 to-teal-600', m: 'Se unió a ZeepubBot', tm: '1h' }
                    ].map((item, i) => (
                        <div key={i} className="flex items-center justify-between group">
                          <div className="flex items-center gap-3">
                            <div className={`size-8 rounded-full bg-gradient-to-tr ${item.c} flex items-center justify-center text-white font-black text-[9px] shadow-sm border border-white/20`}>{item.t}</div>
                            <div className="min-w-0">
                              <p className="text-sm text-white font-black truncate leading-tight tracking-tight">{item.u}</p>
                              <p className="text-[10px] text-gray-400 truncate uppercase tracking-widest">{item.m}</p>
                            </div>
                          </div>
                          <span className="text-[10px] text-gray-600 font-black">{item.tm}</span>
                        </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ==================== VIEW 2: SYSTEM (Ops & Logs) ==================== */}
        {currentView === 'system' && (
           <div className="animate-in fade-in duration-300 space-y-8 px-1">
              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
                 <div>
                   <h2 className="text-3xl font-black text-white mb-2 tracking-tight">Infraestructura del Sistema</h2>
                   <p className="text-gray-400 text-sm">Salud técnica y registros de despliegue.</p>
                 </div>
                 <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 border border-green-500/20 rounded-xl text-green-500 text-[10px] font-black tracking-widest uppercase">
                    <div className="w-2.5 h-2.5 bg-green-500 rounded-full animate-pulse shadow-[0_0_12px_rgba(34,197,94,0.6)]"></div>
                    Versión Estable v7.2
                 </div>
              </div>

              {/* Crystal Stats cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                 <div className="glass-panel p-6 rounded-2xl flex items-center gap-5 hover:translate-y-[-2px] transition-all border border-white/5">
                    <div className="p-4 bg-blue-500/10 rounded-2xl border border-blue-500/10">
                      <Server className="w-8 h-8 text-blue-500" />
                    </div>
                    <div>
                       <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1">Tiempo de Actividad</p>
                       <p className="text-2xl font-bold text-white font-mono">14d 22h 10m</p>
                    </div>
                 </div>
                 <div className="glass-panel p-6 rounded-2xl flex items-center gap-5 hover:translate-y-[-2px] transition-all border border-white/5">
                    <div className="p-4 bg-purple-500/10 rounded-2xl border border-purple-500/10">
                      <Cpu className="w-8 h-8 text-purple-500" />
                    </div>
                    <div>
                       <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1">Carga de Proceso</p>
                       <p className="text-2xl font-bold text-white font-mono">12% Promedio</p>
                    </div>
                 </div>
                 <div className="glass-panel p-6 rounded-2xl flex items-center gap-5 hover:translate-y-[-2px] transition-all border border-white/5">
                    <div className="p-4 bg-amber-500/10 rounded-2xl border border-amber-500/10">
                      <HardDrive className="w-8 h-8 text-amber-500" />
                    </div>
                    <div>
                       <p className="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-1">Caché de Memoria</p>
                       <p className="text-2xl font-bold text-white font-mono">2.4 / 8.0 <span className="text-xs font-normal">GB</span></p>
                    </div>
                 </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                 <div className="lg:col-span-1 glass-panel rounded-2xl p-6 flex flex-col space-y-6 border border-white/5">
                    <h3 className="text-lg font-black text-white uppercase tracking-tight flex items-center gap-2">
                       <Activity className="w-5 h-5 text-primary" />
                       Herramientas
                    </h3>
                    <div className="space-y-4 flex-1">
                       {[
                         { icon: Scan, title: 'Sync de Biblioteca', desc: 'Refrescar índice con archivos locales.', action: 'SINCRONIZAR' },
                         { icon: Database, title: 'Respaldo del Sistema', desc: 'Exportar snapshot completo de DB.', action: 'RESPALDAR', sec: true },
                         { icon: Eraser, title: 'Limpiar Caché', desc: 'Borrar metadatos temporales.', action: 'PURGAR', sec: true },
                       ].map((item, i) => (
                          <div key={i} className="p-4 rounded-xl bg-black/20 border border-white/5 hover:border-primary/40 transition-all cursor-pointer group shadow-inner">
                             <div className="flex justify-between items-center mb-2">
                                <h4 className="font-black text-slate-200 text-xs uppercase tracking-tight">{item.title}</h4>
                                <item.icon className="w-4 h-4 text-gray-500 group-hover:text-primary transition-colors" />
                             </div>
                             <p className="text-[10px] text-gray-500 mb-4 font-medium leading-relaxed">{item.desc}</p>
                             <button className={`w-full py-2.5 rounded-lg text-[10px] font-black tracking-widest transition-all uppercase ${
                               item.sec 
                                 ? 'bg-white/10 hover:bg-white/20 text-slate-300' 
                                 : 'bg-primary hover:bg-primary-dark text-white shadow-lg shadow-primary/20'
                             }`}>{item.action}</button>
                          </div>
                       ))}
                    </div>
                 </div>

                 <div className="lg:col-span-2 glass-panel rounded-2xl overflow-hidden flex flex-col min-h-[500px] border border-white/5">
                    <div className="p-4 bg-black/20 border-b border-white/5 flex justify-between items-center">
                       <h3 className="text-[10px] font-black text-slate-300 flex items-center gap-2 uppercase tracking-widest">
                          <Terminal className="w-4 h-4 text-primary" /> Feed de Logs en Vivo
                       </h3>
                       <div className="flex gap-2">
                          <span className="text-[10px] font-mono text-gray-500">STREAM_TR: ON</span>
                       </div>
                    </div>
                    <div className="flex-1 bg-black/40 p-6 font-mono text-[11px] overflow-y-auto space-y-2 text-gray-400">
                       <div className="flex gap-4"><span className="text-gray-600 font-bold shrink-0">10:42:01</span> <span className="text-blue-400 font-black shrink-0">INFO</span> <span className="flex-1">Kernel ZeepubBot inicializado con éxito (v2.4.0-web)</span></div>
                       <div className="flex gap-4"><span className="text-gray-600 font-bold shrink-0">10:42:05</span> <span className="text-blue-400 font-black shrink-0">INFO</span> <span className="flex-1">Estableciendo túnel seguro a gateway API... <span className="text-green-500">CONECTADO</span></span></div>
                       <div className="flex gap-4"><span className="text-gray-600 font-bold shrink-0">10:42:06</span> <span className="text-yellow-500 font-black shrink-0">WARN</span> <span className="flex-1">Pico de tráfico de entrada detectado (1,402 req/sec)</span></div>
                       <div className="flex gap-4"><span className="text-gray-600 font-bold shrink-0">10:43:12</span> <span className="text-blue-400 font-black shrink-0">INFO</span> <span className="flex-1">Procesando trabajo por lotes ID: <span className="underline italic text-gray-300">#930211-Sync</span></span></div>
                       <div className="pl-24 text-[10px] text-gray-500 leading-relaxed border-l border-slate-800 ml-2 py-1">
                          → Validando checksums HASH...<br/>
                          → Encontrados 12 objetos nuevos en s3://books-primary<br/>
                          → Indexando metadatos para "The Great Gatsby"...
                       </div>
                       <div className="flex gap-4"><span className="text-gray-600 font-bold shrink-0">10:43:45</span> <span className="text-green-500 font-black shrink-0">OK</span> <span className="flex-1 font-black">Sync completada. Estado de biblioteca sincronizado con DB.</span></div>
                       <div className="text-gray-400 animate-pulse mt-4 flex gap-1 items-center">
                          <span className="w-1.5 h-3 bg-primary/40 block"></span>
                          <span>Escuchando eventos del sistema...</span>
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        )}

        {/* ==================== VIEW 3: TIERS (User Mgmt) ==================== */}
        {currentView === 'tiers' && (
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
                            <li className="flex items-center gap-2 text-xs text-gray-400"><CheckCircle className="w-3 h-3 text-green-500" /> Acceso a Catálogo Público</li>
                            <li className="flex items-center gap-2 text-xs text-gray-400"><CheckCircle className="w-3 h-3 text-green-500" /> 1 Descarga Diaria</li>
                            <li className="flex items-center gap-2 text-xs text-gray-400"><Ban className="w-3 h-3 text-red-500" /> Sin Solicitudes</li>
                        </ul>
                        <button className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-bold text-white transition-colors border border-white/5">Editar Permisos</button>
                    </div>
                </div>

                {/* VIP Tier */}
                <div className="glass-panel p-6 rounded-2xl border border-primary/20 relative overflow-hidden group hover:border-primary/50 transition-all">
                    <div className="absolute inset-0 bg-primary/5"></div>
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Gem className="w-16 h-16 text-primary" />
                    </div>
                    <div className="relative z-10">
                        <span className="text-[10px] font-black uppercase tracking-widest text-primary mb-2 block">Más Popular</span>
                        <h3 className="text-2xl font-black text-white mb-4">VIP</h3>
                        <ul className="space-y-2 mb-6">
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-primary" /> Descargas Ilimitadas</li>
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-primary" /> Solicitudes Prioritarias</li>
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-primary" /> Acceso Anticipado</li>
                        </ul>
                        <button className="w-full py-2 rounded-lg bg-primary hover:bg-primary-dark text-xs font-bold text-white transition-colors shadow-lg shadow-primary/20">Configurar</button>
                    </div>
                </div>

                {/* Legend Tier */}
                <div className="glass-panel p-6 rounded-2xl border border-yellow-500/20 relative overflow-hidden group hover:border-yellow-500/50 transition-all">
                    <div className="absolute inset-0 bg-yellow-500/5"></div>
                    <div className="absolute top-0 right-0 p-4 opacity-10">
                        <Medal className="w-16 h-16 text-yellow-500" />
                    </div>
                    <div className="relative z-10">
                        <span className="text-[10px] font-black uppercase tracking-widest text-yellow-500 mb-2 block">Supporter</span>
                        <h3 className="text-2xl font-black text-white mb-4">Leyenda</h3>
                        <ul className="space-y-2 mb-6">
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-yellow-500" /> Todo lo de VIP</li>
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-yellow-500" /> Insignia de Perfil</li>
                            <li className="flex items-center gap-2 text-xs text-gray-300"><CheckCircle className="w-3 h-3 text-yellow-500" /> Canal de Soporte Directo</li>
                        </ul>
                        <button className="w-full py-2 rounded-lg bg-yellow-500/10 hover:bg-yellow-500/20 text-xs font-bold text-yellow-500 border border-yellow-500/20 transition-colors">Configurar</button>
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
                            <input type="text" placeholder="Filtrar por ID o Usuario..." className="pl-9 pr-4 py-2 bg-black/20 border border-white/10 rounded-lg text-xs text-white focus:outline-none focus:border-primary w-64" />
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
                            {[
                                { id: '#5892104', user: 'Alex_Reader', tier: 'VIP', quota: 12, max: 100, color: 'bg-purple-500 text-white' },
                                { id: '#9218401', user: 'BookWorm_99', tier: 'GRATIS', quota: 9, max: 10, color: 'bg-gray-500 text-white', warn: true },
                                { id: '#1102938', user: 'Elite_Alpha', tier: 'LEYENDA', quota: 5, max: '∞', color: 'bg-yellow-500 text-black' },
                                { id: '#4810293', user: 'New_User_01', tier: 'GRATIS', quota: 0, max: 10, color: 'bg-gray-500 text-white' },
                                { id: '#8819203', user: 'MangaLoverX', tier: 'VIP', quota: 45, max: 100, color: 'bg-purple-500 text-white' },
                            ].map((row, i) => (
                                <tr key={i} className="hover:bg-white/5 transition-colors group cursor-pointer" onClick={() => setSelectedUserId(row.id)}>
                                    <td className="p-4 text-xs font-mono text-gray-500 font-bold">{row.id}</td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${row.color.includes('purple') ? 'bg-purple-500/20 text-purple-400' : row.color.includes('yellow') ? 'bg-yellow-500/20 text-yellow-400' : 'bg-gray-700 text-gray-300'}`}>
                                                {row.user[0]}
                                            </div>
                                            <span className="text-sm font-bold text-white">{row.user}</span>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded text-[10px] font-black uppercase tracking-wider ${
                                            row.tier === 'VIP' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/20' : 
                                            row.tier === 'LEYENDA' ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/20' : 
                                            'bg-white/10 text-gray-400 border border-white/10'
                                        }`}>
                                            {row.tier}
                                        </span>
                                    </td>
                                    <td className="p-4">
                                        <div className="w-32">
                                            <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden mb-1">
                                                <div 
                                                    className={`h-full rounded-full ${row.warn ? 'bg-red-500' : 'bg-primary'}`} 
                                                    style={{ width: typeof row.max === 'number' ? `${(row.quota / row.max) * 100}%` : '5%' }}
                                                ></div>
                                            </div>
                                            <span className={`text-[10px] font-mono ${row.warn ? 'text-red-400 font-bold' : 'text-gray-500'}`}>
                                                {row.quota} / {row.max}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="p-4 text-right">
                                        <div className="flex justify-end gap-2 opacity-50 group-hover:opacity-100 transition-opacity">
                                            <button className="p-1.5 rounded-lg hover:bg-white/10 text-gray-400 hover:text-white transition-colors"><RotateCcw className="w-4 h-4" /></button>
                                            <button className="p-1.5 rounded-lg hover:bg-red-500/20 text-gray-400 hover:text-red-400 transition-colors"><Ban className="w-4 h-4" /></button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
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

      </div>
    </div>
  );
};