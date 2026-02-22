import React, { useState, useEffect, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ShieldCheck,
  BarChart3,
  Server,
  Home,
  ChevronLeft,
  RefreshCw,
  Palette,
  FileWarning,
  UploadCloud,
  Layers,
  Send,
  Activity
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { api } from '@shared/services/api';
import { MonitorDashboard } from './MonitorDashboard';
import { SystemDashboard } from './SystemDashboard';
import { AccessDashboard } from './AccessDashboard';
import { AppearanceDashboard } from '@features/settings/pages/AppearanceDashboard';
import { DuplicatesDashboard } from './DuplicatesDashboard';
import { UploadHistoryDashboard } from '@features/upload/pages/UploadHistoryDashboard';
import { PublisherDashboard } from '@features/publisher/pages/PublisherDashboard';
import { ObservatoryPage } from './ObservatoryPage';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface AdminProps {
  onNavigate?: (tab: string) => void;
}

export const Admin: React.FC<AdminProps> = ({ onNavigate }) => {
  const { settings } = useTheme();
  const { webApp } = useTelegram();
  const [searchParams, setSearchParams] = useSearchParams();
  const { state: navState, setContextType, setMenuOpen, setCustomActions, registerCallbacks, setVisible } = useNavigation();

  const isViewSelectorOpen = navState.isMenuOpen;
  const setIsViewSelectorOpen = setMenuOpen;

  // Derived state from URL
  const currentView = (searchParams.get('view') as 'monitor' | 'system' | 'access' | 'interface' | 'duplicates' | 'uploads' | 'publisher' | 'observatory') || 'monitor';
  const selectedUserId = searchParams.get('userId');
  const tierName = searchParams.get('tierName');
  const tierColor = searchParams.get('tierColor');
  const configuringTier = useMemo(() =>
    tierName ? { name: tierName, color: tierColor || '' } : null,
    [tierName, tierColor]
  );

  // Local UI state
  const [saving, setSaving] = useState(false);
  const [canUndo, setCanUndo] = useState(false);
  const [canSave, setCanSave] = useState(false);

  const undoRef = React.useRef<(() => void) | null>(null);
  const saveRef = React.useRef<(() => void) | null>(null);
  const [levels, setLevels] = useState<{ id: string, name: string, color: string }[]>([]);

  // Stable callbacks for child refs — prevents re-render cascades
  const stableSetUndoRef = React.useCallback((fn: () => void) => { undoRef.current = fn; }, []);
  const stableSetSaveRef = React.useCallback((fn: () => void) => { saveRef.current = fn; }, []);

  useEffect(() => {
    const fetchLevels = async () => {
      try {
        const res = await api.getAdminTiers();
        if (res.levels) setLevels(res.levels);
      } catch (err) { }
    };
    fetchLevels();
  }, []);

  // Contextual back action
  const handleBack = React.useCallback(() => {
    webApp?.HapticFeedback?.impactOccurred('light');
    if (selectedUserId || configuringTier) {
      // Step back from detail to list
      setSearchParams(prev => {
        const newParams = new URLSearchParams(prev);
        newParams.delete('userId');
        newParams.delete('tierName');
        newParams.delete('tierColor');
        return newParams;
      });
    } else {
      // Exit admin to dashboard
      onNavigate && onNavigate('dashboard');
    }
  }, [webApp, selectedUserId, configuringTier, setSearchParams, onNavigate]);

  useEffect(() => {
    setContextType('admin');
    setVisible(true);

    const views = [
      { id: 'monitor', label: 'Monitor', icon: BarChart3 },
      { id: 'observatory', label: 'Observatorio', icon: Activity },
      { id: 'system', label: 'Sistema', icon: Server },
      { id: 'interface', label: 'Interfaz', icon: Palette },
      { id: 'access', label: 'Acceso', icon: ShieldCheck },
      { id: 'duplicates', label: 'Duplicados', icon: FileWarning },
      { id: 'uploads', label: 'Subidas', icon: UploadCloud },
      { id: 'publisher', label: 'Publicador', icon: Send },
    ];

    setCustomActions({
      title: selectedUserId ? 'Perfil Usuario' : (views.find(v => v.id === currentView)?.label || 'Admin'),
      buttons: views.map(v => ({
        id: v.id,
        label: v.label,
        icon: v.icon,
        onClick: () => {
          setSearchParams(prev => {
            const newParams = new URLSearchParams(prev);
            newParams.set('view', v.id);
            newParams.delete('userId');
            newParams.delete('tierName');
            newParams.delete('tierColor');
            return newParams;
          });
        },
        highlight: currentView === v.id && !selectedUserId
      }))
    });

    registerCallbacks({
      onBack: handleBack
    });

    return () => {
      setContextType('main');
    };
  }, [setContextType, setVisible, setCustomActions, registerCallbacks, currentView, selectedUserId, setSearchParams, handleBack]);

  const setCurrentView = (view: string) => {
    setSearchParams(prev => {
      const newParams = new URLSearchParams(prev);
      newParams.set('view', view);
      newParams.delete('userId');
      newParams.delete('tierName');
      newParams.delete('tierColor');
      return newParams;
    });
    webApp?.HapticFeedback?.impactOccurred('medium');
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
            setUndoRef={stableSetUndoRef}
            setSaveRef={stableSetSaveRef}
          />
        );
      case 'interface':
        return (
          <AppearanceDashboard
            onSavingChange={setSaving}
            onCanUndoChange={setCanUndo}
            onCanSaveChange={setCanSave}
            setUndoRef={stableSetUndoRef}
            setSaveRef={stableSetSaveRef}
          />
        );
      case 'duplicates': return <DuplicatesDashboard />;
      case 'uploads': return <UploadHistoryDashboard />;
      case 'publisher': return <PublisherDashboard />;
      case 'observatory': return <ObservatoryPage />;
      default: return <MonitorDashboard />;
    }
  };

  return (
    <div className="relative min-h-screen">
      <div className="fixed top-0 left-0 w-full h-[600px] bg-gradient-to-br from-primary/10 via-transparent to-transparent pointer-events-none opacity-50 z-0"></div>

      <div className="max-w-[1800px] mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-700 font-sans relative z-10">

        {/* Header Only (Internal Navigation is handled by Floating Nav) */}
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 mb-8">
          <div className="flex items-center gap-4">
            <div className="p-2.5 bg-primary/20 rounded-premium-sm border border-primary/20">
              <ShieldCheck className="text-primary w-8 h-8 md:w-10 md:h-10" />
            </div>
            <h1 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              Panel <span className="text-primary font-black">Admin</span>
            </h1>
          </div>
        </div>

        {/* View Content */}
        <div className="min-h-[600px] mb-20">
          {renderView()}
        </div>
      </div>
    </div>
  );
};
