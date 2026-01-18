import React, { createContext, useContext, useEffect, useState } from 'react';
import { useTheme } from './ThemeContext';

interface TelegramUser {
  id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
  photo_url?: string;
}

export interface UserStatus {
  user: {
    id: number;
    username: string;
    role: string;
    status_label: string;
    downloads: {
      used: number;
      limit: number;
    };
  };
  hasUnlimitedDownloads: boolean;
}

interface TelegramContextType {
  webApp: any;
  user: TelegramUser | null;
  status: UserStatus | null;
  isAdmin: boolean;
  isBetaTester: boolean;  // Controls new vs old UI
  customThemes: boolean;  // Controls if user can personalize UI
  showRecommendations: boolean; // Controls if recommendations are shown
  setShowRecommendations: (value: boolean) => void;
  isExpanded: boolean;
  ready: boolean;
  refreshStatus: () => Promise<void>;
  // Level simulation for admins
  simulatedLevel: number | null;
  setSimulatedLevel: (levelId: number | null) => void;
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
  const [simulatedLevel, setSimulatedLevel] = useState<number | null>(null);
  const { updateSettings } = useTheme();

  const refreshStatus = async () => {
    try {
      const { api } = await import('../src/services/api');
      const res = await api.getUserStatus();
      setStatus(res);
    } catch (e) {
      console.error("Failed to refresh user status", e);
    }
  };

  // Fetch beta tester status from access endpoint
  const fetchBetaTesterStatus = async (userId: number) => {
    try {
      const response = await fetch('/api/user/access', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-Init-Data': (window as any).Telegram?.WebApp?.initData || ''
        },
        body: JSON.stringify({ user_id: userId, force: false })
      });
      if (response.ok) {
        const data = await response.json();
        setIsBetaTester(data.isBetaTester || data.isAdmin || false);
        setCustomThemes(data.customThemes || data.isAdmin || false);
        setShowRecommendations(data.showRecommendations);
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

      // Initialize
      tg.ready();
      setReady(true);

      // Expand by default
      if (!tg.isExpanded) {
        tg.expand();
        setIsExpanded(true);
      }

      // Get user data
      if (tg.initDataUnsafe?.user) {
        setUser(tg.initDataUnsafe.user);
        // Fetch beta tester status
        fetchBetaTesterStatus(tg.initDataUnsafe.user.id);
      }

      // Initial status fetch
      refreshStatus();

      // Sync Theme
      const applyTelegramTheme = () => {
        if (tg.themeParams) {
          const bg = tg.themeParams.bg_color || '#000000';
          const buttonColor = tg.themeParams.button_color || '#2b6cee';
          updateSettings({
            primaryColor: buttonColor
          });
          document.documentElement.style.setProperty('--app-bg', bg);
        }
      };

      applyTelegramTheme();

    } else {
      // Fallback for browser testing
      console.log("Telegram WebApp not detected. Running in browser mode.");
      setReady(true);
      // Mock user for dev - dev users are beta testers
      setUser({
        id: 123456,
        first_name: "Dev",
        last_name: "User",
        username: "dev_user",
        photo_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"
      });
      setIsBetaTester(true); // Dev mode = always beta tester for testing new UI
      refreshStatus();
    }
  }, []);

  const isAdmin = status?.user?.role === 'admin';

  // Admins are always beta testers
  const effectiveBetaTester = isAdmin || isBetaTester;

  return (
    <TelegramContext.Provider value={{
      webApp,
      user,
      status,
      isAdmin,
      isBetaTester: effectiveBetaTester,
      customThemes: isAdmin || customThemes,
      showRecommendations: showRecommendations,
      setShowRecommendations: setShowRecommendations,
      isExpanded,
      ready,
      refreshStatus,
      simulatedLevel,
      setSimulatedLevel
    }}>
      {children}
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