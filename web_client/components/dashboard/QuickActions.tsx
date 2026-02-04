import React from 'react';
import { LucideIcon } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';

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
                        className="group relative h-36 md:h-44 flex flex-col items-center justify-center text-center gap-3 md:gap-4 cursor-pointer active:scale-95 hover:scale-[1.02] transition-all duration-700"
                        aria-label={`Acceder a ${item.label}`}
                    >
                        <div className="absolute inset-0 glass-panel rounded-[2rem] md:rounded-[2.8rem] bg-white/[0.01] group-hover:bg-white/[0.07] group-hover:border-white/20 group-hover:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] transition-all duration-1000"></div>

                        {/* Dynamic Corner Glow */}
                        <div
                            className={`absolute -top-4 -right-4 w-32 h-32 rounded-full ${item.bg} blur-[60px] transition-all duration-1000 pointer-events-none`}
                            style={{
                                opacity: (settings.cardGlowIntensity ?? 0.5) * 0.15,
                                filter: `blur(${40 + (settings.cardGlowIntensity * 40)}px)`
                            }}
                        ></div>
                        <div
                            className={`absolute -top-4 -right-4 w-16 h-16 rounded-full ${item.bg} blur-[30px] opacity-0 group-hover:opacity-100 transition-all duration-1000 pointer-events-none`}
                            style={{ opacity: (settings.cardGlowIntensity ?? 0.5) }}
                        ></div>

                        <div className={`relative z-10 p-3 md:p-5 rounded-2xl md:rounded-[1.6rem] ${item.bg} ${item.color} border border-white/5 shadow-inner group-hover:scale-110 group-hover:-translate-y-2 transition-all duration-1000`}>
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
