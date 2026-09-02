import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
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
    Loader2,
    Grid,
    List,
    Download,
    Eye,
    Calendar,
    Star,
    Building2,
    FileSpreadsheet,
    Edit3
} from 'lucide-react';
import { api } from '@shared/services/api';
import { SchedulePostModal } from '../components/SchedulePostModal';

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
    rating?: number;
    downloads?: number;
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
    page_count?: number;
    word_count?: number;
    updated_at?: string;
}

export const EditorialSeriesDetail: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();

    const [activeTab, setActiveTab] = useState<'volumes' | 'edit'>('volumes');
    const [volumeViewMode, setVolumeViewMode] = useState<'grid' | 'list'>('grid');
    const [loading, setLoading] = useState(true);
    const [series, setSeries] = useState<SeriesDetail | null>(null);
    const [books, setBooks] = useState<AssociatedBook[]>([]);

    // Form State for Admin Tab
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

    // Quick Schedule Modal
    const [scheduleBook, setScheduleBook] = useState<any | null>(null);

    const showToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ text, type });
        setTimeout(() => setToast(null), 4000);
    };

    const fetchSeriesData = async () => {
        if (!id) return;
        setLoading(true);
        try {
            const res = await api.getSeriesDetail(id);
            if (res && res.series) {
                const s = res.series;
                setSeries(s);
                setName(s.name || '');
                setSeriesSpanish(s.series_spanish || '');
                setSeriesEnglish(s.series_english || '');
                setAuthor(s.author || '');
                setIllustrator(s.illustrator || '');
                setDescription(s.description || '');
                setBookType(s.book_type || 'Novela Ligera');
                setDemography(s.demographics?.[0] || 'Seinen');
                setTags(s.tags || []);
                setCoverUrl(s.cover_url || '');
                setAliases(s.aliases || []);

                // Sort books by volume numeric
                const rawBooks = res.books || s.books || [];
                const sortedBooks = [...rawBooks].sort((a, b) => {
                    const volA = parseFloat(String(a.volume)) || 0;
                    const volB = parseFloat(String(b.volume)) || 0;
                    return volA - volB;
                });
                setBooks(sortedBooks);
            } else {
                showToast('No se encontró la serie solicitada', 'error');
            }
        } catch (err: any) {
            console.error('Error cargando detalle de serie:', err);
            showToast(err.message || 'Error de conexión', 'error');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchSeriesData();
    }, [id]);

    const handleSaveMetadata = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!series) return;
        setIsSaving(true);
        try {
            const payload = {
                name,
                series_spanish: seriesSpanish,
                series_english: seriesEnglish,
                author,
                illustrator,
                description,
                book_type: bookType,
                demographics: [demography],
                tags,
                cover_url: coverUrl,
            };

            await api.updateSeries(series.series_hash || series.id, payload);
            showToast('¡Metadatos de la serie actualizados con éxito!', 'success');
            await fetchSeriesData();
        } catch (err: any) {
            console.error('Error guardando serie:', err);
            showToast(err.message || 'Error al guardar serie', 'error');
        } finally {
            setIsSaving(false);
        }
    };

    const handleAddAlias = async () => {
        if (!newAliasInput.trim() || !series) return;
        setAddingAlias(true);
        try {
            await api.addSeriesAlias(series.series_hash || series.id, newAliasInput.trim());
            setNewAliasInput('');
            showToast('Alias agregado correctamente', 'success');
            await fetchSeriesData();
        } catch (err: any) {
            showToast(err.message || 'Error al agregar alias', 'error');
        } finally {
            setAddingAlias(false);
        }
    };

    const handleRemoveAlias = async (aliasId: number) => {
        try {
            await api.deleteSeriesAlias(aliasId);
            showToast('Alias eliminado', 'info');
            await fetchSeriesData();
        } catch (err: any) {
            showToast(err.message || 'Error al eliminar alias', 'error');
        }
    };

    const handleUnlinkBook = async (bookId: string, bookTitle: string) => {
        if (!confirm(`¿Desvincular el volumen "${bookTitle}" de esta serie?`)) return;
        try {
            await api.updateBookMetadata(bookId, { series_id: null });
            showToast('Volumen desvinculado', 'success');
            await fetchSeriesData();
        } catch (err: any) {
            showToast(err.message || 'Error al desvincular libro', 'error');
        }
    };

    const handleSearchBooksToAttach = async () => {
        if (!searchQuery.trim()) return;
        setSearching(true);
        try {
            const res = await api.searchBooks(searchQuery.trim());
            const items = res?.books || res?.results || [];
            setSearchResults(items);
        } catch (err) {
            console.error('Error buscando libros para vincular:', err);
        } finally {
            setSearching(false);
        }
    };

    const handleAttachBook = async (bookId: string) => {
        if (!series) return;
        try {
            await api.updateBookMetadata(bookId, { series_id: series.series_hash || series.id });
            showToast('Volumen vinculado con éxito', 'success');
            setIsAttachModalOpen(false);
            setSearchQuery('');
            setSearchResults([]);
            await fetchSeriesData();
        } catch (err: any) {
            showToast(err.message || 'Error vinculando volumen', 'error');
        }
    };

    const handleMergeSeries = async () => {
        if (!series || !mergeSourceHash.trim()) return;
        if (!confirm(`¿Estás seguro de fusionar la serie "${mergeSourceHash}" dentro de esta serie? Esta acción reasignará todos sus volúmenes y alias.`)) return;

        setMerging(true);
        try {
            await api.mergeSeries(series.series_hash || series.id, mergeSourceHash.trim());
            showToast('Series unificadas exitosamente', 'success');
            setIsMergeModalOpen(false);
            setMergeSourceHash('');
            await fetchSeriesData();
        } catch (err: any) {
            showToast(err.message || 'Error al unificar series', 'error');
        } finally {
            setMerging(false);
        }
    };

    const handleDirectDownload = async (e: React.MouseEvent, book: any) => {
        e.stopPropagation();
        const bookId = book.id || book.book_hash;
        const downloadUrl = `/api/bot/download_file/${bookId}`;
        showToast('Descargando archivo EPUB desde el servidor...', 'info');

        try {
            const headers: Record<string, string> = {};
            const tgData = (window as any).Telegram?.WebApp?.initData;
            if (tgData) {
                headers['X-Telegram-Init-Data'] = tgData;
            }

            const response = await fetch(downloadUrl, { headers, credentials: 'include' });
            if (!response.ok) {
                const errJson = await response.json().catch(() => ({}));
                throw new Error(errJson.detail || errJson.error || `HTTP ${response.status}`);
            }

            const blob = await response.blob();
            const blobUrl = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = blobUrl;
            const rawTitle = book.title || book.filename?.replace('.epub', '') || 'libro';
            const safeName = rawTitle.replace(/[^\w\s\-\.]/gi, '').trim() || 'libro';
            a.download = `${safeName}.epub`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(blobUrl);
            showToast('¡Descarga completada con éxito!', 'success');
        } catch (err: any) {
            console.error('Error en descarga directa:', err);
            showToast(err.message || 'Error al descargar archivo EPUB', 'error');
        }
    };

    if (loading) {
        return (
            <div className="w-full py-32 flex flex-col items-center justify-center gap-4">
                <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
                <span className="text-xs text-gray-400 font-mono">Cargando serie y volúmenes...</span>
            </div>
        );
    }

    if (!series) {
        return (
            <div className="w-full max-w-2xl mx-auto py-24 text-center space-y-4">
                <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
                <h3 className="text-xl font-bold text-white">Serie no encontrada</h3>
                <p className="text-xs text-gray-400">No se pudo encontrar la serie con identificador {id}.</p>
                <button
                    onClick={() => navigate('/app-v2/library')}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-bold transition-all"
                >
                    <ArrowLeft className="w-4 h-4" /> Volver al Catálogo
                </button>
            </div>
        );
    }

    const seriesMainTitle = series.series_english || series.name;
    const seriesHeroCover = series.cover_url || (books[0]?.cover_url) || `/api/library/covers/${series.series_hash || series.id}.jpg`;

    return (
        <div className="w-full max-w-[2200px] mx-auto space-y-6 animate-in fade-in duration-300">
            {/* Breadcrumbs */}
            <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2 text-xs text-gray-400 flex-wrap">
                    <button
                        onClick={() => navigate('/app-v2/library')}
                        className="hover:text-white transition-colors flex items-center gap-1 font-medium"
                    >
                        <Layers className="w-3.5 h-3.5 text-indigo-400" /> Catálogo Editorial
                    </button>
                    <span>›</span>
                    <span className="text-white font-bold truncate max-w-[300px]">{seriesMainTitle}</span>
                </div>

                <button
                    onClick={() => navigate('/app-v2/library')}
                    className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 transition-all flex items-center gap-1.5 text-xs font-bold active:scale-95"
                >
                    <ArrowLeft className="w-4 h-4" /> <span>Volver al Catálogo</span>
                </button>
            </div>

            {/* Toast Feedback */}
            {toast && (
                <div
                    className={`p-4 rounded-2xl flex items-center gap-3 text-xs font-bold shadow-xl animate-in fade-in duration-200 ${
                        toast.type === 'success'
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : toast.type === 'error'
                            ? 'bg-red-500/10 text-red-300 border border-red-500/20'
                            : 'bg-indigo-500/10 text-indigo-300 border border-indigo-500/20'
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

            {/* TOP HERO BANNER: Banner Resumen de la Serie */}
            <div className="relative rounded-[2.5rem] overflow-hidden border border-white/10 bg-slate-900/60 backdrop-blur-2xl shadow-2xl p-6 sm:p-8">
                {/* Backdrop Blur Glow */}
                <div
                    className="absolute inset-0 opacity-15 bg-cover bg-center filter blur-3xl scale-110 pointer-events-none"
                    style={{ backgroundImage: `url(${seriesHeroCover})` }}
                />

                <div className="relative z-10 flex flex-col md:flex-row gap-6 sm:gap-8 items-start">
                    {/* Series Hero Cover */}
                    <div className="w-36 sm:w-48 xl:w-56 shrink-0 aspect-[2/3] rounded-3xl overflow-hidden shadow-2xl border border-white/15 bg-slate-950/80 group">
                        {seriesHeroCover ? (
                            <img
                                src={seriesHeroCover}
                                alt={seriesMainTitle}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            />
                        ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                                <BookOpen className="w-10 h-10" />
                                <span className="text-[10px]">Sin Portada</span>
                            </div>
                        )}
                    </div>

                    {/* Series Summary Content */}
                    <div className="flex-1 space-y-4 min-w-0">
                        {/* Tags and Badges */}
                        <div className="flex items-center gap-2 flex-wrap">
                            <span className="px-3 py-1 rounded-xl bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 text-[11px] font-black uppercase tracking-wider">
                                {series.book_type || 'Novela Ligera'}
                            </span>
                            <span className="px-3 py-1 rounded-xl bg-purple-600/20 border border-purple-500/30 text-purple-300 text-[11px] font-black uppercase tracking-wider">
                                {series.demographics?.[0] || 'Seinen'}
                            </span>
                            {series.slug && (
                                <span className="px-3 py-1 rounded-xl bg-white/5 border border-white/10 text-gray-300 font-mono text-[11px]">
                                    #{series.slug}
                                </span>
                            )}
                        </div>

                        {/* 3 Titles Cascade */}
                        <div className="space-y-1">
                            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black text-white tracking-tight leading-tight">
                                {seriesMainTitle}
                            </h1>
                            {series.series_spanish && series.series_spanish !== seriesMainTitle && (
                                <h3 className="text-base sm:text-lg font-bold text-amber-300/90 flex items-center gap-2">
                                    <span>🇪🇸</span> {series.series_spanish}
                                </h3>
                            )}
                            {series.name && series.name !== seriesMainTitle && (
                                <h4 className="text-xs sm:text-sm text-gray-400 font-medium flex items-center gap-2">
                                    <span>🇯🇵</span> {series.name}
                                </h4>
                            )}
                        </div>

                        {/* Metadata row */}
                        <div className="flex items-center gap-5 text-xs text-gray-300 flex-wrap pt-1 font-medium">
                            <span className="flex items-center gap-1.5">
                                <User className="w-4 h-4 text-indigo-400" />
                                <span>{series.author || 'Autor desconocido'}</span>
                            </span>
                            {series.illustrator && (
                                <span className="flex items-center gap-1.5">
                                    <Sparkles className="w-4 h-4 text-purple-400" />
                                    <span>{series.illustrator}</span>
                                </span>
                            )}
                            <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
                                <BookOpen className="w-4 h-4" />
                                <span>{books.length} Volúmenes</span>
                            </span>
                        </div>

                        {/* Genre chips */}
                        {tags && tags.length > 0 && (
                            <div className="flex items-center gap-1.5 flex-wrap pt-1">
                                {tags.map((t, idx) => (
                                    <span
                                        key={idx}
                                        className="px-2.5 py-0.5 rounded-lg bg-slate-950/80 border border-white/10 text-[10px] font-black uppercase text-gray-300"
                                    >
                                        {t}
                                    </span>
                                ))}
                            </div>
                        )}

                        {/* Series Synopsis */}
                        {series.description && (
                            <p className="text-xs sm:text-sm text-gray-300/90 line-clamp-3 leading-relaxed pt-1 font-normal">
                                {series.description}
                            </p>
                        )}
                    </div>
                </div>

                {/* Tab Switcher: Volúmenes vs Editor de Metadatos */}
                <div className="flex items-center justify-between gap-4 mt-6 pt-6 border-t border-white/10 flex-wrap">
                    <div className="flex items-center gap-2 p-1 bg-slate-950/80 border border-white/10 rounded-2xl">
                        <button
                            type="button"
                            onClick={() => setActiveTab('volumes')}
                            className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                                activeTab === 'volumes'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-black'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            <BookOpen className="w-4 h-4" />
                            <span>Volúmenes ({books.length})</span>
                        </button>

                        <button
                            type="button"
                            onClick={() => setActiveTab('edit')}
                            className={`px-5 py-2.5 rounded-xl text-xs font-bold transition-all flex items-center gap-2 ${
                                activeTab === 'edit'
                                    ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30 font-black'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            <Edit3 className="w-4 h-4" />
                            <span>Editor de Metadatos & Vinculación</span>
                        </button>
                    </div>

                    {activeTab === 'volumes' && (
                        <div className="flex items-center gap-2">
                            {/* View Mode Toggle */}
                            <div className="flex items-center gap-1 p-1 bg-slate-950/80 border border-white/10 rounded-xl">
                                <button
                                    type="button"
                                    onClick={() => setVolumeViewMode('grid')}
                                    className={`p-1.5 rounded-lg transition-all ${
                                        volumeViewMode === 'grid' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
                                    }`}
                                    title="Modo Cuadrícula"
                                >
                                    <Grid className="w-4 h-4" />
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setVolumeViewMode('list')}
                                    className={`p-1.5 rounded-lg transition-all ${
                                        volumeViewMode === 'list' ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-white'
                                    }`}
                                    title="Modo Lista"
                                >
                                    <List className="w-4 h-4" />
                                </button>
                            </div>

                            <button
                                type="button"
                                onClick={() => setIsAttachModalOpen(true)}
                                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-indigo-600/30 transition-all active:scale-95"
                            >
                                <Plus className="w-4 h-4" /> <span>Vincular Tomo</span>
                            </button>
                        </div>
                    )}
                </div>
            </div>

            {/* TAB 1: VOLUMES EXPLORATION */}
            {activeTab === 'volumes' && (
                <div className="space-y-4">
                    {books.length === 0 ? (
                        <div className="py-24 text-center bg-slate-900/40 border border-white/10 rounded-3xl p-8 space-y-3">
                            <BookOpen className="w-12 h-12 text-gray-600 mx-auto" />
                            <h3 className="text-base font-bold text-white">No hay volúmenes vinculados aún</h3>
                            <p className="text-xs text-gray-400">
                                Usa el botón "Vincular Tomo" o busca libros huérfanos para asignarlos a esta serie.
                            </p>
                            <button
                                onClick={() => setIsAttachModalOpen(true)}
                                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-lg"
                            >
                                <Plus className="w-4 h-4" /> Vincular Primer Tomo
                            </button>
                        </div>
                    ) : volumeViewMode === 'grid' ? (
                        /* Grid Mode for Volumes */
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-5">
                            {books.map((b) => (
                                <div
                                    key={b.id}
                                    onClick={() => navigate(`/app-v2/book/${b.id || b.book_hash}`)}
                                    className="group relative rounded-3xl bg-slate-900/40 border border-white/10 hover:border-indigo-500/50 p-3.5 flex flex-col justify-between backdrop-blur-xl shadow-xl hover:shadow-2xl hover:-translate-y-1.5 transition-all duration-300 cursor-pointer"
                                >
                                    {/* Cover Frame */}
                                    <div className="relative aspect-[2/3] rounded-2xl overflow-hidden bg-slate-950 border border-white/5 shadow-md">
                                        {b.cover_url || b.cover_thumb ? (
                                            <img
                                                src={b.cover_url || b.cover_thumb}
                                                alt={b.title}
                                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex flex-col items-center justify-center text-gray-600 gap-2">
                                                <BookOpen className="w-8 h-8" />
                                                <span className="text-[10px]">Volumen {b.volume}</span>
                                            </div>
                                        )}

                                        {/* Volume Badge Ribbon */}
                                        <div className="absolute top-2.5 left-2.5 px-2.5 py-1 rounded-lg bg-indigo-600/90 backdrop-blur-md text-white text-[11px] font-black shadow-lg font-mono">
                                            Vol. {b.volume}
                                        </div>
                                    </div>

                                    {/* Book Info */}
                                    <div className="pt-3 space-y-1 min-w-0">
                                        <h4 className="text-xs font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                                            {b.spanish_title || b.title}
                                        </h4>
                                        <div className="flex items-center justify-between text-[10px] text-gray-400">
                                            <span className="truncate">✍️ {b.translator || 'Sin traductor'}</span>
                                            {b.size_mb && <span className="font-mono text-gray-500">{b.size_mb} MB</span>}
                                        </div>
                                    </div>

                                    {/* Card Hover Action Bar */}
                                    <div className="pt-2.5 mt-2 border-t border-white/5 flex items-center justify-between gap-1.5">
                                        <button
                                            type="button"
                                            onClick={(e) => handleDirectDownload(e, b)}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-blue-600 text-gray-300 hover:text-white transition-all"
                                            title="Descargar EPUB"
                                        >
                                            <Download className="w-3.5 h-3.5" />
                                        </button>

                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setScheduleBook(b);
                                            }}
                                            className="p-1.5 rounded-lg bg-white/5 hover:bg-indigo-600 text-gray-300 hover:text-white transition-all"
                                            title="Programar publicación"
                                        >
                                            <Sparkles className="w-3.5 h-3.5" />
                                        </button>

                                        <span className="text-[10px] font-bold text-indigo-400 group-hover:underline flex items-center gap-0.5">
                                            Ver <Eye className="w-3 h-3" />
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        /* List Mode for Volumes */
                        <div className="rounded-3xl bg-slate-900/50 border border-white/10 backdrop-blur-xl shadow-xl overflow-hidden divide-y divide-white/5">
                            {books.map((b) => (
                                <div
                                    key={b.id}
                                    onClick={() => navigate(`/app-v2/book/${b.id || b.book_hash}`)}
                                    className="p-4 sm:p-5 flex items-center justify-between gap-4 hover:bg-white/[0.03] transition-colors cursor-pointer group"
                                >
                                    <div className="flex items-center gap-4 min-w-0">
                                        <div className="w-12 h-16 rounded-xl overflow-hidden bg-slate-950 border border-white/10 shrink-0">
                                            {b.cover_url || b.cover_thumb ? (
                                                <img src={b.cover_url || b.cover_thumb} alt={b.title} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center text-gray-600">
                                                    <BookOpen className="w-4 h-4" />
                                                </div>
                                            )}
                                        </div>

                                        <div className="min-w-0 space-y-1">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-mono text-xs font-black">
                                                    Volumen {b.volume}
                                                </span>
                                                <h4 className="text-sm font-bold text-white truncate group-hover:text-indigo-300 transition-colors">
                                                    {b.spanish_title || b.title}
                                                </h4>
                                            </div>
                                            <div className="text-xs text-gray-400 flex items-center gap-3">
                                                <span>✍️ {b.translator || 'Sin traductor'}</span>
                                                {b.layout_by && <span>📓 #{b.layout_by}</span>}
                                                {b.size_mb && <span className="font-mono">💾 {b.size_mb} MB</span>}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 shrink-0">
                                        <button
                                            type="button"
                                            onClick={(e) => handleDirectDownload(e, b)}
                                            className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-blue-600 text-gray-300 hover:text-white text-xs font-bold flex items-center gap-1.5 transition-all"
                                        >
                                            <Download className="w-3.5 h-3.5" />
                                            <span className="hidden sm:inline">Descargar</span>
                                        </button>

                                        <button
                                            type="button"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                navigate(`/app-v2/book/${b.id || b.book_hash}`);
                                            }}
                                            className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black flex items-center gap-1.5 transition-all shadow-lg"
                                        >
                                            <Eye className="w-3.5 h-3.5" />
                                            <span>Detalles</span>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* TAB 2: METADATA & LINKING EDITOR (Admin tools) */}
            {activeTab === 'edit' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    {/* Left Form: Series Metadata (6 cols) */}
                    <form
                        onSubmit={handleSaveMetadata}
                        className="lg:col-span-6 bg-slate-900/50 border border-white/10 rounded-3xl p-6 sm:p-7 space-y-5 backdrop-blur-xl shadow-xl"
                    >
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <FileSpreadsheet className="w-4 h-4 text-indigo-400" /> Metadatos Principales de la Serie
                            </h3>
                            <button
                                type="button"
                                onClick={() => setIsMergeModalOpen(true)}
                                className="px-3 py-1.5 rounded-xl bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 text-xs font-bold border border-purple-500/30 flex items-center gap-1.5 transition-all"
                            >
                                <GitMerge className="w-3.5 h-3.5" /> Fusionar Serie
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Inglés (Oficial Internacional)
                                </label>
                                <input
                                    type="text"
                                    value={seriesEnglish}
                                    onChange={(e) => setSeriesEnglish(e.target.value)}
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Español
                                </label>
                                <input
                                    type="text"
                                    value={seriesSpanish}
                                    onChange={(e) => setSeriesSpanish(e.target.value)}
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold text-amber-300"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">
                                    Título en Japonés / Romaji
                                </label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Autor</label>
                                    <input
                                        type="text"
                                        value={author}
                                        onChange={(e) => setAuthor(e.target.value)}
                                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Ilustrador</label>
                                    <input
                                        type="text"
                                        value={illustrator}
                                        onChange={(e) => setIllustrator(e.target.value)}
                                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Tipo de Obra</label>
                                    <select
                                        value={bookType}
                                        onChange={(e) => setBookType(e.target.value)}
                                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
                                    >
                                        <option value="Novela Ligera">Novela Ligera</option>
                                        <option value="Web Novel">Web Novel</option>
                                        <option value="Manga">Manga</option>
                                        <option value="Novela Visual">Novela Visual</option>
                                        <option value="Libro General">Libro General</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Demografía</label>
                                    <select
                                        value={demography}
                                        onChange={(e) => setDemography(e.target.value)}
                                        className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 font-bold"
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
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">URL Portada</label>
                                <input
                                    type="text"
                                    value={coverUrl}
                                    onChange={(e) => setCoverUrl(e.target.value)}
                                    placeholder="https://... o /api/library/covers/..."
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono"
                                />
                            </div>

                            <div>
                                <label className="block text-[11px] font-bold text-gray-400 uppercase mb-1">Sinopsis de la Serie</label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={4}
                                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white leading-relaxed"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isSaving}
                            className="w-full py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 shadow-xl shadow-indigo-600/30 transition-all active:scale-95 disabled:opacity-50"
                        >
                            {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                            <span>Guardar Metadatos</span>
                        </button>
                    </form>

                    {/* Right Column: Aliases + Volume Linking (6 cols) */}
                    <div className="lg:col-span-6 space-y-6">
                        {/* Aliases Card */}
                        <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between border-b border-white/10 pb-3">
                                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                    <Tag className="w-4 h-4 text-cyan-400" /> Siglas y Títulos Alias ({aliases.length})
                                </h3>
                            </div>

                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={newAliasInput}
                                    onChange={(e) => setNewAliasInput(e.target.value)}
                                    placeholder="Ej. Toaru Majutsu no Index, Index..."
                                    className="flex-1 px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white"
                                />
                                <button
                                    type="button"
                                    onClick={handleAddAlias}
                                    disabled={addingAlias}
                                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md"
                                >
                                    + Añadir
                                </button>
                            </div>

                            <div className="flex flex-wrap gap-2 pt-2">
                                {aliases.map((al) => (
                                    <span
                                        key={al.id}
                                        className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl bg-white/5 border border-white/10 text-xs text-gray-200"
                                    >
                                        <span>{al.alias}</span>
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveAlias(al.id)}
                                            className="text-gray-500 hover:text-red-400 transition-colors"
                                        >
                                            <X className="w-3.5 h-3.5" />
                                        </button>
                                    </span>
                                ))}
                            </div>
                        </div>

                        {/* Linked Books Management Card */}
                        <div className="bg-slate-900/50 border border-white/10 rounded-3xl p-6 space-y-4 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between border-b border-white/10 pb-3">
                                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                    <BookOpen className="w-4 h-4 text-indigo-400" /> Gestión de Volúmenes Vinculados ({books.length})
                                </h3>
                                <button
                                    type="button"
                                    onClick={() => setIsAttachModalOpen(true)}
                                    className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5 shadow-md"
                                >
                                    <Plus className="w-3.5 h-3.5" /> Vincular Tomo
                                </button>
                            </div>

                            <div className="space-y-2 max-h-[400px] overflow-y-auto pr-1">
                                {books.map((b) => (
                                    <div
                                        key={b.id}
                                        className="p-3 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between gap-3 text-xs"
                                    >
                                        <div className="flex items-center gap-3 min-w-0">
                                            <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-300 font-mono font-bold shrink-0">
                                                Vol. {b.volume}
                                            </span>
                                            <span className="text-white truncate font-medium">{b.spanish_title || b.title}</span>
                                        </div>

                                        <button
                                            type="button"
                                            onClick={() => handleUnlinkBook(b.id, b.title)}
                                            className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors shrink-0"
                                            title="Desvincular volumen"
                                        >
                                            <Trash2 className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Merge Modal */}
            {isMergeModalOpen && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <GitMerge className="w-4 h-4 text-purple-400" /> Fusionar con Otra Serie
                            </h3>
                            <button onClick={() => setIsMergeModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                        <p className="text-xs text-gray-400">
                            Introduce el hash o identificador de la serie duplicada que deseas absorber dentro de esta serie principal.
                        </p>
                        <input
                            type="text"
                            value={mergeSourceHash}
                            onChange={(e) => setMergeSourceHash(e.target.value)}
                            placeholder="series_hash_de_la_serie_duplicada"
                            className="w-full px-3.5 py-2.5 bg-slate-950 border border-white/10 rounded-xl text-xs text-white font-mono"
                        />
                        <div className="flex justify-end gap-2 pt-2">
                            <button
                                onClick={() => setIsMergeModalOpen(false)}
                                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-xs font-bold"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleMergeSeries}
                                disabled={merging || !mergeSourceHash.trim()}
                                className="px-5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold shadow-lg disabled:opacity-50"
                            >
                                {merging ? 'Fusionando...' : 'Confirmar Fusión'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Attach Volume Modal */}
            {isAttachModalOpen && (
                <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-white/10 rounded-3xl p-6 max-w-xl w-full space-y-4 shadow-2xl">
                        <div className="flex items-center justify-between border-b border-white/10 pb-3">
                            <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                <Link2 className="w-4 h-4 text-indigo-400" /> Vincular Libro EPUB a la Serie
                            </h3>
                            <button onClick={() => setIsAttachModalOpen(false)} className="text-gray-400 hover:text-white">
                                <X className="w-4 h-4" />
                            </button>
                        </div>

                        <div className="flex gap-2">
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && handleSearchBooksToAttach()}
                                placeholder="Buscar libro por título o hash..."
                                className="flex-1 px-3.5 py-2 bg-slate-950 border border-white/10 rounded-xl text-xs text-white"
                            />
                            <button
                                onClick={handleSearchBooksToAttach}
                                disabled={searching}
                                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shadow-md"
                            >
                                {searching ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                            </button>
                        </div>

                        <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                            {searchResults.map((sb) => (
                                <div
                                    key={sb.id}
                                    className="p-3 rounded-2xl bg-slate-950/70 border border-white/5 flex items-center justify-between gap-3 text-xs"
                                >
                                    <div className="min-w-0">
                                        <div className="font-bold text-white truncate">{sb.title}</div>
                                        <div className="text-[10px] text-gray-400">Vol. {sb.volume || '—'} • {sb.author || 'Sin autor'}</div>
                                    </div>
                                    <button
                                        onClick={() => handleAttachBook(sb.id)}
                                        className="px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold shrink-0"
                                    >
                                        Vincular
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Schedule Modal */}
            {scheduleBook && (
                <SchedulePostModal
                    isOpen={!!scheduleBook}
                    onClose={() => setScheduleBook(null)}
                    book={scheduleBook}
                    onSuccess={() => {
                        setScheduleBook(null);
                        fetchSeries();
                    }}
                />
            )}
        </div>
    );
};
