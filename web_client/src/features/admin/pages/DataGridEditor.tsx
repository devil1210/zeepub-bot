import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    Filter,
    Save,
    RotateCcw,
    Sparkles,
    ChevronDown,
    ChevronRight,
    Copy,
    Check,
    AlertCircle,
    Database,
    BookOpen,
    Layers,
    FileText,
    Hash,
    RefreshCw,
    ExternalLink,
    X,
    CheckCircle2,
    SlidersHorizontal,
    Table,
    Tag,
    GitMerge,
    Plus,
    Trash2,
} from 'lucide-react';
import { api } from '@shared/services/api';
import { useTheme } from '@shared/contexts/ThemeContext';
import { useNavigation } from '@shared/contexts/NavigationContext';
import { useTelegram } from '@shared/contexts/TelegramContext';

interface BookGridItem {
    id: string;
    book_hash: string;
    series_id: string;
    title: string;
    volume: number | string;
    edition: string;
    translator: string;
    layout_by: string;
    filename: string;
    file_size: number;
    size_mb: string;
    filepath: string;
    cover_url: string;
    language: string;
    updated_at: string | null;
}

interface SeriesGridItem {
    id: string;
    series_hash: string;
    name: string;
    series_english: string;
    series_spanish: string;
    slug: string;
    author: string;
    author_jap: string;
    illustrator: string;
    illustrator_jap: string;
    description: string;
    publisher: string;
    book_type: string;
    demographics: string[];
    tags: string[];
    aliases?: Array<{ id: number; alias: string }>;
    cover_url: string;
    book_count: number;
    books: BookGridItem[];
    updated_at: string | null;
}

export const DataGridEditor: React.FC = () => {
    const navigate = useNavigate();
    const { settings } = useTheme();
    const { webApp } = useTelegram();
    const { setContextType, setCustomActions, setVisible } = useNavigation();

    // Data State
    const [seriesList, setSeriesList] = useState<SeriesGridItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [totalSeries, setTotalSeries] = useState(0);
    const [totalBooks, setTotalBooks] = useState(0);
    const [page, setPage] = useState(1);
    const [pages, setPages] = useState(1);
    const [limit, setLimit] = useState(25);

    // Filters
    const [query, setQuery] = useState('');
    const [debouncedQuery, setDebouncedQuery] = useState('');
    const [missingFilter, setMissingFilter] = useState('all');
    const [bookTypeFilter, setBookTypeFilter] = useState('');
    const [sortBy, setSortBy] = useState('name_asc');

    // UI State
    const [expandedSeries, setExpandedSeries] = useState<Set<string>>(new Set());
    const [copiedHash, setCopiedHash] = useState<string | null>(null);
    const [toastMessage, setToastMessage] = useState<{ text: string; type: 'success' | 'error' | 'info' } | null>(null);

    // Dirty / Modified Tracking: map of id -> modified object
    const [modifiedSeries, setModifiedSeries] = useState<{ [seriesId: string]: Partial<SeriesGridItem> }>({});
    const [modifiedBooks, setModifiedBooks] = useState<{ [bookId: string]: Partial<BookGridItem> }>({});
    const [saving, setSaving] = useState(false);

    // Alias & Fusion Modal State
    const [selectedSeriesForAlias, setSelectedSeriesForAlias] = useState<SeriesGridItem | null>(null);
    const [newAliasInput, setNewAliasInput] = useState('');
    const [addingAlias, setAddingAlias] = useState(false);
    const [mergeSourceHash, setMergeSourceHash] = useState('');
    const [mergingSeries, setMergingSeries] = useState(false);

    const handleAddAlias = async () => {
        if (!selectedSeriesForAlias || !newAliasInput.trim()) return;
        setAddingAlias(true);
        try {
            const res = await (api as any).adminAddSeriesAlias(selectedSeriesForAlias.id, newAliasInput.trim());
            if (res.success) {
                setToastMessage({ text: `Alias "${newAliasInput.trim()}" agregado exitosamente`, type: 'success' });
                const newAliasObj = { id: res.alias_id || Date.now(), alias: newAliasInput.trim() };
                setSelectedSeriesForAlias(prev => (prev ? { ...prev, aliases: [...(prev.aliases || []), newAliasObj] } : null));
                setSeriesList(prev => prev.map(s => s.id === selectedSeriesForAlias.id ? { ...s, aliases: [...(s.aliases || []), newAliasObj] } : s));
                setNewAliasInput('');
            } else {
                setToastMessage({ text: res.message || 'Error agregando alias', type: 'error' });
            }
        } catch (err: any) {
            setToastMessage({ text: err.message || 'Error de conexión', type: 'error' });
        } finally {
            setAddingAlias(false);
        }
    };

    const handleDeleteAlias = async (aliasId: number) => {
        if (!selectedSeriesForAlias) return;
        try {
            const res = await (api as any).adminDeleteSeriesAlias(aliasId);
            if (res.success) {
                setToastMessage({ text: 'Alias eliminado exitosamente', type: 'success' });
                setSelectedSeriesForAlias(prev => (prev ? { ...prev, aliases: (prev.aliases || []).filter(a => a.id !== aliasId) } : null));
                setSeriesList(prev => prev.map(s => s.id === selectedSeriesForAlias.id ? { ...s, aliases: (s.aliases || []).filter(a => a.id !== aliasId) } : s));
            }
        } catch (err: any) {
            setToastMessage({ text: 'Error eliminando alias', type: 'error' });
        }
    };

    const handleMergeSeriesInModal = async () => {
        if (!selectedSeriesForAlias || !mergeSourceHash.trim()) return;
        if (selectedSeriesForAlias.id === mergeSourceHash.trim()) {
            setToastMessage({ text: 'No puedes fusionar una serie consigo misma', type: 'error' });
            return;
        }
        if (!confirm(`¿Estás seguro de fusionar la serie secundaria dentro de "${selectedSeriesForAlias.name}"?\nTodos los volúmenes pasarán a esta serie y la otra serie será eliminada.`)) {
            return;
        }
        setMergingSeries(true);
        try {
            const res = await (api as any).adminMergeSeries(selectedSeriesForAlias.id, mergeSourceHash.trim());
            if (res.success) {
                setToastMessage({ text: 'Series fusionadas con éxito', type: 'success' });
                setMergeSourceHash('');
                setSelectedSeriesForAlias(null);
                fetchData();
            } else {
                setToastMessage({ text: res.message || 'Error en fusión', type: 'error' });
            }
        } catch (err: any) {
            setToastMessage({ text: 'Error fusionando series', type: 'error' });
        } finally {
            setMergingSeries(false);
        }
    };

    // Debounce query
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedQuery(query);
            setPage(1);
        }, 400);
        return () => clearTimeout(timer);
    }, [query]);

    // Navigation setup
    useEffect(() => {
        setContextType('admin');
        setVisible(true);
        setCustomActions({
            title: 'Editor Data Grid',
            buttons: []
        });
    }, [setContextType, setVisible, setCustomActions]);

    const showToast = (text: string, type: 'success' | 'error' | 'info' = 'success') => {
        setToastMessage({ text, type });
        setTimeout(() => setToastMessage(null), 3500);
    };

    // Load Data
    const loadGridData = useCallback(async (showIndicator = true) => {
        if (showIndicator) setLoading(true);
        else setRefreshing(true);

        try {
            const res = await api.getLibraryGrid({
                query: debouncedQuery,
                missing_filter: missingFilter,
                book_type: bookTypeFilter,
                page,
                limit,
                sort_by: sortBy,
            });

            if (res.success) {
                setSeriesList(res.series || []);
                setTotalSeries(res.total_series || 0);
                setTotalBooks(res.total_books || 0);
                setPages(res.pages || 1);
            } else {
                showToast(res.message || 'Error al cargar datos del catálogo', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error conectando con el servidor', 'error');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, [debouncedQuery, missingFilter, bookTypeFilter, page, limit, sortBy]);

    useEffect(() => {
        loadGridData();
    }, [loadGridData]);

    // Expand / Collapse
    const toggleExpand = (seriesId: string) => {
        webApp?.HapticFeedback?.impactOccurred('light');
        setExpandedSeries(prev => {
            const next = new Set(prev);
            if (next.has(seriesId)) next.delete(seriesId);
            else next.add(seriesId);
            return next;
        });
    };

    const expandAll = () => {
        webApp?.HapticFeedback?.impactOccurred('medium');
        setExpandedSeries(new Set(seriesList.map(s => s.id)));
    };

    const collapseAll = () => {
        webApp?.HapticFeedback?.impactOccurred('medium');
        setExpandedSeries(new Set());
    };

    // Copy to clipboard helper
    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopiedHash(id);
        webApp?.HapticFeedback?.notificationOccurred('success');
        setTimeout(() => setCopiedHash(null), 2000);
    };

    // Series change handler
    const handleSeriesChange = (seriesId: string, field: keyof SeriesGridItem, value: any) => {
        setModifiedSeries(prev => {
            const current = prev[seriesId] || {};
            return {
                ...prev,
                [seriesId]: {
                    ...current,
                    id: seriesId,
                    [field]: value
                }
            };
        });
    };

    // Book change handler
    const handleBookChange = (bookId: string, field: keyof BookGridItem, value: any) => {
        setModifiedBooks(prev => {
            const current = prev[bookId] || {};
            return {
                ...prev,
                [bookId]: {
                    ...current,
                    id: bookId,
                    [field]: value
                }
            };
        });
    };

    // Single series save
    const handleSaveSeries = async (seriesId: string) => {
        const changes = modifiedSeries[seriesId];
        if (!changes) return;

        setSaving(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            const res = await api.updateSeriesGrid(seriesId, changes);
            if (res.success) {
                // Update local state
                setSeriesList(prev => prev.map(s => s.id === seriesId ? { ...s, ...changes } : s));
                setModifiedSeries(prev => {
                    const next = { ...prev };
                    delete next[seriesId];
                    return next;
                });
                showToast(`Serie "${changes.name || seriesId}" guardada ✓`);
            } else {
                showToast(res.message || 'Error al guardar serie', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al guardar cambios', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Single book save
    const handleSaveBook = async (bookId: string) => {
        const changes = modifiedBooks[bookId];
        if (!changes) return;

        setSaving(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            const res = await api.updateBookGrid(bookId, changes);
            if (res.success) {
                // Update local state in series list
                setSeriesList(prev => prev.map(s => ({
                    ...s,
                    books: s.books.map(b => b.id === bookId ? { ...b, ...changes } : b)
                })));
                setModifiedBooks(prev => {
                    const next = { ...prev };
                    delete next[bookId];
                    return next;
                });
                showToast('Volumen guardado correctamente ✓');
            } else {
                showToast(res.message || 'Error al guardar volumen', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al guardar cambios', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Auto-recalculate slug
    const handleRecalculateSlug = async (seriesId: string) => {
        setSaving(true);
        try {
            webApp?.HapticFeedback?.impactOccurred('medium');
            const res = await api.recalculateSeriesSlug(seriesId);
            if (res.success && res.slug) {
                setSeriesList(prev => prev.map(s => s.id === seriesId ? { ...s, slug: res.slug } : s));
                setModifiedSeries(prev => {
                    const current = prev[seriesId] || {};
                    return {
                        ...prev,
                        [seriesId]: { ...current, id: seriesId, slug: res.slug }
                    };
                });
                showToast(`Slug recalculado: ${res.slug}`);
            } else {
                showToast(res.message || 'Error recalculando slug', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al recalcular slug', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Bulk save all pending changes
    const handleBulkSave = async () => {
        const seriesUpdates = Object.values(modifiedSeries);
        const bookUpdates = Object.values(modifiedBooks);

        if (seriesUpdates.length === 0 && bookUpdates.length === 0) return;

        setSaving(true);
        try {
            webApp?.HapticFeedback?.notificationOccurred('start');
            const res = await api.bulkSaveGrid(seriesUpdates, bookUpdates);
            if (res.success) {
                // Apply all changes locally
                setSeriesList(prev => prev.map(s => {
                    const sMod = modifiedSeries[s.id];
                    const updatedSeries = sMod ? { ...s, ...sMod } : s;
                    return {
                        ...updatedSeries,
                        books: updatedSeries.books.map(b => {
                            const bMod = modifiedBooks[b.id];
                            return bMod ? { ...b, ...bMod } : b;
                        })
                    };
                }));

                setModifiedSeries({});
                setModifiedBooks({});
                webApp?.HapticFeedback?.notificationOccurred('success');
                showToast(res.message || 'Todos los cambios fueron guardados exitosamente ✓');
            } else {
                showToast(res.message || 'Error en guardado masivo', 'error');
            }
        } catch (err: any) {
            showToast(err.message || 'Error al procesar guardado masivo', 'error');
        } finally {
            setSaving(false);
        }
    };

    // Discard all changes
    const handleDiscardChanges = () => {
        webApp?.HapticFeedback?.impactOccurred('medium');
        setModifiedSeries({});
        setModifiedBooks({});
        showToast('Cambios pendientes descartados', 'info');
    };

    const pendingSeriesCount = Object.keys(modifiedSeries).length;
    const pendingBooksCount = Object.keys(modifiedBooks).length;
    const totalPendingCount = pendingSeriesCount + pendingBooksCount;

    return (
        <div className="w-full max-w-7xl mx-auto space-y-6 pb-28 px-2 sm:px-4 text-white">
            {/* Header Title */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-white/5 bg-slate-900/60 backdrop-blur-xl">
                <div>
                    <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-primary/20 text-primary border border-primary/30 shadow-lg shadow-primary/10">
                            <Table className="w-6 h-6" />
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white flex items-center gap-2">
                                Editor de Catálogo <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-primary/20 text-primary border border-primary/30 uppercase">Data Grid</span>
                            </h1>
                            <p className="text-xs sm:text-sm text-slate-400">
                                Edición de metadatos en vivo agrupada por serie y volúmenes con validación automática.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Global Metrics Badge */}
                <div className="flex items-center gap-3 self-start md:self-auto">
                    <div className="px-3.5 py-1.5 rounded-xl bg-slate-800/80 border border-white/5 text-xs flex items-center gap-2 text-slate-300">
                        <Layers className="w-4 h-4 text-primary" />
                        <span><strong>{totalSeries}</strong> series</span>
                    </div>
                    <div className="px-3.5 py-1.5 rounded-xl bg-slate-800/80 border border-white/5 text-xs flex items-center gap-2 text-slate-300">
                        <BookOpen className="w-4 h-4 text-emerald-400" />
                        <span><strong>{totalBooks}</strong> volúmenes</span>
                    </div>
                    <button
                        onClick={() => loadGridData(false)}
                        disabled={refreshing || loading}
                        className="p-2 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 text-slate-300 hover:text-white transition-all active:scale-95"
                        title="Recargar catálogo"
                    >
                        <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin text-primary' : ''}`} />
                    </button>
                </div>
            </div>

            {/* Filter Bar */}
            <div className="glass-panel p-4 rounded-2xl border border-white/5 bg-slate-900/50 backdrop-blur-xl space-y-3">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                    {/* Search Input */}
                    <div className="relative">
                        <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                        <input
                            type="text"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Buscar serie, autor, traductor..."
                            className="w-full pl-10 pr-9 py-2 rounded-xl bg-slate-800/80 border border-white/10 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-primary focus:ring-1 focus:ring-primary transition-all"
                        />
                        {query && (
                            <button
                                onClick={() => setQuery('')}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                            >
                                <X className="w-3.5 h-3.5" />
                            </button>
                        )}
                    </div>

                    {/* Missing Filter */}
                    <div>
                        <select
                            value={missingFilter}
                            onChange={(e) => {
                                setMissingFilter(e.target.value);
                                setPage(1);
                            }}
                            className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 text-sm text-white focus:outline-none focus:border-primary transition-all"
                        >
                            <option value="all">🔍 Todas las series</option>
                            <option value="no_slug">⚠️ Sin Slug (#Hashtag)</option>
                            <option value="no_english">🇬🇧 Sin Título en Inglés</option>
                            <option value="no_spanish">🇪🇸 Sin Título en Español</option>
                            <option value="no_illustrator">🎨 Sin Ilustrador</option>
                            <option value="no_translator">🌐 Sin Traductor</option>
                            <option value="no_synopsis">📝 Sin Sinopsis</option>
                            <option value="single_volume">📦 Volumen Único</option>
                            <option value="multi_volume">📚 Multi-Volumen</option>
                        </select>
                    </div>

                    {/* Type Filter */}
                    <div>
                        <select
                            value={bookTypeFilter}
                            onChange={(e) => {
                                setBookTypeFilter(e.target.value);
                                setPage(1);
                            }}
                            className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 text-sm text-white focus:outline-none focus:border-primary transition-all"
                        >
                            <option value="">🏷️ Todos los tipos</option>
                            <option value="Novela Ligera">Novela Ligera</option>
                            <option value="Web Novel">Web Novel</option>
                            <option value="Novela Visual">Novela Visual</option>
                            <option value="Manga">Manga</option>
                        </select>
                    </div>

                    {/* Sort Filter */}
                    <div>
                        <select
                            value={sortBy}
                            onChange={(e) => {
                                setSortBy(e.target.value);
                                setPage(1);
                            }}
                            className="w-full px-3 py-2 rounded-xl bg-slate-800/80 border border-white/10 text-sm text-white focus:outline-none focus:border-primary transition-all"
                        >
                            <option value="name_asc">🔤 Nombre (A - Z)</option>
                            <option value="name_desc">🔤 Nombre (Z - A)</option>
                            <option value="books_desc">📚 Mayor Cantidad Volúmenes</option>
                            <option value="updated_desc">🕒 Modificados Recientemente</option>
                        </select>
                    </div>
                </div>

                {/* View Controls / Expand-Collapse All */}
                <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-white/5 text-xs text-slate-400">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={expandAll}
                            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 border border-white/5 text-slate-300 transition-all"
                        >
                            Desplegar Todos
                        </button>
                        <button
                            onClick={collapseAll}
                            className="px-2.5 py-1 rounded-lg bg-slate-800/60 hover:bg-slate-700/60 border border-white/5 text-slate-300 transition-all"
                        >
                            Colapsar Todos
                        </button>
                    </div>

                    <div className="flex items-center gap-2">
                        <span>Mostrar por página:</span>
                        {[25, 50, 100].map(val => (
                            <button
                                key={val}
                                onClick={() => {
                                    setLimit(val);
                                    setPage(1);
                                }}
                                className={`px-2 py-0.5 rounded-md font-mono text-xs transition-all ${limit === val ? 'bg-primary text-white font-bold' : 'bg-slate-800 text-slate-400 hover:text-white'
                                    }`}
                            >
                                {val}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Table / Hierarchical Grid */}
            <div className="glass-panel rounded-2xl border border-white/5 bg-slate-900/60 backdrop-blur-xl overflow-hidden shadow-2xl">
                {loading ? (
                    <div className="py-20 flex flex-col items-center justify-center space-y-4">
                        <div className="w-10 h-10 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
                        <p className="text-sm font-medium text-slate-400">Cargando catálogo...</p>
                    </div>
                ) : seriesList.length === 0 ? (
                    <div className="py-16 text-center space-y-3">
                        <div className="w-12 h-12 mx-auto rounded-full bg-slate-800/80 flex items-center justify-center text-slate-400">
                            <Search className="w-6 h-6" />
                        </div>
                        <p className="text-base font-semibold text-slate-300">No se encontraron series</p>
                        <p className="text-xs text-slate-500 max-w-sm mx-auto">
                            Intenta ajustar los filtros de búsqueda o restablecer los criterios.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left border-collapse min-w-[950px]">
                            {/* Table Head */}
                            <thead>
                                <tr className="border-b border-white/10 bg-slate-800/70 text-[11px] uppercase tracking-wider font-bold text-slate-300">
                                    <th className="py-3.5 px-3 w-10 text-center"></th>
                                    <th className="py-3.5 px-2 w-12 text-center">Portada</th>
                                    <th className="py-3.5 px-3 min-w-[200px]">Título Romaji / Canónico</th>
                                    <th className="py-3.5 px-3 min-w-[180px]">Título en Inglés</th>
                                    <th className="py-3.5 px-3 min-w-[180px]">Título en Español</th>
                                    <th className="py-3.5 px-3 min-w-[180px]">Slug (#Hashtag)</th>
                                    <th className="py-3.5 px-3 min-w-[140px]">Autor</th>
                                    <th className="py-3.5 px-3 min-w-[140px]">Ilustrador</th>
                                    <th className="py-3.5 px-3 w-32">Tipo</th>
                                    <th className="py-3.5 px-3 w-28 text-center">Acciones</th>
                                </tr>
                            </thead>

                            {/* Table Body */}
                            <tbody className="divide-y divide-white/5 text-xs">
                                {seriesList.map(series => {
                                    const isExpanded = expandedSeries.has(series.id);
                                    const isSeriesDirty = Boolean(modifiedSeries[series.id]);
                                    const currentSeries = { ...series, ...(modifiedSeries[series.id] || {}) };

                                    return (
                                        <React.Fragment key={series.id}>
                                            {/* Series Parent Row */}
                                            <tr className={`group transition-colors ${isSeriesDirty
                                                ? 'bg-amber-500/10 hover:bg-amber-500/15'
                                                : isExpanded
                                                    ? 'bg-slate-800/40 hover:bg-slate-800/60'
                                                    : 'hover:bg-slate-800/30'
                                                }`}>
                                                {/* Expand / Collapse Button */}
                                                <td className="py-3 px-3 text-center">
                                                    <button
                                                        onClick={() => toggleExpand(series.id)}
                                                        className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-slate-700/50 transition-all"
                                                    >
                                                        {isExpanded ? (
                                                            <ChevronDown className="w-4 h-4 text-primary" />
                                                        ) : (
                                                            <ChevronRight className="w-4 h-4" />
                                                        )}
                                                    </button>
                                                </td>

                                                {/* Cover Thumbnail (Click to open full SeriesDetailPage) */}
                                                <td className="py-3 px-2 text-center">
                                                    <div 
                                                        onClick={() => navigate(`/admin/series/${series.id}`)}
                                                        className="cursor-pointer group relative inline-block"
                                                        title="Haga clic para abrir el Editor Completo de Serie"
                                                    >
                                                        {series.cover_url ? (
                                                            <img
                                                                src={series.cover_url}
                                                                alt={series.name}
                                                                className="w-9 h-12 object-cover rounded-md border border-white/10 shadow-sm mx-auto group-hover:border-indigo-400 group-hover:scale-105 transition-all"
                                                                loading="lazy"
                                                            />
                                                        ) : (
                                                            <div className="w-9 h-12 rounded-md bg-slate-800 border border-white/5 flex items-center justify-center text-slate-500 text-[10px] mx-auto group-hover:border-indigo-400 transition-all">
                                                                N/A
                                                            </div>
                                                        )}
                                                    </div>
                                                </td>

                                                {/* Series Romaji Name */}
                                                <td className="py-3 px-3 font-medium text-slate-100">
                                                    <div className="space-y-1.5">
                                                        <input
                                                            type="text"
                                                            value={currentSeries.name || ''}
                                                            onChange={(e) => handleSeriesChange(series.id, 'name', e.target.value)}
                                                            className="w-full bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 font-semibold text-white transition-all outline-none"
                                                            title="Nombre Canónico de la serie"
                                                        />
                                                        <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-slate-400">
                                                            <span className="px-1.5 py-0.5 rounded bg-slate-800/90 text-primary border border-primary/20 font-bold">
                                                                {series.book_count} vol.
                                                            </span>
                                                            <button
                                                                onClick={() => navigate(`/admin/series/${series.id}`)}
                                                                className="px-2 py-0.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold flex items-center gap-1 transition-all active:scale-95 shadow-sm shadow-indigo-600/30"
                                                                title="Abrir Editor Completo de Serie"
                                                            >
                                                                <ExternalLink className="w-3 h-3" />
                                                                Editar
                                                            </button>
                                                            <button
                                                                onClick={() => setSelectedSeriesForAlias(series)}
                                                                className="px-2 py-0.5 rounded bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold flex items-center gap-1 transition-all active:scale-95"
                                                                title="Gestionar alias y fusionar series"
                                                            >
                                                                <Tag className="w-3 h-3" />
                                                                Alias
                                                            </button>
                                                        </div>
                                                    </div>
                                                </td>

                                                {/* English Title */}
                                                <td className="py-3 px-3">
                                                    <input
                                                        type="text"
                                                        value={currentSeries.series_english || ''}
                                                        placeholder="English title..."
                                                        onChange={(e) => handleSeriesChange(series.id, 'series_english', e.target.value)}
                                                        className="w-full bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 text-slate-200 placeholder-slate-400 transition-all outline-none"
                                                    />
                                                </td>

                                                {/* Spanish Title */}
                                                <td className="py-3 px-3">
                                                    <input
                                                        type="text"
                                                        value={currentSeries.series_spanish || ''}
                                                        placeholder="Título en español..."
                                                        onChange={(e) => handleSeriesChange(series.id, 'series_spanish', e.target.value)}
                                                        className="w-full bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 text-slate-200 placeholder-slate-400 transition-all outline-none"
                                                    />
                                                </td>

                                                {/* Slug (#Hashtag) with Auto-recalc */}
                                                <td className="py-3 px-3">
                                                    <div className="flex items-center gap-1">
                                                        <input
                                                            type="text"
                                                            value={currentSeries.slug || ''}
                                                            placeholder="#Slug_Serie"
                                                            onChange={(e) => handleSeriesChange(series.id, 'slug', e.target.value)}
                                                            className="w-full font-mono text-[11px] text-primary font-semibold bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 transition-all outline-none"
                                                        />
                                                        <button
                                                            onClick={() => handleRecalculateSlug(series.id)}
                                                            className="p-1 rounded bg-slate-800/80 hover:bg-primary/20 hover:text-primary text-slate-400 border border-white/5 transition-all"
                                                            title="Auto-generar slug canónico"
                                                        >
                                                            <Sparkles className="w-3.5 h-3.5" />
                                                        </button>
                                                    </div>
                                                </td>

                                                {/* Author */}
                                                <td className="py-3 px-3">
                                                    <input
                                                        type="text"
                                                        value={currentSeries.author || ''}
                                                        placeholder="Autor..."
                                                        onChange={(e) => handleSeriesChange(series.id, 'author', e.target.value)}
                                                        className="w-full bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 text-slate-300 placeholder-slate-400 transition-all outline-none"
                                                    />
                                                </td>

                                                {/* Illustrator */}
                                                <td className="py-3 px-3">
                                                    <input
                                                        type="text"
                                                        value={currentSeries.illustrator || ''}
                                                        placeholder="Ilustrador..."
                                                        onChange={(e) => handleSeriesChange(series.id, 'illustrator', e.target.value)}
                                                        className="w-full bg-transparent hover:bg-slate-800/70 focus:bg-slate-900 border border-transparent focus:border-primary rounded-md px-2 py-1 text-slate-300 placeholder-slate-400 transition-all outline-none"
                                                    />
                                                </td>

                                                {/* Book Type */}
                                                <td className="py-3 px-3">
                                                    <select
                                                        value={currentSeries.book_type || 'Novela Ligera'}
                                                        onChange={(e) => handleSeriesChange(series.id, 'book_type', e.target.value)}
                                                        className="w-full bg-slate-800/60 border border-white/5 text-[11px] rounded-md px-2 py-1 text-slate-300 focus:border-primary outline-none"
                                                    >
                                                        <option value="Novela Ligera">Novela Ligera</option>
                                                        <option value="Web Novel">Web Novel</option>
                                                        <option value="Novela Visual">Novela Visual</option>
                                                        <option value="Manga">Manga</option>
                                                    </select>
                                                </td>

                                                {/* Series Actions */}
                                                <td className="py-3 px-3 text-center">
                                                    <div className="flex items-center justify-center gap-1.5">
                                                        <button
                                                            onClick={() => navigate(`/admin/series/${series.id}`)}
                                                            className="px-2 py-1 rounded bg-indigo-600 hover:bg-indigo-500 text-white text-[10px] font-bold flex items-center gap-1 transition-all active:scale-95 shadow-md shadow-indigo-600/20"
                                                            title="Abrir Editor Completo de Serie (Información, Alias y Volúmenes)"
                                                        >
                                                            <ExternalLink className="w-3 h-3" />
                                                            Editar Serie
                                                        </button>
                                                        <button
                                                            onClick={() => setSelectedSeriesForAlias(series)}
                                                            className="px-2 py-1 rounded bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold flex items-center gap-1 transition-all active:scale-95"
                                                            title="Gestionar alias y fusionar series"
                                                        >
                                                            <Tag className="w-3 h-3" />
                                                            Alias / Fusión
                                                        </button>
                                                        {isSeriesDirty && (
                                                            <button
                                                                onClick={() => handleSaveSeries(series.id)}
                                                                disabled={saving}
                                                                className="px-2 py-1 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/30 text-[10px] font-bold flex items-center gap-1 transition-all active:scale-95"
                                                                title="Guardar cambios de esta serie"
                                                            >
                                                                <Save className="w-3 h-3" />
                                                                Guardar
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>

                                            {/* Sub-Rows: Individual Books/Volumes */}
                                            {isExpanded && (
                                                <tr className="bg-slate-950/70 border-b border-white/10">
                                                    <td colSpan={10} className="p-3 sm:p-4">
                                                        <div className="rounded-xl border border-white/10 bg-slate-900/90 p-3 space-y-3">
                                                            <div className="flex items-center justify-between text-xs text-slate-400 font-semibold px-1">
                                                                <span className="flex items-center gap-2 text-slate-300">
                                                                    <BookOpen className="w-4 h-4 text-primary" />
                                                                    Volúmenes de "{series.name}" ({series.books.length})
                                                                </span>
                                                                <span className="text-[11px] font-mono text-slate-400">
                                                                    Hash: {series.id}
                                                                </span>
                                                            </div>

                                                            {series.books.length === 0 ? (
                                                                <div className="py-4 text-center text-slate-400 text-xs">
                                                                    No hay volúmenes registrados para esta serie.
                                                                </div>
                                                            ) : (
                                                                <div className="overflow-x-auto">
                                                                    <table className="w-full text-left text-xs">
                                                                        <thead>
                                                                            <tr className="border-b border-white/10 text-[10px] uppercase font-bold text-slate-400">
                                                                                <th className="py-2 px-2 w-20">Vol.</th>
                                                                                <th className="py-2 px-3 min-w-[220px]">Título del Volumen</th>
                                                                                <th className="py-2 px-3 min-w-[140px]">Traductor</th>
                                                                                <th className="py-2 px-3 min-w-[140px]">Maquetador</th>
                                                                                <th className="py-2 px-3 w-28">Tamaño</th>
                                                                                <th className="py-2 px-3 w-36">Hash Libro</th>
                                                                                <th className="py-2 px-2 w-24 text-center">Acciones</th>
                                                                            </tr>
                                                                        </thead>
                                                                        <tbody className="divide-y divide-white/5">
                                                                            {series.books.map(book => {
                                                                                const isBookDirty = Boolean(modifiedBooks[book.id]);
                                                                                const currentBook = { ...book, ...(modifiedBooks[book.id] || {}) };

                                                                                return (
                                                                                    <tr
                                                                                        key={book.id}
                                                                                        className={`transition-colors ${isBookDirty
                                                                                            ? 'bg-amber-500/10 hover:bg-amber-500/15'
                                                                                            : 'hover:bg-slate-800/40'
                                                                                            }`}
                                                                                    >
                                                                                        {/* Volume Number */}
                                                                                        <td className="py-2 px-2">
                                                                                            <input
                                                                                                type="text"
                                                                                                value={currentBook.volume !== null && currentBook.volume !== undefined ? currentBook.volume : ''}
                                                                                                placeholder="1.0"
                                                                                                onChange={(e) => handleBookChange(book.id, 'volume', e.target.value)}
                                                                                                className="w-16 bg-slate-800/80 focus:bg-slate-900 border border-white/10 focus:border-primary rounded px-1.5 py-0.5 font-bold font-mono text-emerald-400 text-center outline-none"
                                                                                            />
                                                                                        </td>

                                                                                        {/* Book Title */}
                                                                                        <td className="py-2 px-3">
                                                                                            <input
                                                                                                type="text"
                                                                                                value={currentBook.title || ''}
                                                                                                placeholder="Título del volumen..."
                                                                                                onChange={(e) => handleBookChange(book.id, 'title', e.target.value)}
                                                                                                className="w-full bg-transparent hover:bg-slate-800/60 focus:bg-slate-900 border border-transparent focus:border-primary rounded px-2 py-0.5 text-slate-200 outline-none"
                                                                                            />
                                                                                        </td>

                                                                                        {/* Translator */}
                                                                                        <td className="py-2 px-3">
                                                                                            <input
                                                                                                type="text"
                                                                                                value={currentBook.translator || ''}
                                                                                                placeholder="Traductor / Fansub..."
                                                                                                onChange={(e) => handleBookChange(book.id, 'translator', e.target.value)}
                                                                                                className="w-full bg-transparent hover:bg-slate-800/60 focus:bg-slate-900 border border-transparent focus:border-primary rounded px-2 py-0.5 text-slate-300 outline-none"
                                                                                            />
                                                                                        </td>

                                                                                        {/* Layout By */}
                                                                                        <td className="py-2 px-3">
                                                                                            <input
                                                                                                type="text"
                                                                                                value={currentBook.layout_by || ''}
                                                                                                placeholder="Maquetador..."
                                                                                                onChange={(e) => handleBookChange(book.id, 'layout_by', e.target.value)}
                                                                                                className="w-full bg-transparent hover:bg-slate-800/60 focus:bg-slate-900 border border-transparent focus:border-primary rounded px-2 py-0.5 text-slate-300 outline-none"
                                                                                            />
                                                                                        </td>

                                                                                        {/* File Size */}
                                                                                        <td className="py-2 px-3 text-slate-400 font-mono text-[11px]">
                                                                                            {book.size_mb}
                                                                                        </td>

                                                                                        {/* Book Hash */}
                                                                                        <td className="py-2 px-3">
                                                                                            <button
                                                                                                onClick={() => handleCopy(book.book_hash, book.id)}
                                                                                                className="flex items-center gap-1 px-2 py-0.5 rounded bg-slate-800/90 hover:bg-slate-700/90 text-slate-300 border border-white/5 font-mono text-[10px] transition-all"
                                                                                                title="Copiar hash del libro"
                                                                                            >
                                                                                                {copiedHash === book.id ? (
                                                                                                    <Check className="w-3 h-3 text-emerald-400" />
                                                                                                ) : (
                                                                                                    <Copy className="w-3 h-3 text-slate-400" />
                                                                                                )}
                                                                                                {book.book_hash.substring(0, 8)}...
                                                                                            </button>
                                                                                        </td>

                                                                                        {/* Book Action */}
                                                                                        <td className="py-2 px-2 text-center">
                                                                                            {isBookDirty && (
                                                                                                <button
                                                                                                    onClick={() => handleSaveBook(book.id)}
                                                                                                    disabled={saving}
                                                                                                    className="px-2 py-0.5 rounded bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold transition-all active:scale-95"
                                                                                                >
                                                                                                    Guardar
                                                                                                </button>
                                                                                            )}
                                                                                        </td>
                                                                                    </tr>
                                                                                );
                                                                            })}
                                                                        </tbody>
                                                                    </table>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            )}
                                        </React.Fragment>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                )}

                {/* Pagination Bar */}
                <div className="p-4 border-t border-white/10 bg-slate-900/80 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
                    <div>
                        Mostrando página <strong>{page}</strong> de <strong>{pages}</strong> ({totalSeries} series encontradas)
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page <= 1 || loading}
                            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-all"
                        >
                            Anterior
                        </button>
                        <span className="px-3 py-1 rounded-lg bg-primary/20 text-primary font-bold border border-primary/30">
                            {page} / {pages}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(pages, p + 1))}
                            disabled={page >= pages || loading}
                            className="px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-slate-700/80 border border-white/10 disabled:opacity-40 disabled:cursor-not-allowed text-slate-200 transition-all"
                        >
                            Siguiente
                        </button>
                    </div>
                </div>
            </div>

            {/* Floating Batch Save Bar */}
            {totalPendingCount > 0 && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-11/12 max-w-xl glass-panel p-4 rounded-2xl border border-amber-500/30 bg-slate-900/95 backdrop-blur-2xl shadow-2xl flex items-center justify-between gap-4 animate-in slide-in-from-bottom-5 duration-300">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 animate-pulse">
                            <SlidersHorizontal className="w-5 h-5" />
                        </div>
                        <div>
                            <p className="text-sm font-bold text-white">
                                {totalPendingCount} cambios pendientes
                            </p>
                            <p className="text-xs text-amber-300/80">
                                {pendingSeriesCount} series, {pendingBooksCount} volúmenes modificados
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleDiscardChanges}
                            disabled={saving}
                            className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300 transition-all active:scale-95"
                        >
                            Descartar
                        </button>
                        <button
                            onClick={handleBulkSave}
                            disabled={saving}
                            className="px-4 py-2 rounded-xl bg-gradient-to-r from-amber-500 to-primary text-xs font-bold text-white shadow-lg shadow-amber-500/20 hover:brightness-110 flex items-center gap-1.5 transition-all active:scale-95 disabled:opacity-50"
                        >
                            <Save className="w-4 h-4" />
                            {saving ? 'Guardando...' : 'Guardar Todo'}
                        </button>
                    </div>
                </div>
            )}

            {/* Alias & Fusion Modal */}
            {selectedSeriesForAlias && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
                    <div className="w-full max-w-xl bg-slate-900/95 border border-white/10 rounded-2xl shadow-2xl overflow-hidden p-6 space-y-6">
                        {/* Modal Header */}
                        <div className="flex items-start justify-between border-b border-white/10 pb-4">
                            <div>
                                <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs uppercase tracking-wider">
                                    <Tag className="w-4 h-4" />
                                    Gestión de Alias y Fusión
                                </div>
                                <h3 className="text-lg font-bold text-white mt-1">
                                    {selectedSeriesForAlias.name}
                                </h3>
                                <p className="text-xs font-mono text-slate-400 mt-0.5">
                                    ID: {selectedSeriesForAlias.id}
                                </p>
                            </div>
                            <button
                                onClick={() => setSelectedSeriesForAlias(null)}
                                className="p-1 rounded-lg hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Section 1: Alias List & Add */}
                        <div className="space-y-3">
                            <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                                <Tag className="w-3.5 h-3.5 text-indigo-400" />
                                Títulos Alias Registrados
                            </h4>

                            <div className="flex flex-wrap gap-1.5 min-h-[40px] p-3 rounded-xl bg-slate-950/60 border border-white/5">
                                {(!selectedSeriesForAlias.aliases || selectedSeriesForAlias.aliases.length === 0) ? (
                                    <span className="text-xs text-slate-500 italic">No hay alias asignados aún</span>
                                ) : (
                                    selectedSeriesForAlias.aliases.map(al => (
                                        <span key={al.id} className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-500/10 border border-indigo-500/30 text-indigo-200 text-xs font-medium">
                                            {al.alias}
                                            <button
                                                onClick={() => handleDeleteAlias(al.id)}
                                                className="hover:text-rose-400 transition-colors ml-0.5"
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
                                    placeholder="Agregar un nuevo alias (ej. Título en Romaji o Fansub)..."
                                    value={newAliasInput}
                                    onChange={(e) => setNewAliasInput(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleAddAlias()}
                                    className="flex-1 px-3 py-2 text-xs rounded-xl bg-slate-950/80 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                                />
                                <button
                                    onClick={handleAddAlias}
                                    disabled={addingAlias || !newAliasInput.trim()}
                                    className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1 transition-all active:scale-95 shadow-md shadow-indigo-600/20"
                                >
                                    <Plus className="w-4 h-4" />
                                    Añadir
                                </button>
                            </div>
                        </div>

                        {/* Section 2: Fusion / Merge */}
                        <div className="space-y-3 pt-3 border-t border-white/10">
                            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider flex items-center gap-1.5">
                                <GitMerge className="w-3.5 h-3.5" />
                                Fusionar Serie Secundaria aquí (1-Click Merge)
                            </h4>
                            <p className="text-xs text-slate-400">
                                Ingrese el ID / Hash de otra serie duplicada para transferir todos sus volúmenes y alias a esta serie principal.
                            </p>
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Hash / ID de la serie secundaria a eliminar..."
                                    value={mergeSourceHash}
                                    onChange={(e) => setMergeSourceHash(e.target.value)}
                                    className="flex-1 px-3 py-2 text-xs font-mono rounded-xl bg-slate-950/80 border border-white/10 text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
                                />
                                <button
                                    onClick={handleMergeSeriesInModal}
                                    disabled={mergingSeries || !mergeSourceHash.trim()}
                                    className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-bold flex items-center gap-1.5 transition-all active:scale-95 shadow-md shadow-amber-600/20"
                                >
                                    <GitMerge className="w-4 h-4" />
                                    {mergingSeries ? 'Fusionando...' : 'Fusionar'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Toast Notification */}
            {toastMessage && (
                <div className="fixed top-6 right-6 z-50 animate-in slide-in-from-top-3 duration-300">
                    <div className={`px-4 py-3 rounded-xl backdrop-blur-xl border text-xs sm:text-sm font-medium shadow-2xl flex items-center gap-2.5 ${toastMessage.type === 'success'
                        ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-200'
                        : toastMessage.type === 'error'
                            ? 'bg-rose-950/90 border-rose-500/40 text-rose-200'
                            : 'bg-slate-900/90 border-primary/40 text-primary-200'
                        }`}>
                        {toastMessage.type === 'success' && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                        {toastMessage.type === 'error' && <AlertCircle className="w-4 h-4 text-rose-400" />}
                        {toastMessage.type === 'info' && <Database className="w-4 h-4 text-primary" />}
                        <span>{toastMessage.text}</span>
                    </div>
                </div>
            )}
        </div>
    );
};
