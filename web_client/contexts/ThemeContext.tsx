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
  glassBlur: 12,
  theme: 'dark',
  fontSize: 14,
  coverWidth: 120,
  colorfulCards: false,
  colorfulCardOpacity: 0.85,
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Use CloudStorage hook for persistent theme settings
  const { value: settings, saveValue: setSavedSettings, isLoading } = useCloudStorage<ThemeSettings>(
    'zeepub_theme_settings',
    defaultSettings
  );

  // Sync with backend on mount
  useEffect(() => {
    const syncWithBackend = async () => {
      try {
        const { api } = await import('../src/services/api');
        const backendSettings = await api.getUiSettings();
        if (backendSettings) {
          // Merge backend settings into CloudStorage
          // We prioritize backend settings if they exist
          const merged = { ...settings, ...backendSettings };

          // Map backend keys to frontend keys if they differ
          if (backendSettings.glassOpacity !== undefined) {
            merged.glassOpacity = backendSettings.glassOpacity;
          }

          setSavedSettings(merged);
        }
      } catch (e) {
        console.error("Failed to sync theme with backend", e);
      }
    };

    if (!isLoading) {
      syncWithBackend();
    }
  }, [isLoading]);

  useEffect(() => {
    // Apply settings to CSS variables (no localStorage needed - handled by hook)

    // Apply settings to CSS variables
    const root = document.documentElement;
    root.style.setProperty('--color-primary', settings.primaryColor);
    root.style.setProperty('--color-primary-dark', settings.primaryColorDark);

    // Add RGB components for primary color to allow alpha variations
    const r = parseInt(settings.primaryColor.substring(1, 3), 16);
    const g = parseInt(settings.primaryColor.substring(3, 5), 16);
    const b = parseInt(settings.primaryColor.substring(5, 7), 16);
    root.style.setProperty('--color-primary-rgb', `${r}, ${g}, ${b}`);

    root.style.setProperty('--glass-opacity', (settings.glassOpacity ?? 0.6).toString());
    root.style.setProperty('--nav-opacity', (settings.navOpacity ?? 0.8).toString());
    root.style.setProperty('--accent-opacity', (settings.accentOpacity ?? 0.2).toString());
    root.style.setProperty('--searchbar-opacity', (settings.searchBarOpacity ?? 0.8).toString());
    root.style.setProperty('--header-opacity', (settings.headerOpacity ?? 0.9).toString());
    root.style.setProperty('--glass-blur', `${settings.glassBlur ?? 12}px`);
    root.style.setProperty('--cover-width', `${settings.coverWidth ?? 120}px`);

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

  const updateSettings = (newSettings: Partial<ThemeSettings>) => {
    const updatedSettings = { ...settings, ...newSettings };
    setSavedSettings(updatedSettings);
  };

  const resetSettings = () => {
    // CloudStorage will handle persistence automatically
    setSavedSettings(defaultSettings);
  };

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
  return context;
};

// Helper to darken hex color for "primary-dark" generation
export function adjustBrightness(hex: string, percent: number) {
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