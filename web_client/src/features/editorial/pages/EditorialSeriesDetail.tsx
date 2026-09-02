import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    BookOpen,
    ArrowLeft,
    Save,
    Plus,
    Trash2,
    Search,
    Link2,
    Check,
    AlertCircle,
    CheckCircle2,
    ExternalLink,
    X,
    RefreshCw,
    Tag,
    GitMerge,
    Layers,
    User,
    Image,
    Sparkles,
    Loader2
} from 'lucide-react';
import { api } from '@shared/services/api';

interface SeriesDetail {
    id: string;
    series_hash?: string;
    name: string;
    series_english?: string;
    series_spanish?: string;
    slug?: string;
    author?: string;
    author_jap?: string;
    illustrator?: string;
    illustrator_jap?: string;
    description?: string;
    publisher?: string;
    book_type?: string;
    demographics?: string[];
    tags?: string[];
    cover_url?: string;
    book_count?: number;
    aliases?: Array<{ id: number; alias: string }>;
}

interface AssociatedBook {
    id: string;
    book_hash?: string;
    title: string;
    spanish_title?: string;
    volume: number | string;
    edition?: string;
    translator?: string;
    layout_by?: string;
    editor?: string;
    filepath?: string;
    cover_url?: string;
    cover_thumb?: string;
    size_mb?: string;
    language?: string;
}

export const EditorialSeriesDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [loading, setLoading] = useState(true);
    const [series, setSeries] = useState<SeriesDetail | null>(null);
    const [books, setBooks] = useState<AssociatedBook[]>([]);

    // Form State
    const [name, setName] = useState('');
    const [seriesSpanish, setSeriesSpanish] = useState('');
    const [seriesEnglish, setSeriesEnglish] = useState('');
    const [author, setAuthor] = useState('');
    const [illustrator, setIllustrator] = useState('');
    const [description, setDescription] = useState('');
    const [bookType, setBookType] = useState('Novela Ligera');
    const [demography, setDemography] = useState('Seinen');
    const [tags, setTags] = useState<string[]>([]);
    const [coverUrl, setCoverUrl] = useState('');
    const [aliases, setAliases] = useState<Array<{ id: number; alias: string }>>([]);

    // Alias Add State
    const [newAliasInput, setNewAliasInput] = useState('');
    const [addingAlias, setAddingAlias] = useState(false);

    // Save & Merge State
    const [isSaving, setIsSaving] = useState(false);
    const [toast, setToast] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);
    const [isMergeModalOpen, setIsMergeModalOpen] = useState(false);
    const [mergeSourceHash, setMergeSourceHash] = useState('');
    const [merging, setMerging] = useState(false);

    // Attach Volume State
    const [isAttachModalOpen, setIsAttachModalOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);
    const [attachingBookId, setAttachingBookId] = useState<string | null>(null);

    const showToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ text, type });
        setTimeout(() => setToast(null), 3000);
    };

    const loadData = async () => {
        if (!id) return;
        try {
            setLoading(true);
            const res = await (api as any).adminGetSeriesDetail(id);
            let seriesItem: any = null;
            let booksItem: any[] = [];

            if (res && res.success && res.series) {
                seriesItem = res.series;
                booksItem = res.series.books || [];
            } else {
                const gridRes = await api.getLibraryGrid({ query: id, limit: 1 });
                if (gridRes && gridRes.series && gridRes.series.length > 0) {
                    seriesItem =
                        gridRes.series.find((s: any) => s.id === id || s.series_hash === id || s.slug === id) ||
                        gridRes.series[0];
                    booksItem = seriesItem.books || [];
                }
            }

            if (seriesItem) {
                setSeries(seriesItem);
                setName(seriesItem.name || seriesItem.title || '');
                setSeriesSpanish(seriesItem.series_spanish || '');
                setSeriesEnglish(seriesItem.series_english || '');
                setAuthor(seriesItem.author || '');
                setIllustrator(seriesItem.illustrator || '');
                setDescription(seriesItem.description || '');
                setBookType(seriesItem.book_type || 'Novela Ligera');
                const loadedDemo =
                    Array.isArray(seriesItem.demographics) && seriesItem.demographics.length > 0
                        ? seriesItem.demographics[0]
                        : seriesItem.demography || 'Seinen';
                setDemography(loadedDemo);
                setTags(Array.isArray(seriesItem.tags) ? seriesItem.tags : []);
                setCoverUrl(seriesItem.cover_url || '');
                setAliases(seriesItem.aliases || []);
                setBooks(booksItem);
            }
        } catch (err: any) {
            console.error('Error cargando detalles de serie:', err);
            showToast('Error cargando serie: ' + (err?.message || ''), 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [id]);

    const handleSaveSeries = async (e?: React.FormEvent) => {
        if (e) e.preventDefault();
        if (!name.trim()) {
            showToast('El nombre de la serie es obligatorio', 'error');
            return;
        }

        try {
            setIsSaving(true);
            const res = await api.updateSeriesGrid(series?.id || id!, {
                name: name.trim(),
                series_spanish: seriesSpanish.trim() || undefined,
                series_english: seriesEnglish.trim() || undefined,
                author: author.trim() || undefined,
                illustrator: illustrator.trim() || undefined,
                description: description.trim() || undefined,
                book_type: bookType,
                demographics: [demography],
                tags: tags,
                cover_url: coverUrl.trim() || undefined,
            });

            if (res && res.success !== false) {
                showToast('Cambios de serie guardados con éxito', 'success');
                loadData();
            } else {
                showToast(res?.message || 'Error al guardar', 'error');
            }
        } catch (err: any) {
            console.error('Error al guardar serie:', err);
            showToast('Error al guardar: ' + (err?.message || ''), 'error');
        } finally {
            setIsSaving(false);
        }
    };

    const handleAddAlias = async () => {
        if (!newAliasInput.trim() || !id) return;
        try {
            setAddingAlias(true);
            const res = await (api as any).adminAddSeriesAlias(series?.id || id, newAliasInput.trim());
            if (res.success) {
                showToast(`Alias "${newAliasInput.trim()}" agregado`, 'success');
                setAliases((prev) => [...prev, { id: res.alias_id || Date.now(), alias: newAliasInput.trim() }]);
                setNewAliasInput('');
            } else {
                showToast(res.message || 'Error agregando alias', 'error');
            }
        } catch (err: any) {
            showToast('Error al agregar alias', 'error');
        } finally {
            setAddingAlias(false);
        }
    };

    const handleDeleteAlias = async (aliasId: number) => {
        try {
            const res = await (api as any).adminDeleteSeriesAlias(aliasId);
            if (res.success) {
                showToast('Alias eliminado', 'success');
                setAliases((prev) => prev.filter((a) => a.id !== aliasId));
            }
        } catch (err: any) {
            showToast('Error eliminando alias', 'error');
        }
    };

    const handleMergeSeries = async () => {
        if (!mergeSourceHash.trim() || !series) return;
        if (mergeSourceHash.trim() === series.id) {
            showToast('No puedes fusionar la serie consigo misma', 'error');
            return;
        }

        try {
            setMerging(true);
            const res = await (api as any).adminMergeSeries(series.id, mergeSourceHash.trim());
            if (res.success) {
                showToast('Series fusionadas exitosamente', 'success');
                setIsMergeModalOpen(false);
                setMergeSourceHash('');
                loadData();
            } else {
                showToast(res.message || 'Error en la fusión de series', 'error');
            }
        } catch (err: any) {
            showToast('Error al fusionar series', 'error');
        } finally {
            setMerging(false);
        }
    };

    const handleSearchBooksToAttach = async (q: string) => {
        setSearchQuery(q);
        if (!q.trim() || q.length < 2) {
            setSearchResults([]);
            return;
        }
        try {
            setSearching(true);
            const res = await api.getLibraryGrid({ query: q, limit: 10 });
            if (res && res.series) {
                const foundBooks: any[] = [];
                res.series.forEach((s: any) => {
                    if (s.books) {
                        s.books.forEach((b: any) => {
                            foundBooks.push({ ...b, seriesName: s.name });
                        });
                    }
                });
                setSearchResults(foundBooks);
            }
        } catch (err) {
            console.error('Error buscando libros para vincular:', err);
        } finally {
            setSearching(false);
        }
    };

    const handleAttachBook = async (bookId: string) => {
        if (!series) return;
        try {
            setAttachingBookId(bookId);
            const res = await api.updateBookGrid(bookId, { series_id: series.id });
            if (res && res.success !== false) {
                showToast('Volumen vinculado a la serie', 'success');
                setIsAttachModalOpen(false);
                loadData();
            }
        } catch (err: any) {
            showToast('Error vinculando volumen', 'error');
        } finally {
            setAttachingBookId(null);
        }
    };

    const handleUnlinkBook = async (bookId: string, bookTitle: string) => {
        if (!confirm(`¿Desvincular "${bookTitle}" de esta serie?`)) return;
        try {
            const res = await api.updateBookGrid(bookId, { series_id: null });
            if (res && res.success !== false) {
                showToast('Volumen desvinculado', 'success');
                setBooks((prev) => prev.filter((b) => b.id !== bookId));
            }
        } catch (err) {
            showToast('Error desvinculando volumen', 'error');
        }
    };

    const hashtagSlug = name
        ? '#' + name.replace(/[^a-zA-Z0-9]/g, '_').replace(/_+/g, '_')
        : '#Serie';

    if (loading) {
        return (
            <div className="py-32 flex flex-col items-center justify-center">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mb-4" />
                <p className="text-gray-400 text-xs font-mono tracking-widest uppercase">Cargando Editor de Serie...</p>
            </div>
        );
    }

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Top Navigation Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <button
                    onClick={() => navigate('/app-v2/series')}
                    className="flex items-center gap-2 px-4 py-2 rounded-2xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/5 transition-all self-start"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver al Catálogo de Series
                </button>

                <div className="flex items-center gap-2 self-end sm:self-auto">
                    <span className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/5 text-[11px] text-gray-400 font-mono">
                        ID: {series?.id || id}
                    </span>
                    <span className="px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 font-bold flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5" /> {books.length} Volúmenes Asociados
                    </span>
                </div>
            </div>

            {/* Toast Alerts */}
            {toast && (
                <div
                    className={`p-3.5 rounded-2xl flex items-center gap-2.5 text-xs font-medium ${
                        toast.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-red-500/10 text-red-300 border border-red-500/20'
                    }`}
                >
                    {toast.type === 'success' ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : (
                        <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
                    )}
                    <span>{toast.text}</span>
                </div>
            )}

            {/* Series Hero Banner */}
            <div className="bg-slate-900/60 border border-white/10 rounded-3xl p-6 shadow-2xl backdrop-blur-2xl flex flex-col md:flex-row items-center md:items-start justify-between gap-6">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
                    <div className="w-28 h-40 sm:w-32 sm:h-44 rounded-2xl bg-black/50 border border-white/10 overflow-hidden shadow-xl shrink-0 flex items-center justify-center">
                        {coverUrl ? (
                            <img src={coverUrl} alt={name} className="w-full h-full object-cover" />
                        ) : (
                            <BookOpen className="w-10 h-10 text-gray-600" />
                        )}
                    </div>

                    <div className="space-y-2">
                        <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                            <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-black uppercase bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                                {bookType}
                            </span>
                            <span className="px-2.5 py-0.5 rounded-lg text-[10px] font-mono font-bold bg-white/5 text-gray-400 border border-white/10">
                                {hashtagSlug}
                            </span>
                        </div>

                        <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">{name || 'Sin Título'}</h1>
                        {seriesSpanish && seriesSpanish !== name && (
                            <p className="text-sm text-indigo-300 font-medium">🇪🇸 {seriesSpanish}</p>
                        )}

                        <div className="text-xs text-gray-400 flex flex-wrap items-center justify-center sm:justify-start gap-4 pt-1">
                            {author && (
                                <span className="flex items-center gap-1">
                                    <User className="w-3.5 h-3.5 text-indigo-400" /> Autor: <strong className="text-gray-200">{author}</strong>
                                </span>
                            )}
                            {illustrator && (
                                <span className="flex items-center gap-1">
                                    <Sparkles className="w-3.5 h-3.5 text-purple-400" /> Ilus: <strong className="text-gray-200">{illustrator}</strong>
                                </span>
                            )}
                        </div>
                    </div>
                </div>

                {/* Top Action Buttons */}
                <div className="flex flex-wrap sm:flex-nowrap items-center gap-3 shrink-0">
                    <button
                        onClick={() => setIsAttachModalOpen(true)}
                        className="px-4 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-2 shadow-lg shadow-indigo-600/30 active:scale-95 transition-all"
                    >
                        <Plus className="w-4 h-4" /> Vincular Volumen
                    </button>
                    <button
                        onClick={() => setIsMergeModalOpen(true)}
                        className="px-4 py-2.5 rounded-2xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 text-xs font-bold flex items-center gap-2 border border-amber-500/20 transition-all active:scale-95"
                    >
                        <GitMerge className="w-4 h-4" /> Fusionar Serie
                    </button>
                </div>
            </div>

            {/* Main Editor Grid (Side by Side 2K Widescreen) */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Panel: General Info (5 cols) */}
                <form
                    onSubmit={handleSaveSeries}
                    className="lg:col-span-5 bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 shadow-2xl backdrop-blur-xl flex flex-col justify-between"
                >
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 text-sm font-bold text-white border-b border-white/10 pb-3">
                            <Layers className="w-4 h-4 text-indigo-400" /> Información General de Serie
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                Nombre Canónico (Romaji / Título Principal) <span className="text-indigo-400">*</span>
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                required
                            />
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Español
                                </label>
                                <input
                                    type="text"
                                    value={seriesSpanish}
                                    onChange={(e) => setSeriesSpanish(e.target.value)}
                                    placeholder="Traducción oficial..."
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Inglés
                                </label>
                                <input
                                    type="text"
                                    value={seriesEnglish}
                                    onChange={(e) => setSeriesEnglish(e.target.value)}
                                    placeholder="English licensed title..."
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Autor</label>
                                <input
                                    type="text"
                                    value={author}
                                    onChange={(e) => setAuthor(e.target.value)}
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Ilustrador</label>
                                <input
                                    type="text"
                                    value={illustrator}
                                    onChange={(e) => setIllustrator(e.target.value)}
                                    className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Tipo de Serie</label>
                                <select
                                    value={bookType}
                                    onChange={(e) => setBookType(e.target.value)}
                                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                >
                                    <option value="Novela Ligera">Novela Ligera</option>
                                    <option value="Web Novel">Web Novel</option>
                                    <option value="Manga">Manga</option>
                                    <option value="Novela Visual">Novela Visual</option>
                                    <option value="Libro">Libro General</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Demografía</label>
                                <select
                                    value={demography}
                                    onChange={(e) => setDemography(e.target.value)}
                                    className="w-full px-3 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                >
                                    <option value="Seinen">Seinen</option>
                                    <option value="Shounen">Shounen</option>
                                    <option value="Josei">Josei</option>
                                    <option value="Shoujo">Shoujo</option>
                                    <option value="General">General</option>
                                </select>
                            </div>
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">URL Portada Serie</label>
                            <input
                                type="text"
                                value={coverUrl}
                                onChange={(e) => setCoverUrl(e.target.value)}
                                placeholder="https://... o /api/library/covers/..."
                                className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                            />
                        </div>

                        {/* Aliases Section */}
                        <div className="pt-2 border-t border-white/5 space-y-2">
                            <div className="flex items-center justify-between text-[11px] font-bold text-gray-400 uppercase">
                                <span>Siglas / Títulos Alias (Detección Auto)</span>
                                <span>{aliases.length} Alias</span>
                            </div>

                            <div className="flex flex-wrap gap-1.5">
                                {aliases.map((al) => (
                                    <span
                                        key={al.id}
                                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-white/5 border border-white/10 text-xs text-gray-200"
                                    >
                                        <span>{al.alias}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleDeleteAlias(al.id)}
                                            className="p-0.5 text-gray-400 hover:text-red-400 transition-colors"
                                        >
                                            <X className="w-3 h-3" />
                                        </button>
                                    </span>
                                ))}
                            </div>

                            <div className="flex gap-2 pt-1">
                                <input
                                    type="text"
                                    value={newAliasInput}
                                    onChange={(e) => setNewAliasInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            handleAddAlias();
                                        }
                                    }}
                                    placeholder="Agregar nuevo alias de maquetador o traducción..."
                                    className="flex-1 px-3 py-1.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                                <button
                                    type="button"
                                    onClick={handleAddAlias}
                                    disabled={addingAlias}
                                    className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 transition-all"
                                >
                                    + Añadir
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Descripción / Sinopsis</label>
                            <textarea
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                rows={4}
                                className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 leading-relaxed"
                            />
                        </div>
                    </div>

                    <div className="pt-4 border-t border-white/10">
                        <button
                            type="submit"
                            disabled={isSaving}
                            className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-2 shadow-xl shadow-indigo-600/30 active:scale-95 transition-all disabled:opacity-50"
                        >
                            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            <span>Guardar Cambios de Serie</span>
                        </button>
                    </div>
                </form>

                {/* Right Panel: Associated Books Grid (7 cols) */}
                <div className="lg:col-span-7 bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 shadow-2xl backdrop-blur-xl">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                        <div>
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <BookOpen className="w-4 h-4 text-indigo-400" /> Libros EPUB Asociados ({books.length})
                            </h3>
                            <p className="text-xs text-gray-400">Volúmenes que pertenecen automáticamente a esta serie.</p>
                        </div>

                        <button
                            onClick={() => setIsAttachModalOpen(true)}
                            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white text-xs font-bold border border-white/10 flex items-center gap-1.5 transition-all"
                        >
                            <Plus className="w-3.5 h-3.5" /> Vincular Otro
                        </button>
                    </div>

                    {books.length === 0 ? (
                        <div className="py-20 text-center text-gray-500 text-xs">
                            No hay volúmenes vinculados a esta serie actualmente.
                        </div>
                    ) : (
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 max-h-[720px] overflow-y-auto pr-1">
                            {books.map((b) => (
                                <div
                                    key={b.id}
                                    className="p-3.5 rounded-2xl bg-slate-950/80 border border-white/10 hover:border-indigo-500/40 flex items-center justify-between gap-3 shadow-lg transition-all group"
                                >
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-12 h-16 rounded-xl bg-slate-900 border border-white/5 overflow-hidden shrink-0 flex items-center justify-center">
                                            {b.cover_url || b.cover_thumb ? (
                                                <img
                                                    src={b.cover_url || b.cover_thumb}
                                                    alt={b.title}
                                                    className="w-full h-full object-cover"
                                                />
                                            ) : (
                                                <BookOpen className="w-5 h-5 text-gray-600" />
                                            )}
                                        </div>

                                        <div className="min-w-0">
                                            <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-bold font-mono">
                                                Vol. {b.volume}
                                            </span>
                                            <h4 className="text-xs font-bold text-white truncate mt-1 group-hover:text-indigo-300 transition-colors">
                                                {b.spanish_title || b.title}
                                            </h4>
                                            <div className="text-[10px] text-gray-400 truncate mt-0.5">
                                                ✍️ {b.translator || 'Sin traductor'}
                                            </div>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => handleUnlinkBook(b.id, b.title)}
                                        className="p-2 rounded-lg bg-white/5 hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-colors"
                                        title="Desvincular volumen"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Merge Modal */}
            {isMergeModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="relative w-full max-w-md bg-slate-900 border border-white/10 rounded-3xl shadow-2xl p-6 space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <GitMerge className="w-4 h-4 text-amber-400" /> Fusionar con Otra Serie
                            </h3>
                            <button onClick={() => setIsMergeModalOpen(false)} className="p-1 text-gray-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <p className="text-xs text-gray-400 leading-relaxed">
                            Ingresa el ID o hash de la serie de origen. Todos sus volúmenes y alias se transferirán a <strong>{name}</strong> y la serie de origen será eliminada.
                        </p>

                        <input
                            type="text"
                            value={mergeSourceHash}
                            onChange={(e) => setMergeSourceHash(e.target.value)}
                            placeholder="ID / Hash de la serie a absorber..."
                            className="w-full px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                        />

                        <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
                            <button
                                onClick={() => setIsMergeModalOpen(false)}
                                className="px-4 py-2 text-xs font-bold text-gray-400 hover:text-white"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleMergeSeries}
                                disabled={merging || !mergeSourceHash.trim()}
                                className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold flex items-center gap-1.5 shadow-lg disabled:opacity-50"
                            >
                                {merging ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitMerge className="w-3.5 h-3.5" />}
                                <span>Confirmar Fusión</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Attach Book Modal */}
            {isAttachModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="relative w-full max-w-xl bg-slate-900 border border-white/10 rounded-3xl shadow-2xl p-6 space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Plus className="w-4 h-4 text-indigo-400" /> Vincular Volumen a esta Serie
                            </h3>
                            <button onClick={() => setIsAttachModalOpen(false)} className="p-1 text-gray-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="relative">
                            <Search className="w-4 h-4 text-gray-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => handleSearchBooksToAttach(e.target.value)}
                                placeholder="Buscar libro por título, tomo o nombre de archivo..."
                                className="w-full pl-10 pr-4 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        <div className="max-h-60 overflow-y-auto space-y-2 pr-1">
                            {searching ? (
                                <div className="py-8 flex justify-center">
                                    <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
                                </div>
                            ) : searchResults.length === 0 ? (
                                <div className="py-8 text-center text-xs text-gray-500">
                                    {searchQuery ? 'No se encontraron libros' : 'Escribe para buscar volúmenes'}
                                </div>
                            ) : (
                                searchResults.map((bk) => (
                                    <div
                                        key={bk.id}
                                        className="p-3 rounded-xl bg-slate-950 border border-white/5 flex items-center justify-between gap-3 text-xs"
                                    >
                                        <div className="min-w-0">
                                            <div className="font-bold text-white truncate">{bk.title}</div>
                                            <div className="text-[10px] text-gray-400">
                                                Vol. {bk.volume || 1} • Serie actual: {bk.seriesName || 'Ninguna'}
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => handleAttachBook(bk.id)}
                                            disabled={attachingBookId === bk.id}
                                            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shrink-0 transition-all"
                                        >
                                            {attachingBookId === bk.id ? 'Vinculando...' : 'Vincular'}
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
