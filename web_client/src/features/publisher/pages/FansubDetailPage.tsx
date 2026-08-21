import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    Building2, Globe, Facebook, MessageSquare, Heart, Twitter, Coffee, 
    ArrowLeft, Save, Plus, Trash2, Search, BookOpen, Link2, Check,
    AlertCircle, ExternalLink, X, RefreshCw
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
import { workgroupsApi, TranslatorsGroupItem, AttachedBookItem } from '../services/workgroupsApi';
import { api } from '@shared/services/api';

export const FansubDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { settings } = useTheme();
    const { webApp, isStaff } = useTelegram();

    const [loading, setLoading] = useState(true);
    const [group, setGroup] = useState<TranslatorsGroupItem | null>(null);
    const [books, setBooks] = useState<AttachedBookItem[]>([]);
    
    // Form Edit State
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
    const [saveSuccess, setSaveSuccess] = useState(false);

    // Book search & attach modal/section
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);
    const [selectedRole, setSelectedRole] = useState<'translator' | 'editor' | 'layout'>('translator');
    const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
    const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

    const loadData = async () => {
        if (!id) return;
        try {
            setLoading(true);
            const res = await workgroupsApi.getDetail(Number(id));
            if (res && res.group) {
                setGroup(res.group);
                setName(res.group.name || '');
                setSiglas(res.group.siglas || '');
                setDescription(res.group.description || '');
                setLinks({
                    web: res.group.links?.web || '',
                    fb: res.group.links?.fb || '',
                    discord: res.group.links?.discord || '',
                    patreon: res.group.links?.patreon || '',
                    twitter: res.group.links?.twitter || '',
                    donations: res.group.links?.donations || '',
                });
                setBooks(res.books || []);
            }
        } catch (err: any) {
            console.error("Error loading fansub details:", err);
            webApp?.showAlert?.("Error al cargar datos del fansub: " + (err?.message || ""));
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [id]);

    // Handle Save Group Info
    const handleSaveGroup = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!name.trim()) {
            webApp?.showAlert?.("El nombre del grupo es obligatorio");
            return;
        }

        try {
            setIsSaving(true);
            webApp?.HapticFeedback?.impactOccurred('medium');
            await workgroupsApi.save({
                id: Number(id),
                name: name.trim(),
                siglas: siglas.trim() || undefined,
                description: description.trim() || undefined,
                links
            });
            setSaveSuccess(true);
            webApp?.HapticFeedback?.notificationOccurred('success');
            setTimeout(() => setSaveSuccess(false), 2500);
            // Refresh
            const updated = await workgroupsApi.getDetail(Number(id));
            if (updated?.group) setGroup(updated.group);
        } catch (err: any) {
            console.error("Error saving fansub:", err);
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.("Error al guardar: " + (err?.message || ""));
        } finally {
            setIsSaving(false);
        }
    };

    // Search Books to Attach
    const handleSearchBooks = async (query: string) => {
        setSearchQuery(query);
        if (!query.trim() || query.length < 2) {
            setSearchResults([]);
            return;
        }

        try {
            setSearching(true);
            const res = await api.search(query.trim());
            const items = res.books || res.results || [];
            // Filter out already attached
            const attachedIds = new Set(books.map(b => b.id));
            setSearchResults(items.filter((b: any) => !attachedIds.has(b.id)));
        } catch (err) {
            console.error("Error searching books:", err);
        } finally {
            setSearching(false);
        }
    };

    // Attach Book
    const handleAttachBook = async (bookId: string) => {
        if (!id) return;
        try {
            setActionLoadingId(bookId);
            webApp?.HapticFeedback?.impactOccurred('medium');
            await workgroupsApi.attachBook(Number(id), bookId, selectedRole);
            webApp?.HapticFeedback?.notificationOccurred('success');
            // Remove from search results and reload list
            setSearchResults(prev => prev.filter(b => b.id !== bookId));
            await loadData();
        } catch (err: any) {
            console.error("Error attaching book:", err);
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.("No se pudo vincular el libro: " + (err?.message || ""));
        } finally {
            setActionLoadingId(null);
        }
    };

    // Detach Book
    const handleDetachBook = async (bookId: string, bookTitle: string) => {
        if (!id) return;
        if (!window.confirm(`¿Desvincular "${bookTitle}" de este grupo?`)) return;

        try {
            setActionLoadingId(bookId);
            webApp?.HapticFeedback?.impactOccurred('medium');
            await workgroupsApi.detachBook(Number(id), bookId);
            webApp?.HapticFeedback?.notificationOccurred('success');
            setBooks(prev => prev.filter(b => b.id !== bookId));
        } catch (err: any) {
            console.error("Error detaching book:", err);
            webApp?.HapticFeedback?.notificationOccurred('error');
            webApp?.showAlert?.("No se pudo desvincular el libro: " + (err?.message || ""));
        } finally {
            setActionLoadingId(null);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-[60vh]">
                <div className="flex flex-col items-center gap-3">
                    <RefreshCw className="w-8 h-8 text-primary animate-spin" />
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Cargando Fansub...</span>
                </div>
            </div>
        );
    }

    if (!group) {
        return (
            <div className="max-w-4xl mx-auto p-6 text-center">
                <div className="glass-panel rounded-premium p-10 flex flex-col items-center gap-4">
                    <AlertCircle className="w-12 h-12 text-red-400" />
                    <h2 className="text-lg font-bold text-white">Grupo no encontrado</h2>
                    <button
                        onClick={() => navigate('/admin?tab=workgroups')}
                        className="px-4 py-2 bg-primary text-white rounded-premium text-xs font-bold"
                    >
                        Volver a Fansubs
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6 animate-in fade-in duration-300">
            {/* Top Navigation */}
            <div className="flex items-center justify-between">
                <button
                    onClick={() => navigate('/admin?tab=workgroups')}
                    className="flex items-center gap-2 px-3 py-1.5 glass-panel rounded-xl border border-white/5 hover:bg-white/10 text-gray-300 hover:text-white transition-all text-xs font-bold cursor-pointer"
                >
                    <ArrowLeft className="w-4 h-4" />
                    <span>Volver a Fansubs</span>
                </button>

                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold text-gray-400 bg-white/5 px-2.5 py-1 rounded-full border border-white/5">
                        ID: {group.id}
                    </span>
                    <span className="text-[10px] font-bold text-primary bg-primary/10 px-2.5 py-1 rounded-full border border-primary/20">
                        {books.length} Libros Asociados
                    </span>
                </div>
            </div>

            {/* Header Card */}
            <div 
                className="glass-panel rounded-premium p-6 border border-white/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 shadow-xl"
                style={{
                    background: `rgba(var(--glass-rgb), 0.85)`,
                    backdropFilter: `blur(${settings.glassBlur}px)`
                }}
            >
                <div className="flex items-center gap-4">
                    <div className="p-3.5 rounded-2xl bg-gradient-to-br from-primary/30 to-primary/10 text-primary border border-primary/20 shadow-lg shadow-primary/10">
                        <Building2 className="w-7 h-7" />
                    </div>
                    <div>
                        <div className="flex items-center gap-2.5">
                            <h1 className="text-xl sm:text-2xl font-black text-white">{group.name}</h1>
                            {group.siglas && (
                                <span className="px-2.5 py-0.5 rounded-full bg-white/10 text-xs font-bold text-gray-300 border border-white/10">
                                    {group.siglas}
                                </span>
                            )}
                        </div>
                        <p className="text-xs text-gray-400 mt-1 max-w-xl">
                            {group.description || 'Sin descripción registrada para este grupo traductor/fansub.'}
                        </p>
                    </div>
                </div>

                <div className="flex gap-2 w-full md:w-auto">
                    <button
                        onClick={() => setIsAttachModalOpen(true)}
                        className="flex-1 md:flex-none px-4 py-2.5 bg-primary hover:brightness-110 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-primary/20 active:scale-95 transition-all cursor-pointer"
                    >
                        <Plus className="w-4 h-4" />
                        <span>Vincular Libro</span>
                    </button>
                </div>
            </div>

            {/* Main Grid: Left Edit Form, Right Attached Books */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                
                {/* Form: Editar Redes y Datos (4 Cols) */}
                <div className="lg:col-span-5 space-y-6">
                    <div 
                        className="glass-panel rounded-premium p-5 border border-white/10 space-y-4"
                        style={{
                            background: `rgba(var(--glass-rgb), 0.75)`,
                            backdropFilter: `blur(${settings.glassBlur}px)`
                        }}
                    >
                        <div className="flex justify-between items-center pb-3 border-b border-white/5">
                            <h3 className="text-xs font-black uppercase tracking-wider text-primary/90 flex items-center gap-2">
                                <Link2 className="w-4 h-4" />
                                Información y Redes
                            </h3>
                            {saveSuccess && (
                                <span className="text-[10px] font-bold text-green-400 flex items-center gap-1 animate-in fade-in">
                                    <Check className="w-3.5 h-3.5" /> Guardado
                                </span>
                            )}
                        </div>

                        <form onSubmit={handleSaveGroup} className="space-y-4">
                            <div>
                                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                    Nombre del Grupo / Fansub *
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    placeholder="Ej: Novelas Ligeras Fansub"
                                    className="w-full p-2.5 glass-panel rounded-xl border border-white/10 bg-black/20 text-xs text-white focus:border-primary/50 outline-none"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                        Siglas / Alias
                                    </label>
                                    <input
                                        type="text"
                                        value={siglas}
                                        onChange={(e) => setSiglas(e.target.value)}
                                        placeholder="Ej: NLF"
                                        className="w-full p-2.5 glass-panel rounded-xl border border-white/10 bg-black/20 text-xs text-white focus:border-primary/50 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                        Libros Asignados
                                    </label>
                                    <div className="w-full p-2.5 glass-panel rounded-xl border border-white/5 bg-white/5 text-xs text-gray-400 font-bold text-center">
                                        {books.length} Epubs
                                    </div>
                                </div>
                            </div>

                            <div>
                                <label className="text-[10px] font-bold text-gray-400 uppercase tracking-wider block mb-1">
                                    Descripción / Bio
                                </label>
                                <textarea
                                    rows={2}
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    placeholder="Breve reseña del fansub o traductor..."
                                    className="w-full p-2.5 glass-panel rounded-xl border border-white/10 bg-black/20 text-xs text-white focus:border-primary/50 outline-none resize-none"
                                />
                            </div>

                            {/* Enlaces de Redes Sociales */}
                            <div className="pt-2 border-t border-white/5 space-y-3">
                                <span className="text-[10px] font-black uppercase tracking-wider text-gray-300 block">
                                    Enlaces Oficiales (Inyección en Plantillas)
                                </span>

                                <div className="space-y-2">
                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 shrink-0">
                                            <Globe className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.web}
                                            onChange={(e) => setLinks({ ...links, web: e.target.value })}
                                            placeholder="https://fansub.com"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-blue-600/10 text-blue-400 shrink-0">
                                            <Facebook className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.fb}
                                            onChange={(e) => setLinks({ ...links, fb: e.target.value })}
                                            placeholder="https://facebook.com/pagina"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-300 shrink-0">
                                            <MessageSquare className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.discord}
                                            onChange={(e) => setLinks({ ...links, discord: e.target.value })}
                                            placeholder="https://discord.gg/invite"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-red-500/10 text-red-400 shrink-0">
                                            <Heart className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.patreon}
                                            onChange={(e) => setLinks({ ...links, patreon: e.target.value })}
                                            placeholder="https://patreon.com/fansub"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-sky-500/10 text-sky-400 shrink-0">
                                            <Twitter className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.twitter}
                                            onChange={(e) => setLinks({ ...links, twitter: e.target.value })}
                                            placeholder="https://twitter.com/fansub"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>

                                    <div className="flex items-center gap-2">
                                        <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 shrink-0">
                                            <Coffee className="w-3.5 h-3.5" />
                                        </div>
                                        <input
                                            type="url"
                                            value={links.donations}
                                            onChange={(e) => setLinks({ ...links, donations: e.target.value })}
                                            placeholder="https://ko-fi.com/fansub"
                                            className="w-full p-2 glass-panel rounded-lg border border-white/10 bg-black/20 text-[11px] text-white focus:border-primary/50 outline-none"
                                        />
                                    </div>
                                </div>
                            </div>

                            <button
                                type="submit"
                                disabled={isSaving}
                                className="w-full py-2.5 bg-primary hover:brightness-110 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg shadow-primary/20 active:scale-98 transition-all cursor-pointer disabled:opacity-50"
                            >
                                <Save className="w-4 h-4" />
                                <span>{isSaving ? 'Guardando Cambios...' : 'Guardar Cambios'}</span>
                            </button>
                        </form>
                    </div>
                </div>

                {/* Right: Listado de Libros Asociados (7 Cols) */}
                <div className="lg:col-span-7 space-y-4">
                    <div className="flex justify-between items-center px-1">
                        <div>
                            <h3 className="text-xs font-black uppercase tracking-wider text-primary/90 flex items-center gap-2">
                                <BookOpen className="w-4 h-4" />
                                Libros EPUB Asociados ({books.length})
                            </h3>
                            <p className="text-[11px] text-gray-400">
                                Libros que usan automáticamente los enlaces y créditos de este grupo.
                            </p>
                        </div>

                        <button
                            onClick={() => setIsAttachModalOpen(true)}
                            className="px-3 py-1.5 glass-panel rounded-xl border border-primary/30 bg-primary/10 hover:bg-primary/20 text-primary text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer"
                        >
                            <Plus className="w-3.5 h-3.5" />
                            <span>Vincular Otro</span>
                        </button>
                    </div>

                    {books.length === 0 ? (
                        <div className="glass-panel rounded-premium p-10 flex flex-col items-center gap-3 text-center border border-white/5">
                            <BookOpen className="w-8 h-8 text-gray-500" />
                            <div>
                                <h4 className="text-xs font-bold text-white">No hay libros asociados aún</h4>
                                <p className="text-[11px] text-gray-400 mt-1 max-w-sm">
                                    Haz clic en "Vincular Libro" para buscar en el catálogo y asociar los EPUBs correspondientes a este fansub.
                                </p>
                            </div>
                            <button
                                onClick={() => setIsAttachModalOpen(true)}
                                className="mt-2 px-4 py-2 bg-primary/20 hover:bg-primary/30 text-primary border border-primary/30 rounded-xl text-xs font-bold flex items-center gap-2 transition-all cursor-pointer"
                            >
                                <Plus className="w-4 h-4" />
                                <span>Buscar y Vincular Libros</span>
                            </button>
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {books.map((book) => (
                                <div
                                    key={book.id}
                                    className="glass-panel rounded-premium p-3 border border-white/5 hover:border-primary/30 transition-all flex gap-3 items-center justify-between group"
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-12 h-16 rounded-lg bg-black/40 overflow-hidden shrink-0 border border-white/10 relative">
                                            {book.cover_thumb || book.cover_low ? (
                                                <img 
                                                    src={book.cover_thumb || book.cover_low} 
                                                    alt={book.title} 
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                    <BookOpen className="w-5 h-5" />
                                                </div>
                                            )}
                                            {book.volume !== undefined && book.volume !== null && (
                                                <span className="absolute bottom-0 right-0 bg-primary/90 text-white text-[8px] font-black px-1 rounded-tl">
                                                    V{book.volume}
                                                </span>
                                            )}
                                        </div>

                                        <div className="min-w-0 flex flex-col">
                                            <h4 
                                                onClick={() => navigate(`/book/${book.id}`)}
                                                className="text-xs font-bold text-white hover:text-primary transition-colors truncate cursor-pointer"
                                                title={book.title}
                                            >
                                                {book.title}
                                            </h4>
                                            {book.author && (
                                                <span className="text-[10px] text-gray-400 truncate">
                                                    ✍️ {book.author}
                                                </span>
                                            )}
                                            <span className="mt-1 inline-block px-1.5 py-0.5 rounded bg-white/10 text-gray-300 text-[9px] font-semibold w-max capitalize">
                                                {book.role === 'translator' ? 'Traducción' : book.role === 'layout' ? 'Maquetación' : 'Edición'}
                                            </span>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-1 shrink-0">
                                        <button
                                            onClick={() => navigate(`/book/${book.id}`)}
                                            className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                                            title="Ver Ficha del Libro"
                                        >
                                            <ExternalLink className="w-3.5 h-3.5" />
                                        </button>
                                        <button
                                            onClick={() => handleDetachBook(book.id, book.title)}
                                            disabled={actionLoadingId === book.id}
                                            className="p-1.5 text-gray-400 hover:text-red-400 rounded-lg hover:bg-red-500/10 transition-colors disabled:opacity-50"
                                            title="Desvincular del Grupo"
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Modal: Buscar y Vincular Libro */}
            {isAttachModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div 
                        className="w-full max-w-lg glass-panel rounded-premium p-6 border border-white/10 space-y-4 shadow-2xl animate-in zoom-in-95 max-h-[85vh] flex flex-col"
                        style={{
                            background: `rgba(var(--glass-rgb), 0.95)`,
                            backdropFilter: `blur(${settings.glassBlur + 8}px)`
                        }}
                    >
                        <div className="flex justify-between items-center pb-3 border-b border-white/5 shrink-0">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-primary/10 rounded-xl text-primary">
                                    <Plus className="w-4 h-4" />
                                </div>
                                <div>
                                    <h3 className="text-xs font-black uppercase tracking-wider text-white">Vincular Libro EPUB</h3>
                                    <p className="text-[10px] text-gray-400">Busca en tu biblioteca local para asociarlo a {group.name}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => {
                                    setIsAttachModalOpen(false);
                                    setSearchQuery('');
                                    setSearchResults([]);
                                }}
                                className="p-1.5 text-gray-400 hover:text-white rounded-lg hover:bg-white/10 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Search Input & Role */}
                        <div className="space-y-3 shrink-0">
                            <div className="relative">
                                <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3" />
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => handleSearchBooks(e.target.value)}
                                    placeholder="Escribe el título del libro..."
                                    className="w-full pl-9 pr-4 py-2.5 glass-panel rounded-xl border border-white/10 bg-black/20 text-xs text-white focus:border-primary/50 outline-none"
                                    autoFocus
                                />
                                {searching && (
                                    <RefreshCw className="w-3.5 h-3.5 text-primary animate-spin absolute right-3 top-3" />
                                )}
                            </div>

                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Rol:</span>
                                <div className="flex gap-1.5">
                                    {(['translator', 'layout', 'editor'] as const).map((role) => (
                                        <button
                                            key={role}
                                            type="button"
                                            onClick={() => setSelectedRole(role)}
                                            className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition-all ${
                                                selectedRole === role
                                                    ? 'bg-primary text-white shadow-md shadow-primary/20'
                                                    : 'glass-panel text-gray-400 hover:text-white border border-white/5'
                                            }`}
                                        >
                                            {role === 'translator' ? 'Traductor' : role === 'layout' ? 'Maquetador' : 'Editor'}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Results List */}
                        <div className="overflow-y-auto space-y-2 flex-1 pr-1 custom-scrollbar">
                            {searchResults.length === 0 ? (
                                <div className="p-8 text-center text-gray-400 text-xs">
                                    {searchQuery.length >= 2 ? (
                                        <span>No se encontraron libros para vincular</span>
                                    ) : (
                                        <span>Escribe al menos 2 letras para buscar en el catálogo</span>
                                    )}
                                </div>
                            ) : (
                                searchResults.map((book) => (
                                    <div
                                        key={book.id}
                                        className="glass-panel rounded-xl p-2.5 border border-white/5 flex items-center justify-between gap-3 hover:border-primary/30 transition-all"
                                    >
                                        <div className="flex items-center gap-2.5 min-w-0">
                                            <div className="w-9 h-12 rounded bg-black/40 overflow-hidden shrink-0 border border-white/10">
                                                {book.cover_thumb || book.cover_low ? (
                                                    <img src={book.cover_thumb || book.cover_low} alt={book.title} className="w-full h-full object-cover" />
                                                ) : (
                                                    <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                        <BookOpen className="w-4 h-4" />
                                                    </div>
                                                )}
                                            </div>
                                            <div className="min-w-0">
                                                <h5 className="text-xs font-bold text-white truncate">{book.title}</h5>
                                                <span className="text-[10px] text-gray-400 block truncate">
                                                    {book.author || 'Autor desconocido'} {book.volume ? `• Vol. ${book.volume}` : ''}
                                                </span>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => handleAttachBook(book.id)}
                                            disabled={actionLoadingId === book.id}
                                            className="px-3 py-1.5 bg-primary hover:brightness-110 text-white rounded-lg text-[10px] font-bold shrink-0 flex items-center gap-1 active:scale-95 transition-all disabled:opacity-50"
                                        >
                                            <Plus className="w-3 h-3" />
                                            <span>{actionLoadingId === book.id ? 'Vinculando...' : 'Vincular'}</span>
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
