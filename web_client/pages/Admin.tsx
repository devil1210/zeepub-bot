import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ShieldCheck,
  BarChart3,
  Server,
  Home,
  ChevronLeft,
  ChevronUp,
  RefreshCw,
  RotateCcw,
  Save,
  Palette,
  FileWarning,
  LayoutGrid
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { MonitorDashboard } from './MonitorDashboard';
import { SystemDashboard } from './SystemDashboard';
import { AccessDashboard } from './AccessDashboard';
import { AppearanceDashboard } from './AppearanceDashboard';
import { DuplicatesDashboard } from './DuplicatesDashboard';

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const [searchParams, setSearchParams] = useSearchParams();
  const [isViewSelectorOpen, setIsViewSelectorOpen] = useState(false);

  // Derived state from URL
  const currentView = (searchParams.get('view') as 'monitor' | 'system' | 'access' | 'interface' | 'duplicates') || 'monitor';
  const selectedUserId = searchParams.get('userId');
  const tierName = searchParams.get('tierName');
  const tierColor = searchParams.get('tierColor');
  const configuringTier = tierName ? { name: tierName, color: tierColor || '' } : null;

  // Local UI state
  const [saving, setSaving] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canSave, setCanSave] = useState(false);

  const undoRef = React.useRef<(() => void) | null>(null);
  const saveRef = React.useRef<(() => void) | null>(null);

  const viewOptions = useMemo(() => [
    { id: 'monitor', label: 'Monitor', icon: BarChart3 },
    { id: 'system', label: 'Sistema', icon: Server },
    { id: 'interface', label: 'Interfaz', icon: Palette },
    { id: 'access', label: 'Niveles y Acceso', icon: ShieldCheck },
    { id: 'duplicates', label: 'Duplicados', icon: FileWarning },
  ] as const, []);

  const currentViewLabel = viewOptions.find(v => v.id === currentView)?.label || 'Panel';

  const setCurrentView = (view: string) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      newParams.set('view', view);
      newParams.delete('userId');
      newParams.delete('tierName');
      newParams.delete('tierColor');
      return newParams;
    });
    setIsViewSelectorOpen(false);
  };

  const setSelectedUserId = (id: string | null) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (id) newParams.set('userId', id);
      else newParams.delete('userId');
      return newParams;
    });
  };

  const setConfiguringTier = (tier: { name: string; color: string } | null) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      if (tier) {
        newParams.set('tierName', tier.name);
        newParams.set('tierColor', tier.color);
      } else {
        newParams.delete('tierName');
        newParams.delete('tierColor');
      }
      return newParams;
    });
  };

  const renderView = () => {
    switch (currentView) {
      case 'monitor': return <MonitorDashboard />;
      case 'system': return <SystemDashboard />;
      case 'access':
        return (
          <AccessDashboard
            onSelectUser={setSelectedUserId}
            onConfigureTier={setConfiguringTier}
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
      case 'duplicates': return <DuplicatesDashboard />;
      default: return <MonitorDashboard />;
    }
  };

  const isDetailView = !!selectedUserId || !!configuringTier;

  // Contextual back action
  const handleBack = () => {
    if (isDetailView) {
      // Step back from detail to list
      setSelectedUserId(null);
      setConfiguringTier(null);
    } else {
      // Exit admin to dashboard
      onNavigate && onNavigate('dashboard');
    }
  };

  return (
    <div className="relative min-h-screen">
      <div className="fixed top-0 left-0 w-full h-[600px] bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none opacity-50 z-0"></div>

      <div className="max-w-7xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-700 font-sans relative z-10">

        {/* Desktop Header */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-primary/20 rounded-2xl border border-primary/20">
              <ShieldCheck className="text-primary w-8 h-8 md:w-10 md:h-10" />
            </div>
            <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              Panel <span className="text-primary font-black">Admin</span>
            </h1>
          </div>

          <div className="hidden md:flex items-center gap-1 bg-white/[0.03] p-1.5 rounded-2xl border border-white/5 backdrop-blur-md">
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
        </div>

        {/* View Content */}
        <div className="min-h-[600px] mb-20">
          {renderView()}
        </div>

        {/* --- ADAPTIVE CONTEXTUAL NAVIGATION (Mobile & Desktop Floating) --- */}
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[90%] max-w-lg z-50 flex flex-col gap-3">

          {/* View Selection Overlay (Menu) */}
          {isViewSelectorOpen && !isDetailView && (
            <div
              className="glass-panel rounded-3xl p-3 border border-white/10 shadow-2xl animate-in slide-in-from-bottom-4 fade-in duration-300 overflow-hidden"
              style={{
                background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
                backdropFilter: `blur(${settings.glassBlur}px)`,
                WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
              }}
            >
              <div className="grid grid-cols-2 gap-2">
                {viewOptions.map((option) => {
                  const isActive = currentView === option.id;
                  return (
                    <button
                      key={option.id}
                      onClick={() => setCurrentView(option.id)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-2xl transition-all border ${isActive
                        ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20'
                        : 'bg-white/5 text-gray-400 border-transparent hover:bg-white/10 hover:text-white'
                        }`}
                    >
                      <option.icon className="w-4 h-4" />
                      <span className="text-[10px] font-bold uppercase tracking-wider">{option.label}</span>
                    </button>
                  );
                })}
                <button
                  onClick={() => handleBack()}
                  className="flex items-center gap-3 px-4 py-3 rounded-2xl bg-white/5 text-gray-400 border border-transparent hover:bg-red-500/20 hover:text-red-400 transition-all font-bold text-[10px] uppercase tracking-wider"
                >
                  <Home className="w-4 h-4" />
                  Salir
                </button>
              </div>
            </div>
          )}

          {/* Main Navigation Bar */}
          <div
            className="glass-panel rounded-3xl p-1.5 border border-white/10 shadow-2xl flex items-center justify-between"
            style={{
              background: `rgba(var(--glass-rgb), ${settings.navOpacity})`,
              backdropFilter: `blur(${settings.glassBlur}px)`,
              WebkitBackdropFilter: `blur(${settings.glassBlur}px)`
            }}
          >
            {/* Contextual Back Button */}
            <button
              onClick={handleBack}
              className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl text-gray-400 hover:text-white transition-all group"
            >
              <div className="p-1.5 rounded-full group-hover:bg-white/5 transition-colors">
                <ChevronLeft className="w-5 h-5" strokeWidth={2.5} />
              </div>
              <span className="text-[9px] font-black uppercase tracking-widest mt-0.5">{isDetailView ? 'Atrás' : 'Salir'}</span>
            </button>

            <div className="w-px h-8 bg-white/10"></div>

            {/* View Context / Selector Toggle */}
            <button
              onClick={() => !isDetailView && setIsViewSelectorOpen(!isViewSelectorOpen)}
              disabled={isDetailView}
              className={`flex-[2] flex items-center justify-center gap-2 px-4 py-2 rounded-2xl transition-all ${isViewSelectorOpen ? 'text-primary' : 'text-gray-300'} ${isDetailView ? 'opacity-80' : 'hover:bg-white/5 cursor-pointer'}`}
            >
              <div className="flex flex-col items-center min-w-0">
                <div className="flex items-center gap-2">
                  {!isDetailView && <LayoutGrid className="w-3.5 h-3.5 opacity-50" />}
                  <span className="text-[10px] font-black uppercase tracking-[0.15em] truncate">
                    {isDetailView ? (configuringTier ? 'Ajustes' : 'Usuario') : currentViewLabel}
                  </span>
                  {!isDetailView && <ChevronUp className={`w-3.5 h-3.5 transition-transform duration-300 ${isViewSelectorOpen ? 'rotate-180' : ''}`} />}
                </div>
              </div>
            </button>

            <div className="w-px h-8 bg-white/10"></div>

            {/* Action Group: Save/Undo (Visible if Detail or Interface) */}
            {(isDetailView || currentView === 'interface') ? (
              <div className="flex-1 flex items-center justify-center gap-1 pr-1">
                <button
                  onClick={() => undoRef.current?.()}
                  disabled={!canUndo}
                  className="p-2.5 rounded-xl text-gray-500 hover:text-white disabled:opacity-20 transition-all"
                >
                  <RotateCcw className="w-4.5 h-4.5" />
                </button>
                <button
                  onClick={() => saveRef.current?.()}
                  disabled={saving || !canSave}
                  className="p-2.5 bg-primary rounded-xl text-white shadow-lg shadow-primary/30 active:scale-90 disabled:opacity-30 disabled:grayscale transition-all"
                >
                  {saving ? <RefreshCw className="w-4.5 h-4.5 animate-spin" /> : <Save className="w-4.5 h-4.5" />}
                </button>
              </div>
            ) : (
              <button
                onClick={() => window.location.reload()}
                className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl text-gray-400 hover:text-white transition-all group"
              >
                <div className="p-1.5 rounded-full group-hover:bg-white/5 transition-colors">
                  <RefreshCw className="w-4.5 h-4.5" />
                </div>
                <span className="text-[9px] font-black uppercase tracking-widest mt-0.5">Sync</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
