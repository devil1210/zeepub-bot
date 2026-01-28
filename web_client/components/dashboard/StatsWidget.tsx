import React from 'react';
import { Download, TrendingUp, Zap } from 'lucide-react';

interface StatsWidgetProps {
    userLevel: string;
    role: string | null;
    username: string;
    photoUrl?: string;
    downloadsUsed: number;
    limitDisplay: string | number;
    progressPercent: number;
    totalDownloads: number;
    isUnlimited: boolean;
    settings: any;
}

export const StatsWidget: React.FC<StatsWidgetProps> = ({
    userLevel,
    role,
    username,
    photoUrl,
    downloadsUsed,
    limitDisplay,
    progressPercent,
    totalDownloads,
    isUnlimited,
    settings
}) => {
    return (
        <div className="glass-panel rounded-[3rem] p-10 relative overflow-hidden group hover:scale-[1.01] transition-all duration-700 shadow-premium border-white/10">
            <div
                className="absolute -top-32 -right-32 w-80 h-80 bg-primary/10 rounded-full blur-[120px] group-hover:bg-primary/20 transition-all duration-1000 pointer-events-none"
                style={{ opacity: settings.cardGlowIntensity }}
            ></div>

            <div className="flex items-center gap-6 mb-12 relative z-10">
                <div className="relative group/avatar">
                    <div className="absolute -inset-2 bg-gradient-to-tr from-primary via-purple-500 to-blue-400 rounded-premium blur opacity-30 group-hover/avatar:opacity-80 transition duration-700 animate-pulse"></div>
                    <div className="relative w-24 h-24 rounded-[2rem] p-[3px] bg-white/10 overflow-hidden shadow-2xl">
                        <div className="w-full h-full rounded-[1.85rem] bg-[#0a0a0c] flex items-center justify-center overflow-hidden">
                            <img
                                src={photoUrl || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=200"}
                                alt="Profile"
                                className="w-full h-full object-cover group-hover/avatar:scale-110 transition duration-1000"
                            />
                        </div>
                        <div className="absolute bottom-1 right-1 w-7 h-7 bg-green-500 border-4 border-[#0a0a0c] rounded-full shadow-lg z-20"></div>
                    </div>
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-white font-black text-3xl tracking-tighter leading-none mb-2 truncate">{userLevel}</h3>
                    <div className="flex flex-wrap items-center gap-3">
                        <span className="px-2 py-0.5 rounded-lg bg-primary/20 text-primary text-[9px] font-black uppercase tracking-[0.2em] border border-primary/20">{role || "Free Member"}</span>
                        <div className="w-1.5 h-1.5 rounded-full bg-white/10"></div>
                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest truncate">{username}</span>
                    </div>
                </div>
            </div>

            <div className="space-y-10 relative z-10">
                <div className="bg-white/[0.03] rounded-[2.5rem] p-8 border border-white/5 shadow-inner backdrop-blur-3xl relative overflow-hidden group/quota">
                    <div className="absolute -top-6 -right-6 p-2 opacity-[0.03] rotate-12">
                        <Zap className="w-32 h-32 text-primary" />
                    </div>
                    <div className="flex justify-between items-end mb-6 relative z-10">
                        <div className="flex flex-col gap-1">
                            <span className="text-gray-500 text-[10px] font-black uppercase tracking-[0.25em] flex items-center gap-2">
                                <Zap className="w-4 h-4 text-primary animate-pulse" />
                                Consumo Diario
                            </span>
                            <span className="text-white font-black text-4xl tracking-tighter">{downloadsUsed}</span>
                        </div>
                        <div className="flex flex-col items-end gap-1">
                            <span className="text-gray-700 text-[8px] font-black uppercase tracking-widest">Límite Total</span>
                            <span className="text-gray-500 font-black text-xl tracking-tighter">/ {limitDisplay}</span>
                        </div>
                    </div>

                    {!isUnlimited && (
                        <div className="relative w-full h-3 bg-black/40 rounded-full overflow-hidden p-[1px] border border-white/5 shadow-inner">
                            <div className="absolute inset-0 bg-primary/10 blur-[4px]"></div>
                            <div
                                className="relative h-full bg-gradient-to-r from-primary via-blue-400 to-indigo-500 rounded-full shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.6)] transition-all duration-1000 ease-out-expo"
                                style={{ width: `${progressPercent}%` }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                            </div>
                        </div>
                    )}
                    {isUnlimited && (
                        <div className="w-full h-2.5 bg-gradient-to-r from-amber-500/20 via-yellow-400/40 to-amber-200/20 rounded-full animate-shimmer bg-[length:200%_100%]"></div>
                    )}
                </div>

                <div className="grid grid-cols-2 gap-6">
                    <div className="glass-panel rounded-[2rem] p-6 border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] hover:border-white/20 transition-all duration-700">
                        <div className="p-4 bg-blue-500/10 rounded-premium-sm text-blue-400 mb-4 border border-blue-500/10 shadow-xl group-hover/stat:scale-110 group-hover/stat:rotate-3 transition-all duration-700">
                            <TrendingUp className="w-6 h-6" strokeWidth={2.5} />
                        </div>
                        <span className="text-white font-black text-2xl tracking-tighter">Top 5%</span>
                        <span className="text-[10px] text-gray-500 uppercase font-black tracking-widest mt-2 opacity-50">Status Ranking</span>
                    </div>
                    <div className="glass-panel rounded-[2rem] p-6 border-white/5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/[0.05] hover:border-white/20 transition-all duration-700">
                        <div className="p-4 bg-primary/10 rounded-premium-sm text-primary mb-4 border border-primary/10 shadow-xl group-hover/stat:scale-110 group-hover/stat:-rotate-3 transition-all duration-700">
                            <Download className="w-6 h-6" strokeWidth={2.5} />
                        </div>
                        <span className="text-white font-black text-2xl tracking-tighter">{totalDownloads}</span>
                        <span className="text-[10px] text-gray-500 uppercase font-black tracking-widest mt-2 opacity-50">Libros Leídos</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
