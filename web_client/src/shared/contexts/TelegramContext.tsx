import React, { createContext, useContext, useEffect, useState } from 'react';
import { useTheme } from './ThemeContext';
import { api, setSimulatedLevelHeader } from '@shared/services/api';
import { supabase } from '@shared/services/supabase';
import { preloadCriticalResources } from '@telegram/utils/telegramOptimizations';
import { syncTelegramTheme } from '@telegram/utils/themeSync';


import { TelegramLinkModal } from '@shared/components/TelegramLinkModal';

interface TelegramUser {
  id: number | string;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

export interface TelegramExtendedInfo {
  nickname?: string;
  name?: string;
  username?: string;
  roles: string[];
  insignias: string[];
  customStatus?: string;
  hasLibraryAccess?: boolean;
  canRequestBooks?: boolean;
  canUploadEpub?: boolean;
  titlePreference?: 'romaji' | 'english' | 'original';
}

export interface UserStatus {
  user: {
    id: number | string;
    username: string;
    tg_username?: string;       // @username real de Telegram (sin @)
    telegram_id?: number | string;
    email?: string;
    is_telegram_linked?: boolean;
    needs_telegram_link?: boolean;
    is_real_admin?: boolean;
    level: string;
    role: string | null;
    status_label: string;
    has_library_access: boolean;
    can_request_books: boolean;
    can_upload_epub: boolean;
    can_download: boolean;
    can_read: boolean;
    downloads: {
      used: number;
      limit: number | null;
      total?: number;
    };
    photo_url?: string;
  };
  hasUnlimitedDownloads: boolean;
}

interface TelegramContextType {
  webApp: any;
  user: TelegramUser | null;
  status: UserStatus | null;
  isAdmin: boolean;
  isRealAdmin: boolean;
  isStaff: boolean;
  isLinkModalOpen: boolean;
  setIsLinkModalOpen: (open: boolean) => void;

  isBetaTester: boolean;  // Controls new vs old UI
  customThemes: boolean;  // Controls if user can personalize UI
  showRecommendations: boolean; // Controls if recommendations are shown
  setShowRecommendations: (value: boolean) => void;
  isExpanded: boolean;
  ready: boolean;
  allowThemeTemplates: boolean; // Controls if user can select theme templates
  refreshStatus: () => Promise<void>;
  logout: () => Promise<void>;
  unlinkTelegram: () => Promise<void>;
  extendedInfo: TelegramExtendedInfo | null;
  // Level simulation for admins
  simulatedLevel: number | null;
  setSimulatedLevel: (levelId: number | null) => void;
  canUploadEpub: boolean;
  uiExportedSettings: string[];
  botInfo: { name: string; username: string; version: string; avatar: string } | null;
  titlePreference: 'romaji' | 'english' | 'original';
}

const TelegramContext = createContext<TelegramContextType | undefined>(undefined);

export const TelegramProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [webApp, setWebApp] = useState<any>(null);
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [status, setStatus] = useState<UserStatus | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [ready, setReady] = useState(false);
  const [isBetaTester, setIsBetaTester] = useState(false);
  const [customThemes, setCustomThemes] = useState(false);
  const [showRecommendations, setShowRecommendations] = useState(true);
  const [extendedInfo, setExtendedInfo] = useState<TelegramExtendedInfo | null>(null);
  const [simulatedLevel, setSimulatedLevel] = useState<number | null>(null);
  const [uiExportedSettings, setUiExportedSettings] = useState<string[]>(['theme', 'primaryColor', 'fontSize']);
  const [allowThemeTemplates, setAllowThemeTemplates] = useState(false);
  const [isAdminFromAccess, setIsAdminFromAccess] = useState(false);
  const [botInfo, setBotInfo] = useState<any>(null);
  const [titlePreference, setTitlePreference] = useState<'romaji' | 'english' | 'original'>('romaji');
  const { updateSettings } = useTheme();

  const [isTelegram, setIsTelegram] = useState(false);

  // Load simulated level from storage on mount
  useEffect(() => {
    const saved = localStorage.getItem('simulatedLevel');
    if (saved && saved !== 'null') {
      const levelId = parseInt(saved);
      if (!isNaN(levelId)) {
        setSimulatedLevel(levelId);
        setSimulatedLevelHeader(levelId);
      }
    }
  }, []);

  // Supabase Session Observer
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session && !isTelegram) {
        // Map Supabase User to TelegramUser format cleanly
        const sbUser = session.user;
        setUser({
          id: sbUser.id,
          first_name: sbUser.user_metadata.full_name || sbUser.email?.split('@')[0] || 'Web User',
          username: sbUser.email || 'web_user',
          photo_url: sbUser.user_metadata.avatar_url
        });
        refreshStatus();
        fetchBetaTesterStatus(sbUser.id);
      }
    });

    const { data: authListener } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (event === 'SIGNED_IN' && session && !isTelegram) {
        const sbUser = session.user;
        setUser({
          id: sbUser.id,
          first_name: sbUser.user_metadata.full_name || sbUser.email?.split('@')[0] || 'Web User',
          username: sbUser.email || 'web_user',
          photo_url: sbUser.user_metadata.avatar_url
        });
        refreshStatus();
        fetchBetaTesterStatus(sbUser.id);
      } else if (event === 'SIGNED_OUT') {
        if (!isTelegram) setUser(null);
      }
    });

    return () => authListener.subscription.unsubscribe();
  }, [isTelegram]);

  const handleSetSimulatedLevel = (levelId: number | null) => {
    setSimulatedLevel(levelId);
    setSimulatedLevelHeader(levelId);
    if (levelId === null) {
      localStorage.removeItem('simulatedLevel');
    } else {
      localStorage.setItem('simulatedLevel', levelId.toString());
    }
    // Refresh status to see the effects of simulation
    refreshStatus();
  };

  const refreshStatus = async () => {
    try {
      const { api } = await import('@shared/services/api');
      const res = await api.getUserStatus();
      setStatus(res);

      if (res && res.user) {
        const rawName = res.user.username || '';
        const cleanName = (rawName && !rawName.startsWith('User_')) ? rawName : (res.user.role === 'admin' || res.isAdmin ? 'Administrador' : `Usuario ${res.user.id}`);

        setUser(prev => prev ? {
          ...prev,
          id: res.user.id,
          first_name: (prev.first_name && !prev.first_name.startsWith('User_')) ? prev.first_name : cleanName,
          username: res.user.tg_username || res.user.username,
          photo_url: res.user.photo_url || prev.photo_url
        } : {
          id: res.user.id,
          first_name: cleanName,
          username: res.user.tg_username || res.user.username,
          photo_url: res.user.photo_url
        });

        fetchBetaTesterStatus(res.user.id);
      }
    } catch (e) {
      console.error("Failed to refresh user status", e);
    }
  };

  const refreshBotInfo = async () => {
    try {
      const { api } = await import('@shared/services/api');
      const res = await api.rpc('bot_info');
      setBotInfo(res);
    } catch (e) {
      console.error("Failed to fetch bot info", e);
    }
  };

  // Fetch beta tester status from access endpoint
  const fetchBetaTesterStatus = async (userId: number | string) => {
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
        'X-Telegram-Init-Data': (window as any).Telegram?.WebApp?.initData || ''
      };

      const { data: { session } } = await supabase.auth.getSession();
      if (session?.access_token) {
        headers['Authorization'] = `Bearer ${session.access_token}`;
        headers['X-Auth-Method'] = 'supabase';
      }

      const response = await fetch('/api/user/access', {
        method: 'POST',
        headers,
        body: JSON.stringify({ user_id: userId, force: false })
      });
      if (response.ok) {
        const data = await response.json();
        setIsBetaTester(data.isBetaTester || data.isAdmin || false);
        setCustomThemes(data.custom_themes || data.customThemes || false);
        setShowRecommendations(data.show_recommendations !== false);
        setAllowThemeTemplates(data.allow_theme_templates || data.allowThemeTemplates || false);
        setIsAdminFromAccess(data.isAdmin || false);
        setTitlePreference(data.titlePreference || 'romaji');

        if (data.ui_exported_settings) {
          setUiExportedSettings(data.ui_exported_settings);
        }

        setExtendedInfo({
          nickname: data.nickname,
          name: data.name,
          username: data.username,
          roles: data.roles || [],
          insignias: data.insignias || [],
          customStatus: data.customStatus || data.status_label,
          hasLibraryAccess: data.hasLibraryAccess,
          canRequestBooks: data.canRequestBooks,
          canUploadEpub: data.canUploadEpub,
          titlePreference: data.titlePreference
        });

        // If the access endpoint says we're admin, update the status to reflect it
        if (data.isAdmin && !status) {
          setStatus({
            user: {
              id: userId,
              username: data.nickname || `User_${userId}`,
              level: 'admin',
              role: data.role || null,
              status_label: data.status_label || 'Admin',
              has_library_access: data.hasLibraryAccess !== false,
              can_request_books: data.canRequestBooks !== false,
              can_upload_epub: data.canUploadEpub !== false,
              can_download: true,
              can_read: true,
              downloads: { used: 0, limit: null, total: 0 }
            },
            hasUnlimitedDownloads: true
          });
        }
      }
    } catch (e) {
      console.log('Could not fetch beta tester status from access endpoint');
    }
  };

  useEffect(() => {
    // Check if running inside Telegram
    if (typeof window !== 'undefined' && (window as any).Telegram?.WebApp) {
      const tg = (window as any).Telegram.WebApp;
      setWebApp(tg);
      setIsTelegram(true);

      // --- INITIAL THEME SYNC ---
      syncTelegramTheme(tg);

      const onThemeChanged = () => syncTelegramTheme(tg);
      tg.onEvent('themeChanged', onThemeChanged);

      try {
        tg.expand();
        tg.enableClosingConfirmation();

        if (tg.isVerticalSwipesEnabled !== undefined) {
          tg.disableVerticalSwipes();
        }

        if (tg.viewportStableHeight) {
          document.documentElement.style.setProperty(
            '--tg-viewport-stable-height',
            `${tg.viewportStableHeight}px`
          );
        }
      } catch (e) {
        console.warn('⚠️ Some Telegram optimizations failed:', e);
      }

      if (tg.initDataUnsafe?.user) {
        const tgUser = tg.initDataUnsafe.user;
        setUser({
          id: tgUser.id,
          first_name: tgUser.first_name,
          last_name: tgUser.last_name,
          username: tgUser.username,
          language_code: tgUser.language_code,
          photo_url: tgUser.photo_url
        });
        fetchBetaTesterStatus(tgUser.id);
      }

      setIsExpanded(tg.isExpanded);
      tg.ready();
      setReady(true);

      preloadCriticalResources();

      refreshStatus();
      refreshBotInfo();

      return () => {
        tg.offEvent('themeChanged', onThemeChanged);
      };
    } else {
      // Standalone Web App Mode
      const initWeb = async () => {
        try {
          await Promise.all([refreshStatus(), refreshBotInfo()]);
        } catch (e) {
          console.error("Standalone web init error", e);
        } finally {
          setReady(true);
        }
      };
      initWeb();
    }
  }, []);

  const isRealAdmin =
    isAdminFromAccess ||
    (status as any)?.isAdmin === true ||
    status?.user?.is_real_admin === true ||
    status?.user?.role === 'admin' ||
    status?.user?.level === 'admin' ||
    status?.user?.level === 'Administrador' ||
    status?.user?.status_label === 'Admin 🛠️' ||
    status?.user?.id === 133994080 ||
    user?.id === 133994080;

  const isAdmin =
    simulatedLevel !== null
      ? false
      : isRealAdmin;


  const isStaff =
    isAdmin ||
    status?.user?.role === 'staff' ||
    status?.user?.level === 'staff' ||
    status?.user?.level === 'Staff';

  // Admins are always beta testers
  const effectiveBetaTester = isAdmin || isBetaTester;

  const [isLinkModalOpen, setIsLinkModalOpen] = useState(false);

  useEffect(() => {
    const dismissed = sessionStorage.getItem('dismissed_telegram_link_modal');
    if (status?.user?.needs_telegram_link && !dismissed) {
      setIsLinkModalOpen(true);
    }
  }, [status?.user?.needs_telegram_link]);

  const handleCloseLinkModal = () => {
    sessionStorage.setItem('dismissed_telegram_link_modal', 'true');
    setIsLinkModalOpen(false);
  };

  const handleLogout = async () => {
    try {
      localStorage.clear();
      sessionStorage.clear();
      document.cookie = "tg_session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
      if (supabase) {
        await supabase.auth.signOut().catch(() => {});
      }
    } catch (e) {
      console.error('Logout error:', e);
    } finally {
      setStatus(null);
      setUser(null);
      // Redirect to backend logout route which clears tg_session cookie & Cloudflare Access session
      window.location.href = '/api/oauth/logout';
    }
  };

  const handleUnlinkTelegram = async () => {
    try {
      const { api } = await import('@shared/services/api');
      const res = await api.unlinkTelegram();
      if (res && res.success !== false) {
        webApp?.HapticFeedback?.notificationOccurred('success');
        if (webApp?.showAlert) {
          webApp.showAlert('✅ Cuenta de Telegram desvinculada con éxito.');
        } else {
          alert('✅ Cuenta de Telegram desvinculada con éxito.');
        }
        await refreshStatus();
      } else {
        webApp?.HapticFeedback?.notificationOccurred('error');
        const errStr = res?.error || res?.message || 'No se pudo desvincular la cuenta.';
        if (webApp?.showAlert) webApp.showAlert('❌ ' + errStr);
        else alert('❌ ' + errStr);
      }
    } catch (e: any) {
      console.error('Unlink error:', e);
      webApp?.HapticFeedback?.notificationOccurred('error');
      const msg = e.message || 'Error de servidor';
      if (webApp?.showAlert) webApp.showAlert('❌ Error al desvincular: ' + msg);
      else alert('❌ Error al desvincular: ' + msg);
    }
  };

  return (
    <TelegramContext.Provider value={{
      webApp,
      user,
      status,
      isAdmin,
      isRealAdmin,
      isStaff,
      isLinkModalOpen,
      setIsLinkModalOpen,
      isBetaTester: effectiveBetaTester,

      customThemes: isAdmin || customThemes,
      showRecommendations: showRecommendations,
      setShowRecommendations: setShowRecommendations,
      isExpanded,
      ready,
      allowThemeTemplates: isAdmin || allowThemeTemplates,
      refreshStatus,
      logout: handleLogout,
      unlinkTelegram: handleUnlinkTelegram,
      extendedInfo,
      simulatedLevel,
      setSimulatedLevel: handleSetSimulatedLevel,
      canUploadEpub: isAdmin || extendedInfo?.canUploadEpub || status?.user?.can_upload_epub || false,
      uiExportedSettings,
      botInfo,
      titlePreference
    }}>

      {children}
      <TelegramLinkModal
        isOpen={isLinkModalOpen}
        email={status?.user?.email}
        onClose={handleCloseLinkModal}
        onSuccess={() => {
          sessionStorage.removeItem('dismissed_telegram_link_modal');
          refreshStatus();
        }}
      />
    </TelegramContext.Provider>
  );
};

export const useTelegram = () => {
  const context = useContext(TelegramContext);
  if (context === undefined) {
    throw new Error('useTelegram must be used within a TelegramProvider');
  }
  return context;
};
