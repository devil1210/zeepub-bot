import React from 'react';
import { LucideIcon } from 'lucide-react';

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
    if (actions.length === 0) return null;

    return (
        <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 delay-100">
            {title && <h3 className="text-[11px] font-black text-primary/60 uppercase tracking-[0.3em] mb-6 px-1 drop-shadow-sm">{title}</h3>}
            <div className={`grid gap-6 grid-cols-2 ${actions.length > 4 ? 'md:grid-cols-3' : 'sm:grid-cols-4'}`}>
                {actions.map((item) => (
                    <button
                        key={item.id}
                        onClick={() => onNavigate(item.id)}
                        className="group relative h-44 flex flex-col items-center justify-center text-center gap-4 cursor-pointer active:scale-95 hover:scale-[1.02] transition-all duration-500"
                        aria-label={`Acceder a ${item.label}`}
                    >
                        <div className={`absolute inset-0 rounded-[2.8rem] bg-[var(--panel-bg)] border border-[var(--panel-border)] group-hover:bg-white/[0.07] group-hover:border-white/20 group-hover:shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)] transition-all duration-700`}></div>
                        <div className={`absolute w-16 h-16 rounded-full ${item.bg} blur-2xl opacity-0 group-hover:opacity-40 transition-opacity duration-700`}></div>
                        <div className={`relative z-10 p-5 rounded-[1.6rem] ${item.bg} ${item.color} border border-white/5 shadow-inner group-hover:scale-110 group-hover:-translate-y-2 transition-all duration-700`}>
                            <item.icon className="w-8 h-8" strokeWidth={2.5} />
                        </div>
                        <div className="relative z-10">
                            <span className="block text-white font-black text-[13px] uppercase tracking-[0.15em] mb-1.5 drop-shadow-sm group-hover:text-primary transition-colors">{item.label}</span>
                            <span className="block text-gray-500 text-[10px] font-bold uppercase tracking-[0.2em] opacity-50 group-hover:opacity-100 transition-opacity duration-500">{item.desc}</span>
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};
