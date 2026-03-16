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
        <div className="glass-panel rounded-premium-lg p-8 relative overflow-hidden group hover:scale-[1.005] transition-all duration-500 shadow-premium border border-white/5"
            style={{
                background: `rgba(var(--glass-rgb), ${settings.glassOpacity})`,
                backdropFilter: `blur(var(--glass-blur)) saturate(${settings.glassSaturation}%)`,
                WebkitBackdropFilter: `blur(var(--glass-blur)) saturate(${settings.glassSaturation}%)`
            }}
        >
            {/* Ambient Glow */}
            <div
                className="absolute -top-32 -right-32 w-80 h-80 bg-primary/10 rounded-premium-full blur-[100px] group-hover:bg-primary/15 transition-all duration-1000 pointer-events-none"
                style={{ opacity: settings.cardGlowIntensity * 0.5 }}
            ></div>

            <div className="flex items-center gap-5 mb-10 relative z-10">
                <div className="relative group/avatar">
                    <div className="absolute -inset-1.5 bg-gradient-to-tr from-primary via-purple-500 to-blue-400 rounded-premium-lg blur-sm opacity-20 group-hover/avatar:opacity-60 transition duration-700"></div>
                    <div className="relative w-20 h-20 rounded-premium-lg p-[2px] bg-white/5 overflow-hidden shadow-xl">
                        <div className="w-full h-full rounded-[calc(var(--radius-premium)-2px)] bg-[#0a0a0c] flex items-center justify-center overflow-hidden">
                            <img
                                src={photoUrl || "https://images.unsplash.com/photo-1544947950-fa07a98d237f?q=80&w=200"}
                                alt="Profile"
                                className="w-full h-full object-cover group-hover/avatar:scale-105 transition duration-700"
                            />
                        </div>
                    </div>
                </div>
                <div className="flex-1 min-w-0">
                    <h3 className="text-white font-bold text-2xl tracking-tight mb-1 truncate">{userLevel}</h3>
                    <div className="flex flex-wrap items-center gap-2.5">
                        <span className="px-1.5 py-0.5 rounded-premium-sm bg-primary/20 text-primary text-[8px] font-black uppercase tracking-wider border border-primary/20">{role || "Free Member"}</span>
                        <div className="w-1.5 h-1.5 rounded-premium-full bg-white/10"></div>
                        <span className="text-[10px] text-gray-500 font-medium uppercase tracking-widest truncate">{username}</span>
                    </div>
                </div>
            </div>

            <div className="space-y-8 relative z-10">
                <div className="bg-white/5 rounded-premium-lg p-6 border border-white/5 shadow-inner backdrop-blur-md relative overflow-hidden group/quota transition-colors duration-500 hover:border-white/10">
                    <div className="absolute -top-4 -right-4 p-2 opacity-[0.02] rotate-12 transition-transform duration-700 group-hover/quota:scale-110">
                        <Zap className="w-24 h-24 text-primary" />
                    </div>

                    <div className="flex justify-between items-end mb-5 relative z-10">
                        <div className="flex flex-col gap-0.5">
                            <span className="text-gray-500 text-[9px] font-bold uppercase tracking-widest flex items-center gap-2">
                                <Zap className="w-3.5 h-3.5 text-primary" />
                                Consumo Diario
                            </span>
                            <span className="text-white font-bold text-3xl tracking-tight">{downloadsUsed}</span>
                        </div>
                        <div className="flex flex-col items-end gap-0.5">
                            <span className="text-gray-500 text-[8px] font-medium uppercase tracking-widest">Límite</span>
                            <span className="text-gray-400 font-bold text-lg tracking-tight">/ {limitDisplay}</span>
                        </div>
                    </div>

                    {!isUnlimited && (
                        <div className="relative w-full h-2 bg-black/40 rounded-premium-full overflow-hidden border border-white/5 shadow-inner">
                            <div
                                className="relative h-full bg-primary rounded-premium-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.4)] transition-all duration-1000 ease-out"
                                style={{ width: `${progressPercent}%`, backgroundColor: settings.primaryColor }}
                            >
                                <div className="absolute inset-0 bg-gradient-to-t from-white/10 to-transparent"></div>
                            </div>
                        </div>
                    )}
                    {isUnlimited && (
                        <div className="w-full h-2 bg-gradient-to-r from-primary/20 via-primary/40 to-primary/20 rounded-premium-full animate-shimmer bg-[length:200%_100%]"></div>
                    )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div className="glass-panel-sub rounded-premium-lg p-5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/5 transition-all duration-500">
                        <div className="p-3 bg-primary/10 rounded-premium-sm text-primary mb-3 border border-primary/10 shadow-lg group-hover/stat:scale-105 transition-all duration-500">
                            <TrendingUp className="w-5 h-5" strokeWidth={2} />
                        </div>
                        <span className="text-white font-bold text-xl tracking-tight">Top 5%</span>
                        <span className="text-[9px] text-gray-500 uppercase font-medium tracking-widest mt-1.5 opacity-60">Ranking</span>
                    </div>
                    <div className="glass-panel-sub rounded-premium-lg p-5 flex flex-col items-center justify-center text-center group/stat hover:bg-white/5 transition-all duration-500">
                        <div className="p-3 bg-primary/10 rounded-premium-sm text-primary mb-3 border border-primary/10 shadow-lg group-hover/stat:scale-105 transition-all duration-500">
                            <Download className="w-5 h-5" strokeWidth={2} />
                        </div>
                        <span className="text-white font-bold text-xl tracking-tight">{totalDownloads}</span>
                        <span className="text-[9px] text-gray-500 uppercase font-medium tracking-widest mt-1.5 opacity-60">Leídos</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
