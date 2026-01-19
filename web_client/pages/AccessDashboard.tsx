import React, { useState, useEffect, useRef } from 'react';
import {
    ShieldCheck,
    Star,
    TrendingUp,
    Search,
    Users,
    ArrowLeft,
    CheckCircle,
    RotateCcw,
    Save,
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

export const AccessDashboard: React.FC = () => {
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

    if (selectedUserId) {
        return <UserPermissions userId={selectedUserId} onBack={() => { setSelectedUserId(null); fetchData(); }} />;
    }

    if (configuringTier) {
        return <TierConfiguration tierName={configuringTier.name} onBack={() => { setConfiguringTier(null); fetchData(); }} />;
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
                    const isPopular = level.name.toLowerCase() === 'vip';

                    return (
                        <div
                            key={level.id}
                            className="glass-panel p-6 rounded-3xl border border-white/5 bg-white/5 relative overflow-hidden group hover:border-primary/30 transition-all flex flex-col justify-between"
                        >
                            <div className="relative z-10">
                                <div className="flex justify-between items-start mb-6">
                                    <div>
                                        <span className="text-[10px] font-black uppercase tracking-widest text-gray-500 mb-1 block">
                                            {isDefault ? 'Nivel por Defecto' : 'Nivel de Usuario'}
                                        </span>
                                        <h3 className="text-2xl font-black text-white">{level.name}</h3>
                                    </div>
                                    <div className={`p-2.5 rounded-xl border border-white/10`} style={{ backgroundColor: `${level.color}20`, color: level.color }}>
                                        <ShieldCheck className="w-5 h-5" />
                                    </div>
                                </div>

                                <div className="space-y-4 mb-8">
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <CheckCircle className="w-4 h-4 text-primary" />
                                        <span>{level.dailyDownloads} Descargas diarias</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <CheckCircle className={`w-4 h-4 ${level.earlyAccess ? 'text-primary' : 'text-gray-600'}`} />
                                        <span className={level.earlyAccess ? 'text-gray-200' : 'text-gray-600'}>Acceso Anticipado</span>
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-400">
                                        <CheckCircle className={`w-4 h-4 ${level.customThemes ? 'text-primary' : 'text-gray-600'}`} />
                                        <span className={level.customThemes ? 'text-gray-200' : 'text-gray-600'}>Temas Personalizados</span>
                                    </div>
                                </div>
                            </div>

                            <button
                                onClick={() => setConfiguringTier({ name: level.name, color: level.color })}
                                className="w-full py-3 rounded-2xl bg-white/5 hover:bg-white/10 text-white text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all active:scale-95"
                            >
                                Configurar Nivel
                            </button>
                        </div>
                    );
                })}
            </div>

            {/* Users List Table */}
            <div className="glass-panel border border-white/5 bg-white/5 rounded-3xl p-8">
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
                            className="pl-10 pr-4 py-2 bg-black/20 border border-white/10 rounded-2xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-primary w-full sm:w-80"
                        />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-gray-500 font-black uppercase tracking-wider">
                                <th className="pb-4 px-2">Usuario</th>
                                <th className="pb-4 px-2">Nivel</th>
                                <th className="pb-4 px-2">Uso Diario</th>
                                <th className="pb-4 px-2">Total Descargas</th>
                                <th className="pb-4 px-2 text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {users.map((user) => (
                                <tr key={user.id} className="group hover:bg-white/[0.01] transition-colors">
                                    <td className="py-4 px-2">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold border border-primary/20">
                                                {user.username.charAt(0).toUpperCase()}
                                            </div>
                                            <div>
                                                <p className="font-bold text-gray-200">@{user.username}</p>
                                                <p className="text-[10px] text-gray-500">ID: {user.id}</p>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-4 px-2">
                                        <span
                                            className="px-2 py-0.5 rounded text-[9px] font-black uppercase border"
                                            style={{ backgroundColor: `${user.level.color}10`, color: user.level.color, borderColor: `${user.level.color}20` }}
                                        >
                                            {user.level.name}
                                        </span>
                                    </td>
                                    <td className="py-4 px-2">
                                        <div className="flex flex-col gap-1">
                                            <div className="flex justify-between text-[9px] font-bold">
                                                <span className="text-gray-500">{user.downloads.used} / {user.downloads.limit}</span>
                                            </div>
                                            <div className="w-24 h-1 bg-white/5 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-primary"
                                                    style={{ width: `${(user.downloads.used / user.downloads.limit) * 100}%` }}
                                                ></div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="py-4 px-2 font-mono text-gray-400">{user.downloads.total}</td>
                                    <td className="py-4 px-2 text-right">
                                        <button
                                            onClick={() => setSelectedUserId(user.id)}
                                            className="px-3 py-1.5 bg-white/5 hover:bg-primary hover:text-white rounded-lg text-[9px] font-black uppercase tracking-widest transition-all border border-white/5"
                                        >
                                            Editar Perfil
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
