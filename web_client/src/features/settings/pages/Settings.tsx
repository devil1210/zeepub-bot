import React, { useState, useEffect } from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import {
  RotateCcw,
  Save
} from 'lucide-react';
import { ReportIssueModal } from '@components/ReportIssueModal';
import { RequestBookModal } from '@components/RequestBookModal';

// Modular Components
import { SettingsHero } from '../components/SettingsHero';
import { SettingsNavigation } from '../components/SettingsNavigation';
import { SystemSettings } from '../components/SystemSettings';
import { AestheticSettings } from '../components/AestheticSettings';
import { TroubleshootingSettings } from '../components/TroubleshootingSettings';

interface SettingsProps {
  onNavigate?: (tab: string) => void;
}

export const Settings: React.FC<SettingsProps> = ({ onNavigate }) => {
  const { settings, updateSettings, resetSettings } = useTheme();
  const {
    user: tgUser,
    isAdmin,
    isRealAdmin,
    status,
    customThemes,
    simulatedLevel,
    setSimulatedLevel,
    uiExportedSettings,
    allowThemeTemplates,
    canUploadEpub
  } = useTelegram();

  const [isReportModalOpen, setIsReportModalOpen] = useState(false);
  const [isRequestModalOpen, setIsRequestModalOpen] = useState(false);
  const [availableLevels, setAvailableLevels] = useState<Array<{ id: number, name: string, color: string }>>([]);
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [availableThemes, setAvailableThemes] = useState<any[]>([]);
  const { setContextType, setVisible, setCustomActions, registerCallbacks } = useNavigation();

  useEffect(() => {
    setContextType('settings');
    setVisible(true);
    setCustomActions({
      buttons: [
        { id: 'restore', label: 'Restaurar', icon: RotateCcw, onClick: resetSettings },
        { id: 'save', label: 'Guardar', icon: Save, onClick: handleSave, highlight: true }
      ]
    });
    registerCallbacks({
      onBack: handleBack
    });
    return () => {
      setContextType('main');
    };
  }, [setContextType, setVisible, setCustomActions, registerCallbacks]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveMessage(null);
    try {
      const { api } = await import('@shared/services/api');
      const res = await api.savePersonalSettings(settings);
      if (res.success) {
        setSaveMessage({ type: 'success', text: 'Configuración guardada correctamente' });
        setTimeout(() => setSaveMessage(null), 3000);
      } else {
        throw new Error(res.message || 'Error al guardar');
      }
    } catch (err: any) {
      setSaveMessage({ type: 'error', text: err.message || 'Error al conectar con el servidor' });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearCache = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  const handleBack = () => {
    if (onNavigate) {
      onNavigate('dashboard');
    }
  };

  useEffect(() => {
    if (isRealAdmin) {
      import('@shared/services/api').then(({ api }) => {
        api.getAdminTiers().then((res: any) => {
          if (res.levels) {
            setAvailableLevels([
              { id: 0, name: 'Global (Default)', color: '#ffffff' },
              ...res.levels.map((l: any) => ({
                id: l.id,
                name: l.name,
                color: l.color || '#6b7280'
              }))
            ]);
          }
        }).catch(console.error);
      });
    }
  }, [isRealAdmin]);

  useEffect(() => {
    if (allowThemeTemplates || isAdmin) {
      import('@shared/services/api').then(({ api }) => {
        api.getAvailableThemes().then((res: any) => {
          if (res.success) {
            setAvailableThemes(res.themes);
          }
        }).catch(console.error);
      });
    }
  }, [allowThemeTemplates, isAdmin]);

  const isVisible = (key: string) => {
    if (isAdmin) return true;
    if (!customThemes) return false;
    return uiExportedSettings.includes(key);
  };

  const hasPersonalization = isAdmin || customThemes;

  return (
    <div className="max-w-[1800px] mx-auto pb-32 md:pb-12 p-4 md:p-8 animate-in fade-in duration-300 font-sans text-gray-900 dark:text-gray-100">
      <ReportIssueModal isOpen={isReportModalOpen} onClose={() => setIsReportModalOpen(false)} />
      <RequestBookModal isOpen={isRequestModalOpen} onClose={() => setIsRequestModalOpen(false)} />

      {/* Save Message Notification */}
      {saveMessage && (
        <div className={`fixed top-20 right-4 z-[100] p-4 rounded-premium-sm border animate-in slide-in-from-right-4 duration-300 ${saveMessage.type === 'success' ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-400'
          }`}>
          <div className="flex items-center gap-2">
            <div className={`p-1.5 rounded-lg ${saveMessage.type === 'success' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
              <Save className="w-4 h-4" />
            </div>
            <p className="text-sm font-bold">{saveMessage.text}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-4 space-y-8">
          <SettingsHero
            tgUser={tgUser}
            isAdmin={isAdmin}
            isRealAdmin={isRealAdmin}
            status={status}
            simulatedLevel={simulatedLevel}
            setSimulatedLevel={setSimulatedLevel}
            availableLevels={availableLevels}
          />

          <SettingsNavigation
            isAdmin={isAdmin}
            status={status}
            canUploadEpub={canUploadEpub}
            onNavigate={(tab) => onNavigate && onNavigate(tab)}
            onOpenRequestModal={() => setIsRequestModalOpen(true)}
            onOpenReportModal={() => setIsReportModalOpen(true)}
          />
        </div>

        <div className="lg:col-span-8 space-y-6">
          <SystemSettings
            settings={settings}
            updateSettings={updateSettings}
          />

          {hasPersonalization && (
            <AestheticSettings
              settings={settings}
              updateSettings={updateSettings}
              resetSettings={resetSettings}
              handleSave={handleSave}
              isSaving={isSaving}
              isAdmin={isAdmin}
              allowThemeTemplates={allowThemeTemplates}
              availableThemes={availableThemes}
              isVisible={isVisible}
            />
          )}

          <TroubleshootingSettings
            onClearCache={handleClearCache}
          />
        </div>
      </div>
    </div>
  );
};
