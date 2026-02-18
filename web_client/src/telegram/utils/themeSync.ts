/**
 * Utility to synchronize Telegram Theme Params with Zeepub CSS Variables
 * This ensures the app looks native within Telegram
 */

const hexToRgb = (hex: string): string => {
    let result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
        ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
        : '0, 0, 0';
};

const adjustBrightness = (hex: string, percent: number): string => {
    const num = parseInt(hex.replace("#", ""), 16),
        amt = Math.round(2.55 * percent),
        R = (num >> 16) + amt,
        B = ((num >> 8) & 0x00ff) + amt,
        G = (num & 0x0000ff) + amt;
    return "#" + (0x1000000 + (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 + (B < 255 ? (B < 1 ? 0 : B) : 255) * 0x100 + (G < 255 ? (G < 1 ? 0 : G) : 255)).toString(16).slice(1);
};

export const syncTelegramTheme = (webApp: any) => {
    if (!webApp?.themeParams) return;

    const p = webApp.themeParams;
    const root = document.documentElement;

    console.log('🎨 Syncing with Telegram Theme:', p);

    // 1. Background & Application Base
    if (p.bg_color) {
        root.style.setProperty('--bg-color', p.bg_color);
        root.style.setProperty('--app-bg', p.bg_color);

        // Update header color to match
        webApp.setHeaderColor(p.bg_color);
        webApp.setBackgroundColor(p.bg_color);
    }

    // 2. Primary Brand Colors (Buttons, Links)
    if (p.button_color) {
        root.style.setProperty('--color-primary', p.button_color);
        root.style.setProperty('--color-primary-rgb', hexToRgb(p.button_color));
        root.style.setProperty('--color-primary-dark', adjustBrightness(p.button_color, -15));
    }

    // 3. Glass & Panels (Derived from Secondary Background)
    if (p.secondary_bg_color) {
        // We use secondary background for "glass" tints to ensure contrast
        const rgb = hexToRgb(p.secondary_bg_color);
        root.style.setProperty('--glass-rgb', rgb);

        // Make cards slightly transparent versions of secondary bg
        const cardColor = p.secondary_bg_color;
        root.style.setProperty('--card-color', cardColor); // Fallback

        // Update ThemeContext derived vars manually for immediate effect
        // (Note: These might get overwritten if ThemeContext re-renders, strict sync might be needed in Context)
    }

    // 4. Text Colors (Optional, depends on if app uses specific text vars)
    if (p.text_color) {
        root.style.setProperty('--text-primary', p.text_color);
    }
    if (p.hint_color) {
        root.style.setProperty('--text-secondary', p.hint_color);
    }
};
