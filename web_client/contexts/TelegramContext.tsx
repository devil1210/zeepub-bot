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

interface TelegramContextType {
  webApp: any;
  user: TelegramUser | null;
  isExpanded: boolean;
  ready: boolean;
}

const TelegramContext = createContext<TelegramContextType | undefined>(undefined);

export const TelegramProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [webApp, setWebApp] = useState<any>(null);
  const [user, setUser] = useState<TelegramUser | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [ready, setReady] = useState(false);
  const { updateSettings } = useTheme();

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
      }

      // Sync Theme
      const applyTelegramTheme = () => {
          if (tg.themeParams) {
            // Map Telegram theme params to app theme settings
            const bg = tg.themeParams.bg_color || '#000000';
            const buttonColor = tg.themeParams.button_color || '#2AABEE';
            // Determine if dark or light based on bg color brightness roughly
            // Simple heuristic
            updateSettings({
                primaryColor: buttonColor,
                theme: 'dark' // Force dark for now based on design requirements, or detect
            });
            
            document.documentElement.style.setProperty('--app-bg', bg);
          }
      };
      
      applyTelegramTheme();
      // Listen for theme changes if API supports it (future proofing)
      
    } else {
        // Fallback for browser testing
        console.log("Telegram WebApp not detected. Running in browser mode.");
        setReady(true);
        // Mock user for dev
        setUser({
            id: 123456,
            first_name: "Dev",
            last_name: "User",
            username: "dev_user",
            photo_url: "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"
        });
    }
  }, []);

  return (
    <TelegramContext.Provider value={{ webApp, user, isExpanded, ready }}>
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