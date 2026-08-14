import React from 'react';
import { useTheme } from '@shared/contexts/ThemeContext';
import {
    LayoutDashboard,
    Search,
    Library,
    Settings,
    ShieldCheck,
    Upload,
    BrainCircuit
} from 'lucide-react';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface MobileBottomNavProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({ activeTab, onTabChange }) => {
    const { settings } = useTheme();
    const { isAdmin, canUploadEpub, status, extendedInfo } = useTelegram();
    const hasLibrary = status?.user?.has_library_access !== false && extendedInfo?.hasLibraryAccess !== false;

    const navItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Inicio' },
        { id: 'search', icon: Search, label: 'Catálogo' },
        ...(hasLibrary ? [{ id: 'library', icon: Library, label: 'Mi Lib' }] : []),
        { id: 'settings', icon: Settings, label: 'Ajustes' },
    ];

    // Optional admin items could be in a 'More' menu or just added if space permits
    // For now, let's keep it simple with primary navigation

    return (
        <div
            className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 z-[100] flex flex-col gap-3 w-[90%] max-w-xl px-0 animate-in slide-in-from-bottom-full duration-500"
        >
            <div
                className="glass-panel rounded-premium p-1 border border-black/10 dark:border-white/10 shadow-2xl flex items-center justify-between overflow-hidden"
                style={{
                    background: `rgba(var(--glass-rgb), ${settings.navOpacity || 0.8})`,
                    backdropFilter: `blur(${settings.glassBlur || 12}px)`,
                    WebkitBackdropFilter: `blur(${settings.glassBlur || 12}px)`
                }}
            >
                {navItems.map((item, index) => {
                    const isActive = activeTab === item.id;
                    return (
                        <React.Fragment key={item.id}>
                            <button
                                onClick={() => onTabChange(item.id)}
                                className={`flex-1 flex flex-col items-center justify-center py-2 rounded-premium-sm transition-all duration-300 relative z-10 ${isActive ? 'text-black dark:text-white' : 'text-gray-500 hover:text-black dark:hover:text-white'}`}
                            >
                                <div className={`p-1.5 rounded-full transition-all duration-300 ${isActive ? 'bg-[var(--color-primary)] shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)] translate-y-[-2px]' : ''}`}>
                                    <item.icon
                                        className={`w-4 h-4 transition-transform duration-300 ${isActive ? 'text-white' : ''}`}
                                        strokeWidth={isActive ? 2.5 : 2}
                                    />
                                </div>
                                <span className={`text-[9px] font-black uppercase tracking-widest mt-1 ${isActive ? 'opacity-100' : 'opacity-60'}`}>
                                    {item.label}
                                </span>
                            </button>
                            {index < navItems.length - 1 && (
                                <div className="w-px h-8 bg-black/10 dark:bg-white/5"></div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        </div>
    );
};
