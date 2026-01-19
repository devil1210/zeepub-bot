import React, { useState } from 'react';
import {
  ShieldCheck,
  BarChart3,
  Server,
  Home,
  Monitor as MonitorIcon,
  Layers,
  ChevronRight
} from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import { MonitorDashboard } from './MonitorDashboard';
import { SystemDashboard } from './SystemDashboard';
import { AccessDashboard } from './AccessDashboard';

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const [currentView, setCurrentView] = useState<'monitor' | 'system' | 'access'>('monitor');

  const viewOptions = [
    { id: 'monitor', label: 'Monitor', icon: BarChart3 },
    { id: 'system', label: 'Sistema', icon: Server },
    { id: 'access', label: 'Niveles y Acceso', icon: ShieldCheck },
  ] as const;

  const renderView = () => {
    switch (currentView) {
      case 'monitor':
        return <MonitorDashboard />;
      case 'system':
        return <SystemDashboard />;
      case 'access':
        return <AccessDashboard />;
      default:
        return <MonitorDashboard />;
    }
  };

  return (
    <div className="max-w-7xl mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-500 font-sans">

      {/* Dynamic Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
        <div>
          <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight flex items-center gap-4">
            <div className="p-2 bg-primary rounded-2xl shadow-lg shadow-primary/20">
              <ShieldCheck className="text-white w-8 h-8 md:w-10 md:h-10" />
            </div>
            Panel <span className="text-primary">de Control</span>
          </h1>
        </div>

        {/* Navigation Bar for Desktop */}
        <div className="hidden md:flex items-center gap-2 bg-white/5 p-1.5 rounded-2xl border border-white/5 backdrop-blur-md">
          {viewOptions.map((option) => (
            <button
              key={option.id}
              onClick={() => setCurrentView(option.id)}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${currentView === option.id
                ? 'bg-primary text-white shadow-lg shadow-primary/20 scale-[1.02]'
                : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'
                }`}
            >
              <option.icon className="w-3.5 h-3.5" />
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {/* Sub-Page Content */}
      <div className="min-h-[600px]">
        {renderView()}
      </div>

      {/* Admin Floating Navigation - Consistent for all views */}
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
            className="flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 text-gray-400 hover:text-white group"
          >
            <Home className="w-4 h-4 group-hover:scale-110 transition-transform" strokeWidth={2.5} />
            <span className="text-[9px] font-black uppercase tracking-widest mt-1">Salir</span>
          </button>

          <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>

          {viewOptions.map((v) => (
            <React.Fragment key={v.id}>
              <button
                onClick={() => setCurrentView(v.id)}
                className={`flex-1 flex flex-col items-center justify-center py-2 rounded-2xl transition-all duration-300 ${currentView === v.id ? 'text-primary' : 'text-gray-500 hover:text-gray-300'}`}
              >
                <div className={`p-1.5 rounded-full transition-all duration-300 ${currentView === v.id ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                  <v.icon className={`w-4 h-4 ${currentView === v.id ? 'text-white' : ''}`} strokeWidth={2.5} />
                </div>
                <span className={`text-[8px] font-black uppercase tracking-tight mt-1 whitespace-nowrap overflow-hidden text-center`}>{v.label}</span>
              </button>
              {v.id !== 'access' && <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};
