import React from 'react';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { Send, Palette, PenTool, LogOut, Eye, Unlink } from 'lucide-react';

interface SettingsHeroProps {
    tgUser: any;
    isAdmin: boolean;
    isRealAdmin: boolean;
    status: any;
    simulatedLevel: number | null;
    setSimulatedLevel: (level: number | null) => void;
    availableLevels: any[];
}

export const SettingsHero: React.FC<SettingsHeroProps> = ({
    tgUser,
    isAdmin,
    isRealAdmin,
    status,
    simulatedLevel,
    setSimulatedLevel,
    availableLevels
}) => {
    const { logout, unlinkTelegram, setIsLinkModalOpen } = useTelegram();
    return (
        <>
            {/* Admin Level Simulation Banner */}
            {isRealAdmin && (
                <div className="glass-panel p-4 rounded-premium-sm border border-purple-500/30 bg-purple-500/10 mb-6 animate-in slide-in-from-top-4 duration-300">
                    <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-premium-sm bg-purple-500/20 text-purple-400 border border-purple-500/20">
                                <Eye className="w-5 h-5" />
                            </div>
                            <div>
                                <p className="text-sm font-bold text-white">Simulación de Nivel</p>
                                <p className="text-xs text-gray-400">Ver la interfaz como un usuario de determinado nivel</p>
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <select
                                value={simulatedLevel === 0 ? '0' : (simulatedLevel || '')}
                                onChange={(e) => setSimulatedLevel(e.target.value === '' ? null : parseInt(e.target.value))}
                                className="px-4 py-2 text-sm font-medium border border-white/10 bg-black/20 text-white focus:outline-none focus:ring-1 focus:ring-purple-500 focus:border-purple-500 rounded-premium-sm appearance-none min-w-[160px]"
                            >
                                <option value="">Sin simulación</option>
                                {availableLevels.map(level => (
                                    <option key={level.id} value={level.id} style={{ color: level.color }}>
                                        {level.name}
                                    </option>
                                ))}
                            </select>
                            {simulatedLevel && (
                                <button
                                    onClick={() => setSimulatedLevel(null)}
                                    className="px-3 py-2 text-xs font-bold bg-red-500/20 text-red-400 rounded-lg border border-red-500/20 hover:bg-red-500/30 transition-colors"
                                >
                                    Desactivar
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Profile Card */}
            <div className="relative group">
                <div className="absolute -inset-1 bg-gradient-to-r from-primary/50 to-purple-600/50 rounded-premium-lg blur-2xl opacity-20 group-hover:opacity-40 transition-opacity duration-1000"></div>
                <div className="glass-panel p-10 rounded-premium-lg relative overflow-hidden shadow-premium border-white/10">
                    <div className="absolute top-0 left-0 w-full h-40 bg-gradient-to-br from-primary/40 via-purple-600/20 to-transparent"></div>
                    <div className="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 group-hover:rotate-12 transition-transform duration-1000">
                        <Palette className="w-24 h-24" />
                    </div>

                    <div className="relative flex flex-col items-center text-center mt-6">
                        <div className="relative mb-8">
                            <div className="absolute inset-0 bg-gradient-to-tr from-primary via-purple-500 to-transparent rounded-full blur-xl opacity-30 animate-pulse"></div>
                            <div className="relative">
                                <img
                                    alt="Avatar"
                                    className="h-32 w-32 rounded-full ring-[6px] ring-[#0a0a0c] shadow-[0_0_50px_rgba(0,0,0,0.5)] object-cover z-10 scale-100 group-hover:scale-105 transition-transform duration-700"
                                    src={tgUser?.photo_url || "https://lh3.googleusercontent.com/aida-public/AB6AXuD2rcMIxLOx5eu6yRpav3Y8qGpkFD2kC_fFSpyVjNI_zmfvjfPwU7tT0o4IWo8bJUd_Zt_ZE-XvtCRq0VFH6xkeCOZ6RNUSwUMkYvnq49dlaImBSvbx2y0LQ2ZShi-zZJ9SOX46KZQVmAqGJjihqPPZMUyxWkrYEvOQ0wjuaZfwx1Ux3D3P5FEFAo_3D3gvoUpdmv1x-qcgKh0DHSyh9-GHQ9EN3s9kFdAWafA1e_VN0XlAN9MZ3UD7h_56GH1_qsJ9cFtwIf5rKrw"}
                                />
                                <div className="absolute inset-0 rounded-full border border-white/20 z-20 pointer-events-none"></div>
                            </div>
                            <button className="absolute bottom-1 right-1 z-30 p-2.5 bg-primary rounded-premium-sm text-white shadow-2xl border-4 border-[#0a0a0c] hover:scale-110 active:scale-90 transition-all">
                                <PenTool className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="space-y-1 mb-6">
                            <h2 className="text-3xl font-black text-white tracking-tighter drop-shadow-lg">
                                {tgUser?.first_name ? `${tgUser.first_name} ${tgUser.last_name || ''}` : 'Lectores'}
                            </h2>
                            <p className="text-[11px] text-primary font-black uppercase tracking-[0.4em] opacity-80">
                                {tgUser?.username ? `@${tgUser.username}` : `UID: ${tgUser?.id}`}
                            </p>
                        </div>

                        <div className="flex flex-wrap justify-center gap-2 mb-10">
                            <div className="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] bg-white/[0.03] text-gray-400 border border-white/10 group-hover:border-primary/40 group-hover:text-primary transition-all duration-500">
                                {status?.user?.status_label || 'MIEMBRO'}
                            </div>
                            {isAdmin && (
                                <div className="px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.25em] bg-red-500/10 text-red-500 border border-red-500/20 animate-pulse">
                                    ADMIN
                                </div>
                            )}
                            <div className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-[0.15em] border ${status?.user?.tg_username || status?.user?.is_telegram_linked ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border-amber-500/20'}`}>
                                {status?.user?.tg_username
                                    ? `🟢 TELEGRAM: @${status.user.tg_username}`
                                    : status?.user?.is_telegram_linked
                                        ? `🟢 TELEGRAM VINCULADO`
                                        : '⚠️ TELEGRAM NO VINCULADO'}
                            </div>
                        </div>

                        <div className="w-full space-y-3">
                            <button
                                onClick={() => setIsLinkModalOpen(true)}
                                className="w-full py-3.5 px-6 bg-gradient-to-r from-blue-600/20 to-indigo-600/20 hover:from-blue-600/30 hover:to-indigo-600/30 border border-blue-500/30 rounded-[1.5rem] text-[11px] font-black uppercase tracking-[0.25em] text-blue-400 hover:text-white transition-all flex items-center justify-center gap-3 shadow-lg shadow-blue-500/10"
                            >
                                <Send className="w-4 h-4" />
                                {tgUser?.id || status?.user?.telegram_id ? 'Cambiar / Vincular Telegram ✈️' : 'Vincular Telegram ✈️'}
                            </button>

                            {(tgUser?.id || status?.user?.telegram_id) && (
                                <button
                                    onClick={unlinkTelegram}
                                    className="w-full py-3.5 px-6 bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/20 rounded-[1.5rem] text-[11px] font-black uppercase tracking-[0.25em] text-amber-400 hover:text-amber-300 transition-all flex items-center justify-center gap-3"
                                >
                                    <Unlink className="w-4 h-4" />
                                    Desvincular Telegram 🔗
                                </button>
                            )}

                            <button
                                onClick={logout}
                                className="w-full py-4 px-6 bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 rounded-[1.5rem] text-[11px] font-black uppercase tracking-[0.3em] text-red-400 hover:text-red-300 transition-all flex items-center justify-center gap-3 group/logout shadow-lg shadow-red-500/10"
                            >
                                <LogOut className="w-4 h-4 group-hover/logout:-translate-x-1 transition-transform" />
                                Cerrar Sesión
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};
