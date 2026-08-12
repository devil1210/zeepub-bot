import React, { useState, useEffect } from 'react';
import {
    ShieldCheck,
    Search,
    Users,
    CheckCircle,
    ChevronRight,
    Loader2,
    RefreshCw,
    Settings,
    Zap,
    LayoutGrid
} from 'lucide-react';
import { UserPermissions } from './UserPermissions';
import { TierConfiguration } from './TierConfiguration';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';

interface UserLevel {
    id: string;
    name: string;
    priority: number;
    color: string;
    hasAccess: boolean;
    dailyDownloads: number;
    earlyAccess: boolean;
    customThemes: boolean;
    price: number;
}

interface AdminUser {
    id: string;
    username: string;
    name?: string;
    nickname?: string;
    display_name?: string;
    email?: string;
    is_telegram_linked?: boolean;
    role: string;
    photo_url?: string;
    level: {
        name: string;
        color: string;
    };
    downloads: {
        used: number;
        limit: number;
        total: number;
    };
}

interface AccessDashboardProps {
    onSelectUser: (id: string | null) => void;
    onConfigureTier: (tier: { name: string; color: string } | null) => void;
    onSavingChange?: (saving: boolean) => void;
    onCanUndoChange?: (canUndo: boolean) => void;
    onCanSaveChange?: (canSave: boolean) => void;
    setUndoRef?: (fn: () => void) => void;
    setSaveRef?: (fn: () => void) => void;
}

export const AccessDashboard: React.FC<AccessDashboardProps> = ({
    onSelectUser,
    onConfigureTier,
    onSavingChange,
    onCanUndoChange,
    onCanSaveChange,
    setUndoRef,
    setSaveRef
}) => {
    const { settings } = useTheme();
    const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
    const [configuringTier, setConfiguringTier] = useState<{ name: string; color: string } | null>(null);
    const [levels, setLevels] = useState<UserLevel[]>([]);
    const [users, setUsers] = useState<AdminUser[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');

    const [scanningUser, setScanningUser] = useState<string | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [levelsData, usersData] = await Promise.all([
                api.getAdminTiers(),
                api.getAdminUsers(20, 0, searchQuery)
            ]);

            console.log('Levels data:', levelsData);
            console.log('Users data:', usersData);

            setLevels(levelsData.levels as UserLevel[] || []);
            setUsers(usersData.users as AdminUser[] || []);
        } catch (error) {
            console.error("Error fetching access data:", error);
            // Set empty arrays to prevent black screen
            setLevels([]);
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSyncUserPhoto = async (e: React.MouseEvent, userId: string) => {
        e.stopPropagation();
        try {
            setScanningUser(userId);
            const res = await api.adminScanUser(userId);
            if (res.success) {
                // Update local user state
                setUsers(prev => prev.map(u =>
                    u.id === userId ? { ...u, photo_url: res.photo_url } : u
                ));
            } else {
                alert(res.message || "Error al sincronizar foto");
            }
        } catch (error) {
            console.error("Error scanning user:", error);
        } finally {
            setScanningUser(null);
        }
    };

    useEffect(() => {
        fetchData();
    }, [searchQuery]);

    // Handle internal state and sync with parent
    const handleSelectUser = (id: string | null) => {
        setSelectedUserId(id);
        onSelectUser(id);
    };

    const handleConfigureTier = (tier: { name: string; color: string } | null) => {
        setConfiguringTier(tier);
        onConfigureTier(tier);
    };

    if (selectedUserId) {
        return (
            <UserPermissions
                userId={selectedUserId}
                onBack={() => { handleSelectUser(null); fetchData(); }}
                onSavingChange={onSavingChange}
                onCanUndoChange={onCanUndoChange}
                onCanApplyChange={onCanSaveChange}
                onUndoRef={setUndoRef}
                onSaveRef={setSaveRef}
            />
        );
    }

    if (configuringTier) {
        return (
            <TierConfiguration
                tierName={configuringTier.name}
                tierColor={configuringTier.color}
                onBack={() => { handleConfigureTier(null); fetchData(); }}
                // Add TierConfig specific refs if needed
                onSavingChange={onSavingChange}
                onCanUndoChange={onCanUndoChange}
                onCanApplyChange={onCanSaveChange}
                onUndoRef={setUndoRef}
                onSaveRef={setSaveRef}
            />
        );
    }

    return (
        <div className="flex flex-col gap-10 animate-in fade-in duration-500 pb-36">
            {/* Page Heading */}
            <div className="flex flex-col gap-4">
                <h1 className="text-4xl font-black text-white leading-tight tracking-tighter uppercase">Niveles y Acceso</h1>
                <p className="text-gray-400 text-sm font-medium leading-relaxed max-w-2xl">
                    Configura permisos globales y niveles de suscripción para toda la base de usuarios.
                </p>
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex flex-col items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                    <p className="text-gray-400 text-sm">Cargando datos de acceso...</p>
                </div>
            )}

            {/* Content */}
            {!loading && (
                <>
                    {/* Tier Summary Table */}
                    <div className="glass-panel border border-white/5 rounded-premium overflow-hidden shadow-2xl animate-in slide-in-from-bottom-4 duration-700">
                        <div className="p-8 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <div className="p-3 bg-primary/10 rounded-premium-sm border border-primary/20">
                                    <ShieldCheck className="w-6 h-6 text-primary" />
                                </div>
                                <div>
                                    <h3 className="text-xl font-black text-white uppercase tracking-tight">Resumen de Niveles</h3>
                                    <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Comparativa de privilegios por rango</p>
                                </div>
                            </div>

                            <button
                                onClick={() => handleConfigureTier({ name: levels[0]?.name || 'Global', color: levels[0]?.color || '#ffffff' })}
                                className="px-8 py-3.5 rounded-premium-sm bg-primary text-white text-[10px] font-black uppercase tracking-[0.2em] shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
                            >
                                <Settings className="w-3.5 h-3.5" />
                                Gestionar Niveles
                            </button>
                        </div>

                        <div className="overflow-x-auto custom-scrollbar">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-black/20">
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5">Nivel</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-center">Descargas</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-center">Simultáneas</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-center hidden md:table-cell">Anticipado</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-center hidden lg:table-cell">Temas</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-center hidden xl:table-cell">Subidas</th>
                                        <th className="px-8 py-5 text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 text-right">Estado</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {levels.sort((a, b) => a.priority - b.priority).map((level) => (
                                        <tr key={level.id} className="group hover:bg-white/[0.02] transition-all duration-300">
                                            <td className="px-8 py-6">
                                                <div className="flex items-center gap-4">
                                                    <div
                                                        className="w-10 h-10 rounded-premium-sm flex items-center justify-center border shadow-inner group-hover:scale-110 transition-transform duration-500"
                                                        style={{
                                                            backgroundColor: `${level.color}15`,
                                                            color: level.color,
                                                            borderColor: `${level.color}20`
                                                        }}
                                                    >
                                                        <ShieldCheck className="w-4 h-4" />
                                                    </div>
                                                    <div>
                                                        <p className="font-black text-white text-base tracking-tight group-hover:text-primary transition-colors">{level.name}</p>
                                                        <span className="text-[7px] font-bold text-gray-600 uppercase tracking-widest bg-black/40 px-1.5 py-0.5 rounded border border-white/5">
                                                            P{level.priority}
                                                        </span>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center">
                                                <span className={`text-xs font-black tabular-nums ${level.dailyDownloads === -1 ? 'text-primary' : 'text-gray-300'}`}>
                                                    {level.dailyDownloads === -1 ? '∞' : level.dailyDownloads}
                                                </span>
                                            </td>
                                            <td className="px-8 py-6 text-center">
                                                <span className="text-xs font-black text-gray-400 tabular-nums">
                                                    3
                                                </span>
                                            </td>
                                            <td className="px-8 py-6 text-center hidden md:table-cell">
                                                <div className={`p-1.5 rounded-lg inline-flex ${level.earlyAccess ? 'bg-primary/20 text-primary' : 'bg-white/5 text-gray-800'}`}>
                                                    <Zap className="w-3.5 h-3.5" />
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center hidden lg:table-cell">
                                                <div className={`p-1.5 rounded-lg inline-flex ${level.customThemes ? 'bg-purple-500/20 text-purple-400' : 'bg-white/5 text-gray-800'}`}>
                                                    <LayoutGrid className="w-3.5 h-3.5" />
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-center hidden xl:table-cell">
                                                <div className={`p-1.5 rounded-lg inline-flex ${level.id === '6' ? 'bg-blue-500/20 text-blue-400' : 'bg-white/5 text-gray-800'}`}>
                                                    <Settings className="w-3.5 h-3.5" />
                                                </div>
                                            </td>
                                            <td className="px-8 py-6 text-right">
                                                <span className="text-[8px] font-black uppercase tracking-widest text-emerald-500 flex items-center justify-end gap-1.5">
                                                    <div className="w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
                                                    Activo
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Users List - Dynamic Grid (Square Cards on Mobile) */}
                    <div className="glass-panel border border-white/5 rounded-premium p-6 sm:p-8">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8">
                            <div className="flex items-center gap-3">
                                <Users className="text-primary w-5 h-5" />
                                <h3 className="text-sm font-black text-white uppercase tracking-widest">Gesti&oacute;n de Usuarios</h3>
                            </div>

                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Buscar por ID o Username..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="pl-10 pr-4 py-2.5 bg-black/20 border border-white/10 rounded-premium-sm text-xs text-white focus:outline-none focus:ring-1 focus:ring-primary/50 w-full sm:w-80"
                                />
                            </div>
                        </div>

                        {/* Mobile: Grid of Square Cards | Desktop: Table-like list */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-1 gap-4">
                            {users.length === 0 ? (
                                <div className="py-20 text-center text-gray-500 italic text-sm">No se encontraron usuarios...</div>
                            ) : (
                                users.map((user) => (
                                    <div
                                        key={user.id}
                                        onClick={() => handleSelectUser(user.id)}
                                        className="group bg-white/[0.01] hover:bg-white/[0.04] border border-white/5 hover:border-primary/20 rounded-premium p-5 transition-all duration-300 flex flex-col lg:flex-row lg:items-center gap-6 cursor-pointer relative overflow-hidden"
                                    >
                                        {/* User Info Block */}
                                        <div className="flex items-center gap-5 lg:min-w-[260px] relative z-10">
                                            <div className="w-16 h-16 rounded-premium-sm bg-primary/10 flex items-center justify-center text-primary font-black text-xl border border-primary/10 shadow-inner group-hover:scale-110 transition-transform duration-500 overflow-hidden relative">
                                                {user.photo_url ? (
                                                    <img
                                                        src={user.photo_url}
                                                        alt={user.display_name || user.username}
                                                        className="w-full h-full object-cover"
                                                        onError={(e) => {
                                                            // Fallback if image fails to load
                                                            const target = e.target as HTMLImageElement;
                                                            target.style.display = 'none';
                                                            target.parentElement!.innerText = user.username?.charAt(0).toUpperCase() || '?';
                                                        }}
                                                    />
                                                ) : (
                                                    user.username?.charAt(0).toUpperCase() || '?'
                                                )}
                                                {scanningUser === user.id && (
                                                    <div className="absolute inset-0 bg-black/40 flex items-center justify-center backdrop-blur-sm">
                                                        <Loader2 className="w-6 h-6 text-white animate-spin" />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="min-w-0 flex-1">
                                                <div className="flex flex-col">
                                                    <p className="font-black text-white truncate text-base tracking-tight group-hover:text-primary transition-colors leading-tight">
                                                        {user.display_name || user.name || `@${user.username}` || `Usuario ${user.id.slice(-4)}`}
                                                    </p>
                                                    {user.username && user.username !== 'unknown' && (
                                                        <p className="text-[10px] text-gray-400 font-bold tracking-tight mt-0.5">
                                                            @{user.username} {user.name && user.name !== user.display_name && user.name !== 'unknown' && `• ${user.name}`}
                                                        </p>
                                                    )}
                                                    {user.email && (
                                                        <p className="text-[11px] text-blue-400 font-medium tracking-tight mt-0.5 flex items-center gap-1">
                                                            <span>📧</span> {user.email}
                                                        </p>
                                                    )}
                                                </div>
                                                <div className="flex items-center gap-2 mt-1">
                                                    <button
                                                        onClick={(e) => handleSyncUserPhoto(e, user.id)}
                                                        disabled={scanningUser === user.id}
                                                        className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-primary transition-all active:scale-90"
                                                        title="Sincronizar foto de perfil desde Telegram"
                                                    >
                                                        {scanningUser === user.id ? (
                                                            <Loader2 className="w-3 h-3 animate-spin" />
                                                        ) : (
                                                            <RefreshCw className="w-3 h-3" />
                                                        )}
                                                    </button>
                                                     <span className={`text-[9px] font-bold px-2 py-0.5 rounded-md border ${user.is_telegram_linked || (user.id && !user.id.startsWith('synthetic') && Number(user.id) > 0) ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20' : 'bg-amber-500/10 text-amber-300 border-amber-500/20'}`}>
                                                         {user.is_telegram_linked || (user.id && !user.id.startsWith('synthetic') && Number(user.id) > 0)
                                                             ? `🟢 Telegram: ${user.username && !user.username.startsWith('User_') ? `@${user.username}` : `ID ${user.id}`}`
                                                             : '⚠️ Telegram No Vinculado'}
                                                     </span>
                                                </div>
                                                <p className="text-[10px] text-gray-600 font-mono tracking-tighter mt-1">ID: {user.id}</p>
                                            </div>
                                        </div>

                                        {/* Level Badge */}
                                        <div className="lg:w-36 relative z-10">
                                            <span
                                                className="px-4 py-1.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest border inline-block shadow-lg"
                                                style={{ backgroundColor: `${user.level.color}15`, color: user.level.color, borderColor: `${user.level.color}20` }}
                                            >
                                                {user.level.name}
                                            </span>
                                        </div>

                                        {/* Progress Block */}
                                        <div className="flex-1 flex flex-col gap-3 relative z-10">
                                            <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider">
                                                <span className="text-gray-500">Cuota Diaria</span>
                                                <span className="text-primary">{user.downloads.used} <span className="text-gray-600 mx-1">/</span> {user.downloads.limit === -1 ? '∞' : user.downloads.limit}</span>
                                            </div>
                                            <div className="w-full h-2.5 bg-black/40 rounded-full overflow-hidden p-[1px] border border-white/5">
                                                <div
                                                    className="h-full bg-primary shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)] transition-all duration-700 rounded-full"
                                                    style={{ width: user.downloads.limit === -1 ? '20%' : `${Math.min(100, (user.downloads.used / user.downloads.limit) * 100)}%` }}
                                                ></div>
                                            </div>
                                        </div>

                                        {/* Stats & Action */}
                                        <div className="flex items-center justify-between lg:justify-end gap-10 lg:min-w-[180px] relative z-10">
                                            <div className="text-right">
                                                <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-1">Total DLS</p>
                                                <p className="text-lg font-black text-white tabular-nums">{user.downloads.total}</p>
                                            </div>
                                            <div className="p-3.5 bg-white/5 rounded-[1.25rem] text-gray-500 group-hover:text-white group-hover:bg-primary transition-all duration-300 shadow-lg">
                                                <ChevronRight className="w-5 h-5" strokeWidth={3} />
                                            </div>
                                        </div>

                                        {/* Subtle Row Glow */}
                                        <div className="absolute -left-10 -bottom-10 w-32 h-32 bg-primary/5 rounded-full blur-3xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none" style={{ opacity: settings.cardGlowIntensity * 0.2 }}></div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
};
