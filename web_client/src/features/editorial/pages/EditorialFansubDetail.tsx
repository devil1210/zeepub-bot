import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
    Building2,
    ArrowLeft,
    GitMerge,
    Search,
    BookOpen,
    AlertTriangle,
    CheckCircle2,
    Copy,
    Check,
    Edit3,
    Globe,
    Facebook,
    MessageSquare,
    Heart,
    Twitter,
    Coffee,
    ExternalLink,
    Loader2,
    FileText,
    FolderOpen,
    Save,
    RefreshCw,
    X,
    Filter
} from 'lucide-react';
import {
    workgroupsApi,
    TranslatorsGroupItem,
    AttachedBookItem,
    WorkgroupMergeResponse
} from '@features/publisher/services/workgroupsApi';
import { FansubMergeModal } from '../components/FansubMergeModal';

export const EditorialFansubDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [group, setGroup] = useState<TranslatorsGroupItem | null>(null);
    const [books, setBooks] = useState<AttachedBookItem[]>([]);
    const [allWorkgroups, setAllWorkgroups] = useState<TranslatorsGroupItem[]>([]);

    // Navigation Tabs & Filters
    const [activeTab, setActiveTab] = useState<'audit' | 'edit'>('audit');
    const [filterMode, setFilterMode] = useState<'all' | 'bad' | 'good'>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [copiedPathId, setCopiedPathId] = useState<string | null>(null);

    // Merge Modal State
    const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);

    // Edit Form State
    const [name, setName] = useState('');
    const [siglas, setSiglas] = useState('');
    const [description, setDescription] = useState('');
    const [links, setLinks] = useState({
        web: '',
        fb: '',
        discord: '',
        patreon: '',
        twitter: '',
        donations: '',
    });
    const [isSaving, setIsSaving] = useState(false);
    const [statusMsg, setStatusMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const [isSyncingBooks, setIsSyncingBooks] = useState(false);
    const [syncingBookId, setSyncingBookId] = useState<string | null>(null);

    const loadData = async () => {
        if (!id) return;
        try {
            setLoading(true);
            const [detailRes, listRes] = await Promise.all([
                workgroupsApi.getDetail(Number(id)),
                workgroupsApi.getAll()
            ]);

            if (detailRes && detailRes.group) {
                setGroup(detailRes.group);
                setName(detailRes.group.name || '');
                setSiglas(detailRes.group.siglas || '');
                setDescription(detailRes.group.description || '');
                setLinks({
                    web: detailRes.group.links?.web || '',
                    fb: detailRes.group.links?.fb || '',
                    discord: detailRes.group.links?.discord || '',
                    patreon: detailRes.group.links?.patreon || '',
                    twitter: detailRes.group.links?.twitter || '',
                    donations: detailRes.group.links?.donations || '',
                });
                setBooks(detailRes.books || []);
            }
            setAllWorkgroups(listRes || []);
        } catch (err: any) {
            console.error('Error cargando detalle de fansub:', err);
            setStatusMsg({ type: 'error', text: err.message || 'Error al cargar los datos del fansub' });
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [id]);

    const handleCopyPath = (bookId: string, path: string) => {
        if (!path) return;
        navigator.clipboard.writeText(path);
        setCopiedPathId(bookId);
        setTimeout(() => setCopiedPathId(null), 2000);
    };

    const handleSyncFilteredBooks = async () => {
        if (!id || filteredBooks.length === 0 || isSyncingBooks) return;
        try {
            setIsSyncingBooks(true);
            setStatusMsg(null);
            const bookIds = filteredBooks.map((b) => b.id);
            const res = await workgroupsApi.syncBooks(Number(id), bookIds);
            if (res && res.success) {
                setStatusMsg({
                    type: 'success',
                    text: `✅ ${res.message || `Sincronizados ${res.synced_count} libros desde sus archivos EPUB.`}`
                });
                await loadData();
                setTimeout(() => setStatusMsg(null), 6000);
            } else {
                setStatusMsg({
                    type: 'error',
                    text: res?.message || 'Error al sincronizar libros.'
                });
            }
        } catch (err: any) {
            console.error('Error sincronizando libros filtrados:', err);
            setStatusMsg({
                type: 'error',
                text: err.message || 'Error de conexión al sincronizar libros.'
            });
        } finally {
            setIsSyncingBooks(false);
        }
    };

    const handleSyncSingleBook = async (bookId: string) => {
        if (!id || syncingBookId || isSyncingBooks) return;
        try {
            setSyncingBookId(bookId);
            setStatusMsg(null);
            const res = await workgroupsApi.syncBooks(Number(id), [bookId]);
            if (res && res.success) {
                setStatusMsg({
                    type: 'success',
                    text: `✅ ${res.message || 'Libro sincronizado con éxito desde su archivo EPUB.'}`
                });
                await loadData();
                setTimeout(() => setStatusMsg(null), 5000);
            } else {
                setStatusMsg({
                    type: 'error',
                    text: res?.message || 'Error al sincronizar el libro.'
                });
            }
        } catch (err: any) {
            console.error('Error sincronizando libro:', err);
            setStatusMsg({
                type: 'error',
                text: err.message || 'Error al sincronizar el libro.'
            });
        } finally {
            setSyncingBookId(null);
        }
    };

    const handleSaveGroup = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!name.trim()) {
            setStatusMsg({ type: 'error', text: 'El nombre del grupo es obligatorio.' });
            return;
        }

        try {
            setIsSaving(true);
            setStatusMsg(null);
            await workgroupsApi.save({
                id: Number(id),
                name: name.trim(),
                siglas: siglas.trim() || undefined,
                description: description.trim() || undefined,
                links
            });
            setStatusMsg({ type: 'success', text: 'Información del fansub actualizada correctamente.' });
            await loadData();
            setTimeout(() => setStatusMsg(null), 4000);
        } catch (err: any) {
            console.error('Error al guardar fansub:', err);
            setStatusMsg({ type: 'error', text: err.message || 'Error al guardar los cambios.' });
        } finally {
            setIsSaving(false);
        }
    };

    const handleMergeSuccess = (res: WorkgroupMergeResponse) => {
        setStatusMsg({
            type: 'success',
            text: res.message || `Fusión completada: ${res.merged_count} grupos absorbidos.`
        });
        // If the current group was target, reload; if absorbed, navigate back to list
        if (res.target_id === Number(id)) {
            loadData();
        } else {
            navigate(`/app-v2/fansubs/${res.target_id}`);
        }
    };

    // Calculate Audit Metrics
    const badCount = useMemo(() => books.filter((b) => b.has_bad_metadata).length, [books]);
    const goodCount = useMemo(() => books.length - badCount, [books, badCount]);

    // Filter Books
    const filteredBooks = useMemo(() => {
        return books.filter((b) => {
            // Filter mode
            if (filterMode === 'bad' && !b.has_bad_metadata) return false;
            if (filterMode === 'good' && b.has_bad_metadata) return false;

            // Search query
            if (!searchQuery.trim()) return true;
            const q = searchQuery.toLowerCase();
            return (
                b.title?.toLowerCase().includes(q) ||
                b.spanish_title?.toLowerCase().includes(q) ||
                b.series_spanish?.toLowerCase().includes(q) ||
                b.publisher?.toLowerCase().includes(q) ||
                b.filename?.toLowerCase().includes(q) ||
                b.filepath?.toLowerCase().includes(q) ||
                (b.volume !== undefined && String(b.volume).includes(q))
            );
        });
    }, [books, filterMode, searchQuery]);

    if (loading) {
        return (
            <div className="min-h-[70vh] flex flex-col items-center justify-center space-y-4">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                <p className="text-xs text-gray-400">Cargando catálogo y auditoría del fansub...</p>
            </div>
        );
    }

    if (!group) {
        return (
            <div className="max-w-xl mx-auto py-20 text-center space-y-4">
                <AlertTriangle className="w-12 h-12 text-amber-500 mx-auto" />
                <h2 className="text-lg font-bold text-white">Fansub no encontrado</h2>
                <p className="text-xs text-gray-400">
                    El grupo traductor solicitado no existe o fue fusionado y eliminado previamente.
                </p>
                <Link
                    to="/app-v2/fansubs"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver al Directorio
                </Link>
            </div>
        );
    }

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300 pb-16">
            {/* Top Navigation Breadcrumbs & Back */}
            <div className="flex items-center justify-between">
                <Link
                    to="/app-v2/fansubs"
                    className="inline-flex items-center gap-2 text-xs font-bold text-gray-400 hover:text-white transition-colors bg-slate-900/60 border border-white/10 px-3.5 py-2 rounded-xl backdrop-blur-md"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver al Directorio de Fansubs
                </Link>

                <div className="flex items-center gap-2.5">
                    <button
                        onClick={() => setIsMergeModalOpen(true)}
                        className="px-4 py-2 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 text-xs font-bold flex items-center gap-2 transition-all shadow-lg active:scale-95"
                    >
                        <GitMerge className="w-4 h-4 text-purple-400" /> Fusionar con Otros Fansubs
                    </button>
                    {activeTab === 'edit' && (
                        <button
                            onClick={handleSaveGroup}
                            disabled={isSaving}
                            className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            <span>Guardar Información</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Status Toast */}
            {statusMsg && (
                <div
                    className={`p-4 rounded-2xl flex items-center justify-between gap-3 text-xs font-medium border ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border-red-500/20'
                    }`}
                >
                    <div className="flex items-center gap-2.5">
                        {statusMsg.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                        )}
                        <span>{statusMsg.text}</span>
                    </div>
                    <button onClick={() => setStatusMsg(null)} className="text-gray-400 hover:text-white">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            )}

            {/* Fansub Hero Banner (Glassmorphic) */}
            <div className="bg-slate-900/60 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl relative overflow-hidden shadow-2xl">
                <div className="absolute -right-16 -top-16 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
                <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                    <div className="flex items-start sm:items-center gap-4 sm:gap-5 min-w-0">
                        <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-tr from-indigo-600/30 to-purple-600/30 border border-indigo-500/30 text-indigo-300 flex items-center justify-center font-black text-2xl sm:text-3xl shrink-0 shadow-xl">
                            {group.name?.[0]?.toUpperCase() || 'F'}
                        </div>
                        <div className="space-y-1.5 min-w-0">
                            <div className="flex flex-wrap items-center gap-2.5">
                                <h1 className="text-xl sm:text-2xl font-black text-white tracking-tight truncate">
                                    {group.name}
                                </h1>
                                {group.siglas && (
                                    <span className="px-2 py-0.5 rounded-lg bg-indigo-500/20 text-indigo-300 text-xs font-mono font-bold border border-indigo-500/30">
                                        [{group.siglas}]
                                    </span>
                                )}
                                <span className="px-2 py-0.5 rounded-lg bg-white/5 text-gray-400 text-xs font-mono border border-white/10">
                                    ID #{group.id}
                                </span>
                            </div>

                            {group.description ? (
                                <p className="text-xs text-gray-400 max-w-2xl line-clamp-2">
                                    {group.description}
                                </p>
                            ) : (
                                <p className="text-xs text-gray-500 italic">
                                    Sin descripción registrada. Puedes editarla en la pestaña de configuración.
                                </p>
                            )}

                            {/* Metrics Pills */}
                            <div className="flex flex-wrap items-center gap-2 pt-1">
                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-950/60 border border-white/10 text-xs font-mono text-gray-300">
                                    <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                                    <span><strong>{books.length}</strong> libros asociados</span>
                                </span>

                                {badCount > 0 ? (
                                    <button
                                        onClick={() => {
                                            setActiveTab('audit');
                                            setFilterMode('bad');
                                        }}
                                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-xs font-mono text-amber-300 hover:bg-amber-500/25 transition-all"
                                        title="Haz clic para filtrar y ver los libros con errores"
                                    >
                                        <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                                        <span><strong>{badCount}</strong> con error en EPUB</span>
                                    </button>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-xs font-mono text-emerald-300">
                                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                                        <span>100% metadata consistente</span>
                                    </span>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Social links preview */}
                    <div className="flex items-center gap-2 shrink-0 self-start md:self-auto">
                        {group.links?.web && (
                            <a
                                href={group.links.web}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-indigo-400 transition-colors"
                                title={group.links.web}
                            >
                                <Globe className="w-4 h-4" />
                            </a>
                        )}
                        {group.links?.fb && (
                            <a
                                href={group.links.fb}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-blue-400 transition-colors"
                                title={group.links.fb}
                            >
                                <Facebook className="w-4 h-4" />
                            </a>
                        )}
                        {group.links?.discord && (
                            <a
                                href={group.links.discord}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-indigo-400 transition-colors"
                                title={group.links.discord}
                            >
                                <MessageSquare className="w-4 h-4" />
                            </a>
                        )}
                        {group.links?.patreon && (
                            <a
                                href={group.links.patreon}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-pink-400 transition-colors"
                                title={group.links.patreon}
                            >
                                <Heart className="w-4 h-4" />
                            </a>
                        )}
                        {group.links?.twitter && (
                            <a
                                href={group.links.twitter}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-sky-400 transition-colors"
                                title={group.links.twitter}
                            >
                                <Twitter className="w-4 h-4" />
                            </a>
                        )}
                        {group.links?.donations && (
                            <a
                                href={group.links.donations}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-amber-400 transition-colors"
                                title={group.links.donations}
                            >
                                <Coffee className="w-4 h-4" />
                            </a>
                        )}
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-white/10 pb-2">
                <button
                    onClick={() => setActiveTab('audit')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                        activeTab === 'audit'
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <BookOpen className="w-4 h-4" />
                    <span>Auditoría de EPUBs & Libros</span>
                    <span
                        className={`px-1.5 py-0.5 rounded-full text-[10px] font-mono ${
                            badCount > 0 ? 'bg-amber-500 text-black font-bold' : 'bg-white/20 text-white'
                        }`}
                    >
                        {books.length}
                    </span>
                </button>

                <button
                    onClick={() => setActiveTab('edit')}
                    className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                        activeTab === 'edit'
                            ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30'
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                >
                    <Edit3 className="w-4 h-4" />
                    <span>Ficha del Fansub & Redes</span>
                </button>
            </div>

            {/* Floating Global Status / Sync Alert */}
            {statusMsg && (
                <div
                    className={`p-4 rounded-2xl text-xs font-bold flex items-center justify-between gap-3 shadow-lg border backdrop-blur-xl animate-in fade-in duration-300 ${
                        statusMsg.type === 'success'
                            ? 'bg-emerald-950/40 border-emerald-500/40 text-emerald-300 shadow-emerald-950/30'
                            : 'bg-red-950/40 border-red-500/40 text-red-300 shadow-red-950/30'
                    }`}
                >
                    <div className="flex items-center gap-2.5">
                        {statusMsg.type === 'success' ? (
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                        ) : (
                            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
                        )}
                        <span>{statusMsg.text}</span>
                    </div>
                    <button
                        type="button"
                        onClick={() => setStatusMsg(null)}
                        className="p-1 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-colors"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>
            )}

            {/* TAB 1: EPUB AUDIT & BOOKS LIST */}
            {activeTab === 'audit' && (
                <div className="space-y-4">
                    {/* Filter Bar & Search */}
                    <div className="bg-slate-900/50 border border-white/10 rounded-2xl p-3.5 backdrop-blur-xl flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
                        {/* Filter Mode Buttons */}
                        <div className="flex flex-wrap items-center gap-1.5">
                            <button
                                onClick={() => setFilterMode('all')}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                    filterMode === 'all'
                                        ? 'bg-white/15 text-white border border-white/20 shadow-md'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                }`}
                            >
                                <span>Todos</span>
                                <span className="font-mono text-[10px] opacity-70">({books.length})</span>
                            </button>

                            <button
                                onClick={() => setFilterMode('bad')}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                    filterMode === 'bad'
                                        ? 'bg-amber-500 text-black border border-amber-400 shadow-md'
                                        : 'text-amber-300 hover:bg-amber-500/15 border border-amber-500/20'
                                }`}
                            >
                                <AlertTriangle className="w-3.5 h-3.5" />
                                <span>Solo con error en archivo</span>
                                <span className="font-mono text-[10px] font-black">({badCount})</span>
                            </button>

                            <button
                                onClick={() => setFilterMode('good')}
                                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 ${
                                    filterMode === 'good'
                                        ? 'bg-emerald-500 text-black border border-emerald-400 shadow-md'
                                        : 'text-emerald-300 hover:bg-emerald-500/15 border border-emerald-500/20'
                                }`}
                            >
                                <CheckCircle2 className="w-3.5 h-3.5" />
                                <span>Solo metadata correcta</span>
                                <span className="font-mono text-[10px] opacity-70">({goodCount})</span>
                            </button>
                        </div>

                        {/* Actions & Search */}
                        <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
                            {/* Botón de Sincronización de Libros Filtrados */}
                            <button
                                type="button"
                                onClick={handleSyncFilteredBooks}
                                disabled={isSyncingBooks || filteredBooks.length === 0}
                                className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shadow-lg whitespace-nowrap active:scale-95 ${
                                    isSyncingBooks
                                        ? 'bg-indigo-600/50 text-indigo-200 cursor-wait border border-indigo-400/30'
                                        : filteredBooks.length === 0
                                        ? 'bg-slate-800/40 text-gray-500 border border-white/5 cursor-not-allowed'
                                        : 'bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white border border-white/20 shadow-indigo-600/25'
                                }`}
                                title="Re-escanear metadatos directamente de los archivos EPUB filtrados para comprobar si se corrigió el OPF en disco"
                            >
                                <RefreshCw className={`w-3.5 h-3.5 ${isSyncingBooks ? 'animate-spin' : ''}`} />
                                <span>{isSyncingBooks ? 'Sincronizando...' : `Sincronizar filtrados (${filteredBooks.length})`}</span>
                            </button>

                            {/* Search Input */}
                            <div className="relative min-w-[240px]">
                                <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-1/2 -translate-y-1/2" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Filtrar por título, volumen, archivo..."
                                    className="w-full pl-9 pr-4 py-1.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                                />
                                {searchQuery && (
                                    <button
                                        onClick={() => setSearchQuery('')}
                                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                                    >
                                        <X className="w-3.5 h-3.5" />
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Notice for Typesetter / Maquetador */}
                    {badCount > 0 && filterMode === 'bad' && (
                        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/30 text-amber-200 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4 backdrop-blur-md">
                            <div className="flex items-start gap-3">
                                <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                                <div className="space-y-1">
                                    <p className="font-bold">
                                        Guía para el Maquetador: {badCount} archivos requieren corrección en sus metadatos internos
                                    </p>
                                    <p className="text-gray-300 leading-relaxed text-[11px]">
                                        El campo <code className="bg-black/30 px-1 py-0.5 rounded font-mono text-amber-300">dc:publisher</code> dentro del OPF del EPUB no coincide exactamente con el nombre oficial del grupo <strong>"{group.name}"</strong> (por ejemplo: mayúsculas incorrectas, un punto final extra o un texto distinto). Puedes copiar la ruta del archivo, corregirlo con tu editor (Sigil/Calibre) y usar el botón de sincronización para verificar de inmediato.
                                    </p>
                                </div>
                            </div>
                            <button
                                type="button"
                                onClick={handleSyncFilteredBooks}
                                disabled={isSyncingBooks || filteredBooks.length === 0}
                                className="shrink-0 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black text-xs font-black flex items-center gap-2 shadow-lg transition-all active:scale-95 disabled:opacity-50"
                            >
                                <RefreshCw className={`w-4 h-4 ${isSyncingBooks ? 'animate-spin' : ''}`} />
                                <span>{isSyncingBooks ? 'Comprobando...' : 'Comprobar correcciones ahora'}</span>
                            </button>
                        </div>
                    )}

                    {/* Book Cards Grid / List */}
                    {filteredBooks.length === 0 ? (
                        <div className="py-20 text-center bg-slate-900/40 rounded-3xl border border-white/5 space-y-2">
                            <p className="text-xs text-gray-400">
                                {filterMode === 'bad'
                                    ? '🎉 ¡Excelente! No hay libros con errores de metadatos en este grupo.'
                                    : 'No se encontraron libros que coincidan con los criterios de búsqueda.'}
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {filteredBooks.map((b) => {
                                const isCopied = copiedPathId === b.id;
                                return (
                                    <div
                                        key={b.id}
                                        className={`rounded-2xl p-4 transition-all border backdrop-blur-xl flex flex-col lg:flex-row lg:items-center justify-between gap-4 ${
                                            b.has_bad_metadata
                                                ? 'bg-amber-950/10 border-amber-500/30 hover:border-amber-500/50 shadow-lg shadow-amber-950/20'
                                                : 'bg-slate-900/60 border-white/10 hover:border-white/20 shadow-md'
                                        }`}
                                    >
                                        {/* Book Basic Info */}
                                        <div className="flex items-start gap-3.5 min-w-0 flex-1">
                                            {/* Cover */}
                                            <div className="w-12 h-16 sm:w-14 sm:h-20 rounded-xl bg-slate-950 border border-white/10 overflow-hidden shrink-0 shadow-md flex items-center justify-center">
                                                {b.cover_thumb || b.cover_low ? (
                                                    <img
                                                        src={b.cover_thumb || b.cover_low}
                                                        alt={b.title}
                                                        className="w-full h-full object-cover"
                                                        loading="lazy"
                                                    />
                                                ) : (
                                                    <BookOpen className="w-6 h-6 text-gray-600" />
                                                )}
                                            </div>

                                            {/* Titles & File details */}
                                            <div className="space-y-1.5 min-w-0 flex-1">
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <h3 className="text-xs sm:text-sm font-bold text-white truncate max-w-xl">
                                                        {b.spanish_title || b.title}
                                                    </h3>
                                                    {b.volume !== undefined && b.volume !== null && (
                                                        <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] font-bold border border-indigo-500/30">
                                                            Vol. {b.volume}
                                                        </span>
                                                    )}
                                                    {b.role && (
                                                        <span className="px-1.5 py-0.5 rounded bg-white/10 text-gray-400 font-mono text-[10px]">
                                                            Rol: {b.role}
                                                        </span>
                                                    )}
                                                </div>

                                                {b.series_spanish && b.series_spanish !== b.spanish_title && (
                                                    <div className="text-[11px] text-gray-400 truncate">
                                                        Serie: {b.series_spanish}
                                                    </div>
                                                )}

                                                {/* Filepath chip with copy */}
                                                <div className="flex items-center gap-2 pt-0.5">
                                                    <div
                                                        className="px-2.5 py-1 rounded-lg bg-slate-950/80 border border-white/5 font-mono text-[10px] text-gray-400 truncate max-w-lg"
                                                        title={b.filepath || b.filename || b.id}
                                                    >
                                                        {b.filename || b.filepath || b.id}
                                                    </div>
                                                    {b.filepath && (
                                                        <div className="flex items-center gap-1.5">
                                                            <button
                                                                onClick={() => handleCopyPath(b.id, b.filepath!)}
                                                                className={`p-1.5 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-all ${
                                                                    isCopied
                                                                        ? 'bg-emerald-500 text-black'
                                                                        : 'bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white'
                                                                }`}
                                                                title="Copiar ruta absoluta del archivo EPUB para el maquetador"
                                                            >
                                                                {isCopied ? (
                                                                    <>
                                                                        <Check className="w-3 h-3 stroke-[3]" />
                                                                        <span>¡Copiado!</span>
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <Copy className="w-3 h-3" />
                                                                        <span>Copiar Ruta</span>
                                                                    </>
                                                                )}
                                                            </button>

                                                            <button
                                                                onClick={() => handleSyncSingleBook(b.id)}
                                                                disabled={syncingBookId === b.id || isSyncingBooks}
                                                                className={`p-1.5 rounded-lg text-[10px] font-bold flex items-center gap-1 transition-all ${
                                                                    syncingBookId === b.id
                                                                        ? 'bg-indigo-600/40 text-indigo-300'
                                                                        : 'bg-white/5 hover:bg-indigo-600/20 text-gray-300 hover:text-indigo-300'
                                                                }`}
                                                                title="Re-escanear este archivo EPUB en disco para actualizar sus metadatos"
                                                            >
                                                                <RefreshCw className={`w-3 h-3 ${syncingBookId === b.id ? 'animate-spin' : ''}`} />
                                                                <span>{syncingBookId === b.id ? 'Sincronizando...' : 'Re-escanear'}</span>
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>

                                        {/* Metadata Audit Discrepancy Box */}
                                        <div className="lg:w-80 shrink-0 p-3 rounded-xl bg-slate-950/60 border border-white/5 space-y-1.5">
                                            <div className="flex items-center justify-between text-[11px]">
                                                <span className="text-gray-500">Esperado:</span>
                                                <span className="font-bold text-white font-mono truncate max-w-[170px]">
                                                    {group.name}
                                                </span>
                                            </div>

                                            <div className="flex items-center justify-between text-[11px]">
                                                <span className="text-gray-500">En EPUB (dc:publisher):</span>
                                                <span
                                                    className={`font-mono font-bold truncate max-w-[170px] ${
                                                        b.has_bad_metadata ? 'text-amber-300' : 'text-emerald-400'
                                                    }`}
                                                >
                                                    {b.publisher ? `"${b.publisher}"` : 'Sin definir'}
                                                </span>
                                            </div>

                                            {/* Status Badge */}
                                            <div className="pt-1 border-t border-white/5">
                                                {b.has_bad_metadata ? (
                                                    <div className="p-1.5 rounded-lg bg-amber-500/15 border border-amber-500/30 text-amber-200 text-[10px] font-medium flex items-center gap-1.5">
                                                        <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                                                        <span className="leading-tight">
                                                            {b.metadata_issue || 'Metadata inconsistente en el archivo'}
                                                        </span>
                                                    </div>
                                                ) : (
                                                    <div className="p-1 rounded-lg bg-emerald-500/10 text-emerald-400 text-[10px] font-medium flex items-center gap-1">
                                                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                                                        <span>Coincide exactamente</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}

            {/* TAB 2: EDIT FANSUB & SOCIAL LINKS */}
            {activeTab === 'edit' && (
                <form onSubmit={handleSaveGroup} className="space-y-6 max-w-4xl">
                    <div className="bg-slate-900/60 border border-white/10 rounded-3xl p-6 sm:p-8 backdrop-blur-xl space-y-6 shadow-2xl">
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider border-b border-white/10 pb-3 flex items-center gap-2">
                            <Building2 className="w-4 h-4 text-indigo-400" /> Información General del Fansub
                        </h3>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-300 mb-1.5">
                                    Nombre Oficial del Fansub *
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Ej: Tamashi's Project"
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    required
                                />
                            </div>

                            <div>
                                <label className="block text-xs font-bold text-gray-300 mb-1.5">
                                    Siglas Oficiales [TAG]
                                </label>
                                <input
                                    type="text"
                                    value={siglas}
                                    onChange={(e) => setSiglas(e.target.value)}
                                    placeholder="Ej: TP"
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono uppercase focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-300 mb-1.5">
                                Notas Editoriales / Descripción
                            </label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Notas sobre el fansub, integrantes, géneros que traducen..."
                                rows={3}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        {/* Social Links */}
                        <div className="space-y-4 pt-4 border-t border-white/10">
                            <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                                Enlaces Oficiales y Redes (Se inyectan en publicaciones)
                            </h4>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <Globe className="w-3.5 h-3.5 text-indigo-400" /> Sitio Web Oficial
                                    </label>
                                    <input
                                        type="url"
                                        value={links.web}
                                        onChange={(e) => setLinks({ ...links, web: e.target.value })}
                                        placeholder="https://..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <Facebook className="w-3.5 h-3.5 text-blue-400" /> Página de Facebook
                                    </label>
                                    <input
                                        type="url"
                                        value={links.fb}
                                        onChange={(e) => setLinks({ ...links, fb: e.target.value })}
                                        placeholder="https://facebook.com/..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <MessageSquare className="w-3.5 h-3.5 text-indigo-400" /> Servidor de Discord
                                    </label>
                                    <input
                                        type="url"
                                        value={links.discord}
                                        onChange={(e) => setLinks({ ...links, discord: e.target.value })}
                                        placeholder="https://discord.gg/..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <Twitter className="w-3.5 h-3.5 text-sky-400" /> Twitter / X
                                    </label>
                                    <input
                                        type="url"
                                        value={links.twitter}
                                        onChange={(e) => setLinks({ ...links, twitter: e.target.value })}
                                        placeholder="https://twitter.com/..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <Heart className="w-3.5 h-3.5 text-pink-400" /> Patreon / Membresía
                                    </label>
                                    <input
                                        type="url"
                                        value={links.patreon}
                                        onChange={(e) => setLinks({ ...links, patreon: e.target.value })}
                                        placeholder="https://patreon.com/..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>

                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 mb-1 flex items-center gap-1.5">
                                        <Coffee className="w-3.5 h-3.5 text-amber-400" /> Ko-fi / Donaciones
                                    </label>
                                    <input
                                        type="url"
                                        value={links.donations}
                                        onChange={(e) => setLinks({ ...links, donations: e.target.value })}
                                        placeholder="https://ko-fi.com/..."
                                        className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end gap-3 pt-4 border-t border-white/10">
                            <button
                                type="submit"
                                disabled={isSaving}
                                className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-xl shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
                            >
                                {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                <span>Guardar Ficha Editorial</span>
                            </button>
                        </div>
                    </div>
                </form>
            )}

            {/* Merge Modal */}
            <FansubMergeModal
                isOpen={isMergeModalOpen}
                onClose={() => setIsMergeModalOpen(false)}
                workgroups={allWorkgroups}
                initialTargetId={group.id}
                onMergeSuccess={handleMergeSuccess}
            />
        </div>
    );
};
