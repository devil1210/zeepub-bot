import React, { createContext, useContext, useState, useEffect } from 'react';

interface ThemeSettings {
  primaryColor: string;
  primaryColorDark: string; // Typically a darker shade
  glassOpacity: number;
  glassBlur: number;
  theme: 'dark' | 'light' | 'amoled';
  fontSize: number;
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
  glassBlur: 12,
  theme: 'dark',
  fontSize: 14,
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<ThemeSettings>(defaultSettings);

  useEffect(() => {
    // Apply settings to CSS variables
    const root = document.documentElement;
    root.style.setProperty('--color-primary', settings.primaryColor);
    root.style.setProperty('--color-primary-dark', settings.primaryColorDark);
    root.style.setProperty('--glass-opacity', settings.glassOpacity.toString());
    root.style.setProperty('--glass-blur', `${settings.glassBlur}px`);
    
    // Apply base font size (simplistic approach for demo)
    root.style.fontSize = `${settings.fontSize}px`;

    // Handle Theme Classes & Variables
    if (settings.theme === 'light') {
      root.classList.remove('dark');
      root.style.setProperty('--app-bg', '#f0f2f5');
      root.style.setProperty('--glass-rgb', '255, 255, 255');
    } else {
      root.classList.add('dark');
      root.style.setProperty('--glass-rgb', '30, 35, 45');
      
      if (settings.theme === 'amoled') {
         root.style.setProperty('--app-bg', '#000000');
      } else {
         // Default Dark
         root.style.setProperty('--app-bg', '#050505'); 
      }
    }

  }, [settings]);

  const updateSettings = (newSettings: Partial<ThemeSettings>) => {
    setSettings(prev => ({ ...prev, ...newSettings }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
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