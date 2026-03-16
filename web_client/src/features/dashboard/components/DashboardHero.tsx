import React from 'react';

interface DashboardHeroProps {
    userName: string;
    customStatus?: string;
    insignias?: string[];
}

export const DashboardHero: React.FC<DashboardHeroProps> = ({ userName, customStatus, insignias }) => {
    return (
        <div className="pt-6 md:pt-4 relative group">
            <div className="absolute -top-20 -left-20 w-80 h-80 bg-primary/5 rounded-premium-full blur-[100px] pointer-events-none animate-pulse-slow"></div>
            <div className="relative">
                <div className="flex items-center gap-3 mb-4 animate-in fade-in slide-in-from-left-4 duration-700">
                    <span className="px-3 py-1 rounded-premium-full bg-primary/10 border border-primary/10 text-primary text-[10px] font-black uppercase tracking-[0.2em] shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.2)]">
                        Vista General
                    </span>
                    <div className="w-1.5 h-1.5 rounded-premium-full bg-primary/40"></div>
                    <span className="text-gray-500 text-[10px] font-bold uppercase tracking-widest">
                        {new Date().toLocaleDateString('es-ES', { weekday: 'long', day: 'numeric', month: 'long' })}
                    </span>
                </div>
                <h1 className="text-5xl md:text-6xl lg:text-8xl font-black text-gray-900 dark:text-white tracking-tighter mb-6 leading-[0.95] drop-shadow-2xl">
                    Hola, <br />
                    <span className="text-transparent bg-clip-text bg-gradient-to-br from-primary via-blue-400 to-indigo-500 animate-gradient-x">
                        {userName}
                    </span> 👋
                </h1>
                <p className="text-gray-400 text-xl md:text-2xl mb-2 font-medium opacity-80 max-w-2xl leading-relaxed">
                    {customStatus || "Hoy es un gran día para descubrir mundos nuevos a través de la lectura."}
                </p>

                {insignias && insignias.length > 0 && (
                    <div className="flex flex-wrap gap-2.5 mt-8">
                        {insignias.map((badge, idx) => (
                            <div
                                key={idx}
                                className="px-5 py-2 rounded-premium-sm text-[10px] font-black uppercase tracking-widest bg-white/5 text-gray-300 border border-white/5 hover:border-primary/50 hover:bg-primary/10 hover:text-primary transition-all duration-500 cursor-default flex items-center gap-2 group/badge"
                            >
                                <div className="w-2 h-2 rounded-premium-full bg-primary group-hover:scale-125 transition-transform shadow-[0_0_8px_rgba(var(--color-primary-rgb),0.5)]"></div>
                                {badge}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
