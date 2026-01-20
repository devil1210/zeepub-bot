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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {levels.sort((a, b) => a.priority - b.priority).map((level) => {
                    const isDefault = level.id === '1' || level.name.toLowerCase() === 'gratis' || level.name.toLowerCase() === 'gratuito';

                    return (
                        <div
                            key={level.id}
                            className="glass-panel p-6 rounded-3xl border border-white/5 relative overflow-hidden group hover:border-primary/30 transition-all flex flex-col justify-between"
                        >
                            <div className="relative z-10">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 mb-1 block">
                                            {isDefault ? 'Nivel por Defecto' : 'Nivel de Usuario'}
                                        </span>
                                        <h3 className="text-2xl font-black text-white">{level.name}</h3>
                                    </div>
                                    <div className={`p-2.5 rounded-xl border border-white/10 shadow-lg shadow-black/20`} style={{ backgroundColor: `${level.color}20`, color: level.color }}>
                                        <ShieldCheck className="w-5 h-5" />
                                    </div>
                                </div>

                                <div className="space-y-4 mb-8">
                                    <div className="flex items-center gap-2 text-xs text-gray-400 font-medium">
                                        <CheckCircle className="w-4 h-4 text-primary" />
                                        <span>{level.dailyDownloads} Descargas diarias</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-400 font-medium">
                                        <CheckCircle className={`w-4 h-4 ${level.earlyAccess ? 'text-primary' : 'text-gray-700'}`} />
                                        <span className={level.earlyAccess ? 'text-gray-200' : 'text-gray-700'}>Acceso Anticipado</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-400 font-medium">
                                        <CheckCircle className={`w-4 h-4 ${level.customThemes ? 'text-primary' : 'text-gray-700'}`} />
                                        <span className={level.customThemes ? 'text-gray-200' : 'text-gray-700'}>Temas Personalizados</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => handleConfigureTier({ name: level.name, color: level.color })}
                                className="w-full py-3 rounded-2xl bg-white/[0.03] hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all active:scale-95"
                            >
                                Configurar Nivel
                            </button>
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
                                className="group bg-white/[0.02] hover:bg-white/[0.05] border border-white/5 hover:border-primary/20 rounded-3xl p-5 transition-all flex flex-col lg:flex-row lg:items-center gap-5 cursor-pointer"
                            >
                                {/* User Info Block */}
                                <div className="flex items-center gap-4 lg:min-w-[240px]">
                                    <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center text-primary font-black text-lg border border-primary/10 shadow-inner group-hover:scale-105 transition-transform">
                                        {user.username?.charAt(0).toUpperCase() || '?'}
                                    </div>
                                    <div className="min-w-0">
                                        <p className="font-black text-white truncate text-base">@{user.username || 'unknown'}</p>
                                        <p className="text-[10px] text-gray-500 font-mono">ID: {user.id}</p>
                                    </div>
                                </div>

                                {/* Level Badge */}
                                <div className="lg:w-32">
                                    <span
                                        className="px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-wider border inline-block"
                                        style={{ backgroundColor: `${user.level.color}10`, color: user.level.color, borderColor: `${user.level.color}20` }}
                                    >
                                        {user.level.name}
                                    </span>
                                </div>

                                {/* Progress Block */}
                                <div className="flex-1 flex flex-col gap-2">
                                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-tighter">
                                        <span className="text-gray-500">Cuota Diaria</span>
                                        <span className="text-primary">{user.downloads.used} / {user.downloads.limit === -1 ? '∞' : user.downloads.limit}</span>
                                    </div>
                                    <div className="w-full h-2 bg-black/40 rounded-full overflow-hidden border border-white/5">
                                        <div
                                            className="h-full bg-primary shadow-[0_0_10px_rgba(var(--primary-rgb),0.5)] transition-all duration-500"
                                            style={{ width: user.downloads.limit === -1 ? '20%' : `${Math.min(100, (user.downloads.used / user.downloads.limit) * 100)}%` }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Stats & Action */}
                                <div className="flex items-center justify-between lg:justify-end gap-8 lg:min-w-[150px]">
                                    <div className="text-right">
                                        <p className="text-[9px] text-gray-500 font-black uppercase">Total</p>
                                        <p className="text-sm font-black text-gray-300 tabular-nums">{user.downloads.total}</p>
                                    </div>
                                    <div className="p-3 bg-white/5 rounded-2xl text-gray-500 group-hover:text-primary group-hover:bg-primary/10 transition-all">
                                        <ChevronRight className="w-5 h-5" />
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};
