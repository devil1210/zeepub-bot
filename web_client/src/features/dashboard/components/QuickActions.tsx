import React from 'react';
import { LucideIcon } from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';

interface QuickActionItem {
    id: string;
    icon: LucideIcon;
    label: string;
    desc: string;
    color: string;
    bg: string;
    visible: boolean;
}

interface QuickActionsProps {
    actions: QuickActionItem[];
    onNavigate: (id: string) => void;
    title?: string;
}

export const QuickActions: React.FC<QuickActionsProps> = ({ actions, onNavigate, title }) => {
    const { settings } = useTheme();
    if (actions.length === 0) return null;

    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
            {title && <h3 className="text-[11px] font-black text-primary/60 uppercase tracking-[0.3em] mb-4 px-1 drop-shadow-sm">{title}</h3>}
            <div className={`grid gap-4 md:gap-6 grid-cols-2 ${actions.length > 4 ? 'md:grid-cols-3' : 'sm:grid-cols-4'}`}>
                {actions.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className="group relative h-36 md:h-44 flex flex-col items-center justify-center text-center gap-3 md:gap-4 cursor-pointer active:scale-95 transition-transform duration-300 will-change-transform"
                        aria-label={`Acceder a ${item.label}`}
                    >
                        <div className="absolute inset-0 glass-panel rounded-[2rem] md:rounded-[2.8rem] transition-all duration-500 border border-[var(--panel-border)] shadow-premium backdrop-blur-3xl group-hover:bg-white/[0.05] group-hover:border-[var(--panel-border-hover)] group-hover:shadow-[0_20px_40px_-12px_rgba(0,0,0,0.5)]"
                            style={{
                                background: `rgba(var(--glass-rgb), ${settings.glassOpacity * 0.5})`,
                                backdropFilter: `blur(${settings.glassBlur}px) saturate(${settings.glassSaturation}%)`,
                                WebkitBackdropFilter: `blur(${settings.glassBlur}px) saturate(${settings.glassSaturation}%)`
                            }}
                        ></div>

                        {/* Dynamic Corner Glow */}
                        <div
                            className={`absolute -top-4 -right-4 w-32 h-32 rounded-full ${item.bg} blur-[40px] pointer-events-none opacity-0 group-hover:opacity-10 transition-opacity duration-500`}
                            style={{
                                filter: `blur(${30 + (settings.cardGlowIntensity * 20)}px)`
                            }}
                        ></div>
                        <div
                            className={`absolute -top-4 -right-4 w-16 h-16 rounded-full ${item.bg} blur-[20px] opacity-0 group-hover:opacity-60 transition-opacity duration-500 pointer-events-none`}
                        ></div>

                        <div className={`relative z-10 p-3 md:p-5 rounded-2xl md:rounded-[1.6rem] ${item.bg} ${item.color} border border-white/5 shadow-inner transition-transform duration-500 group-hover:-translate-y-2 group-hover:shadow-xl group-hover:shadow-primary/10 will-change-transform`}>
                            <item.icon className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
                        </div>
                        <div className="relative z-10 px-2">
                            <span className="block text-white font-black text-[11px] md:text-[13px] uppercase tracking-[0.15em] mb-1 drop-shadow-sm group-hover:text-primary transition-colors duration-500">{item.label}</span>
                            <span className="block text-gray-500 text-[8px] md:text-[10px] font-bold uppercase tracking-[0.2em] opacity-50 group-hover:opacity-100 transition-opacity duration-700">{item.desc}</span>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};
