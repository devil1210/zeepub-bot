import React, { useState, useEffect } from 'react';
import {
    ShieldCheck,
    Search,
    Users,
    CheckCircle,
    ChevronRight,
    Loader2
} from 'lucide-react';
import { UserPermissions } from './UserPermissions';
import { TierConfiguration } from './TierConfiguration';
import { api } from '../src/services/api';
import { useTheme } from '../contexts/ThemeContext';

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
    role: string;
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

    const fetchData = async () => {
        try {
            setLoading(true);
            const [levelsData, usersData] = await Promise.all([
                api.getAdminTiers(),
                api.getAdminUsers(20, 0, searchQuery)
            ]);
            setLevels(levelsData.levels as UserLevel[] || []);
            setUsers(usersData.users as AdminUser[] || []);
        } catch (error) {
            console.error("Error fetching access data:", error);
        } finally {
            setLoading(false);
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
        <div className="flex flex-col gap-10 animate-in fade-in duration-500">
            {/* Page Heading */}
            <div className="flex flex-col gap-4">
                <h1 className="text-4xl font-black text-white leading-tight tracking-tighter uppercase">Niveles y Acceso</h1>
                <p className="text-gray-400 text-sm font-medium leading-relaxed max-w-2xl">
                    Configura permisos globales y niveles de suscripción para toda la base de usuarios.
                </p>
            </div>

            {/* Tier Cards Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {levels.sort((a, b) => a.priority - b.priority).map((level) => {
                    const isDefault = level.id === '1' || level.name.toLowerCase() === 'gratis' || level.name.toLowerCase() === 'gratuito';

                    return (
                        <div
                            key={level.id}
                            className="glass-panel p-8 rounded-[2rem] relative overflow-hidden group hover:scale-[1.02] transition-all duration-500 border border-white/5 shadow-2xl flex flex-col justify-between"
                        >
                            <div className="relative z-10">
                                <div className="flex justify-between items-start mb-8">
                                    <div>
                                        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 mb-2 block">
                                            {isDefault ? 'Nivel por Defecto' : 'Nivel de Usuario'}
                                        </span>
                                        <h3 className="text-3xl font-black text-white tracking-tight">{level.name}</h3>
                                    </div>
                                    <div
                                        className="p-4 rounded-2xl border shadow-lg transition-transform duration-500 group-hover:scale-110"
                                        style={{
                                            backgroundColor: `${level.color}20`,
                                            color: level.color,
                                            borderColor: `${level.color}30`
                                        }}
                                    >
                                        <ShieldCheck className="w-6 h-6" />
                                    </div>
                                </div>

                                <div className="space-y-4 mb-10">
                                    <div className="flex items-center gap-3 text-[11px] text-gray-400 font-bold uppercase tracking-wider">
                                        <CheckCircle className="w-4 h-4 text-primary" strokeWidth={3} />
                                        <span>{level.dailyDownloads === -1 ? 'Descargas Ilimitadas' : `${level.dailyDownloads} Descargas diarias`}</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-[11px] text-gray-400 font-bold uppercase tracking-wider">
                                        <CheckCircle className={`w-4 h-4 ${level.earlyAccess ? 'text-primary' : 'text-gray-800'}`} strokeWidth={3} />
                                        <span className={level.earlyAccess ? 'text-gray-200' : 'text-gray-600'}>Acceso Anticipado</span>
                                    </div>
                                    <div className="flex items-center gap-3 text-[11px] text-gray-400 font-bold uppercase tracking-wider">
                                        <CheckCircle className={`w-4 h-4 ${level.customThemes ? 'text-primary' : 'text-gray-800'}`} strokeWidth={3} />
                                        <span className={level.customThemes ? 'text-gray-200' : 'text-gray-600'}>Temas Personalizados</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => handleConfigureTier({ name: level.name, color: level.color })}
                                className="w-full py-4 rounded-2xl bg-white/[0.03] hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-[0.2em] border border-white/5 transition-all active:scale-95 shadow-lg relative z-10"
                            >
                                Configurar Nivel
                            </button>

                            {/* Background Glow */}
                            <div
                                className="absolute -right-8 -bottom-8 w-32 h-32 rounded-full blur-[60px] group-hover:scale-150 transition-all duration-700 pointer-events-none"
                                style={{
                                    backgroundColor: `${level.color}15`,
                                    opacity: settings.cardGlowIntensity
                                }}
                            ></div>
                        </div>
                    );
                })}
            </div>

            {/* Users List - Dynamic Grid (Square Cards on Mobile) */}
            <div className="glass-panel border border-white/5 rounded-3xl p-6 sm:p-8">
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
                            className="pl-10 pr-4 py-2.5 bg-black/20 border border-white/10 rounded-2xl text-xs text-white focus:outline-none focus:ring-1 focus:ring-primary/50 w-full sm:w-80"
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
                                className="group bg-white/[0.01] hover:bg-white/[0.04] border border-white/5 hover:border-primary/20 rounded-3xl p-5 transition-all duration-300 flex flex-col lg:flex-row lg:items-center gap-6 cursor-pointer relative overflow-hidden"
                            >
                                {/* User Info Block */}
                                <div className="flex items-center gap-5 lg:min-w-[260px] relative z-10">
                                    <div className="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center text-primary font-black text-xl border border-primary/10 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                        {user.username?.charAt(0).toUpperCase() || '?'}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-black text-white truncate text-base tracking-tight group-hover:text-primary transition-colors">@{user.username || 'unknown'}</p>
                                        <p className="text-[10px] text-gray-600 font-mono tracking-tighter mt-1">ID: {user.id}</p>
                                    </div>
                                </div>

                                {/* Level Badge */}
                                <div className="lg:w-36 relative z-10">
                                    <span
                                        className="px-4 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest border inline-block shadow-lg"
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
        </div>
    );
};
