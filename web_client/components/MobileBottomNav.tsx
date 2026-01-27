import React from 'react';
import { useTheme } from '../contexts/ThemeContext';
import {
    LayoutDashboard,
    Search,
    Library,
    Settings,
    ShieldCheck,
    Upload,
    BrainCircuit
} from 'lucide-react';
import { useTelegram } from '../contexts/TelegramContext';

interface MobileBottomNavProps {
    activeTab: string;
    onTabChange: (tab: string) => void;
}

export const MobileBottomNav: React.FC<MobileBottomNavProps> = ({ activeTab, onTabChange }) => {
    const { settings } = useTheme();
    const { isAdmin, canUploadEpub } = useTelegram();

    const navItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Inicio' },
        { id: 'search', icon: Search, label: 'Catálogo' },
        { id: 'library', icon: Library, label: 'Mi Lib' },
        { id: 'settings', icon: Settings, label: 'Ajustes' },
    ];

    // Optional admin items could be in a 'More' menu or just added if space permits
    // For now, let's keep it simple with primary navigation

    return (
        <div
            className="md:hidden fixed bottom-0 left-0 right-0 z-[100] pb-[env(safe-area-inset-bottom)] pt-2 px-6 shadow-[0_-10px_40px_-5px_rgba(0,0,0,0.5)] border-t border-white/5 animate-in slide-in-from-bottom-full duration-500"
            style={{
                background: `rgba(var(--glass-rgb), ${settings.navOpacity || 0.95})`,
                backdropFilter: `blur(${settings.glassBlur || 20}px)`,
                WebkitBackdropFilter: `blur(${settings.glassBlur || 20}px)`
            }}
        >
            <div className="flex items-center justify-between max-w-md mx-auto h-16">
                {navItems.map((item) => {
                    const isActive = activeTab === item.id;
                    return (
                        <button
                            key={item.id}
                            onClick={() => onTabChange(item.id)}
                            className="relative group flex flex-col items-center justify-center gap-1 w-14 h-full"
                        >
                            {/* Active Indicator Light */}
                            {isActive && (
                                <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-8 h-1 bg-primary rounded-b-full shadow-[0_2px_10px_rgba(var(--color-primary-rgb),0.8)] animate-in fade-in duration-300"></div>
                            )}

                            {/* Icon Wrapper */}
                            <div className={`p-1.5 rounded-xl transition-all duration-300 ${isActive ? 'bg-white/10 text-primary -translate-y-1' : 'text-gray-400 group-hover:text-white'}`}>
                                <item.icon
                                    className={`w-5 h-5 transition-transform duration-300 ${isActive ? 'scale-110' : 'group-active:scale-95'}`}
                                    strokeWidth={isActive ? 2.5 : 2}
                                />
                            </div>

                            {/* Label */}
                            <span className={`text-[9px] font-black uppercase tracking-wider transition-all duration-300 ${isActive ? 'text-white opacity-100 translate-y-0' : 'text-gray-500 opacity-60'}`}>
                                {item.label}
                            </span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
};
