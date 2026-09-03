import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
    Building2,
    Search,
    Plus,
    Edit3,
    Trash2,
    Globe,
    Facebook,
    MessageSquare,
    Heart,
    Twitter,
    Coffee,
    Loader2,
    CheckCircle2,
    AlertCircle,
    BookOpen,
    Tag,
    ExternalLink,
    GitMerge
} from 'lucide-react';
import {
    workgroupsApi,
    TranslatorsGroupItem,
    WorkgroupMergeResponse
} from '@features/publisher/services/workgroupsApi';
import { WorkgroupModal } from '@features/publisher/components/WorkgroupModal';
import { FansubMergeModal } from '../components/FansubMergeModal';

export const EditorialFansubs: React.FC = () => {
    const navigate = useNavigate();
    const [workgroups, setWorkgroups] = useState<TranslatorsGroupItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedWorkgroup, setSelectedWorkgroup] = useState<TranslatorsGroupItem | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
    const [mergeTargetId, setMergeTargetId] = useState<number | null>(null);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

    const fetchWorkgroups = async () => {
        setLoading(true);
        try {
            const list = await workgroupsApi.getAll();
            setWorkgroups(list || []);
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

    const handleEdit = (wg: TranslatorsGroupItem) => {
        setSelectedWorkgroup(wg);
        setIsModalOpen(true);
    };

    const handleDelete = async (id: number) => {
        try {
            await workgroupsApi.delete(id);
            setStatusMsg({ type: 'success', text: 'Grupo traductor eliminado correctamente' });
            fetchWorkgroups();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al eliminar grupo' });
        }
    };

    const filtered = workgroups.filter((w) => {
        if (!searchQuery.trim()) return true;
        const q = searchQuery.toLowerCase();
        return (
            w.name?.toLowerCase().includes(q) ||
            w.siglas?.toLowerCase().includes(q) ||
            w.description?.toLowerCase().includes(q) ||
            w.links?.web?.toLowerCase().includes(q)
        );
    });

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl sm:text-3xl font-black text-white tracking-tight flex items-center gap-3">
                        <Building2 className="w-7 h-7 text-indigo-400" /> Directorio de Fansubs & Grupos Traductores
                    </h2>
                    <p className="text-xs sm:text-sm text-gray-400 mt-1">
                        Gestión de créditos editoriales, siglas oficiales y enlaces a redes que se inyectan en publicaciones ({filtered.length} grupos).
                    </p>
                </div>

                <div className="flex items-center gap-2.5">
                    <button
                        onClick={() => {
                            setMergeTargetId(null);
                            setIsMergeModalOpen(true);
                        }}
                        className="px-4 py-2.5 rounded-2xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-bold flex items-center gap-2 shadow-lg transition-all active:scale-95"
                    >
                        <GitMerge className="w-4 h-4 text-purple-400" /> Fusionar Grupos
                    </button>
                    <button
                        onClick={handleCreate}
                        className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-xl shadow-indigo-600/30 active:scale-95 transition-all"
                    >
                        <Plus className="w-4 h-4" /> Nuevo Grupo Traductor
                    </button>
                </div>
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
                    placeholder="Buscar por nombre, siglas [TAG], enlaces de contacto..."
                    className="w-full pl-10 pr-4 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
            </div>

            {/* Fansub Cards Grid (2K Widescreen) */}
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
                    {filtered.map((wg) => {
                        const hasLinks = wg.links && Object.values(wg.links).some((v) => Boolean(v));
                        return (
                            <div
                                key={wg.id}
                                className="bg-slate-900/50 border border-white/10 hover:border-indigo-500/40 rounded-3xl p-5 shadow-xl hover:shadow-2xl transition-all flex flex-col justify-between space-y-4 backdrop-blur-xl group"
                            >
                                <div className="space-y-3">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="flex items-center gap-3">
                                            <Link
                                                to={`/app-v2/fansubs/${wg.id}`}
                                                className="w-10 h-10 rounded-2xl bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/20 flex items-center justify-center font-black text-sm shrink-0 transition-all hover:scale-105"
                                                title="Ver detalle y auditoría"
                                            >
                                                {wg.name?.[0]?.toUpperCase() || 'F'}
                                            </Link>
                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <Link
                                                        to={`/app-v2/fansubs/${wg.id}`}
                                                        className="text-xs font-bold text-white hover:text-indigo-300 transition-colors truncate block"
                                                        title="Abrir página de detalle y auditoría"
                                                    >
                                                        {wg.name}
                                                    </Link>
                                                    {wg.siglas && (
                                                        <span className="px-1.5 py-0.5 rounded bg-white/10 text-gray-300 text-[10px] font-mono font-bold shrink-0">
                                                            {wg.siglas}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-[10px] text-gray-500 font-mono mt-0.5">
                                                    ID #{wg.id}
                                                </div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-1">
                                            <button
                                                onClick={() => {
                                                    setMergeTargetId(wg.id);
                                                    setIsMergeModalOpen(true);
                                                }}
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-purple-500/20 text-gray-400 hover:text-purple-300 transition-all"
                                                title="Fusionar duplicados dentro de este grupo"
                                            >
                                                <GitMerge className="w-3.5 h-3.5" />
                                            </button>
                                            <button
                                                onClick={() => handleEdit(wg)}
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-all"
                                                title="Editar Fansub"
                                            >
                                                <Edit3 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    </div>

                                    {wg.description ? (
                                        <p className="text-[11px] text-gray-400 line-clamp-2 leading-relaxed">
                                            {wg.description}
                                        </p>
                                    ) : (
                                        <p className="text-[11px] text-gray-600 italic">
                                            Sin notas registradas
                                        </p>
                                    )}

                                    {/* Links & Socials */}
                                    <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-white/5">
                                        {wg.links?.web && (
                                            <a
                                                href={wg.links.web}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-indigo-400 hover:text-indigo-300 transition-colors"
                                                title={`Web: ${wg.links.web}`}
                                            >
                                                <Globe className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {wg.links?.fb && (
                                            <a
                                                href={wg.links.fb}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-blue-400 hover:text-blue-300 transition-colors"
                                                title={`Facebook: ${wg.links.fb}`}
                                            >
                                                <Facebook className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {wg.links?.discord && (
                                            <a
                                                href={wg.links.discord}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-indigo-400 hover:text-indigo-300 transition-colors"
                                                title={`Discord: ${wg.links.discord}`}
                                            >
                                                <MessageSquare className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {wg.links?.patreon && (
                                            <a
                                                href={wg.links.patreon}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-pink-400 hover:text-pink-300 transition-colors"
                                                title={`Patreon: ${wg.links.patreon}`}
                                            >
                                                <Heart className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {wg.links?.twitter && (
                                            <a
                                                href={wg.links.twitter}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-sky-400 hover:text-sky-300 transition-colors"
                                                title={`Twitter/X: ${wg.links.twitter}`}
                                            >
                                                <Twitter className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {wg.links?.donations && (
                                            <a
                                                href={wg.links.donations}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-amber-400 hover:text-amber-300 transition-colors"
                                                title={`Donaciones / Ko-fi: ${wg.links.donations}`}
                                            >
                                                <Coffee className="w-3.5 h-3.5" />
                                            </a>
                                        )}
                                        {!hasLinks && (
                                            <span className="text-[10px] text-gray-600 italic">Sin enlaces registrados</span>
                                        )}
                                    </div>
                                </div>

                                {/* Footer: Books Count and Audit Link */}
                                <div className="pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-400 font-mono">
                                    <div className="flex items-center gap-1.5">
                                        <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                                        <span>{wg.books_count || 0} libros</span>
                                    </div>
                                    <Link
                                        to={`/app-v2/fansubs/${wg.id}`}
                                        className="text-[11px] text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-1 transition-colors"
                                    >
                                        <span>Auditoría</span>
                                        <ExternalLink className="w-3 h-3" />
                                    </Link>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Modals */}
            <WorkgroupModal
                isOpen={isModalOpen}
                group={selectedWorkgroup}
                onClose={() => setIsModalOpen(false)}
                onSave={async (data) => {
                    await workgroupsApi.save(data);
                    setIsModalOpen(false);
                    fetchWorkgroups();
                    setStatusMsg({ type: 'success', text: 'Grupo traductor guardado con éxito' });
                }}
                onDelete={handleDelete}
            />

            <FansubMergeModal
                isOpen={isMergeModalOpen}
                onClose={() => setIsMergeModalOpen(false)}
                workgroups={workgroups}
                initialTargetId={mergeTargetId}
                onMergeSuccess={(res) => {
                    fetchWorkgroups();
                    setStatusMsg({
                        type: 'success',
                        text: res.message || `Fusión completada con éxito.`
                    });
                }}
            />
        </div>
    );
};
