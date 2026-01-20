import React, { useState } from 'react';
import {
  ShieldCheck,
  BarChart3,
  Server,
  Home,
  Search,
  Bell,
  RefreshCw,
  RotateCcw,
  Save,
  Layers,
  UserCircle,
  Palette
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { MonitorDashboard } from './MonitorDashboard';
import { SystemDashboard } from './SystemDashboard';
import { AccessDashboard } from './AccessDashboard';
import { AppearanceDashboard } from './AppearanceDashboard';

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const [currentView, setCurrentView] = useState<'monitor' | 'system' | 'access' | 'interface'>('monitor');

  // Child view states (inherited from children or managed here)
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [configuringTier, setConfiguringTier] = useState<{ name: string; color: string } | null>(null);
  const [saving, setSaving] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canSave, setCanSave] = useState(false);

  // Refs for actions (passed to children)
  const undoRef = React.useRef<(() => void) | null>(null);
  const saveRef = React.useRef<(() => void) | null>(null);

  const viewOptions = [
    { id: 'monitor', label: 'Monitor', icon: BarChart3 },
    { id: 'system', label: 'Sistema', icon: Server },
    { id: 'interface', label: 'Interfaz', icon: Palette },
    { id: 'access', label: 'Niveles y Acceso', icon: ShieldCheck },
  ] as const;

  const renderView = () => {
    switch (currentView) {
      case 'monitor':
        return <MonitorDashboard />;
      case 'system':
        return <SystemDashboard />;
      case 'access':
        return (
          <AccessDashboard
            onSelectUser={setSelectedUserId}
            onConfigureTier={setConfiguringTier}
            // Connect refs and states if needed
            onSavingChange={setSaving}
            onCanUndoChange={setCanUndo}
            onCanSaveChange={setCanSave}
            setUndoRef={(fn) => { undoRef.current = fn; }}
            setSaveRef={(fn) => { saveRef.current = fn; }}
          />
        );
      case 'interface':
        return (
          <AppearanceDashboard
            onSavingChange={setSaving}
            onCanUndoChange={setCanUndo}
            onCanSaveChange={setCanSave}
            setUndoRef={(fn) => { undoRef.current = fn; }}
            setSaveRef={(fn) => { saveRef.current = fn; }}
          />
        );
      default:
        return <MonitorDashboard />;
    }
  };

  const isEditMode = !!selectedUserId || !!configuringTier;

  return (
    <div className="relative min-h-screen">
      {/* Background Glow */}
      <div className="fixed top-0 left-0 w-full h-[600px] bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none opacity-50 z-0"></div>

      <div className="max-w-7xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-700 font-sans relative z-10">

        {/* Header - Row 1: Title and Tabs */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-4">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-primary/20 rounded-2xl border border-primary/20">
              <ShieldCheck className="text-primary w-8 h-8 md:w-10 md:h-10" />
            </div>
            <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              Panel <span className="text-primary font-black">de Control</span>
            </h1>
          </div>

          {/* Sub-Tabs (Desktop) */}
          {!isEditMode && (
            <div className="flex items-center gap-1 bg-white/[0.03] p-1.5 rounded-2xl border border-white/5 backdrop-blur-md">
              {viewOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => setCurrentView(option.id)}
                  className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${currentView === option.id
                    ? 'bg-primary/90 text-white shadow-lg shadow-primary/20 scale-[1.02]'
                    : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                    }`}
                >
                  <option.icon className="w-3.5 h-3.5" />
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Header - Row 2: Status Badges and Tools */}
        {!isEditMode && (
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-10">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/5 rounded-xl text-[11px] font-bold text-gray-400">
                <span className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]"></span>
                Bot Status: Online
              </div>
              <div className="px-3 py-1.5 bg-white/5 border border-white/5 rounded-xl text-[11px] font-bold text-gray-400">
                Version: v7.1.1
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="relative group">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-primary transition-colors" />
                <input
                  className="pl-10 pr-4 py-2 bg-black/20 border border-white/10 rounded-xl text-xs focus:outline-none focus:ring-1 focus:ring-primary/50 w-full sm:w-64 text-white placeholder-gray-600 transition-all"
                  placeholder="Search logs, books..."
                  type="text"
                />
              </div>
              <button className="p-2.5 bg-white/5 border border-white/10 rounded-xl text-gray-500 hover:text-white transition-all hover:bg-white/10 relative">
                <Bell className="w-4 h-4" />
                <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-primary rounded-full border border-black animate-pulse"></span>
              </button>
              <button
                onClick={() => window.location.reload()}
                className="flex items-center gap-2 px-5 py-2 text-xs font-black uppercase tracking-widest text-white bg-slate-900 border border-white/10 rounded-xl hover:bg-black transition-all active:scale-95 shadow-lg"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Refresh
              </button>
            </div>
          </div>
        )}

        {/* Edit Mode Back Header */}
        {isEditMode && (
          <div className="flex items-center gap-4 mb-10 animate-in slide-in-from-left-4 duration-300">
            <button
              onClick={() => { setSelectedUserId(null); setConfiguringTier(null); }}
              className="p-2 rounded-xl bg-white/5 border border-white/10 text-gray-400 hover:text-white transition-all"
            >
              <RotateCcw className="w-5 h-5" />
            </button>
            <div>
              <h2 className="text-xl font-bold text-white uppercase tracking-tight">
                {configuringTier ? `Configurando Nivel: ${configuringTier.name}` : `Permisos de Usuario`}
              </h2>
              <p className="text-xs text-gray-500 font-medium">Estás en modo de edición avanzada</p>
            </div>
          </div>
        )}

        {/* Sub-Page Content */}
        <div className="min-h-[600px] mb-20">
          {renderView()}
        </div>

        {/* Admin Floating Navigation - Updated Labels */}
        <div className="fixed bottom-6 left-8 right-8 z-50 animate-in slide-in-from-bottom-4 duration-300 max-w-7xl mx-auto">
          <div
            className="glass-panel rounded-3xl p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
            style={{
              background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
              backdropFilter: `blur(${settings.glassBlur}px)`,
              WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
            }}
          >
            {isEditMode ? (
              /* Edit Mode Nav: Inicio | Restaurar | Guardar | Nivel Acceso */
              <>
                <button
                  onClick={() => { setSelectedUserId(null); setConfiguringTier(null); }}
                  className="flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white"
                >
                  <Home className="w-4 h-4" strokeWidth={2.5} />
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Inicio</span>
                </button>

                <div className="w-px h-8 bg-white/5"></div>

                <button
                  onClick={() => undoRef.current?.()}
                  disabled={!canUndo}
                  className="flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white disabled:opacity-20"
                >
                  <RotateCcw className="w-4 h-4" strokeWidth={2.5} />
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Restaurar</span>
                </button>

                <div className="w-px h-8 bg-white/5"></div>

                <button
                  onClick={() => saveRef.current?.()}
                  disabled={saving || !canSave}
                  className="flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 text-primary hover:text-primary-light disabled:opacity-20 translate-y-[-2px]"
                >
                  <div className="p-1 px-3 bg-primary rounded-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)]">
                    {saving ? <RefreshCw className="w-4 h-4 animate-spin text-white" /> : <Save className="w-4 h-4 text-white" strokeWidth={2.5} />}
                  </div>
                  <span className="text-[8px] font-black uppercase tracking-tight mt-1">Guardar</span>
                </button>

                <div className="w-px h-8 bg-white/5"></div>

                <button
                  onClick={() => { setSelectedUserId(null); setConfiguringTier(null); }}
                  className="flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white"
                >
                  <Layers className="w-4 h-4" strokeWidth={2.5} />
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Nivel Acceso</span>
                </button>
              </>
            ) : (
              /* Normal Mode Nav: Salir | Monitor | Sistema | Niveles */
              <>
                <button
                  onClick={() => onNavigate && onNavigate('dashboard')}
                  className="flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white group"
                >
                  <Home className="w-4 h-4 group-hover:scale-110 transition-transform" strokeWidth={2.5} />
                  <span className="text-[9px] font-black uppercase tracking-widest mt-1">Salir</span>
                </button>

                <div className="w-px h-8 bg-white/5"></div>

                {viewOptions.map((v) => (
                  <React.Fragment key={v.id}>
                    <button
                      onClick={() => setCurrentView(v.id)}
                      className={`flex-1 flex flex-col items-center justify-center py-2.5 rounded-2xl transition-all duration-300 ${currentView === v.id ? 'text-primary' : 'text-gray-500 hover:text-gray-300'}`}
                    >
                      <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === v.id ? 'bg-primary shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                        <v.icon className={`w-4 h-4 ${currentView === v.id ? 'text-white' : ''}`} strokeWidth={2.5} />
                      </div>
                      <span className={`text-[8px] font-black uppercase tracking-tight mt-1 whitespace-nowrap overflow-hidden text-center`}>{v.label}</span>
                    </button>
                    {v.id !== 'access' && <div className="w-px h-8 bg-white/5"></div>}
                  </React.Fragment>
                ))}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
