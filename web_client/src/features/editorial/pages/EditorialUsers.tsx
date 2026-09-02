import React, { useState, useEffect } from 'react';
import { Users, Search, Shield, ShieldCheck, ShieldAlert, Loader2, Save, CheckCircle2, AlertCircle } from 'lucide-react';
import { api } from '@shared/services/api';

export const EditorialUsers: React.FC = () => {
    const [users, setUsers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [tiers, setTiers] = useState<any[]>([]);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const res = await api.getAdminUsers(50, 0, searchQuery);
            setUsers(res?.users || []);
            const tiersRes = await api.getAdminTiers();
            setTiers(tiersRes?.tiers || []);
        } catch (err) {
            console.error('Error cargando usuarios:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleRoleChange = async (userId: string, levelId: number) => {
        try {
            await api.setAdminUserLevel(userId, levelId);
            setStatusMsg({ type: 'success', text: 'Nivel y permisos del usuario actualizados' });
            fetchUsers();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al actualizar usuario' });
        }
    };

    return (
        <div className="w-full max-w-[2100px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-black text-white tracking-tight flex items-center gap-2">
                        <Users className="w-6 h-6 text-indigo-400" /> Gestión de Usuarios y Permisos
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">
                        Control de roles editoriales, administradores y límites de descarga.
                    </p>
                </div>
            </div>

            {statusMsg && (
                <div
                    className={`p-3 rounded-xl flex items-center gap-2 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? <CheckCircle2 className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Table */}
            <div className="bg-slate-900/40 border border-white/10 rounded-2xl overflow-hidden shadow-2xl backdrop-blur-xl">
                {loading ? (
                    <div className="py-24 flex items-center justify-center">
                        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border-collapse">
                            <thead>
                                <tr className="border-b border-white/10 bg-slate-950/60 text-gray-400 font-bold uppercase tracking-wider text-[10px]">
                                    <th className="p-4">Usuario</th>
                                    <th className="p-4">Telegram ID</th>
                                    <th className="p-4">Nivel / Rol</th>
                                    <th className="p-4">Última Actividad</th>
                                    <th className="p-4 text-right">Asignar Nivel</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-white/5">
                                {users.map((u) => (
                                    <tr key={u.id} className="hover:bg-white/[0.02] transition-colors">
                                        <td className="p-4">
                                            <div className="font-bold text-white">
                                                {u.first_name || u.nickname || 'Usuario'} {u.last_name || ''}
                                            </div>
                                            <div className="text-[11px] text-gray-400">
                                                {u.username ? `@${u.username}` : 'Sin username'}
                                            </div>
                                        </td>
                                        <td className="p-4 font-mono text-gray-400">
                                            {u.telegram_id || u.id}
                                        </td>
                                        <td className="p-4">
                                            <span className="px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                                                {u.tier_name || u.level_name || 'Standard'}
                                            </span>
                                        </td>
                                        <td className="p-4 text-gray-400 text-[11px]">
                                            {u.last_activity ? new Date(u.last_activity).toLocaleDateString() : 'N/A'}
                                        </td>
                                        <td className="p-4 text-right">
                                            <select
                                                value={u.level_id || 1}
                                                onChange={(e) => handleRoleChange(u.id || u.telegram_id, Number(e.target.value))}
                                                className="px-3 py-1.5 rounded-lg bg-slate-950 border border-white/10 text-xs font-bold text-white focus:outline-none focus:border-indigo-500"
                                            >
                                                {tiers.map((t) => (
                                                    <option key={t.id} value={t.id}>
                                                        {t.name} (Nivel {t.id})
                                                    </option>
                                                ))}
                                            </select>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};
