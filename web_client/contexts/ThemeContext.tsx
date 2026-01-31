import React, { createContext, useContext, useEffect } from 'react';
import { useCloudStorage } from '../src/hooks/useCloudStorage';

interface ThemeSettings {
  primaryColor: string;
  primaryColorDark: string;
  glassOpacity: number;
  navOpacity: number;
  accentOpacity: number;
  searchBarOpacity: number;
  headerOpacity: number;
  glassBlur: number;
  theme: 'dark' | 'light' | 'amoled';
  fontSize: number;
  coverWidth: number;
  colorfulCards: boolean;
  colorfulCardOpacity: number;
  coverQuality: 'pequeña' | 'mediana' | 'grande' | 'original';
  backgroundColor: string;
  cardColor: string;
  bannerContentOffset: number;
  cardGlowIntensity: number;
  borderRadius: number;
  borderWidth: number;
}

interface ThemeContextType {
  settings: ThemeSettings;
  updateSettings: (newSettings: Partial<ThemeSettings>) => void;
  resetSettings: () => void;
}

const defaultSettings: ThemeSettings = {
  primaryColor: '#2b6cee',
  primaryColorDark: '#1a4bb0',
  glassOpacity: 0.6,
  navOpacity: 0.8,
  accentOpacity: 0.2,
  searchBarOpacity: 0.8,
  headerOpacity: 0.9,
  glassBlur: 12, /* Enterprise Standard v3.5.0 */
  theme: 'dark',
  fontSize: 14,
  coverWidth: 120,
  colorfulCards: false,
  colorfulCardOpacity: 0.85,
  coverQuality: 'mediana',
  backgroundColor: '#0f172a',
  cardColor: '#1e293b',
  bannerContentOffset: 0,
  cardGlowIntensity: 0.5,
  borderRadius: 24,
  borderWidth: 1,
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Helper functions for CloudStorage cache
const CACHE_KEY = 'zeepub_theme_cache';

const loadFromCloudStorage = async (): Promise<{ settings: ThemeSettings; version: number } | null> => {
  try {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp?.CloudStorage) {
      return new Promise((resolve) => {
        window.Telegram.WebApp.CloudStorage.getItem(CACHE_KEY, (error, result) => {
          if (error || !result) {
            resolve(null);
            return;
          }
          try {
            resolve(JSON.parse(result));
          } catch {
            resolve(null);
          }
        });
      });
    }

    // Fallback to localStorage
    const cached = localStorage.getItem(CACHE_KEY);
    return cached ? JSON.parse(cached) : null;
  } catch {
    return null;
  }
};

const saveToCloudStorage = async (settings: ThemeSettings, version: number): Promise<void> => {
  const cacheData = JSON.stringify({ settings, version, timestamp: Date.now() });

  try {
    if (typeof window !== 'undefined' && window.Telegram?.WebApp?.CloudStorage) {
      return new Promise((resolve) => {
        window.Telegram.WebApp.CloudStorage.setItem(CACHE_KEY, cacheData, () => {
          resolve();
        });
      });
    }

    // Fallback to localStorage
    localStorage.setItem(CACHE_KEY, cacheData);
  } catch (e) {
    console.error("Failed to save theme cache", e);
  }
};

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Use local state with smart caching
  const [settings, setSettings] = React.useState<ThemeSettings>(defaultSettings);
  const [isLoading, setIsLoading] = React.useState(true);
  const [settingsVersion, setSettingsVersion] = React.useState<number>(0);

  // Load from backend with smart caching
  useEffect(() => {
    const loadWithCache = async () => {
      try {
        const { api } = await import('../src/services/api');

        // 1. Try to load from CloudStorage first (instant)
        const cached = await loadFromCloudStorage();
        if (cached) {
          setSettings(cached.settings);
          setSettingsVersion(cached.version || 0);
          setIsLoading(false); // Show UI immediately with cached data
        }

        console.log("🎨 Loading UI settings...");
        // 2. Check backend version
        const backendSettings = await api.getUiSettings();
        console.log("🎨 Backend UI settings received:", backendSettings);

        if (backendSettings) {
          const backendVersion = backendSettings.ui_version || backendSettings.last_updated || 0;

          // 3. Only update if backend has newer version
          if (!cached || backendVersion > (cached.version || 0)) {
            console.log(`🔄 Updating theme from backend (v${backendVersion})`);
            const merged = { ...defaultSettings, ...backendSettings };
            console.log("🎨 Merged settings:", merged);
            setSettings(merged);
            setSettingsVersion(backendVersion);

            // Save to cache for next time
            await saveToCloudStorage(merged, backendVersion);
          } else {
            console.log(`✅ Using cached theme (v${cached.version})`);
          }
        }
      } catch (e) {
        console.error("❌ Failed to load theme:", e);
      } finally {
        console.log("🎨 Theme loading finished.");
        setIsLoading(false);
      }
    };

    // Safety timeout: don't let the loading screen hang forever
    const timeout = setTimeout(() => {
      if (isLoading) {
        console.warn("⚠️ Theme loading timed out, starting with defaults.");
        setIsLoading(false);
      }
    }, 3500);

    loadWithCache().finally(() => clearTimeout(timeout));
  }, []);

  useEffect(() => {
    // Apply settings to CSS variables (no localStorage needed - handled by hook)

    // Helper to safely get hex components
    const getHexPart = (hex: string | undefined | null, start: number, end: number, fallback: string = '00') => {
      if (!hex || typeof hex !== 'string' || hex.length < end) return parseInt(fallback, 16);
      try {
        const val = hex.substring(start, end);
        return parseInt(val, 16) || parseInt(fallback, 16);
      } catch (e) {
        return parseInt(fallback, 16);
      }
    };

    // Apply settings to CSS variables
    const root = document.documentElement;
    const primaryColor = settings.primaryColor || defaultSettings.primaryColor;
    root.style.setProperty('--color-primary', primaryColor);
    root.style.setProperty('--color-primary-dark', settings.primaryColorDark || defaultSettings.primaryColorDark);

    // Add RGB components for primary color to allow alpha variations
    const r = getHexPart(primaryColor, 1, 3);
    const g = getHexPart(primaryColor, 3, 5);
    const b = getHexPart(primaryColor, 5, 7);
    root.style.setProperty('--color-primary-rgb', `${r}, ${g}, ${b}`);

    root.style.setProperty('--glass-opacity', (settings.glassOpacity ?? 0.6).toString());
    root.style.setProperty('--nav-opacity', (settings.navOpacity ?? 0.8).toString());
    root.style.setProperty('--accent-opacity', (settings.accentOpacity ?? 0.2).toString());
    root.style.setProperty('--searchbar-opacity', (settings.searchBarOpacity ?? 0.8).toString());
    root.style.setProperty('--header-opacity', (settings.headerOpacity ?? 0.9).toString());
    root.style.setProperty('--glass-blur', `${settings.glassBlur ?? 12}px`);
    root.style.setProperty('--cover-width', `${settings.coverWidth ?? 120}px`);
    root.style.setProperty('--banner-content-offset', `${settings.bannerContentOffset ?? 0}px`);
    root.style.setProperty('--card-glow-intensity', (settings.cardGlowIntensity ?? 0.5).toString());
    root.style.setProperty('--radius-premium', `${settings.borderRadius ?? 24}px`);
    root.style.setProperty('--border-width-premium', `${settings.borderWidth ?? 1}px`);
    const bgColor = settings.theme === 'amoled' ? '#000000' : (settings.backgroundColor ?? '#0f172a');
    root.style.setProperty('--bg-color', bgColor);
    root.style.setProperty('--app-bg', bgColor);

    // Handle card color RGB for glass effects (e.g. Nav Bar)
    if (settings.cardColor) {
      const cR = getHexPart(settings.cardColor, 1, 3);
      const cG = getHexPart(settings.cardColor, 3, 5);
      const cB = getHexPart(settings.cardColor, 5, 7);
      root.style.setProperty('--glass-rgb', `${cR}, ${cG}, ${cB}`);

      // Construct card color with transparency - Increased base opacity for better visibility
      let cardAlpha = settings.theme === 'amoled' ? 1 : Math.max(0.8, settings.glassOpacity ?? 0.6);
      if (settings.theme !== 'amoled' && settings.cardColor.length === 9) {
        cardAlpha = getHexPart(settings.cardColor, 7, 9) / 255;
      }

      const cardBase = settings.theme === 'amoled' ? '#000000' : `rgba(${cR}, ${cG}, ${cB}, ${cardAlpha})`;
      root.style.setProperty('--card-color', cardBase);

      // New thematic panel variables
      root.style.setProperty('--panel-bg', cardBase);
      root.style.setProperty('--panel-bg-lighter', `rgba(${cR}, ${cG}, ${cB}, ${Math.min(1, cardAlpha + 0.05)})`);
      root.style.setProperty('--panel-bg-subtle', `rgba(${cR}, ${cG}, ${cB}, ${Math.max(0, cardAlpha - 0.2)})`);
      root.style.setProperty('--panel-border', `rgba(${r}, ${g}, ${b}, 0.1)`);
      root.style.setProperty('--panel-border-hover', `rgba(${r}, ${g}, ${b}, 0.25)`);
    }

    // Handle background color RGB for variations
    if (settings.backgroundColor) {
      const bgR = getHexPart(settings.backgroundColor, 1, 3);
      const bgG = getHexPart(settings.backgroundColor, 3, 5);
      const bgB = getHexPart(settings.backgroundColor, 5, 7);
      root.style.setProperty('--bg-color-rgb', `${bgR}, ${bgG}, ${bgB}`);

      if (settings.backgroundColor.length === 9) {
        const bgA = getHexPart(settings.backgroundColor, 7, 9) / 255;
        root.style.setProperty('--bg-opacity', bgA.toString());
        root.style.setProperty('--bg-color', settings.backgroundColor);
      } else {
        root.style.setProperty('--bg-opacity', '1');
        root.style.setProperty('--bg-color', settings.backgroundColor);
      }
    }

    // Apply base font size (simplistic approach for demo)
    root.style.fontSize = `${settings.fontSize}px`;

    // Handle Theme Classes & Variables
    if (settings.theme === 'light') {
      root.classList.remove('dark');
      root.classList.remove('amoled');
    } else {
      root.classList.add('dark');

      if (settings.theme === 'amoled') {
        root.classList.add('amoled');
      } else {
        root.classList.remove('amoled');
      }
    }

  }, [settings]);

  const updateSettings = async (newSettings: Partial<ThemeSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSettings(updatedSettings);

    // Persist to backend
    try {
      const { api } = await import('../src/services/api');
      await api.rpc('update_user_setting', { settings: updatedSettings });

      // Update cache with new version
      const newVersion = Date.now();
      setSettingsVersion(newVersion);
      await saveToCloudStorage(updatedSettings, newVersion);
    } catch (e) {
      console.error("Failed to persist theme settings to backend", e);
    }
  };

  const resetSettings = async () => {
    setSettings(defaultSettings);

    // Persist to backend
    try {
      const { api } = await import('../src/services/api');
      await api.rpc('update_user_setting', { settings: defaultSettings });

      // Update cache with new version
      const newVersion = Date.now();
      setSettingsVersion(newVersion);
      await saveToCloudStorage(defaultSettings, newVersion);
    } catch (e) {
      console.error("Failed to reset theme settings on backend", e);
    }
  };

  // Don't render children until settings are loaded or timeout reached
  // This prevents the flash of default theme but avoids black screen if stuck
  // We keep the spinner minimal so it doesn't look like a "black screen"
  if (isLoading) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#2b6cee',
        gap: '12px'
      }}>
        <div style={{
          width: '32px',
          height: '32px',
          border: '3px solid rgba(43, 108, 238, 0.1)',
          borderTopColor: '#2b6cee',
          borderRadius: '50%',
          animation: 'spin 1s linear infinite'
        }} />
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        <div style={{ fontSize: '12px', fontWeight: 'bold', opacity: 0.8 }}>
          Inicializando interfaz...
        </div>
      </div>
    );
  }

  return (
    <ThemeContext.Provider value={{ settings, updateSettings, resetSettings }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  // Expose to window for special access (like Admin Live Preview)
  if (typeof window !== 'undefined') {
    (window as any).useTheme = () => context;
  }
  return context;
};

// Helper to darken hex color for "primary-dark" generation
export function adjustBrightness(hex: string | undefined | null, percent: number) {
  if (!hex || typeof hex !== 'string' || hex.length < 7) return hex || '#000000';

  let r = parseInt(hex.substring(1, 3), 16);
  let g = parseInt(hex.substring(3, 5), 16);
  let b = parseInt(hex.substring(5, 7), 16);

  r = Math.floor(r * (100 + percent) / 100);
  g = Math.floor(g * (100 + percent) / 100);
  b = Math.floor(b * (100 + percent) / 100);

  r = (r < 255) ? r : 255;
  g = (g < 255) ? g : 255;
  b = (b < 255) ? b : 255;

  const rr = ((r.toString(16).length === 1) ? "0" + r.toString(16) : r.toString(16));
  const gg = ((g.toString(16).length === 1) ? "0" + g.toString(16) : g.toString(16));
  const bb = ((b.toString(16).length === 1) ? "0" + b.toString(16) : b.toString(16));

  return "#" + rr + gg + bb;
}
