import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
    BookOpen, ArrowLeft, Save, Plus, Trash2, Search, Link2, Check,
    AlertCircle, ExternalLink, X, RefreshCw, Tag, GitMerge, Layers, User, Image, Sparkles
} from 'lucide-react';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useTelegram } from '@shared/contexts/TelegramContext';
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
    volume: number | string;
    edition?: string;
    translator?: string;
    layout_by?: string;
    editor?: string;
    filepath?: string;
    cover_url?: string;
    size_mb?: string;
    language?: string;
}

export const SeriesDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const { settings } = useTheme();
    const { webApp } = useTelegram();

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
            const gridRes = await api.getLibraryGrid({ query: id, limit: 1 });
            let seriesItem: any = null;
            let booksItem: any[] = [];

            if (gridRes && gridRes.series && gridRes.series.length > 0) {
                seriesItem = gridRes.series.find((s: any) => s.id === id || s.series_hash === id || s.slug === id) || gridRes.series[0];
                booksItem = seriesItem.books || [];
            } else {
                const detailRes = await api.getSeriesDetails(id);
                if (detailRes) {
                    seriesItem = detailRes;
                    booksItem = detailRes.volumes || [];
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
                setCoverUrl(seriesItem.cover_url || (seriesItem.coverUrl ? (typeof seriesItem.coverUrl === 'string' ? seriesItem.coverUrl : seriesItem.coverUrl.medium) : ''));
                setAliases(seriesItem.aliases || []);
                setBooks(booksItem);
            }
        } catch (err: any) {
            console.error("Error cargando detalles de serie:", err);
            showToast("Error cargando serie: " + (err?.message || ""), "error");
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
            showToast("El nombre de la serie es obligatorio", "error");
            return;
        }

        try {
            setIsSaving(true);
            webApp?.HapticFeedback?.impactOccurred('medium');
            const res = await api.updateSeriesGrid(series?.id || id!, {
                name: name.trim(),
                series_spanish: seriesSpanish.trim() || undefined,
                series_english: seriesEnglish.trim() || undefined,
                author: author.trim() || undefined,
                illustrator: illustrator.trim() || undefined,
                description: description.trim() || undefined,
                book_type: bookType,
                cover_url: coverUrl.trim() || undefined,
            });

            if (res && res.success !== false) {
                webApp?.HapticFeedback?.notificationOccurred('success');
                showToast("Cambios de serie guardados con éxito", "success");
                loadData();
            } else {
                showToast(res?.message || "Error al guardar", "error");
            }
        } catch (err: any) {
            console.error("Error al guardar serie:", err);
            webApp?.HapticFeedback?.notificationOccurred('error');
            showToast("Error al guardar: " + (err?.message || ""), "error");
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
                showToast(`Alias "${newAliasInput.trim()}" agregado`, "success");
                setAliases(prev => [...prev, { id: res.alias_id || Date.now(), alias: newAliasInput.trim() }]);
                setNewAliasInput('');
            } else {
                showToast(res.message || "Error agregando alias", "error");
            }
        } catch (err: any) {
            showToast("Error de red al agregar alias", "error");
        } finally {
            setAddingAlias(false);
        }
    };

    const handleDeleteAlias = async (aliasId: number) => {
        try {
            const res = await (api as any).adminDeleteSeriesAlias(aliasId);
            if (res.success) {
                showToast("Alias eliminado", "success");
                setAliases(prev => prev.filter(a => a.id !== aliasId));
            }
        } catch (err: any) {
            showToast("Error eliminando alias", "error");
        }
    };

    const handleMergeSeries = async () => {
        if (!mergeSourceHash.trim() || !series) return;
        if (mergeSourceHash.trim() === series.id) {
            showToast("No puedes fusionar la serie consigo misma", "error");
            return;
        }

        try {
            setMerging(true);
            const res = await (api as any).adminMergeSeries(series.id, mergeSourceHash.trim());
            if (res.success) {
                showToast("Series fusionadas exitosamente", "success");
                setIsMergeModalOpen(false);
                setMergeSourceHash('');
                loadData();
            } else {
                showToast(res.message || "Error en la fusión de series", "error");
            }
        } catch (err: any) {
            showToast("Error al fusionar series", "error");
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
            console.error("Error buscando libros para vincular:", err);
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
                showToast("Volumen vinculado a la serie", "success");
                setIsAttachModalOpen(false);
                loadData();
            }
        } catch (err: any) {
            showToast("Error vinculando volumen", "error");
        } finally {
            setAttachingBookId(null);
        }
    };

    const handleUnlinkBook = async (bookId: string, bookTitle: string) => {
        if (!confirm(`¿Desvincular "${bookTitle}" de esta serie?`)) return;
        try {
            const res = await api.updateBookGrid(bookId, { series_id: null });
            if (res && res.success !== false) {
                showToast("Volumen desvinculado", "success");
                setBooks(prev => prev.filter(b => b.id !== bookId));
            }
        } catch (err) {
            showToast("Error desvinculando volumen", "error");
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
                <div className="animate-spin rounded-full h-10 w-10 border-t-2 border-b-2 border-indigo-500 mb-4"></div>
                <p className="text-slate-400 text-xs font-mono uppercase tracking-widest">Cargando Editor de Serie...</p>
            </div>
        );
    }

    if (!series) {
        return (
            <div className="min-h-screen bg-slate-950 p-6 flex flex-col items-center justify-center text-center">
                <AlertCircle className="w-12 h-12 text-rose-400 mb-3" />
                <h2 className="text-xl font-bold text-white mb-2">Serie No Encontrada</h2>
                <p className="text-slate-400 text-xs mb-6">No se pudieron recuperar los detalles para la serie solicitada.</p>
                <button
                    onClick={() => navigate('/admin?view=datagrid')}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold flex items-center gap-2"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Volver al Catálogo
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-6 md:p-8 space-y-6 animate-in fade-in duration-300">
            {/* Top Navigation & Info Bar */}
            <div className="flex flex-wrap items-center justify-between gap-4 max-w-7xl mx-auto">
                <button
                    onClick={() => navigate('/admin?view=datagrid')}
                    className="px-3.5 py-2 rounded-xl bg-slate-900/80 hover:bg-slate-800 border border-white/10 text-slate-300 hover:text-white text-xs font-semibold flex items-center gap-2 transition-all active:scale-95 shadow-md"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Volver al Editor de Catálogo
                </button>

                <div className="flex items-center gap-2">
                    <span className="px-3 py-1 rounded-xl bg-slate-900/90 border border-white/10 font-mono text-[11px] text-slate-400 shadow-inner">
                        ID: {series.id.slice(0, 16)}...
                    </span>
                    <span className="px-3 py-1 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-bold text-xs shadow-inner flex items-center gap-1.5">
                        <BookOpen className="w-3.5 h-3.5" />
                        {books.length} Volúmenes Asociados
                    </span>
                </div>
            </div>

            {/* Hero Card Header */}
            <div className="max-w-7xl mx-auto bg-slate-900/80 border border-white/10 rounded-2xl p-5 sm:p-6 backdrop-blur-xl shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl -z-10 pointer-events-none"></div>

                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
                    <div className="flex items-center gap-4 sm:gap-6">
                        {coverUrl ? (
                            <img
                                src={coverUrl}
                                alt={series.name}
                                className="w-20 h-28 sm:w-24 sm:h-36 object-cover rounded-xl border border-white/20 shadow-xl flex-shrink-0"
                                onError={(e) => {
                                    (e.target as any).src = 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="150" viewBox="0 0 100 150"><rect width="100" height="150" fill="%231e293b"/><text x="50%" y="50%" fill="%2364748b" dominant-baseline="middle" text-anchor="middle" font-size="12">Sin Portada</text></svg>';
                                }}
                            />
                        ) : (
                            <div className="w-20 h-28 sm:w-24 sm:h-36 rounded-xl bg-slate-800 border border-white/10 flex flex-col items-center justify-center text-slate-500 text-xs font-bold gap-2 flex-shrink-0 shadow-xl">
                                <Image className="w-6 h-6 opacity-40" />
                                Sin Portada
                            </div>
                        )}

                        <div className="space-y-2">
                            <div className="flex flex-wrap items-center gap-2">
                                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold uppercase tracking-wider">
                                    {bookType}
                                </span>
                                {series.slug && (
                                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
                                        #{series.slug}
                                    </span>
                                )}
                            </div>

                            <h1 className="text-xl sm:text-2xl md:text-3xl font-extrabold text-white tracking-tight">
                                {name || series.name}
                            </h1>

                            <p className="text-xs text-slate-400 flex items-center gap-2">
                                <User className="w-3.5 h-3.5 text-indigo-400" />
                                <span>{author || 'Autor No Asignado'}</span>
                                {illustrator && <span className="text-slate-500">• Ilus: {illustrator}</span>}
                            </p>
                        </div>
                    </div>

                    <div className="flex flex-wrap sm:flex-col items-center gap-2.5 w-full sm:w-auto">
                        <button
                            onClick={() => setIsAttachModalOpen(true)}
                            className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center justify-center gap-2 transition-all active:scale-95 shadow-lg shadow-indigo-600/20"
                        >
                            <Plus className="w-4 h-4" />
                            Vincular Volumen
                        </button>
                        <button
                            onClick={() => setIsMergeModalOpen(true)}
                            className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 text-xs font-bold flex items-center justify-center gap-2 transition-all active:scale-95"
                        >
                            <GitMerge className="w-4 h-4" />
                            Fusionar Serie
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Content: Two Columns */}
            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Column: Form and Aliases (5 cols) */}
                <div className="lg:col-span-5 space-y-6">
                    <form onSubmit={handleSaveSeries} className="bg-slate-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl shadow-xl space-y-5">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                                <Layers className="w-4 h-4 text-indigo-400" />
                                Información General de Serie
                            </h3>
                        </div>

                        {/* Nombre Canónico */}
                        <div className="space-y-1.5">
                            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                Nombre Canónico (Romaji / Título Principal) *
                            </label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full px-3.5 py-2.5 text-xs font-semibold rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                placeholder="Ej. Arifureta Shokugyou de Sekai Saikyou"
                            />
                        </div>

                        {/* Título en Español e Inglés */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    Título en Español
                                </label>
                                <input
                                    type="text"
                                    value={seriesSpanish}
                                    onChange={(e) => setSeriesSpanish(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Ej. Arifureta: De ordinario al más fuerte del mundo"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    Título en Inglés
                                </label>
                                <input
                                    type="text"
                                    value={seriesEnglish}
                                    onChange={(e) => setSeriesEnglish(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Ej. Arifureta: From Commonplace to World's Strongest"
                                />
                            </div>
                        </div>

                        {/* Autor e Ilustrador */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    Autor
                                </label>
                                <input
                                    type="text"
                                    value={author}
                                    onChange={(e) => setAuthor(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Ej. Ryo Shirakome"
                                />
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    Ilustrador
                                </label>
                                <input
                                    type="text"
                                    value={illustrator}
                                    onChange={(e) => setIllustrator(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="Ej. Takayaki"
                                />
                            </div>
                        </div>

                        {/* Tipo de Libro y Portada */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    Tipo de Serie
                                </label>
                                <select
                                    value={bookType}
                                    onChange={(e) => setBookType(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                >
                                    <option value="Novela Ligera">Novela Ligera</option>
                                    <option value="Web Novel">Web Novel</option>
                                    <option value="Novela Visual">Novela Visual</option>
                                    <option value="Manga">Manga</option>
                                </select>
                            </div>

                            <div className="space-y-1.5">
                                <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                    URL Portada Serie
                                </label>
                                <input
                                    type="text"
                                    value={coverUrl}
                                    onChange={(e) => setCoverUrl(e.target.value)}
                                    className="w-full px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors"
                                    placeholder="URL de imagen..."
                                />
                            </div>
                        </div>

                        {/* Siglas / Títulos Alias */}
                        <div className="space-y-2 pt-2 border-t border-white/10">
                            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between">
                                <span>Siglas / Títulos Alias (Detección Auto)</span>
                                <span className="text-[10px] text-slate-500 font-normal">{aliases.length} Alias</span>
                            </label>

                            <div className="flex flex-wrap gap-1.5 min-h-[44px] p-2.5 rounded-xl bg-slate-950/80 border border-white/10">
                                {aliases.length === 0 ? (
                                    <span className="text-xs text-slate-500 italic p-1">Sin alias alternativos registrados</span>
                                ) : (
                                    aliases.map(al => (
                                        <span key={al.id} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-semibold">
                                            {al.alias}
                                            <button
                                                type="button"
                                                onClick={() => handleDeleteAlias(al.id)}
                                                className="hover:text-rose-400 transition-colors ml-1"
                                                title="Eliminar alias"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </span>
                                    ))
                                )}
                            </div>

                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={newAliasInput}
                                    onChange={(e) => setNewAliasInput(e.target.value)}
                                    onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddAlias(); } }}
                                    placeholder="Agregar nuevo alias de maquetador o traducción..."
                                    className="flex-1 px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                                />
                                <button
                                    type="button"
                                    onClick={handleAddAlias}
                                    disabled={addingAlias || !newAliasInput.trim()}
                                    className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1 transition-all active:scale-95 disabled:opacity-50"
                                >
                                    <Plus className="w-3.5 h-3.5" />
                                    Añadir
                                </button>
                            </div>
                        </div>

                        {/* Descripción / Sinopsis */}
                        <div className="space-y-1.5 pt-2 border-t border-white/10">
                            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                                Descripción / Sinopsis
                            </label>
                            <textarea
                                rows={4}
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                className="w-full px-3.5 py-2.5 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                                placeholder="Reseña o sinopsis de la serie..."
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isSaving}
                            className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white text-xs font-bold shadow-lg shadow-indigo-600/25 flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50"
                        >
                            <Save className="w-4 h-4" />
                            {isSaving ? 'Guardando Cambios...' : 'Guardar Cambios de Serie'}
                        </button>
                    </form>
                </div>

                {/* Right Column: Associated Books / Volumes (7 cols) */}
                <div className="lg:col-span-7 space-y-4">
                    <div className="bg-slate-900/80 border border-white/10 rounded-2xl p-5 backdrop-blur-xl shadow-xl space-y-4">
                        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 pb-3">
                            <div>
                                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-indigo-400" />
                                    Libros EPUB Asociados ({books.length})
                                </h3>
                                <p className="text-[11px] text-slate-400 mt-0.5">
                                    Volúmenes que pertenecen automáticamente a esta serie.
                                </p>
                            </div>

                            <button
                                onClick={() => setIsAttachModalOpen(true)}
                                className="px-3 py-1.5 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95"
                            >
                                <Plus className="w-3.5 h-3.5" />
                                Vincular Otro
                            </button>
                        </div>

                        {books.length === 0 ? (
                            <div className="py-12 text-center space-y-3">
                                <BookOpen className="w-10 h-10 text-slate-600 mx-auto" />
                                <p className="text-xs text-slate-400">No hay volúmenes vinculados a esta serie actualmente.</p>
                                <button
                                    onClick={() => setIsAttachModalOpen(true)}
                                    className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold inline-flex items-center gap-2"
                                >
                                    <Plus className="w-4 h-4" />
                                    Vincular Primer Volumen
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                                {books.map((book) => (
                                    <div key={book.id} className="p-3 rounded-xl bg-slate-950/70 border border-white/10 hover:border-indigo-500/30 transition-all flex items-start gap-3 group">
                                        {book.cover_url ? (
                                            <img
                                                src={book.cover_url}
                                                alt={book.title}
                                                className="w-12 h-16 object-cover rounded-lg border border-white/10 flex-shrink-0"
                                            />
                                        ) : (
                                            <div className="w-12 h-16 rounded-lg bg-slate-900 border border-white/5 flex items-center justify-center text-slate-600 text-[9px] flex-shrink-0">
                                                No Img
                                            </div>
                                        )}

                                        <div className="flex-1 min-w-0 space-y-1">
                                            <div className="flex items-center justify-between gap-1">
                                                <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-bold">
                                                    Vol. {book.volume}
                                                </span>
                                                <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-opacity">
                                                    <button
                                                        onClick={() => handleUnlinkBook(book.id, book.title)}
                                                        className="p-1 text-slate-400 hover:text-rose-400 transition-colors"
                                                        title="Desvincular volumen"
                                                    >
                                                        <Trash2 className="w-3.5 h-3.5" />
                                                    </button>
                                                </div>
                                            </div>

                                            <h4 className="text-xs font-bold text-white truncate" title={book.title}>
                                                {book.title}
                                            </h4>

                                            <p className="text-[10px] text-slate-400 truncate">
                                                ✍️ {book.translator || 'Traductor No Reg.'}
                                            </p>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Merge Modal */}
            {isMergeModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider flex items-center gap-2">
                                <GitMerge className="w-4 h-4" />
                                Fusionar con Otra Serie
                            </h3>
                            <button onClick={() => setIsMergeModalOpen(false)} className="text-slate-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                        <p className="text-xs text-slate-300">
                            Ingresa el Hash / ID de la serie secundaria. Todos sus libros y alias se transferirán a <strong>{series.name}</strong> y la serie secundaria se borrará.
                        </p>
                        <input
                            type="text"
                            placeholder="Hash de la serie a fusionar..."
                            value={mergeSourceHash}
                            onChange={(e) => setMergeSourceHash(e.target.value)}
                            className="w-full px-3 py-2 text-xs font-mono rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-amber-500"
                        />
                        <div className="flex justify-end gap-2 pt-2">
                            <button onClick={() => setIsMergeModalOpen(false)} className="px-3 py-2 rounded-xl bg-slate-800 text-xs font-bold text-slate-300">
                                Cancelar
                            </button>
                            <button
                                onClick={handleMergeSeries}
                                disabled={merging || !mergeSourceHash.trim()}
                                className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold flex items-center gap-1.5"
                            >
                                <GitMerge className="w-4 h-4" />
                                {merging ? 'Fusionando...' : 'Confirmar Fusión'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Attach Volume Modal */}
            {isAttachModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="w-full max-w-lg bg-slate-900 border border-white/10 rounded-2xl p-6 shadow-2xl space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-2">
                                <Plus className="w-4 h-4" />
                                Vincular Volumen Existente
                            </h3>
                            <button onClick={() => setIsAttachModalOpen(false)} className="text-slate-400 hover:text-white">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="relative">
                            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                            <input
                                type="text"
                                placeholder="Buscar libro por título o nombre..."
                                value={searchQuery}
                                onChange={(e) => handleSearchBooksToAttach(e.target.value)}
                                className="w-full pl-9 pr-3 py-2.5 text-xs rounded-xl bg-slate-950 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                            />
                        </div>

                        <div className="max-h-60 overflow-y-auto space-y-2 divide-y divide-white/5">
                            {searching ? (
                                <p className="text-xs text-slate-400 text-center py-4">Buscando volúmenes...</p>
                            ) : searchResults.length === 0 ? (
                                <p className="text-xs text-slate-500 text-center py-4">Escribe un título para buscar volúmenes existentes.</p>
                            ) : (
                                searchResults.map((item) => (
                                    <div key={item.id} className="pt-2 flex items-center justify-between text-xs">
                                        <div>
                                            <p className="font-bold text-white">{item.title}</p>
                                            <p className="text-[10px] text-slate-400">Serie actual: {item.seriesName || 'Ninguna'} • Vol {item.volume}</p>
                                        </div>
                                        <button
                                            onClick={() => handleAttachBook(item.id)}
                                            disabled={attachingBookId === item.id}
                                            className="px-3 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-bold"
                                        >
                                            {attachingBookId === item.id ? 'Vinculando...' : 'Vincular'}
                                        </button>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toast && (
                <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top-3 duration-300">
                    <div className={`px-4 py-3 rounded-xl backdrop-blur-xl border text-xs sm:text-sm font-medium shadow-2xl flex items-center gap-2.5 ${
                        toast.type === 'success' ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200' : 'bg-rose-950/90 border-rose-500/40 text-rose-200'
                    }`}>
                        {toast.type === 'success' ? <Check className="w-4 h-4 text-emerald-400" /> : <AlertCircle className="w-4 h-4 text-rose-400" />}
                        <span>{toast.text}</span>
                    </div>
                </div>
            )}
        </div>
    );
};
