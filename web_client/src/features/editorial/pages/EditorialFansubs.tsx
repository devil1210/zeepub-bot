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
    GitMerge,
    AlertTriangle
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
    const [bookFilter, setBookFilter] = useState<'with_books' | 'with_issues' | 'without_books' | 'all'>('with_books');
    const [selectedWorkgroup, setSelectedWorkgroup] = useState<TranslatorsGroupItem | null>(null);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
    const [isPurgeModalOpen, setIsPurgeModalOpen] = useState(false);
    const [purging, setPurging] = useState(false);
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

    const handlePurgeEmpty = async () => {
        setPurging(true);
        try {
            const res = await workgroupsApi.purgeEmpty();
            setIsPurgeModalOpen(false);
            setStatusMsg({
                type: 'success',
                text: res.message || `Se purgaron ${res.deleted_count} grupos vacíos.`
            });
            await fetchWorkgroups();
        } catch (err: any) {
            setStatusMsg({ type: 'error', text: err.message || 'Error al purgar grupos vacíos' });
        } finally {
            setPurging(false);
        }
    };

    const countWithBooks = workgroups.filter((w) => (w.books_count || 0) > 0).length;
    const countWithIssues = workgroups.filter((w) => (w.bad_metadata_count || 0) > 0).length;
    const countWithoutBooks = workgroups.filter((w) => (w.books_count || 0) === 0).length;

    const filtered = workgroups.filter((w) => {
        if (bookFilter === 'with_books' && (w.books_count || 0) === 0) return false;
        if (bookFilter === 'with_issues' && (w.bad_metadata_count || 0) === 0) return false;
        if (bookFilter === 'without_books' && (w.books_count || 0) > 0) return false;

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
                        Gestión de créditos editoriales, siglas oficiales y enlaces a redes que se inyectan en publicaciones ({filtered.length} visibles de {workgroups.length} registrados).
                    </p>
                </div>

                <div className="flex flex-wrap items-center gap-2.5">
                    {countWithoutBooks > 0 && (
                        <button
                            onClick={() => setIsPurgeModalOpen(true)}
                            className="px-3.5 py-2.5 rounded-2xl bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 text-xs font-bold flex items-center gap-2 shadow-lg transition-all active:scale-95"
                            title={`Eliminar permanentemente ${countWithoutBooks} grupos con 0 libros`}
                        >
                            <Trash2 className="w-4 h-4 text-rose-400" /> Purgar Vacíos ({countWithoutBooks})
                        </button>
                    )}
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

            {/* Search & Filter Tabs */}
            <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                <div className="relative flex-1">
                    <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2 pointer-events-none" />
                    <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Buscar por nombre, siglas [TAG], enlaces de contacto..."
                        className="w-full pl-10 pr-8 py-2.5 bg-slate-900/60 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                    />
                    {searchQuery && (
                        <button
                            type="button"
                            onClick={() => setSearchQuery('')}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white text-xs p-1"
                            title="Limpiar búsqueda"
                        >
                            ✕
                        </button>
                    )}
                </div>

                {/* Filter Tabs */}
                <div className="flex items-center p-1 bg-slate-900/80 border border-white/10 rounded-2xl shrink-0 self-start sm:self-auto backdrop-blur-md">
                    <button
                        type="button"
                        onClick={() => setBookFilter('with_books')}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            bookFilter === 'with_books'
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                    >
                        <span>Con Libros</span>
                        <span
                            className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                bookFilter === 'with_books'
                                    ? 'bg-indigo-900/80 text-indigo-200'
                                    : 'bg-white/10 text-gray-400'
                            }`}
                        >
                            {countWithBooks}
                        </span>
                    </button>

                    <button
                        type="button"
                        onClick={() => setBookFilter('with_issues')}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            bookFilter === 'with_issues'
                                ? 'bg-amber-600 text-white shadow-md shadow-amber-600/30'
                                : countWithIssues > 0
                                ? 'text-amber-400 hover:text-amber-200 hover:bg-amber-500/10'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                        title="Ver fansubs con volúmenes que presentan observaciones o discrepancias en el OPF"
                    >
                        <AlertTriangle className={`w-3.5 h-3.5 ${bookFilter === 'with_issues' ? 'text-white' : 'text-amber-400'}`} />
                        <span>Con Obs. OPF</span>
                        <span
                            className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                bookFilter === 'with_issues'
                                    ? 'bg-amber-900/80 text-amber-200'
                                    : countWithIssues > 0
                                    ? 'bg-amber-500/20 text-amber-300'
                                    : 'bg-white/10 text-gray-400'
                            }`}
                        >
                            {countWithIssues}
                        </span>
                    </button>

                    <button
                        type="button"
                        onClick={() => setBookFilter('without_books')}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            bookFilter === 'without_books'
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                    >
                        <span>Sin Libros</span>
                        <span
                            className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                bookFilter === 'without_books'
                                    ? 'bg-indigo-900/80 text-indigo-200'
                                    : 'bg-white/10 text-gray-400'
                            }`}
                        >
                            {countWithoutBooks}
                        </span>
                    </button>

                    <button
                        type="button"
                        onClick={() => setBookFilter('all')}
                        className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                            bookFilter === 'all'
                                ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/30'
                                : 'text-gray-400 hover:text-white hover:bg-white/5'
                        }`}
                    >
                        <span>Todos</span>
                        <span
                            className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono font-bold ${
                                bookFilter === 'all'
                                    ? 'bg-indigo-900/80 text-indigo-200'
                                    : 'bg-white/10 text-gray-400'
                            }`}
                        >
                            {workgroups.length}
                        </span>
                    </button>
                </div>
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
                        const hasIssues = (wg.bad_metadata_count || 0) > 0;
                        return (
                            <div
                                key={wg.id}
                                className={`border rounded-3xl p-5 shadow-xl hover:shadow-2xl transition-all flex flex-col justify-between space-y-4 backdrop-blur-xl group ${
                                    hasIssues
                                        ? 'bg-slate-900/60 border-amber-500/30 hover:border-amber-400/50 shadow-amber-950/10'
                                        : 'bg-slate-900/50 border-white/10 hover:border-indigo-500/40'
                                }`}
                            >
                                <div className="space-y-3">
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="flex items-center gap-3">
                                            <Link
                                                to={`/app-v2/fansubs/${wg.id}`}
                                                className={`w-10 h-10 rounded-2xl border flex items-center justify-center font-black text-sm shrink-0 transition-all hover:scale-105 ${
                                                    hasIssues
                                                        ? 'bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border-amber-500/30'
                                                        : 'bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border-indigo-500/20'
                                                }`}
                                                title="Ver detalle y auditoría"
                                            >
                                                {wg.name?.[0]?.toUpperCase() || 'F'}
                                            </Link>
                                            <div className="min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <Link
                                                        to={`/app-v2/fansubs/${wg.id}`}
                                                        className={`text-xs font-bold transition-colors truncate block ${
                                                            hasIssues ? 'text-white hover:text-amber-300' : 'text-white hover:text-indigo-300'
                                                        }`}
                                                        title="Abrir página de detalle y auditoría"
                                                    >
                                                        {wg.name}
                                                    </Link>
                                                    {wg.siglas && (
                                                        <span className="px-1.5 py-0.5 rounded bg-white/10 text-gray-300 text-[10px] font-mono font-bold shrink-0">
                                                            {wg.siglas}
                                                        </span>
                                                    )}
                                                    {hasIssues && (
                                                        <span
                                                            className="px-1.5 py-0.5 rounded bg-amber-500/20 border border-amber-500/40 text-amber-300 text-[10px] font-bold flex items-center gap-1 shrink-0"
                                                            title={`${wg.bad_metadata_count} volumen(es) con observaciones en el metadato dc:publisher del OPF`}
                                                        >
                                                            <AlertTriangle className="w-2.5 h-2.5 text-amber-400 shrink-0" />
                                                            <span>{wg.bad_metadata_count} con obs.</span>
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
                                <div className="pt-2.5 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
                                    <div className="flex items-center gap-2">
                                        <div className="flex items-center gap-1.5 text-gray-400">
                                            <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                                            <span>{wg.books_count || 0} libros</span>
                                        </div>
                                        {hasIssues && (
                                            <span
                                                className="px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[10px] font-bold flex items-center gap-1"
                                                title={`${wg.bad_metadata_count} volumen(es) con observaciones en el metadato dc:publisher`}
                                            >
                                                <AlertTriangle className="w-2.5 h-2.5 text-amber-400" />
                                                <span>{wg.bad_metadata_count} obs.</span>
                                            </span>
                                        )}
                                    </div>
                                    <Link
                                        to={`/app-v2/fansubs/${wg.id}`}
                                        className={`text-[11px] font-bold flex items-center gap-1 transition-colors ${
                                            hasIssues
                                                ? 'text-amber-400 hover:text-amber-300'
                                                : 'text-indigo-400 hover:text-indigo-300'
                                        }`}
                                        title="Abrir auditoría de volúmenes"
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

            {/* Modal de confirmación para Purgar Vacíos */}
            {isPurgeModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="bg-slate-900 border border-rose-500/30 rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4 backdrop-blur-xl">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-2xl bg-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
                                <Trash2 className="w-5 h-5" />
                            </div>
                            <div>
                                <h3 className="text-base font-bold text-white">Purgar Grupos Vacíos</h3>
                                <p className="text-xs text-gray-400">Eliminación permanente de registros sin libros</p>
                            </div>
                        </div>

                        <p className="text-xs text-gray-300 leading-relaxed">
                            Se eliminarán permanentemente <strong className="text-rose-400">{countWithoutBooks} grupos traductores</strong> que tienen <strong className="text-rose-400">0 libros</strong> vinculados en el sistema.
                        </p>

                        <div className="p-3 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-[11px] text-rose-300 flex items-start gap-2">
                            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                            <span>Esta acción no se puede deshacer. Los grupos con 1 o más libros no se verán afectados.</span>
                        </div>

                        <div className="flex items-center justify-end gap-3 pt-2">
                            <button
                                type="button"
                                disabled={purging}
                                onClick={() => setIsPurgeModalOpen(false)}
                                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-bold transition-colors"
                            >
                                Cancelar
                            </button>
                            <button
                                type="button"
                                disabled={purging}
                                onClick={handlePurgeEmpty}
                                className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all shadow-lg shadow-rose-600/30 flex items-center gap-2"
                            >
                                {purging ? (
                                    <>
                                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                        <span>Purgando...</span>
                                    </>
                                ) : (
                                    <>
                                        <Trash2 className="w-3.5 h-3.5" />
                                        <span>Confirmar Purga</span>
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
