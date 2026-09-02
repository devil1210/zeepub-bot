import React, { useState, useEffect } from 'react';
import {
    Building2,
    Search,
    Plus,
    Edit3,
    Trash2,
    Globe,
    Send as TelegramIcon,
    Heart,
    Loader2,
    CheckCircle2,
    AlertCircle,
    ExternalLink,
    Users,
    Sparkles
} from 'lucide-react';
import { api } from '@shared/services/api';
import { WorkgroupModal } from '@features/publisher/components/WorkgroupModal';

export const EditorialFansubs: React.FC = () => {
    const [workgroups, setWorkgroups] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedWorkgroup, setSelectedWorkgroup] = useState<any | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const fetchWorkgroups = async () => {
        setLoading(true);
        try {
            const res = await api.getWorkgroups();
            setWorkgroups(res?.workgroups || res?.items || res || []);
        } catch (err: any) {
            console.error('Error cargando fansubs:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchWorkgroups();
    }, []);

    const handleCreate = () => {
        setSelectedWorkgroup(null);
        setIsModalOpen(true);
    };

    const handleEdit = (wg: any) => {
        setSelectedWorkgroup(wg);
        setIsModalOpen(true);
    };

    const handleDelete = async (id: number, name: string) => {
        if (!confirm(`¿Eliminar el fansub "${name}"?`)) return;
        try {
            await api.deleteWorkgroup(id);
            setStatusMsg({ type: 'success', text: `Fansub "${name}" eliminado correctamente` });
            fetchWorkgroups();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al eliminar fansub' });
        }
    };

    const filtered = (Array.isArray(workgroups) ? workgroups : []).filter((w) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return (
            w.name?.toLowerCase().includes(q) ||
            w.website?.toLowerCase().includes(q) ||
            w.telegram_channel?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Building2 className="w-7 h-7 text-indigo-400" /> Directorio de Fansubs & Grupos de Traducción
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Administración de créditos editoriales, enlaces oficiales y canales de los grupos traductores ({filtered.length} grupos).
                    </p>
                </div>

                <button
                    onClick={handleCreate}
                    className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-xl shadow-indigo-600/30 active:scale-95 transition-all"
                >
                    <Plus className="w-4 h-4" /> Registrar Nuevo Fansub
                </button>
            </div>

            {statusMsg && (
                <div
                    className={`p-3.5 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {statusMsg.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{statusMsg.text}</span>
                </div>
            )}

            {/* Search */}
            <div className="relative">
                <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Buscar fansub por nombre, sitio web o canal de Telegram..."
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
            </div>

            {/* Widescreen Fansubs Cards Grid */}
            {loading ? (
                <div className="py-24 flex items-center justify-center">
                    <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
                </div>
            ) : filtered.length === 0 ? (
                <div className="py-24 text-center text-gray-500 text-xs bg-slate-900/30 rounded-3xl border border-white/5">
                    No se encontraron grupos de traducción registrados.
                </div>
            ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4 gap-5">
                    {filtered.map((wg) => (
                        <div
                            key={wg.id}
                            className="bg-slate-900/50 border border-white/10 hover:border-indigo-500/40 rounded-3xl p-5 shadow-xl hover:shadow-2xl transition-all flex flex-col justify-between space-y-4 backdrop-blur-xl group"
                        >
                            <div className="space-y-3">
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-black text-sm shrink-0">
                                            {wg.name?.[0]?.toUpperCase() || 'F'}
                                        </div>
                                        <div>
                                            <h3 className="text-sm font-bold text-white group-hover:text-indigo-300 transition-colors">
                                                {wg.name}
                                            </h3>
                                            <span className="text-[10px] text-gray-400 font-mono">
                                                ID #{wg.id}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-1">
                                        <button
                                            onClick={() => handleEdit(wg)}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-all"
                                            title="Editar Fansub"
                                        >
                                            <Edit3 className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(wg.id, wg.name)}
                                            className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all"
                                            title="Eliminar Fansub"
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>

                                {wg.description && (
                                    <p className="text-xs text-gray-400 line-clamp-2 italic leading-relaxed">
                                        {wg.description}
                                    </p>
                                )}

                                {/* Links and Channels */}
                                <div className="space-y-1.5 pt-2 border-t border-white/5 text-xs">
                                    {wg.website && (
                                        <a
                                            href={wg.website}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 text-indigo-400 hover:underline truncate"
                                        >
                                            <Globe className="w-3.5 h-3.5 shrink-0" />
                                            <span className="truncate">{wg.website}</span>
                                        </a>
                                    )}

                                    {wg.telegram_channel && (
                                        <div className="flex items-center gap-2 text-cyan-400 truncate">
                                            <TelegramIcon className="w-3.5 h-3.5 shrink-0" />
                                            <span className="truncate">{wg.telegram_channel}</span>
                                        </div>
                                    )}

                                    {wg.donation_url && (
                                        <a
                                            href={wg.donation_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 text-pink-400 hover:underline truncate"
                                        >
                                            <Heart className="w-3.5 h-3.5 shrink-0" />
                                            <span className="truncate">Apoyar con donación</span>
                                        </a>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Modal */}
            <WorkgroupModal
                isOpen={isModalOpen}
                workgroup={selectedWorkgroup}
                onClose={() => setIsModalOpen(false)}
                onSave={async (data) => {
                    await api.saveWorkgroup(data);
                    setIsModalOpen(false);
                    fetchWorkgroups();
                    setStatusMsg({ type: 'success', text: 'Fansub guardado correctamente' });
                }}
            />
        </div>
    );
};
