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
    Edit3,
    ChevronDown,
    ChevronUp,
    Copy,
    AlertTriangle
} from 'lucide-react';
import { api } from '@shared/services/api';
import { SchedulePostModal } from '../components/SchedulePostModal';
import { SeriesMergeModal } from '../components/SeriesMergeModal';
import { SeriesAttachModal } from '../components/SeriesAttachModal';
import { SeriesEditTab } from '../components/SeriesEditTab';
import { EpubEditModal } from '../components/EpubEditModal';
import { SeriesVolumesTab } from '../components/SeriesVolumesTab';

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
    has_bad_metadata?: boolean;
    bad_metadata_count?: number;
    good_metadata_count?: number;
}

interface AssociatedBook {
    id: string;
    book_hash?: string;
    title: string;
    spanish_title?: string;
    volume: number | string;
    edition?: string;
    color_mode?: string;
    is_uncensored?: boolean;
    translator?: string;
    layout_by?: string;
    editor?: string;
    publisher?: string;
    filepath?: string;
    filename?: string;
    cover_url?: string;
    cover_thumb?: string;
    size_mb?: string;
    language?: string;
    page_count?: number;
    word_count?: number;
    updated_at?: string;
    has_bad_metadata?: boolean;
    metadata_issues?: string[];
    metadata_issue?: string;
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

    // EPUB Edit & Audit State
    const [selectedBookForEdit, setSelectedBookForEdit] = useState<any | null>(null);
    const [copiedBookId, setCopiedBookId] = useState<string | null>(null);
    const [syncingBookId, setSyncingBookId] = useState<string | null>(null);
    const [isSyncingAll, setIsSyncingAll] = useState(false);

    // Synopsis Expand State
    const [isSynopsisExpanded, setIsSynopsisExpanded] = useState(false);

    const renderFormattedText = (text: string): React.ReactNode => {
        const tokens = text.split(/(<(?:b|strong|i|em)>.*?<\/(?:b|strong|i|em)>)/gi);
        return tokens.map((token, i) => {
            const bMatch = token.match(/^<(?:b|strong)>(.*?)<\/(?:b|strong)>$/i);
            if (bMatch) {
                return (
                    <strong key={i} className="font-bold text-white">
                        {bMatch[1]}
                    </strong>
                );
            }
            const iMatch = token.match(/^<(?:i|em)>(.*?)<\/(?:i|em)>$/i);
            if (iMatch) {
                return (
                    <em key={i} className="italic text-gray-200">
                        {iMatch[1]}
                    </em>
                );
            }
            const cleanText = token.replace(/<[^>]+>/g, '');
            return cleanText;
        });
    };

    const formatSynopsis = (desc?: string, expanded: boolean = false) => {
        if (!desc) return null;
        const clean = desc
            .replace(/&lt;/g, '<')
            .replace(/&gt;/g, '>')
            .replace(/&amp;/g, '&')
            .replace(/<br\s*\/?>/gi, '\n')
            .replace(/<\/p>/gi, '\n\n')
            .replace(/<p[^>]*>/gi, '');

        const paragraphs = clean
            .split(/\n\s*\n|\n/)
            .map((p) => p.trim())
            .filter(Boolean);

        const filteredParagraphs = paragraphs.filter((p) => {
            const stripped = p.replace(/<[^>]+>/g, '').trim().toUpperCase();
            return !/^(?:AUTOR|AUTORA|TRADUCCI[OÓ]N|TRADUCTOR|CORRECCI[OÓ]N|CORRECTOR|MAQUETACI[OÓ]N|MAQUETADOR)\s*:/i.test(stripped);
        });

        const finalParas = filteredParagraphs.length > 0 ? filteredParagraphs : paragraphs;

        if (finalParas.length === 0) return null;

        const isLong = finalParas.length > 1 || clean.length > 200;

        return (
            <div className="space-y-2 pt-1">
                <div
                    className={`space-y-2 text-xs sm:text-sm text-gray-300/90 leading-relaxed font-normal ${
                        !expanded && isLong ? 'line-clamp-3' : ''
                    }`}
                >
                    {finalParas.map((para, idx) => (
                        <p key={idx}>{renderFormattedText(para)}</p>
                    ))}
                </div>

                {isLong && (
                    <button
                        type="button"
                        onClick={() => setIsSynopsisExpanded(!isSynopsisExpanded)}
                        className="text-xs font-bold text-indigo-400 hover:text-indigo-300 inline-flex items-center gap-1 mt-1 transition-colors cursor-pointer"
                    >
                        <span>{expanded ? 'Mostrar menos' : 'Leer sinopsis completa'}</span>
                        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                )}
            </div>
        );
    };

    const showToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
        setToast({ text, type });
        setTimeout(() => setToast(null), 4000);
    };

    const handleCopyFilepath = (e: React.MouseEvent, book: AssociatedBook) => {
        e.stopPropagation();
        if (!book.filepath) {
            showToast('Ruta de archivo no disponible para este tomo', 'error');
            return;
        }
        navigator.clipboard.writeText(book.filepath);
        setCopiedBookId(String(book.id));
        showToast('Ruta absoluta del EPUB copiada al portapapeles', 'success');
        setTimeout(() => setCopiedBookId(null), 2500);
    };

    const handleSyncSingleBook = async (e: React.MouseEvent, book: AssociatedBook) => {
        e.stopPropagation();
        const bId = String(book.id);
        setSyncingBookId(bId);
        try {
            const res = await api.adminSyncBooks({ book_ids: [Number(bId)] });
            if (res && res.success) {
                showToast(`EPUB re-escaneado desde archivo físico OPF con éxito`, 'success');
                fetchSeriesData();
            } else {
                showToast(res?.error || 'Error al re-escanear EPUB', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al sincronizar libro', 'error');
        } finally {
            setSyncingBookId(null);
        }
    };

    const handleSyncAllObserved = async () => {
        const observedIds = books.filter(b => b.has_bad_metadata).map(b => Number(b.id));
        if (observedIds.length === 0) return;
        setIsSyncingAll(true);
        try {
            const res = await api.adminSyncBooks({ book_ids: observedIds, series_id: series?.id });
            if (res && res.success) {
                showToast(`Sincronizados ${res.synced || observedIds.length} tomos desde sus archivos OPF`, 'success');
                fetchSeriesData();
            } else {
                showToast(res?.error || 'Error al sincronizar tomos observados', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al sincronizar tomos', 'error');
        } finally {
            setIsSyncingAll(false);
        }
    };

    const checkIsColor = (b: AssociatedBook) => {
        return (
            b.color_mode === 'color' ||
            Boolean(b.edition && b.edition.toLowerCase().includes('color')) ||
            Boolean(b.filename && b.filename.toLowerCase().includes('[color]')) ||
            Boolean(b.title && b.title.toLowerCase().includes('[color]'))
        );
    };

    const checkIsUncensored = (b: AssociatedBook) => {
        return (
            Boolean(b.is_uncensored) ||
            Boolean(b.edition && (b.edition.toLowerCase().includes('s/c') || b.edition.toLowerCase().includes('sin censura'))) ||
            Boolean(b.filename && (b.filename.toLowerCase().includes('[s/c]') || b.filename.toLowerCase().includes('sin censura')))
        );
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

                // Deduplicate and sort books by volume numeric
                const rawBooks: AssociatedBook[] = res.books || s.books || [];
                const uniqueMap = new Map<string, AssociatedBook>();
                rawBooks.forEach((b: AssociatedBook) => {
                    const key = b.id || b.book_hash;
                    if (key && !uniqueMap.has(key)) {
                        uniqueMap.set(key, b);
                    }
                });
                const sortedBooks = Array.from(uniqueMap.values()).sort((a, b) => {
                    const volA = parseFloat(String(a.volume)) || 0;
                    const volB = parseFloat(String(b.volume)) || 0;
                    if (volA !== volB) return volA - volB;
                    const isColorA = (a.color_mode === 'color' || (a.edition && a.edition.toLowerCase().includes('color')) || (a.filename && a.filename.toLowerCase().includes('[color]')));
                    const isColorB = (b.color_mode === 'color' || (b.edition && b.edition.toLowerCase().includes('color')) || (b.filename && b.filename.toLowerCase().includes('[color]')));
                    return (isColorA ? 1 : 0) - (isColorB ? 1 : 0);
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

    const seriesMainTitle = (series.series_english || series.name || '').replace(/[\s\:\-\–\—\.]+$/, '').trim();
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
                            {series.series_spanish && series.series_spanish.replace(/[\s\:\-\–\—\.]+$/, '').trim() !== seriesMainTitle && (
                                <h3 className="text-base sm:text-lg font-bold text-amber-300/90 flex items-center gap-2">
                                    <span>🇪🇸</span> {series.series_spanish.replace(/[\s\:\-\–\—\.]+$/, '').trim()}
                                </h3>
                            )}
                            {series.name && series.name.replace(/[\s\:\-\–\—\.]+$/, '').trim() !== seriesMainTitle && (
                                <h4 className="text-xs sm:text-sm text-gray-400 font-medium flex items-center gap-2">
                                    <span>🇯🇵</span> {series.name.replace(/[\s\:\-\–\—\.]+$/, '').trim()}
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
                        {series.description && formatSynopsis(series.description, isSynopsisExpanded)}
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
                <SeriesVolumesTab
                    books={books}
                    volumeViewMode={volumeViewMode}
                    onOpenAttachModal={() => setIsAttachModalOpen(true)}
                    onSyncAllObserved={handleSyncAllObserved}
                    isSyncingAll={isSyncingAll}
                    onCopyFilepath={handleCopyFilepath}
                    copiedBookId={copiedBookId}
                    onSyncSingleBook={handleSyncSingleBook}
                    syncingBookId={syncingBookId}
                    onEditBook={(b) => setSelectedBookForEdit(b)}
                    onScheduleBook={(b) => setScheduleBook(b)}
                    onDirectDownload={handleDirectDownload}
                    onNavigateBook={(bId) => navigate(`/app-v2/book/${bId}`)}
                />
            )}

            {/* TAB 2: METADATA & LINKING EDITOR (Admin tools) */}
            {activeTab === 'edit' && (
                <SeriesEditTab
                    seriesEnglish={seriesEnglish}
                    setSeriesEnglish={setSeriesEnglish}
                    seriesSpanish={seriesSpanish}
                    setSeriesSpanish={setSeriesSpanish}
                    name={name}
                    setName={setName}
                    author={author}
                    setAuthor={setAuthor}
                    illustrator={illustrator}
                    setIllustrator={setIllustrator}
                    bookType={bookType}
                    setBookType={setBookType}
                    demography={demography}
                    setDemography={setDemography}
                    coverUrl={coverUrl}
                    setCoverUrl={setCoverUrl}
                    description={description}
                    setDescription={setDescription}
                    isSaving={isSaving}
                    onSaveMetadata={handleSaveMetadata}
                    onOpenMergeModal={() => setIsMergeModalOpen(true)}
                    aliases={aliases}
                    newAliasInput={newAliasInput}
                    setNewAliasInput={setNewAliasInput}
                    addingAlias={addingAlias}
                    onAddAlias={handleAddAlias}
                    onRemoveAlias={handleRemoveAlias}
                    books={books}
                    onOpenAttachModal={() => setIsAttachModalOpen(true)}
                    onUnlinkBook={handleUnlinkBook}
                />
            )}

            {/* Merge Modal */}
            <SeriesMergeModal
                isOpen={isMergeModalOpen}
                onClose={() => setIsMergeModalOpen(false)}
                mergeSourceHash={mergeSourceHash}
                setMergeSourceHash={setMergeSourceHash}
                onConfirmMerge={handleMergeSeries}
                merging={merging}
            />

            {/* Attach Volume Modal */}
            <SeriesAttachModal
                isOpen={isAttachModalOpen}
                onClose={() => setIsAttachModalOpen(false)}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
                onSearch={handleSearchBooksToAttach}
                searching={searching}
                searchResults={searchResults}
                onAttach={handleAttachBook}
            />

            {/* Schedule Modal */}
            {scheduleBook && (
                <SchedulePostModal
                    isOpen={!!scheduleBook}
                    onClose={() => setScheduleBook(null)}
                    book={scheduleBook}
                    onSuccess={() => {
                        setScheduleBook(null);
                        fetchSeriesData();
                    }}
                />
            )}

            {/* EPUB Edit Modal (Full 2-Column Series-Style Editor) */}
            {selectedBookForEdit && (
                <EpubEditModal
                    isOpen={!!selectedBookForEdit}
                    book={selectedBookForEdit}
                    onClose={() => setSelectedBookForEdit(null)}
                    onSaveSuccess={() => {
                        setSelectedBookForEdit(null);
                        fetchSeriesData();
                    }}
                />
            )}
        </div>
    );
};
