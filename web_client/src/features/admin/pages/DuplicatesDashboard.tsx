import React, { useState, useEffect } from 'react';
import {
    Copy,
    FileWarning,
    Trash2,
    CheckCircle,
    AlertTriangle,
    Search,
    RefreshCw,
    HardDrive,
    Info,
    ArrowRight,
    X,
    Tag,
    Sparkles,
    GitMerge,
    ChevronRight,
    Loader2
} from 'lucide-react';
import { api } from '@shared/services/api';

interface DuplicateEntry {
    id: number;
    title: string;
    author: string;
    hash: string;
    original: string;
    duplicate: string;
    detectedAt: string;
}

interface AISeriesSuggestion {
    id?: number; // Database ID if coming from MetadataProposal
    series_a: {
        hash: string;
        name: string;
        english: string;
        spanish: string;
        author: string;
        count: number;
    };
    series_b: {
        hash: string;
        name: string;
        english: string;
        spanish: string;
        author: string;
        count: number;
    };
    reason: string;
    confidence: number;
    suggested_name: string;
}

export const DuplicatesDashboard: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'books' | 'ai-series'>('books');

    // Hash Duplicates State
    const [duplicates, setDuplicates] = useState<DuplicateEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [clearing, setClearing] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedDuplicate, setSelectedDuplicate] = useState<DuplicateEntry | null>(null);
    const [rechecking, setRechecking] = useState(false);
    const [deletingId, setDeletingId] = useState<number | null>(null);

    // AI Series State
    const [aiSuggestions, setAiSuggestions] = useState<AISeriesSuggestion[]>([]);
    const [scanningAi, setScanningAi] = useState(false);
    const [selectedAiPair, setSelectedAiPair] = useState<AISeriesSuggestion | null>(null);
    const [merging, setMerging] = useState(false);
    const [newName, setNewName] = useState('');

    const fetchDuplicates = async () => {
        setLoading(true);
        try {
            const res = await api.adminGetDuplicates();
            if (res.success) {
                setDuplicates(res.duplicates || []);
            }
        } catch (error) {
            console.error('Error fetching duplicates:', error);
        } finally {
            setLoading(false);
        }
    };

    const refreshAiProposals = async () => {
        try {
            const res = await (api as any).getAiProposals();
            if (res.success) {
                const merges = (res.proposals || [])
                    .filter((p: any) => p.type === 'merge')
                    .map((p: any) => ({
                        id: p.id,
                        series_a: p.proposal.series_a,
                        series_b: p.proposal.series_b,
                        reason: p.proposal.reason,
                        confidence: p.proposal.confidence,
                        suggested_name: p.proposal.suggested_main_name
                    }));
                setAiSuggestions(merges);
            }

            const status = await (api as any).getAiScanStatus();
            if (status.success) {
                setScanningAi(status.is_scanning);
            }
        } catch (error) {
            console.error('Error refreshing AI proposals:', error);
        }
    };

    const fetchAiSeriesDuplicates = async () => {
        setScanningAi(true);
        try {
            const res = await (api as any).adminAiSeriesDuplicateScan();
            if (!res.success) {
                alert(res.message || 'Error al iniciar escaneo');
                setScanningAi(false);
            } else {
                // Iniciar polling
                await refreshAiProposals();
            }
        } catch (error) {
            console.error('Error fetching AI series duplicates:', error);
            setScanningAi(false);
        }
    };

    const handleClear = async () => {
        if (!confirm('¿Estás seguro de que quieres limpiar todo el historial de duplicados detectados? Esto no borrará los archivos, solo los registros de esta tabla.')) return;

        setClearing(true);
        try {
            const res = await api.adminClearDuplicates();
            if (res.success) {
                setDuplicates([]);
            }
        } catch (error) {
            console.error('Error clearing duplicates:', error);
        } finally {
            setClearing(false);
        }
    };

    const handleRecheck = async () => {
        setRechecking(true);
        try {
            const res = await (api as any).adminRecheckDuplicates();
            if (res.success) {
                await fetchDuplicates();
            }
        } catch (error) {
            console.error('Error rechecking duplicates:', error);
        } finally {
            setRechecking(false);
        }
    };

    const handleDeleteFile = async (id: number, target: 'original' | 'duplicate') => {
        const isOriginal = target === 'original';
        const confirmMsg = isOriginal
            ? '¿Estás SEGURO de borrar el archivo ORIGINAL de la biblioteca?\n\nEsta acción eliminará el archivo físico del disco y el registro de la biblioteca. Es irreversible.'
            : '¿Estás seguro de borrar esta copia rechazada?\n\nSe eliminará el archivo del disco para resolver el conflicto.';

        if (!confirm(confirmMsg)) return;

        setDeletingId(id);
        try {
            const res = await (api as any).adminDeleteDuplicateItem(id, target);
            if (res.success) {
                setDuplicates(prev => prev.filter(dup => dup.id !== id));
                setSelectedDuplicate(null);
            } else {
                alert(`Error: ${res.message}`);
            }
        } catch (error) {
            console.error('Error deleting duplicate file:', error);
            alert('Fallo crítico al intentar borrar el archivo.');
        } finally {
            setDeletingId(null);
        }
    };

    const handleMergeSeries = async () => {
        if (!selectedAiPair) return;

        const confirmMsg = `¿Fusionar "${selectedAiPair.series_b.name}" dentro de "${selectedAiPair.series_a.name}"?\n\nTodos los libros pasarán a la serie A y la metadata de la serie B será ELIMINADA.`;
        if (!confirm(confirmMsg)) return;

        setMerging(true);
        try {
            let res;
            if (selectedAiPair.id) {
                // Si viene de la DB (MetadataProposal), usamos la API de AI para aplicar merge
                res = await (api as any).applyAiMerge(selectedAiPair.id);
            } else {
                // Fallback para escaneos directos (si los hubiera)
                res = await (api as any).adminMergeSeries(
                    selectedAiPair.series_a.hash,
                    selectedAiPair.series_b.hash,
                    newName || selectedAiPair.suggested_name
                );
            }

            if (res.success) {
                setAiSuggestions(prev => prev.filter(p => p.id !== selectedAiPair.id));
                setSelectedAiPair(null);
                alert('Series fusionadas con éxito');
            } else {
                alert(`Error: ${res.message}`);
            }
        } catch (error) {
            console.error('Error merging series:', error);
            alert('Fallo al fusionar series.');
        } finally {
            setMerging(false);
        }
    };

    useEffect(() => {
        if (activeTab === 'books') {
            fetchDuplicates();
        } else if (activeTab === 'ai-series') {
            refreshAiProposals();
        }
    }, [activeTab]);

    // Polling effect for AI scanning
    useEffect(() => {
        let interval: NodeJS.Timeout;
        if (activeTab === 'ai-series' && scanningAi) {
            interval = setInterval(() => {
                refreshAiProposals();
            }, 5000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [activeTab, scanningAi]);

    const filtered = duplicates.filter(d =>
        d.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.author?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.duplicate?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="flex flex-col gap-8 animate-in fade-in duration-500 pt-4">
            {/* Header / Intro */}
            <div className="flex flex-col gap-6 md:flex-row md:items-center justify-between">
                <div className="flex items-center gap-6">
                    <div className="p-4 bg-primary/20 rounded-premium text-primary border border-primary/20">
                        <FileWarning className="w-8 h-8" />
                    </div>
                    <div>
                        <h2 className="text-3xl font-black text-white tracking-tighter uppercase">Centro de Resolución</h2>
                        <p className="text-xs text-gray-500 font-bold uppercase tracking-widest opacity-60">Gestión de Duplicados e Integridad de Datos</p>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex p-1 bg-white/5 rounded-premium-sm border border-white/5">
                    <button
                        onClick={() => setActiveTab('books')}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'books'
                            ? 'bg-amber-500 text-white shadow-lg'
                            : 'text-gray-500 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <HardDrive className="w-3.5 h-3.5" />
                        Libros (Hash)
                    </button>
                    <button
                        onClick={() => setActiveTab('ai-series')}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'ai-series'
                            ? 'bg-primary text-white shadow-lg shadow-primary/20'
                            : 'text-gray-500 hover:text-white hover:bg-white/5'
                            }`}
                    >
                        <Sparkles className="w-3.5 h-3.5" />
                        Series (AI)
                    </button>
                </div>
            </div>

            {activeTab === 'books' ? (
                <>
                    {/* Stats & Actions: Books */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 glass-panel p-8 rounded-premium border border-white/5 flex items-center gap-6">
                            <div className="p-4 bg-amber-500/20 rounded-premium-sm text-amber-500 border border-amber-500/20">
                                <Info className="w-8 h-8" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2">Duplicados por Hash</h3>
                                <p className="text-xs text-gray-500 leading-relaxed shadow-glow-sm">
                                    Archivos EPUB con contenido idéntico. Fueron omitidos para evitar registros redundantes.
                                    Se recomienda borrar los duplicados físicamente del disco.
                                </p>
                            </div>
                        </div>

                        <div className="lg:col-span-1 glass-panel p-8 rounded-premium border border-white/5 flex flex-col justify-center items-center text-center">
                            <div className="text-4xl font-black text-amber-500 mb-1">{duplicates.length}</div>
                            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Conflicto de Bitstream</div>
                            <button
                                onClick={handleClear}
                                disabled={clearing || duplicates.length === 0}
                                className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white border border-red-500/20 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-30"
                            >
                                <Trash2 className="w-3.5 h-3.5" />
                                Limpiar Historial
                            </button>
                        </div>
                    </div>

                    <div className="glass-panel rounded-premium border border-white/5 overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-white/5 flex flex-col sm:flex-row items-center justify-between gap-4">
                            <div className="relative w-full sm:w-80 group">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500 group-focus-within:text-primary transition-all" />
                                <input
                                    type="text"
                                    placeholder="Filtrar por título, autor o hash..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="w-full pl-10 pr-4 py-3 bg-white/5 border border-white/10 rounded-premium-sm text-xs text-white focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all"
                                />
                            </div>
                            <div className="flex items-center gap-2">
                                <button
                                    onClick={handleRecheck}
                                    disabled={rechecking || loading}
                                    className="flex items-center gap-2 px-6 py-3 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/20 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all active:scale-95 disabled:opacity-50"
                                >
                                    <RefreshCw className={`w-3.5 h-3.5 ${rechecking ? 'animate-spin' : ''}`} />
                                    Re-verificar Disco
                                </button>
                                <button
                                    onClick={fetchDuplicates}
                                    className="flex items-center gap-2 px-6 py-3 bg-white/5 hover:bg-white/10 text-white border border-white/10 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all active:scale-95"
                                >
                                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                                    Refrescar
                                </button>
                            </div>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-white/[0.02] text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                        <th className="px-6 py-5">Objeto / Información</th>
                                        <th className="px-6 py-5">Chaque de Archivo</th>
                                        <th className="px-6 py-5 text-right">Detalles</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {loading ? (
                                        Array(3).fill(0).map((_, i) => (
                                            <tr key={i} className="animate-pulse">
                                                <td colSpan={3} className="px-6 py-12 text-center text-gray-600 text-[10px] uppercase font-black tracking-widest">Sincronizando registros...</td>
                                            </tr>
                                        ))
                                    ) : filtered.length === 0 ? (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-32 text-center">
                                                <div className="flex flex-col items-center gap-6">
                                                    <div className="p-6 bg-green-500/10 rounded-full text-green-500 border border-green-500/10 shadow-lg shadow-green-500/5">
                                                        <CheckCircle className="w-12 h-12" />
                                                    </div>
                                                    <p className="text-sm font-black text-gray-500 uppercase tracking-widest">Sin duplicados de contenido</p>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        filtered.map((dup) => (
                                            <tr
                                                key={dup.id}
                                                className="group hover:bg-white/[0.01] transition-all cursor-pointer"
                                                onClick={() => setSelectedDuplicate(dup)}
                                            >
                                                <td className="px-6 py-6">
                                                    <div className="flex flex-col gap-1">
                                                        <span className="text-xs font-black text-white group-hover:text-amber-500 transition-colors">{dup.title || 'Título desconocido'}</span>
                                                        <span className="text-[10px] text-gray-500 font-bold uppercase tracking-tight">{dup.author || 'Autor desconocido'}</span>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6">
                                                    <div className="flex flex-col gap-2">
                                                        <div className="flex items-center gap-2">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-sm shadow-green-500/40"></div>
                                                            <span className="text-[10px] text-gray-400 font-mono truncate max-w-[240px]">{dup.original.split(/[/\\]/).pop()}</span>
                                                        </div>
                                                        <div className="flex items-center gap-2 text-red-400">
                                                            <AlertTriangle className="w-3 h-3" />
                                                            <span className="text-[10px] font-mono truncate max-w-[240px]">{dup.duplicate.split(/[/\\]/).pop()}</span>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6 text-right">
                                                    <div className="inline-flex p-2 bg-white/5 rounded-premium-sm text-gray-500 group-hover:text-amber-500 group-hover:bg-amber-500/10 border border-transparent group-hover:border-amber-500/20 transition-all">
                                                        <ChevronRight className="w-4 h-4" />
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            ) : (
                <>
                    {/* Stats & Actions: AI Series */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        <div className="lg:col-span-2 glass-panel p-8 rounded-premium border border-white/5 flex items-center gap-6 bg-gradient-to-br from-primary/5 to-transparent">
                            <div className="p-4 bg-primary/20 rounded-premium-sm text-primary border border-primary/20 shadow-lg shadow-primary/20">
                                <Sparkles className="w-8 h-8" />
                            </div>
                            <div>
                                <h3 className="text-xl font-black text-white uppercase tracking-tight mb-2">Detección Inteligente de Series</h3>
                                <p className="text-xs text-gray-500 leading-relaxed shadow-glow-sm">
                                    La IA analiza series con nombres similares (inglés/español) creadas con hashes distintos debido a ligeras diferencias en metadatos.
                                    Fusionarlas consolidará todos los libros bajo una única entrada canónica.
                                </p>
                            </div>
                        </div>

                        <div className="lg:col-span-1 glass-panel p-8 rounded-premium border border-white/5 flex flex-col justify-center items-center text-center">
                            <div className="text-4xl font-black text-primary mb-1">{aiSuggestions.length}</div>
                            <div className="text-[10px] font-black text-gray-400 uppercase tracking-widest leading-none">Posibles Duplicados</div>
                            <button
                                onClick={fetchAiSeriesDuplicates}
                                disabled={scanningAi}
                                className="mt-6 w-full flex items-center justify-center gap-2 px-4 py-3 bg-primary/10 hover:bg-primary text-white border border-primary/20 rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-30"
                            >
                                {scanningAi ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                                Escanear con IA
                            </button>
                        </div>
                    </div>

                    <div className="glass-panel rounded-premium border border-white/5 overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-white/5 flex items-center justify-between">
                            <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em]">Propuestas de Fusión</h4>
                            <span className="px-3 py-1 bg-white/5 rounded-full text-[8px] font-black text-gray-500 uppercase tracking-widest">Motor: Gemini 2.0 Flash</span>
                        </div>

                        <div className="overflow-x-auto">
                            <table className="w-full text-left border-collapse">
                                <thead>
                                    <tr className="bg-white/[0.02] text-[10px] font-black text-gray-500 uppercase tracking-widest border-b border-white/5">
                                        <th className="px-6 py-5">Series a Comparar</th>
                                        <th className="px-6 py-5">Análisis IA</th>
                                        <th className="px-6 py-5 text-right">Integración</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {scanningAi ? (
                                        Array(3).fill(0).map((_, i) => (
                                            <tr key={i} className="animate-pulse">
                                                <td colSpan={3} className="px-6 py-12 text-center">
                                                    <div className="flex flex-col items-center gap-2">
                                                        <Loader2 className="w-6 h-6 text-primary animate-spin" />
                                                        <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest">IA Analizando biblioteca...</span>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    ) : aiSuggestions.length === 0 ? (
                                        <tr>
                                            <td colSpan={3} className="px-6 py-32 text-center">
                                                <div className="flex flex-col items-center gap-6">
                                                    <div className="p-6 bg-primary/10 rounded-full text-primary border border-primary/10 shadow-lg shadow-primary/5">
                                                        <Sparkles className="w-12 h-12" />
                                                    </div>
                                                    <p className="text-sm font-black text-gray-500 uppercase tracking-widest">No hay series similares detectadas</p>
                                                    <button
                                                        onClick={fetchAiSeriesDuplicates}
                                                        className="px-6 py-2.5 bg-primary/20 text-primary border border-primary/20 rounded-premium-sm text-[10px] font-black uppercase tracking-widest hover:bg-primary hover:text-white transition-all"
                                                    >
                                                        Realizar Escaneo Forzado
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    ) : (
                                        aiSuggestions.map((pair, idx) => (
                                            <tr
                                                key={idx}
                                                className="group hover:bg-white/[0.01] transition-all cursor-pointer"
                                                onClick={() => {
                                                    setSelectedAiPair(pair);
                                                    setNewName(pair.suggested_name);
                                                }}
                                            >
                                                <td className="px-6 py-6">
                                                    <div className="flex flex-col gap-4">
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-8 h-8 flex items-center justify-center bg-blue-500/10 rounded-lg text-[10px] font-black text-blue-400">A</div>
                                                            <div>
                                                                <div className="text-xs font-black text-white">{pair.series_a.name}</div>
                                                                <div className="text-[9px] text-gray-500 uppercase font-black">{pair.series_a.author} • {pair.series_a.count} libros</div>
                                                            </div>
                                                        </div>
                                                        <div className="flex items-center gap-3">
                                                            <div className="w-8 h-8 flex items-center justify-center bg-purple-500/10 rounded-lg text-[10px] font-black text-purple-400">B</div>
                                                            <div>
                                                                <div className="text-xs font-black text-white">{pair.series_b.name}</div>
                                                                <div className="text-[9px] text-gray-500 uppercase font-black">{pair.series_b.author} • {pair.series_b.count} libros</div>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6">
                                                    <div className="flex flex-col gap-2">
                                                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 rounded-full w-fit">
                                                            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
                                                            <span className="text-[9px] font-black text-green-500 uppercase tracking-wider">{Math.round(pair.confidence * 100)}% Confianza</span>
                                                        </div>
                                                        <p className="text-[10px] text-gray-400 italic max-w-sm line-clamp-2 leading-relaxed">"{pair.reason}"</p>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-6 text-right">
                                                    <div className="inline-flex p-3 bg-primary/10 rounded-premium-sm text-primary group-hover:bg-primary group-hover:text-white transition-all shadow-lg shadow-primary/10">
                                                        <GitMerge className="w-4 h-4" />
                                                    </div>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {/* AI Merge Dialog */}
            {selectedAiPair && (
                <div className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-300">
                    <div className="glass-panel w-full max-w-2xl rounded-[2.5rem] border border-white/10 overflow-hidden flex flex-col animate-in zoom-in-95 duration-300">
                        <div className="p-8 border-b border-white/5 bg-gradient-to-r from-primary/10 to-transparent flex items-center justify-between">
                            <div className="flex items-center gap-4">
                                <GitMerge className="w-6 h-6 text-primary" />
                                <h3 className="text-xl font-black text-white uppercase tracking-tighter">Fusión Inteligente</h3>
                            </div>
                            <button onClick={() => setSelectedAiPair(null)} className="p-2 hover:bg-white/5 rounded-full transition-all">
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <div className="p-8 space-y-8">
                            <div className="flex items-center justify-between p-6 bg-white/5 rounded-premium border border-white/5 relative">
                                <div className="flex-1 text-center px-4">
                                    <div className="text-[9px] font-black text-blue-400 uppercase mb-2 tracking-widest">Serie Origen (B)</div>
                                    <div className="text-sm font-black text-white line-clamp-1">{selectedAiPair.series_b.name}</div>
                                    <div className="text-[10px] text-gray-500 font-bold">{selectedAiPair.series_b.count} Libros</div>
                                </div>
                                <div className="p-3 bg-primary/20 rounded-full border border-primary/20 z-10">
                                    <ArrowRight className="w-5 h-5 text-primary" />
                                </div>
                                <div className="flex-1 text-center px-4">
                                    <div className="text-[9px] font-black text-green-400 uppercase mb-2 tracking-widest">Serie Destino (A)</div>
                                    <div className="text-sm font-black text-white line-clamp-1">{selectedAiPair.series_a.name}</div>
                                    <div className="text-[10px] text-gray-500 font-bold">{selectedAiPair.series_a.count} Libros</div>
                                </div>
                                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent"></div>
                            </div>

                            <div className="space-y-4">
                                <label className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Nombre Unificado Final</label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={(e) => setNewName(e.target.value)}
                                    className="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-premium-sm text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary/40 transition-all font-bold"
                                    placeholder="Nombre de la serie..."
                                />
                                <div className="flex items-center gap-2 p-4 bg-primary/5 rounded-premium-sm border border-primary/10">
                                    <Info className="w-4 h-4 text-primary shrink-0" />
                                    <p className="text-[10px] text-gray-400 leading-relaxed font-medium">Recomendación IA: <span className="text-primary font-bold italic">"{selectedAiPair.suggested_name}"</span></p>
                                </div>
                            </div>

                            <div className="p-6 bg-amber-500/5 border border-amber-500/10 rounded-premium-sm">
                                <div className="flex items-center gap-2 text-amber-500 mb-2">
                                    <AlertTriangle className="w-4 h-4" />
                                    <span className="text-[10px] font-black uppercase tracking-widest">Advertencia de Integridad</span>
                                </div>
                                <p className="text-[10px] text-gray-500 leading-relaxed">
                                    Esta acción actualizará todos los registros de <span className="text-white">LocalBook</span> asociados al Hash B para que apunten al Hash A. Se eliminará la metadata antigua. Esta operación es <span className="text-white underline underline-offset-4 decoration-amber-500/40">irreversible</span>.
                                </p>
                            </div>
                        </div>

                        <div className="p-8 bg-white/[0.02] border-t border-white/5 flex gap-4">
                            <button
                                onClick={() => setSelectedAiPair(null)}
                                className="flex-1 py-4 bg-white/5 hover:bg-white/10 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleMergeSeries}
                                disabled={merging}
                                className="flex-1 py-4 bg-primary hover:brightness-110 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
                            >
                                {merging ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitMerge className="w-3.5 h-3.5" />}
                                Finalizar Fusión
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Book Detail View (existing) */}
            {selectedDuplicate && (
                <div className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 md:p-8 animate-in fade-in duration-300">
                    <div className="glass-panel w-full max-w-4xl max-h-[90vh] overflow-hidden rounded-[2.5rem] border border-white/10 flex flex-col shadow-2xl animate-in zoom-in-95 duration-300">
                        {/* Detail Header */}
                        <div className="p-8 border-b border-white/5 flex items-start justify-between">
                            <div className="flex items-center gap-6">
                                <div className="p-4 bg-amber-500/20 rounded-premium-sm text-amber-500 border border-amber-500/20">
                                    <Copy className="w-8 h-8" />
                                </div>
                                <div>
                                    <h2 className="text-2xl font-black text-white uppercase tracking-tighter mb-1">Análisis de Duplicado</h2>
                                    <p className="text-xs text-gray-500 uppercase tracking-widest font-black opacity-60">Hash: {selectedDuplicate.hash}</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setSelectedDuplicate(null)}
                                className="p-3 bg-white/5 hover:bg-white/10 rounded-premium-sm text-gray-400 hover:text-white transition-all"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Detail Content */}
                        <div className="flex-1 overflow-y-auto p-8 space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                <div className="space-y-6">
                                    <h4 className="text-[10px] font-black text-amber-500 uppercase tracking-[0.3em] mb-4">Conflicto de Contenido</h4>

                                    <div className="p-6 bg-green-500/5 border border-green-500/10 rounded-premium-sm space-y-3 relative">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-green-500">
                                                <CheckCircle className="w-4 h-4" />
                                                <span className="text-[10px] font-black uppercase tracking-wider">Original en Sistema</span>
                                            </div>
                                            <button
                                                onClick={() => handleDeleteFile(selectedDuplicate.id, 'original')}
                                                disabled={deletingId !== null}
                                                className="p-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-lg transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <div className="text-xs text-white font-black leading-tight">{selectedDuplicate.title}</div>
                                        <div className="text-[9px] text-gray-500 font-mono break-all line-clamp-2">{selectedDuplicate.original}</div>
                                    </div>

                                    <div className="p-6 bg-red-500/5 border border-red-500/10 rounded-premium-sm space-y-3 relative">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-red-500">
                                                <AlertTriangle className="w-4 h-4" />
                                                <span className="text-[10px] font-black uppercase tracking-wider">Copia omitida</span>
                                            </div>
                                            <button
                                                onClick={() => handleDeleteFile(selectedDuplicate.id, 'duplicate')}
                                                disabled={deletingId !== null}
                                                className="p-2 bg-red-500/10 hover:bg-red-500 text-red-500 hover:text-white rounded-lg transition-all"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                        <div className="text-xs text-white font-black leading-tight">{selectedDuplicate.title}</div>
                                        <div className="text-[9px] text-gray-500 font-mono break-all line-clamp-2">{selectedDuplicate.duplicate}</div>
                                    </div>
                                </div>

                                <div className="space-y-6">
                                    <h4 className="text-[10px] font-black text-gray-400 uppercase tracking-[0.3em] mb-4">Instrucciones</h4>
                                    <div className="p-8 bg-white/2 border border-white/5 rounded-premium text-xs text-gray-400 leading-relaxed italic">
                                        Ambos archivos son binariamente idénticos. Si deseas que ambos convivan como registros separados, edita los metadatos de uno de ellos (título, autor o volumen) y vuelve a escanear.
                                        <br /><br />
                                        De lo contrario, borra la "Copia omitida" para liberar espacio.
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-8 bg-white/[0.02] border-t border-white/5 flex justify-end gap-3">
                            <button
                                onClick={() => setSelectedDuplicate(null)}
                                className="px-8 py-3 bg-white/5 hover:bg-white/10 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all"
                            >
                                Cerrar
                            </button>
                            <button
                                className="px-8 py-3 bg-red-500 hover:brightness-110 text-white rounded-premium-sm text-[10px] font-black uppercase tracking-widest transition-all shadow-lg shadow-red-500/20"
                                onClick={() => handleDeleteFile(selectedDuplicate.id, 'duplicate')}
                            >
                                Borrar Duplicado
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Bottom Help */}
            <div className="p-8 rounded-[2rem] bg-indigo-500/5 border border-indigo-500/10 flex items-start gap-6">
                <div className="p-3 bg-indigo-500/20 rounded-premium-sm text-indigo-400">
                    <Info className="w-5 h-5 " />
                </div>
                <div>
                    <h4 className="text-xs font-black text-indigo-400 mb-2 uppercase tracking-widest">¿Cómo funciona la resolución?</h4>
                    <p className="text-[10px] text-gray-500 leading-relaxed max-w-5xl font-medium tracking-wide">
                        Para <span className="text-white font-bold">Libros</span>, comparamos el bitstream exacto del archivo. Para <span className="text-white font-bold">Series</span>, utilizamos IA (Gemini) para entender si dos etiquetas diferentes se refieren a la misma obra basándonos en nombres en distintos idiomas, autor y número de volúmenes. La fusión es un proceso atómico que garantiza la integridad de la base de datos.
                    </p>
                </div>
            </div>
        </div>
    );
};
