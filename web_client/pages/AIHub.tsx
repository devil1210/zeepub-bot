
import React, { useEffect, useState } from 'react';
import {
    BrainCircuit,
    Sparkles,
    Clock,
    Database,
    Search,
    Activity,
    CheckCircle,
    AlertTriangle,
    Play,
    X,
    ArrowRight,
    Edit2,
    Save,
    Trash2
} from 'lucide-react';
import { api } from '../src/services/api';

export const AIHub: React.FC = () => {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [scanHash, setScanHash] = useState('');
    const [scanResult, setScanResult] = useState<any>(null);
    const [scanning, setScanning] = useState(false);

    // Search State
    const [showSearch, setShowSearch] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    // Proposal State (Interactive Mode)
    const [proposal, setProposal] = useState<any>(null);
    const [showProposal, setShowProposal] = useState(false);
    const [approvedChanges, setApprovedChanges] = useState<any[]>([]);
    const [applyRenames, setApplyRenames] = useState(true);
    const [applyMeta, setApplyMeta] = useState(true);
    const [processingProposal, setProcessingProposal] = useState(false);

    useEffect(() => {
        loadStats();
    }, []);

    const loadStats = async () => {
        try {
            setLoading(true);
            const res = await api.getAiStats();
            if (res.result) {
                setStats(res.result);
            }
        } catch (e) {
            console.error("Failed to load stats", e);
        } finally {
            setLoading(false);
        }
    };

    const handleScan = async () => {
        if (!scanHash) return;
        setScanning(true);
        setScanResult(null);
        setProposal(null);

        try {
            // ALWAYS use dry_run=true first for user safety
            const res = await api.scanSeriesAi(scanHash, true); // true = dry_run

            if (res.dry_run && res.proposal) {
                // Show interactive modal
                setProposal(res.proposal);
                setApprovedChanges(res.proposal?.changes || []);
                setShowProposal(true);
            } else {
                // Fallback (shouldn't happen with new backend)
                setScanResult(res.result || res);
            }
        } catch (e: any) {
            setScanResult({ success: false, message: e.message || "Error desconocido" });
        } finally {
            setScanning(false);
        }
    };

    const handleApplyChanges = async () => {
        if (!proposal) return;
        setProcessingProposal(true);
        try {
            const res = await api.applyAiChanges(
                proposal,
                approvedChanges,
                applyRenames,
                applyMeta
            );
            setScanResult(res);
            setShowProposal(false);
            setProposal(null);
            loadStats(); // Refresh final stats
        } catch (e: any) {
            alert("Error aplicando cambios: " + e.message);
        } finally {
            setProcessingProposal(false);
        }
    };

    const toggleChange = (bookId: number) => {
        const exists = approvedChanges.find(c => c.book_id === bookId);
        if (exists) {
            setApprovedChanges(approvedChanges.filter(c => c.book_id !== bookId));
        } else {
            const originalChange = proposal?.changes?.find((c: any) => c.book_id === bookId);
            if (originalChange) {
                setApprovedChanges([...approvedChanges, originalChange]);
            }
        }
    };

    const runSearch = async () => {
        if (!searchTerm) return;
        setSearching(true);
        try {
            // Use sort='a-z' and type='all' for generic search
            const res = await api.searchBooks(searchTerm, 1, 'all', 'a-z');
            // Flatten results if they are mingled (LibraryService.search_series returns {results: [...]} )
            setSearchResults(res.results || []);
        } catch (e) {
            console.error("Search failed", e);
        } finally {
            setSearching(false);
        }
    };

    const selectSeries = (s: any) => {
        setScanHash(s.series_hash || '');
        setShowSearch(false);
        setSearchResults([]);
        setSearchTerm('');
    };

    if (loading && !stats) {
        return <div className="p-10 text-center text-gray-500 animate-pulse">Cargando Cerebro...</div>;
    }

    const aiActive = stats?.ai_active;
    const backgroundScanEnabled = stats?.background_scan_enabled;
    const aiKeyMasked = stats?.ai_key_masked;

    const handleToggleBackgroundScan = async () => {
        try {
            const nextState = !backgroundScanEnabled;
            // Optimistic update
            setStats({ ...stats, background_scan_enabled: nextState });
            await api.toggleAiBackgroundScan(nextState);
        } catch (e: any) {
            alert("Error cambiando configuración: " + e.message);
            loadStats(); // Revert
        }
    };

    return (
        <div className="max-w-6xl mx-auto px-4 py-8 animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex items-center gap-4 mb-10">
                <div className="p-4 bg-purple-500/10 rounded-3xl border border-purple-500/20">
                    <BrainCircuit className="w-10 h-10 text-purple-400" />
                </div>
                <div>
                    <h1 className="text-4xl font-black text-white tracking-tight">AI Hub</h1>
                    <p className="text-gray-400 font-medium">Centro de Control de Inteligencia Artificial</p>
                </div>
                {aiActive ? (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-green-500/10 border border-green-500/20 rounded-full text-green-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                        Online
                    </div>
                ) : (
                    <div className="ml-auto flex items-center gap-2 px-4 py-1.5 bg-red-500/10 border border-red-500/20 rounded-full text-red-400 text-xs font-black uppercase tracking-widest">
                        <div className="w-2 h-2 rounded-full bg-red-500"></div>
                        Offline (Sin API Key)
                    </div>
                )}
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
                <StatCard
                    label="Libros Procesados"
                    value={stats?.total_processed || 0}
                    icon={CheckCircle}
                    color="text-emerald-400"
                    bg="bg-emerald-500/10"
                />
                <StatCard
                    label="Pendientes"
                    value={stats?.pending_optimization || 0}
                    icon={Clock}
                    color="text-amber-400"
                    bg="bg-amber-500/10"
                />
                <StatCard
                    label="Ahorro Tiempo (Hrs)"
                    value={stats?.time_saved_hours || 0}
                    icon={Sparkles}
                    color="text-purple-400"
                    bg="bg-purple-500/10"
                />
                <StatCard
                    label="Total Biblioteca"
                    value={stats?.total_books || 0}
                    icon={Database}
                    color="text-blue-400"
                    bg="bg-blue-500/10"
                />
            </div>

            {/* Action Area */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                {/* Manual Scan */}
                <div className="lg:col-span-8">
                    <div className="glass-panel p-8 rounded-[2rem] border border-white/5 bg-gradient-to-b from-white/5 to-transparent relative overflow-hidden">
                        <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-primary" />
                            Optimización Manual
                        </h3>

                        <div className="flex gap-4 mb-6">
                            <div className="relative flex-1">
                                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Pegar Hash de Serie (series_hash)..."
                                    value={scanHash}
                                    onChange={(e) => setScanHash(e.target.value)}
                                    className="w-full bg-black/20 border border-white/10 rounded-xl py-3 pl-12 pr-4 text-white placeholder-gray-500 focus:outline-none focus:border-primary/50 transition-all font-mono text-sm"
                                />
                                <button
                                    onClick={() => setShowSearch(true)}
                                    className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all text-xs font-bold uppercase tracking-wider"
                                >
                                    Buscar
                                </button>
                            </div>
                            <button
                                onClick={handleScan}
                                disabled={scanning || !scanHash || !aiActive}
                                className="bg-primary hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed text-white px-8 rounded-xl font-bold flex items-center gap-2 transition-all active:scale-95"
                            >
                                {scanning ? (
                                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        <Play className="w-4 h-4 fill-current" />
                                        Ejecutar
                                    </>
                                )}
                            </button>
                        </div>

                        {scanResult && (
                            <div className={`p-4 rounded-xl border ${scanResult.success ? 'bg-green-500/10 border-green-500/20 text-green-200' : 'bg-red-500/10 border-red-500/20 text-red-200'} animate-in slide-in-from-top-2`}>
                                <div className="flex items-center gap-2 font-bold mb-1">
                                    {scanResult.success ? <CheckCircle className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
                                    {scanResult.success ? "Éxito" : "Error"}
                                </div>
                                <p className="text-sm opacity-90">
                                    {scanResult.message}
                                </p>
                                {scanResult.updated_count !== undefined && (
                                    <p className="text-xs mt-2 opacity-70 uppercase tracking-wider font-bold">
                                        Libros actualizados: {scanResult.updated_count}
                                    </p>
                                )}
                            </div>
                        )}

                        <div className="mt-8 bg-black/20 rounded-xl p-4 border border-white/5">
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Cómo funciona</h4>
                            <p className="text-sm text-gray-500 leading-relaxed">
                                Introduce el <code>series_hash</code> de un libro (puedes verlo en la URL del detalle del libro).
                                La IA analizará un libro representativo de ese grupo, determinará el nombre canónico y normalizará toda la serie.
                            </p>
                        </div>
                    </div>
                </div>

                {/* Info Side */}
                <div className="lg:col-span-4">
                    <div className="glass-panel p-6 rounded-[2rem] border border-white/5 relative h-full flex flex-col">
                        <h3 className="text-lg font-bold text-white mb-6">Configuración de IA</h3>

                        {/* Toggle */}
                        <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/10 mb-8">
                            <div>
                                <h4 className="text-sm font-bold text-white">Escaneo Automático</h4>
                                <p className="text-[10px] text-gray-500 uppercase tracking-widest font-black mt-1">Segundo Plano</p>
                            </div>
                            <button
                                onClick={handleToggleBackgroundScan}
                                className={`w-12 h-6 rounded-full transition-all relative ${backgroundScanEnabled ? 'bg-primary shadow-[0_0_15px_-3px_rgba(59,130,246,0.5)]' : 'bg-white/10'}`}
                            >
                                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${backgroundScanEnabled ? 'left-7' : 'left-1'}`}></div>
                            </button>
                        </div>

                        <h3 className="text-xs font-black text-gray-500 uppercase tracking-[0.2em] mb-4">Notas del Jardinero</h3>
                        <ul className="space-y-4 mb-auto">
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-blue-500 shrink-0"></span>
                                La IA solo actúa sobre campos vacíos o inconsistentes en modo automático.
                            </li>
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-purple-500 shrink-0"></span>
                                El modo manual fuerza una re-evaluación del nombre de la serie.
                            </li>
                            <li className="flex gap-3 text-sm text-gray-400">
                                <span className="w-2 h-2 mt-1.5 rounded-full bg-amber-500 shrink-0"></span>
                                Las cuotas de la API Gemini se respetan automáticamente (Rate Limit).
                            </li>
                        </ul>

                        {/* Debug Info (Masked Key) */}
                        <div className="mt-8 pt-4 border-t border-white/5">
                            <p className="text-[10px] text-gray-600 font-bold uppercase tracking-widest mb-2">Estado del Sistema</p>
                            <div className="flex items-center justify-between text-[10px] font-mono">
                                <span className="text-gray-500">API Key:</span>
                                <span className={aiActive ? "text-green-500/50" : "text-red-500/50"}>{aiKeyMasked}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Proposal Modal (New) */}
            {showProposal && proposal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="w-full max-w-4xl bg-[#0a0a0c] border border-white/10 rounded-3xl overflow-hidden flex flex-col max-h-[90vh] shadow-2xl">
                        {/* Modal Header */}
                        <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                            <div>
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Sparkles className="w-5 h-5 text-purple-400" />
                                    Propuesta de Estandarización
                                </h3>
                                <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider font-bold">
                                    Confianza IA: {(proposal.confidence * 100).toFixed(0)}%
                                </p>
                            </div>
                            <button
                                onClick={() => setShowProposal(false)}
                                className="p-2 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-all"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">

                            {/* Series Name Proposal */}
                            <div className="space-y-4">
                                <div className="flex items-center justify-between">
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide">Nombre de la Serie</h4>
                                    <label className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={applyMeta}
                                            onChange={(e) => setApplyMeta(e.target.checked)}
                                            className="rounded border-white/20 bg-white/5"
                                        />
                                        Aplicar cambio
                                    </label>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20">
                                        <p className="text-xs text-red-400 font-bold uppercase mb-1">Actual</p>
                                        <p className="text-lg font-medium text-white">{proposal.current_series}</p>
                                    </div>
                                    <div className="p-4 rounded-xl bg-green-500/5 border border-green-500/20 relative">
                                        <ArrowRight className="absolute -left-5 top-1/2 -translate-y-1/2 w-6 h-6 text-gray-600 hidden md:block" />
                                        <p className="text-xs text-green-400 font-bold uppercase mb-1">Propuesto</p>
                                        <p className="text-lg font-bold text-green-100">{proposal.proposed_series}</p>
                                        {proposal.reason && (
                                            <p className="text-xs text-gray-500 mt-2 border-t border-white/5 pt-2 italic">
                                                "{proposal.reason}"
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {/* Tags Detected */}
                            {proposal.global_tags?.length > 0 && (
                                <div>
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide mb-3">Tags Detectados</h4>
                                    <div className="flex gap-2">
                                        {proposal.global_tags?.map((tag: string) => (
                                            <span key={tag} className="px-3 py-1 rounded-lg bg-blue-500/20 border border-blue-500/30 text-blue-300 text-xs font-bold">
                                                {tag}
                                            </span>
                                        ))}
                                        {proposal.is_uncensored_series && (
                                            <span className="px-3 py-1 rounded-lg bg-red-500/20 border border-red-500/30 text-red-300 text-xs font-bold">
                                                Uncensored
                                            </span>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* File Renames */}
                            <div>
                                <div className="flex items-center justify-between mb-4">
                                    <h4 className="text-sm font-bold text-gray-300 uppercase tracking-wide">
                                        Archivos a Renombrar ({approvedChanges.length}/{proposal.changes?.length || 0})
                                    </h4>
                                    <label className="flex items-center gap-2 text-xs font-bold text-primary cursor-pointer">
                                        <input
                                            type="checkbox"
                                            checked={applyRenames}
                                            onChange={(e) => setApplyRenames(e.target.checked)}
                                            className="rounded border-white/20 bg-white/5"
                                        />
                                        Habilitar Renombrado
                                    </label>
                                </div>

                                <div className="space-y-2">
                                    {proposal.changes?.map((change: any) => {
                                        const isSelected = approvedChanges.some(c => c.book_id === change.book_id);
                                        return (
                                            <div
                                                key={change.book_id}
                                                className={`p-3 rounded-lg border flex items-center gap-4 text-sm transition-all ${isSelected && applyRenames
                                                    ? 'bg-white/5 border-white/10 opacity-100'
                                                    : 'bg-black/20 border-white/5 opacity-50 grayscale'
                                                    }`}
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={() => toggleChange(change.book_id)}
                                                    disabled={!applyRenames}
                                                    className="rounded border-white/20 bg-white/5 cursor-pointer"
                                                />
                                                <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-2 md:gap-8">
                                                    <div className="text-red-300/70 truncate" title={change.current_filename}>
                                                        {change.current_filename}
                                                    </div>
                                                    <div className="text-green-300 font-mono truncate" title={change.proposed_filename}>
                                                        {change.proposed_filename}
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                        </div>

                        {/* Footer */}
                        <div className="p-6 border-t border-white/10 bg-white/5 flex justify-end gap-3">
                            <button
                                onClick={() => setShowProposal(false)}
                                className="px-6 py-3 rounded-xl font-bold text-gray-400 hover:bg-white/5 transition-all"
                            >
                                Cancelar
                            </button>
                            <button
                                onClick={handleApplyChanges}
                                disabled={processingProposal}
                                className="px-8 py-3 rounded-xl font-bold bg-primary hover:bg-primary/90 text-white flex items-center gap-2 transition-all shadow-lg shadow-primary/20"
                            >
                                {processingProposal ? (
                                    <>
                                        <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                        Aplicando...
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4" />
                                        Aplicar Cambios
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Search Modal */}
            {showSearch && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="w-full max-w-2xl bg-[#0a0a0c] border border-white/10 rounded-3xl p-6 shadow-2xl relative">
                        <button
                            onClick={() => setShowSearch(false)}
                            className="absolute top-4 right-4 text-gray-500 hover:text-white"
                        >
                            <X className="w-6 h-6" />
                        </button>

                        <h3 className="text-xl font-bold text-white mb-6">Buscar Serie</h3>

                        <div className="flex gap-4 mb-6">
                            <input
                                type="text"
                                placeholder="Nombre de la serie..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                onKeyDown={(e) => e.key === 'Enter' && runSearch()}
                                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-primary"
                                autoFocus
                            />
                            <button
                                onClick={runSearch}
                                disabled={searching}
                                className="bg-primary hover:bg-primary/90 text-white px-6 rounded-xl font-bold transition-all"
                            >
                                {searching ? "..." : "Buscar"}
                            </button>
                        </div>

                        <div className="max-h-[300px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                            {searchResults.map((s: any, idx) => (
                                <div
                                    key={idx}
                                    onClick={() => selectSeries(s)}
                                    className="p-3 rounded-xl bg-white/5 hover:bg-white/10 border border-white/5 cursor-pointer flex items-center gap-4 transition-all"
                                >
                                    {s.cover ? (
                                        <img src={s.cover} className="w-10 h-14 object-cover rounded-md" alt="" />
                                    ) : (
                                        <div className="w-10 h-14 bg-white/10 rounded-md flex items-center justify-center">
                                            <Search className="w-4 h-4 opacity-50" />
                                        </div>
                                    )}
                                    <div>
                                        <h4 className="font-bold text-white text-sm">{s.title || s.series}</h4>
                                        <p className="text-xs text-gray-500">{s.author || 'Autor desconocido'}</p>
                                        <p className="text-[10px] text-gray-600 font-mono mt-1">{s.series_hash}</p>
                                    </div>
                                    <div className="ml-auto">
                                        <ArrowRight className="w-4 h-4 text-gray-600" />
                                    </div>
                                </div>
                            ))}
                            {searchTerm && !searching && searchResults.length === 0 && (
                                <p className="text-center text-gray-500 py-8">No se encontraron resultados</p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

const StatCard = ({ label, value, icon: Icon, color, bg }: any) => (
    <div className="glass-panel p-6 rounded-3xl border border-white/5 bg-gradient-to-br from-white/5 to-transparent hover:scale-[1.02] transition-transform duration-500 group">
        <div className="flex justify-between items-start mb-4">
            <div className={`p-3 rounded-2xl ${bg} ${color} border border-white/5 group-hover:scale-110 transition-transform duration-500`}>
                <Icon className="w-6 h-6" />
            </div>
        </div>
        <div className="space-y-1">
            <h4 className="text-3xl font-black text-white tracking-tight">{value}</h4>
            <p className="text-xs font-bold text-gray-500 uppercase tracking-widest">{label}</p>
        </div>
    </div>
);
